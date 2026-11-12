import Foundation
import Darwin

// Native one-shot preflight. No login-item registration and no secret access.
// The scheduled program calls the fail-closed Python supervisor, which by
// default is DISARMED and NEVER performs a backup without explicit approval.
struct Observation: Codable {
    let stage: String
    let state: String
    let errno: Int?
}
struct Summary: Codable {
    let kind: String
    let state: String
    let stages: [Observation]
    let backupAttemptedByNativePreflight: Bool
    let launchAgentRegistrationChanged: Bool
    let permissionChanged: Bool
}

let home = URL(fileURLWithPath: "/Users/yongho")
let root = home.appendingPathComponent("ROUTABL-TechAssets")
let logs = home.appendingPathComponent("Library/Logs/ROUTABL-AssetBackup")
let ssd = URL(fileURLWithPath: "/Volumes/SSD2TB")
let nas = URL(fileURLWithPath: "/Volumes/Dev_Assets")
let supervisor = root.appendingPathComponent("00_GUIDE/ROUTABL_BackupHeadlessSupervisor_v0_1.py")
let mode = CommandLine.arguments.dropFirst().first ?? "--scheduled"
let denied = CommandLine.arguments.first(where: { $0.hasPrefix("--simulate-denial=") })
    .map { String($0.dropFirst("--simulate-denial=".count)) }

func requireDirectory(_ url: URL) throws {
    let attrs = try FileManager.default.attributesOfItem(atPath:url.path)
    guard attrs[.type] as? FileAttributeType == .typeDirectory else {
        throw NSError(domain:NSPOSIXErrorDomain,code:2)
    }
}
func requireFile(_ url: URL) throws {
    let attrs = try FileManager.default.attributesOfItem(atPath:url.path)
    guard attrs[.type] as? FileAttributeType == .typeRegular else {
        throw NSError(domain:NSPOSIXErrorDomain,code:2)
    }
    // Deliberately read a bounded amount. No source code is executed here.
    let h=try FileHandle(forReadingFrom:url)
    defer {try? h.close()}
    guard let bytes=try h.read(upToCount:32), !bytes.isEmpty else {
        throw NSError(domain:NSPOSIXErrorDomain,code:22)
    }
}
let steps:[(String,()throws->Void)]=[
    ("uid_501", {
        guard getuid()==501 && geteuid()==501 else {
            throw NSError(domain:NSPOSIXErrorDomain,code:1)
        }
    }),
    ("home_directory",{try requireDirectory(home)}),
    ("asset_directory",{try requireDirectory(root)}),
    ("logs_directory",{try requireDirectory(logs)}),
    ("state_receipt",{try requireFile(logs.appendingPathComponent("last_selective_v21_result.json"))}),
    ("supervisor_file",{try requireFile(supervisor)}),
    ("ssd_directory",{try requireDirectory(ssd)}),
    ("nas_directory",{try requireDirectory(nas)})
]
var stages:[Observation]=[]
var blocked=false
for (name,work) in steps {
    do {
        if denied==name {throw NSError(domain:NSPOSIXErrorDomain,code:Int(EACCES))}
        try work()
        stages.append(Observation(stage:name,state:"PASS",errno:nil))
    } catch {
        let e=error as NSError
        stages.append(Observation(stage:name,state:"BLOCKED_FIRST_ERROR",errno:e.code))
        blocked=true
        break
    }
}

func printSummary(_ state:String) {
    let report=Summary(kind:"ROUTABL_NATIVE_BACKUP_AGENT_V02",
                       state:state,stages:stages,
                       backupAttemptedByNativePreflight:false,
                       launchAgentRegistrationChanged:false,
                       permissionChanged:false)
    let writer=JSONEncoder()
    writer.outputFormatting=[.sortedKeys]
    if let data=try? writer.encode(report),let string=String(data:data,encoding:.utf8) {
        print(string)
    }
}
if blocked {
    printSummary("BLOCKED_NATIVE_FIRST_ERROR")
    exit(13)
}
if mode=="--probe" {
    printSummary("PASS_NATIVE_USER_CONTEXT_ONLY")
    exit(0)
}
if mode=="--scheduled" {
    // Never inherit stdin for passwords; do not display child stdout/stderr.
    let child=Process()
    child.executableURL=URL(fileURLWithPath:"/usr/bin/python3")
    child.arguments=[supervisor.path,"scheduled"]
    child.standardInput=FileHandle.nullDevice
    child.standardOutput=FileHandle.nullDevice
    child.standardError=FileHandle.nullDevice
    do {
        try child.run()
        child.waitUntilExit()
        let rc=child.terminationStatus
        printSummary(rc==0 ? "SUPERVISOR_EXECUTED_SINGLE_ATTEMPT" : "SUPERVISOR_BLOCKED_OR_FAILED")
        exit(rc)
    } catch {
        printSummary("SUPERVISOR_COULD_NOT_START")
        exit(8)
    }
}
printSummary("UNSUPPORTED_ARGUMENT_NO_ACTION")
exit(4)
