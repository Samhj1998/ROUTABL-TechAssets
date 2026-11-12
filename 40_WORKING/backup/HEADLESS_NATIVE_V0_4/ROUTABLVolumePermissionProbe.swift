import Foundation
import Darwin

// ROUTABL permission-only probe v0.4. NO backup and NO write operations.
// This is started as a bounded subprocess of the SMAppService LaunchAgent.
// It checks limited metadata only, not personal file contents.
struct Item: Codable {let stage:String;let result:String;let errorNumber:Int?}
struct Outcome: Codable {
    let kind:String
    let state:String
    let checks:[Item]
    let filesCopied:Int
    let backupAttempted:Bool
    let permissionsModified:Bool
}

let fileManager=FileManager.default
let locations:[
    (String,String,Bool)
] = [
    ("external_ssd", "/Volumes/SSD2TB", true),
    ("local_encrypted_backup_bundle","/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle",true),
    ("nas_share","/Volumes/Dev_Assets",true),
    ("nas_cas_manifests","/Volumes/Dev_Assets/ROUTABL-TechAssets-Backup/snapshots/ROUTABL-Ciphertext-CAS-v0_1/manifests",true)
]
var results:[Item]=[]
func check(_ name:String,_ path:String,_ directory:Bool)throws {
    let attrs=try fileManager.attributesOfItem(atPath:path)
    guard attrs[.type] as? FileAttributeType == .typeDirectory else {
        throw NSError(domain:NSPOSIXErrorDomain,code:Int(ENOTDIR))
    }
    // Directory enumeration is the actual privacy-sensitive operation. Don't
    // request any file data; use bounded parent watchdog to avoid indefinite
    // NAS SMB or TCC UI waiting.
    _ = try fileManager.contentsOfDirectory(atPath:path).prefix(3)
}
if getuid() != 501 || geteuid() != 501 {
    let v=Outcome(kind:"ROUTABL_TCC_METADATA_PROBE_V04",
                  state:"UID_NOT_APPROVED",checks:[],filesCopied:0,
                  backupAttempted:false,permissionsModified:false)
    let writer=JSONEncoder()
    if let data=try? writer.encode(v),let msg=String(data:data,encoding:.utf8) {print(msg)}
    exit(3)
}
var good=true
for (name,path,isdir) in locations {
    do {
        try check(name,path,isdir)
        results.append(Item(stage:name,result:"PASS",errorNumber:nil))
    } catch {
        let failure=error as NSError
        results.append(Item(stage:name,result:"BLOCKED_FIRST_ERROR",errorNumber:failure.code))
        good=false
        break
    }
}
let status=good ? "PASS_METADATA_READ_ONLY" : "BLOCKED_PERMISSION_OR_STORAGE"
let value=Outcome(kind:"ROUTABL_TCC_METADATA_PROBE_V04",state:status,checks:results,
                  filesCopied:0,backupAttempted:false,permissionsModified:false)
let coder=JSONEncoder();coder.outputFormatting=[.sortedKeys]
if let data=try? coder.encode(value),let output=String(data:data,encoding:.utf8){print(output)}
exit(good ? 0 : 4)
