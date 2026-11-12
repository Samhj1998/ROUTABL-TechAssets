import Foundation
import Darwin

// ROUTABL native read-only access probe. No launchd, backup, image mount, or Keychain.
struct Result: Codable {
    let phase: String
    let state: String
    let errorCode: Int?
}
struct Output: Codable {
    let result: String
    let phases: [Result]
    let backupExecuted: Bool
    let authorizationChanged: Bool
    let launchdPermissionsProven: Bool
}
let home=URL(fileURLWithPath:"/Users/yongho")
let root=home.appendingPathComponent("ROUTABL-TechAssets")
let logs=home.appendingPathComponent("Library/Logs/ROUTABL-AssetBackup")
let fm=FileManager.default
func directory(_ url:URL)throws {
    let a=try fm.attributesOfItem(atPath:url.path)
    guard a[.type] as? FileAttributeType == .typeDirectory else {throw NSError(domain:NSPOSIXErrorDomain,code:2)}
}
func regularFile(_ url:URL)throws -> Data {
    let a=try fm.attributesOfItem(atPath:url.path)
    guard a[.type] as? FileAttributeType == .typeRegular else {throw NSError(domain:NSPOSIXErrorDomain,code:2)}
    return try Data(contentsOf:url)
}
func object(_ url:URL)throws -> [String:Any] {
    guard let o=try JSONSerialization.jsonObject(with:regularFile(url)) as? [String:Any] else {
        throw NSError(domain:NSPOSIXErrorDomain,code:22)
    }
    return o
}
func latest()throws -> [String:Any] {
    let p=root.appendingPathComponent("30_REGISTRY")
    let regex=try NSRegularExpression(pattern:#"^asset_manifest_v0\.(\d+)\.json$"#)
    let files=try fm.contentsOfDirectory(at:p,includingPropertiesForKeys:nil)
    let match=files.compactMap{f -> (Int,URL)? in
        let s=f.lastPathComponent
        let r=NSRange(s.startIndex..<s.endIndex,in:s)
        guard let m=regex.firstMatch(in:s,range:r),let range=Range(m.range(at:1),in:s),
              let n=Int(s[range]) else{return nil}
        return (n,f)
    }.max(by:{$0.0<$1.0})
    guard let m=match else{throw NSError(domain:NSPOSIXErrorDomain,code:2)}
    let d=try object(m.1)
    guard d["schema_version"] as? String=="0.\(m.0)" else{throw NSError(domain:NSPOSIXErrorDomain,code:22)}
    return d
}
let steps:[(String,()throws->Void)]=[
    ("uid",{if getuid() != 501{throw NSError(domain:NSPOSIXErrorDomain,code:1)}}),
    ("home",{try directory(home)}),
    ("asset_root",{try directory(root)}),
    ("logs",{try directory(logs)}),
    ("local_receipt",{let d=try object(logs.appendingPathComponent("last_selective_v21_result.json"));if d["status"] as? String != "SUCCESS"{throw NSError(domain:NSPOSIXErrorDomain,code:22)}}),
    ("nas_receipt",{let d=try object(logs.appendingPathComponent("last_selective_nas_v21_result.json"));if d["status"] as? String != "SUCCESS"{throw NSError(domain:NSPOSIXErrorDomain,code:22)}}),
    ("registry",{let d=try latest();if (d["asset_files"] as? [Any] ?? []).count<64{throw NSError(domain:NSPOSIXErrorDomain,code:22)}}),
    ("backup_source",{_ = try regularFile(root.appendingPathComponent("00_GUIDE/ROUTABL_SelectiveSecureBackup_v2_1.py"))}),
    ("nas_source",{_ = try regularFile(root.appendingPathComponent("00_GUIDE/ROUTABL_NAS_ContentAwareBackup_v0_2.py"))}),
    ("studio_projects",{try directory(home.appendingPathComponent("StudioProjects"))}),
    ("external_ssd",{try directory(URL(fileURLWithPath:"/Volumes/SSD2TB"))}),
    ("nas_mount",{try directory(URL(fileURLWithPath:"/Volumes/Dev_Assets"))}),
    ("nas_cas",{let d=try object(URL(fileURLWithPath:"/Volumes/Dev_Assets/ROUTABL-TechAssets-Backup/snapshots/ROUTABL-Ciphertext-CAS-v0_1/manifests/CAS_ASSET_V21_20261103_214028_KST_24533.json"));if d["components"] as? Int != 141 {throw NSError(domain:NSPOSIXErrorDomain,code:22)}})
]
let simulation=CommandLine.arguments.first(where:{$0.hasPrefix("--simulate-denial=")}).map{String($0.dropFirst("--simulate-denial=".count))}
var results:[Result]=[]
var status="PASS_MANUAL_CONTEXT_ONLY"
for (phase,fn) in steps {
    do {
        if simulation==phase {throw NSError(domain:NSPOSIXErrorDomain,code:Int(EACCES))}
        try fn()
        results.append(Result(phase:phase,state:"PASS",errorCode:nil))
    } catch {
        let e=error as NSError
        results.append(Result(phase:phase,state:"FAIL_CLOSED",errorCode:e.code))
        status="BLOCKED_FIRST_FAILURE"
        break
    }
}
let output=Output(result:status,phases:results,backupExecuted:false,authorizationChanged:false,launchdPermissionsProven:false)
let coder=JSONEncoder();coder.outputFormatting=[.prettyPrinted,.sortedKeys]
if let data=try? coder.encode(output),let txt=String(data:data,encoding:.utf8){print(txt)}
exit(status=="BLOCKED_FIRST_FAILURE" ? 13:0)
