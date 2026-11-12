import Foundation
import Darwin
import CryptoKit

// ROUTABL native LaunchAgent v0.3.
// Fail-closed: no protected network/SSD access or Keychain lookup unless
// explicit local approval exists; no GUI auto-clicks, no password handling.
// A real scheduled backup is NEVER started unless Python policy approves
// and native stage-gated, timeout-bounded preflight finishes successfully.

let home = URL(fileURLWithPath:"/Users/yongho")
let log = home.appendingPathComponent("Library/Logs/ROUTABL-AssetBackup")
let approval = home.appendingPathComponent("Library/Application Support/ROUTABL-AssetBackup/approval_v01.json")
let python = URL(fileURLWithPath:"/usr/bin/python3")
let supervisor = home.appendingPathComponent("ROUTABL-TechAssets/00_GUIDE/ROUTABL_BackupHeadlessSupervisor_v0_2.py")
let expectedSupervisorSHA256 = "49a1533b22a166715bd606c3c151f89d24752c653c5c119f5107267af640f878"
let statusURL = log.appendingPathComponent("last_native_launchagent_v03.json")

struct RunResult {
    let outcome:String
    let elapsed:Double
    let exitCode:Int32
}

func runTimed(_ program:URL, _ arguments:[String], deadline:TimeInterval,
              limitOutput:Bool = false) -> RunResult {
    let task=Process()
    task.executableURL=program
    task.arguments=arguments
    task.standardInput=FileHandle.nullDevice
    task.standardOutput=FileHandle.nullDevice
    task.standardError=FileHandle.nullDevice
    let begin=Date()
    do {
        try task.run()
    } catch {
        return RunResult(outcome:"CHILD_LAUNCH_FAILED",elapsed:0,exitCode:70)
    }
    while task.isRunning && Date().timeIntervalSince(begin)<deadline {
        Thread.sleep(forTimeInterval:0.1)
    }
    if task.isRunning {
        task.terminate()
        let grace=Date()
        while task.isRunning && Date().timeIntervalSince(grace)<2.0 {
            Thread.sleep(forTimeInterval:0.1)
        }
        if task.isRunning {
            kill(task.processIdentifier,SIGKILL)
        }
        return RunResult(outcome:"TIMEOUT_CHILD_TERMINATED",
                         elapsed:Date().timeIntervalSince(begin),exitCode:124)
    }
    let rc=task.terminationStatus
    return RunResult(outcome:rc==0 ? "CHILD_EXIT_ZERO" : "CHILD_NONZERO",
                     elapsed:Date().timeIntervalSince(begin),exitCode:rc)
}

struct Event: Codable {
    let kind:String
    let at:String
    let state:String
    let phase:String
    let backupAttempted:Bool
    let networkVolumeAccessAttempted:Bool
    let permissionsModified:Bool
    let launchAgentRegistrationChanged:Bool
    let childExitCode:Int32?
    let elapsedSeconds:Double?
}
func writeStatus(_ state:String,_ phase:String,backupAttempted:Bool = false,
                 networkAccess:Bool = false,child:RunResult? = nil) {
    let iso=ISO8601DateFormatter().string(from:Date())
    let data=Event(kind:"ROUTABL_NATIVE_LAUNCHAGENT_V03",at:iso,state:state,
                   phase:phase,backupAttempted:backupAttempted,
                   networkVolumeAccessAttempted:networkAccess,
                   permissionsModified:false,launchAgentRegistrationChanged:false,
                   childExitCode:child?.exitCode,
                   elapsedSeconds:child.map {Double(Int($0.elapsed*10))/10})
    let encoder=JSONEncoder()
    encoder.outputFormatting=[.sortedKeys,.prettyPrinted]
    guard let value=try? encoder.encode(data) else {return}
    do {
        let fm=FileManager.default
        var directory:ObjCBool = false
        guard fm.fileExists(atPath:log.path,isDirectory:&directory) && directory.boolValue else {
            throw NSError(domain:NSPOSIXErrorDomain,code:Int(ENOENT))
        }
        let temporary=log.appendingPathComponent(".last_native_v03_\(getpid()).json.partial")
        if fm.fileExists(atPath:temporary.path) {
            throw NSError(domain:NSPOSIXErrorDomain,code:Int(EEXIST))
        }
        guard fm.createFile(atPath:temporary.path,
                            contents:value,attributes:[.posixPermissions:384]) else {
            throw NSError(domain:NSPOSIXErrorDomain,code:Int(EACCES))
        }
        if Darwin.rename(temporary.path,statusURL.path) != 0 {
            throw NSError(domain:NSPOSIXErrorDomain,code:Int(errno))
        }
    } catch {
        print("LOCAL_STATUS_WRITE_FAILED_CLASS_\(type(of:error))")
    }
    print("\(data.state) / \(data.phase)")
}
let cmd=CommandLine.arguments.dropFirst().first ?? "--scheduled"
if getuid() != 501 || geteuid() != 501 {
    writeStatus("BLOCKED_UID","local_identity")
    exit(3)
}
if cmd=="--local-probe" {
    let safe=FileManager.default.fileExists(atPath:supervisor.path)
    writeStatus(safe ? "LOCAL_SAFE_ACCESS_OK" : "BLOCKED_LOCAL_SCRIPT_MISSING",
                "manual_readonly")
    exit(safe ? 0 : 4)
}
if cmd=="--watchdog-selftest" {
    let r=runTimed(URL(fileURLWithPath:"/bin/sleep"),["5"],deadline:0.6)
    let pass=r.outcome=="TIMEOUT_CHILD_TERMINATED" && r.elapsed<4.0
    writeStatus(pass ? "WATCHDOG_TIMEOUT_TEST_PASS":"WATCHDOG_TEST_FAILED",
                "isolated_sleep",child:r)
    exit(pass ? 0 : 7)
}
if cmd != "--scheduled" {
    writeStatus("BLOCKED_UNKNOWN_MODE","arguments")
    exit(2)
}

