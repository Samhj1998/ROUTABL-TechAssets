import AppKit
import Foundation
import ServiceManagement

let plist = "com.routabl.assetbackup.native.v042.plist"
let service = SMAppService.agent(plistName: plist)

if CommandLine.arguments.contains("--status") {
    print("ROUTABL_NATIVE_SAFE_SERVICE_STATUS=\(service.status)")
    print("AUTOMATIC_BACKUP_APPROVED=false")
    exit(0)
}

final class Manager: NSObject, NSApplicationDelegate {
    var window:NSWindow!
    var status:NSTextField!
    var report:NSTextView!
    let helper="ROUTABLBackupAgent"
    func applicationDidFinishLaunching(_ note:Notification) {
        let size=NSRect(x:0,y:0,width:800,height:580)
        window=NSWindow(contentRect:size,
                        styleMask:[.titled,.closable,.miniaturizable],
                        backing:.buffered,defer:false)
        window.title="라우터블 백업 권한·안전관리 v0.4.2"
        window.center()
        window.isReleasedWhenClosed=false
        let panel=NSView(frame:size)
        window.contentView=panel

        let heading=NSTextField(labelWithString:"라우터블 Mac → NAS 자동 백업")
        heading.font=NSFont.boldSystemFont(ofSize:25)
        heading.frame=NSRect(x:28,y:515,width:735,height:34)
        panel.addSubview(heading)

        status=NSTextField(labelWithString:"진단 전용 · 실제 자동 백업은 승인 전 비활성화")
        status.font=NSFont.systemFont(ofSize:14,weight:.medium)
        status.frame=NSRect(x:30,y:483,width:740,height:28)
        panel.addSubview(status)

        let explanation=NSTextField(wrappingLabelWithString:
            "자동 백업 승인은 계속 꺼져 있습니다. NAS 접근 권한은 별도의 읽기 전용 시험으로만 확인합니다. " +
            "시험 동의 후 macOS가 네트워크 볼륨 권한을 요청할 수 있습니다. 실제 백업은 시험 중에도 실행되지 않습니다.")
        explanation.font=NSFont.systemFont(ofSize:13)
        explanation.textColor = .secondaryLabelColor
        explanation.frame=NSRect(x:30,y:417,width:740,height:61)
        panel.addSubview(explanation)

        var offset:CGFloat=29
        for (text,action,width) in [
            ("로컬 안전 진단",#selector(runProbe) as Selector,CGFloat(135)),
            ("안전 에이전트 등록",#selector(registerAgent) as Selector,CGFloat(190)),
            ("등록 해제",#selector(unregisterAgent) as Selector,CGFloat(125)),
            ("등록 상태",#selector(checkStatus) as Selector,CGFloat(122)),
            ("macOS 설정",#selector(showSettings) as Selector,CGFloat(145))
        ] {
            let b=NSButton(title:text,target:self,action:action)
            b.frame=NSRect(x:offset,y:364,width:width,height:35)
            b.bezelStyle = .rounded
            panel.addSubview(b)
            offset += width+4
        }

        let consent=NSButton(title:"NAS·SSD 접근 시험 동의 (백업 없음)",
                 target:self,action:#selector(consentDiagnostic))
        consent.bezelStyle = .rounded
        consent.frame=NSRect(x:30,y:317,width:340,height:35)
        panel.addSubview(consent)
        let revoke=NSButton(title:"접근 시험 동의 취소",
                 target:self,action:#selector(revokeDiagnostic))
        revoke.bezelStyle = .rounded
        revoke.frame=NSRect(x:386,y:317,width:195,height:35)
        panel.addSubview(revoke)

        let note=NSTextField(labelWithString:"상태·오류만 표시합니다. 백업 원본과 암호·복구키는 열람하거나 기록하지 않습니다.")
        note.font=NSFont.systemFont(ofSize:12)
        note.textColor = .secondaryLabelColor
        note.frame=NSRect(x:30,y:282,width:735,height:27)
        panel.addSubview(note)

        let scroll=NSScrollView(frame:NSRect(x:30,y:28,width:740,height:244))
        scroll.hasVerticalScroller=true
        scroll.borderType = .bezelBorder
        report=NSTextView(frame:scroll.bounds)
        report.isEditable=false
        report.isSelectable=true
        report.font=NSFont.monospacedSystemFont(ofSize:12,weight:.regular)
        scroll.documentView=report
        panel.addSubview(scroll)

        updateRegistrationStatus()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps:true)
    }
    func updateRegistrationStatus() {
        let state=String(describing:service.status)
        status.stringValue="LaunchAgent 등록 상태: \(state) · 실제 백업 승인 파일 없음"
        report.string="현재: \(state)\n\n" +
            "로컬 로컬 안전 진단은 NAS·SSD 접근을 시도하지 않습니다.\n" +
            "승인 파일이 없으면 등록돼도 NAS에 접근하지 않고 종료합니다.\n"
    }
    private func diagnosticConsentURL() -> URL {
        URL(fileURLWithPath:
            "/Users/yongho/Library/Application Support/ROUTABL-AssetBackup/diagnostic_consent_v01.json")
    }
    @objc func consentDiagnostic() {
        let alert=NSAlert()
        alert.messageText="NAS·SSD 읽기 전용 접근 시험을 승인하시겠습니까?"
        alert.informativeText="에이전트가 네트워크 볼륨과 외장 SSD 폴더 이름을 확인하기만 합니다. 백업, 복호화, 파일 복사는 하지 않습니다. macOS의 별도 접근 권한 요청은 사용자 본인이 직접 판단해야 합니다."
        alert.alertStyle = .informational
        alert.addButton(withTitle:"접근 시험만 동의")
        alert.addButton(withTitle:"취소")
        guard alert.runModal() == .alertFirstButtonReturn else {return}
        let p=diagnosticConsentURL()
        do {
            if FileManager.default.fileExists(atPath:p.path) {
                report.string="이미 진단 동의 파일이 존재합니다. 먼저 취소 후 다시 진행해 주세요."
                return
            }
            let parent=p.deletingLastPathComponent()
            try FileManager.default.createDirectory(at:parent,withIntermediateDirectories:true,
                attributes:[.posixPermissions:448])
            let obj:[String:Any]=[
                "version":1,"owner_uid":501,"enabled":true,
                "scope":"TCC_METADATA_READ_ONLY","backup_enabled":false
            ]
            let bytes=try JSONSerialization.data(withJSONObject:obj,options:[.sortedKeys])
            guard FileManager.default.createFile(atPath:p.path,contents:bytes,
                attributes:[.posixPermissions:384]) else {
                throw NSError(domain:NSPOSIXErrorDomain,code:13)
            }
            report.string="읽기 전용 접근 시험 동의가 저장됐습니다. 실제 백업 승인은 없습니다. 백그라운드 단발 시험에서 OS 권한 창이 나올 수 있습니다."
            status.stringValue="TCC 접근 시험만 승인됨 · 실제 백업은 비활성화"
        } catch {
            report.string="진단 동의 생성 실패. 파일 접근 상태를 확인하십시오."
        }
    }
    @objc func revokeDiagnostic() {
        let p=diagnosticConsentURL()
        do {
            if FileManager.default.fileExists(atPath:p.path) {
                try FileManager.default.removeItem(at:p)
            }
            report.string="읽기 전용 진단 동의를 취소했습니다. 실제 자동 백업은 변함없이 비활성화 상태입니다."
            status.stringValue="진단 동의 취소됨 · 자동 백업 비활성화"
        } catch {
            report.string="진단 동의 취소 실패. 추가 확인 필요."
        }
    }
    @objc func checkStatus() {updateRegistrationStatus()}
    @objc func showSettings() {SMAppService.openSystemSettingsLoginItems()}
    @objc func runProbe() {
        let helperPath=Bundle.main.bundleURL.appendingPathComponent("Contents/MacOS/\(helper)")
        let task=Process()
        task.executableURL=helperPath
        task.arguments=["--local-probe"]
        task.standardInput=FileHandle.nullDevice
        let out=Pipe()
        task.standardOutput=out
        task.standardError=FileHandle.nullDevice
        do {
            try task.run()
            task.waitUntilExit()
            let data=out.fileHandleForReading.readDataToEndOfFile()
            let text=String(data:data,encoding:.utf8) ?? "결과를 읽을 수 없습니다."
            report.string=text
            let good=task.terminationStatus==0 &&
                    text.contains("LOCAL_SAFE_ACCESS_OK")
            status.stringValue=good
                    ? "로컬 진단 통과 · NAS 권한 별도 승인 필요"
                    : "읽기 전용 진단 실패 · 백업 활성화 금지"
        } catch {
            status.stringValue="진단 도구 실행 실패 · 백업 활성화 금지"
        }
    }
    @objc func registerAgent() {
        let policy=URL(fileURLWithPath:"/Users/yongho/Library/Application Support/ROUTABL-AssetBackup/approval_v01.json")
        if FileManager.default.fileExists(atPath:policy.path) {
            status.stringValue="실제 백업 승인 파일 존재 · 새 에이전트 등록 중단"
            report.string="승인 파일이 존재하므로 미검증 에이전트를 등록하지 않습니다."
            return
        }
        let alert=NSAlert()
        alert.messageText="미승인 안전 에이전트를 등록할까요?"
        alert.informativeText="오전 4:30 한 번 실행하지만 승인 파일이 없으면 NAS에 접근하지 않고 종료합니다. 실제 자동 백업은 별도 승인과 검증 후 활성화합니다."
        alert.alertStyle = .warning
        alert.addButton(withTitle:"안전 에이전트 등록")
        alert.addButton(withTitle:"취소")
        guard alert.runModal() == .alertFirstButtonReturn else {return}
        do {
            try service.register()
            report.string="미승인 안전 에이전트 등록 요청 완료. 시스템 설정에서 상태를 확인하세요."
        } catch {
            report.string="등록 요청 실패. 서비스 등록 상태 및 macOS 승인 여부를 확인하세요.\n오류 분류: \(type(of:error))"
        }
        status.stringValue="등록 명령 실행 후 상태: \(service.status) · 자동 백업은 DISARMED"
    }
    @objc func unregisterAgent() {
        let alert=NSAlert()
        alert.messageText="라우터블 안전 에이전트 등록을 해제할까요?"
        alert.informativeText="라우터블 백업의 기존 성공 보관본이나 암호화 이미지는 변경하지 않습니다."
        alert.addButton(withTitle:"등록 해제")
        alert.addButton(withTitle:"취소")
        guard alert.runModal() == .alertFirstButtonReturn else {return}
        do {
            try service.unregister()
            report.string="안전 에이전트 등록 해제 요청 완료"
        } catch {
            report.string="등록 해제 오류. 시스템 설정을 확인해 주세요."
        }
        status.stringValue="등록 상태: \(service.status)"
    }
}
let application=NSApplication.shared
let delegate=Manager()
application.delegate=delegate
application.setActivationPolicy(.regular)
application.run()