// No network, no volume checks, no Python subprocess before this condition.
if !FileManager.default.fileExists(atPath:approval.path) {
    writeStatus("DISARMED_NO_APPROVAL","local_policy")
    exit(0)
}
guard let supervisorData=try? Data(contentsOf:supervisor),
      SHA256.hash(data:supervisorData).map({String(format:"%02x",$0)}).joined()==expectedSupervisorSHA256 else {
    writeStatus("DISARMED_SUPERVISOR_HASH_CHANGED","local_integrity")
    exit(5)
}
writeStatus("POLICY_FILE_PRESENT","local_preflight")
// Step 1: use bounded child to check approved policy AND network/SSD access.
// A TCC permission sheet may block a child open(), but cannot hang parent.
let probe=runTimed(python,[supervisor.path,"probe"],deadline:20)
if probe.exitCode != 0 {
    let reason=probe.exitCode==124 ? "PROBE_TIMEOUT_NO_RETRY" : "PROBE_NOT_APPROVED_OR_BLOCKED"
    writeStatus(reason,"preflight",networkAccess:true,child:probe)
    exit(9)
}
// Step 2: actual backup only through same-UID, SHA-pinned supervisor.
// Hard upper limit includes network transfer and full verification.
// Supervisor must terminate its own children on its 2600s timeout.
writeStatus("APPROVED_PROBE_PASSED","prebackup",networkAccess:true)
let backupStarted=Date()
let run=runTimed(python,[supervisor.path,"scheduled"],deadline:2750)
if run.exitCode != 0 {
    writeStatus(run.exitCode==124 ? "BACKUP_TIMEOUT_NO_RETRY":"BACKUP_FAILED_NO_RETRY",
                "backup",backupAttempted:true,networkAccess:true,child:run)
    exit(11)
}
let supervisorStatus=log.appendingPathComponent("last_native_backup_supervisor_v02.json")
var verified=false
if let data=try? Data(contentsOf:supervisorStatus),
   let record=try? JSONSerialization.jsonObject(with:data) as? [String:Any],
   record["state"] as? String == "SUCCESS_VERIFIED",
   record["actual_backup_success"] as? Bool == true,
   let stamp=record["date_kst"] as? String,
   let time=ISO8601DateFormatter().date(from:stamp) {
    verified=time.timeIntervalSince(backupStarted)>=(-3.0)
}
if !verified {
    writeStatus("BACKUP_RECEIPT_NOT_CURRENT_OR_NOT_SUCCESS","postbackup",
                backupAttempted:true,networkAccess:true,child:run)
    exit(12)
}
writeStatus("BACKUP_VERIFIED_RECEIPT_CURRENT","postbackup",
            backupAttempted:true,networkAccess:true,child:run)
exit(0)
