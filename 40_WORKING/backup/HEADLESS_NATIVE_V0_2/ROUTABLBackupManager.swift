import AppKit
import Foundation
import ServiceManagement

let plist = "com.routabl.assetbackup.native.v02.plist"
let service = SMAppService.agent(plistName: plist)

if CommandLine.arguments.contains("--status") {
    print("ROUTABL_NATIVE_V02_SERVICE_STATUS=\(service.status)")
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
        window.title="라우터블 백업 자동실행 준비 v0.2"
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
            "1차 관문은 4:30 단발 진단 전용입니다. 실제 백업을 실행하는 승인 파일은 생성되지 않았습니다. " +
            "macOS 권한·SSD·NAS·복원 이미지 마운트 상태를 확인한 뒤, 추후 별도 승인과 실환경 검증으로 운영을 전환합니다.")
        explanation.font=NSFont.systemFont(ofSize:13)
        explanation.textColor = .secondaryLabelColor
        explanation.frame=NSRect(x:30,y:417,width:740,height:61)
        panel.addSubview(explanation)

        var offset:CGFloat=29
        for (text,action,width) in [
            ("안전 진단",#selector(runProbe) as Selector,CGFloat(135)),
            ("진단 에이전트 등록",#selector(registerAgent) as Selector,CGFloat(190)),
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

        let note=NSTextField(labelWithString:"상태·오류만 표시합니다. 백업 원본과 암호·복구키는 열람하거나 기록하지 않습니다.")
        note.font=NSFont.systemFont(ofSize:12)
        note.textColor = .secondaryLabelColor
        note.frame=NSRect(x:30,y:325,width:735,height:27)
        panel.addSubview(note)

        let scroll=NSScrollView(frame:NSRect(x:30,y:28,width:740,height:282))
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
            "안전 진단을 누르면 Swift 네이티브 파일 접근 검사를 실행합니다.\n" +
            "진단 에이전트를 등록하더라도 기본 상태는 DISARMED이며 백업은 실행하지 않습니다.\n"
    }
    @objc func checkStatus() {updateRegistrationStatus()}
    @objc func showSettings() {SMAppService.openSystemSettingsLoginItems()}
    @objc func runProbe() {
        let helperPath=Bundle.main.bundleURL.appendingPathComponent("Contents/MacOS/\(helper)")
        let task=Process()
        task.executableURL=helperPath
        task.arguments=["--probe"]
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
                    text.contains("PASS_NATIVE_USER_CONTEXT_ONLY")
            status.stringValue=good
                    ? "읽기 전용 진단 통과 · 실제 launchd 권한은 미검증"
                    : "읽기 전용 진단 실패 · 백업 활성화 금지"
        } catch {
            status.stringValue="진단 도구 실행 실패 · 백업 활성화 금지"
        }
    }
    @objc func registerAgent() {
        let alert=NSAlert()
        alert.messageText="진단 전용 백그라운드 작업만 등록할까요?"
        alert.informativeText="기본 비활성화 상태로 매일 오전 4:30 한 번만 접근 진단을 실행합니다. 실제 백업은 수행하지 않습니다. 등록 이후 macOS가 추가 승인을 요청할 수 있습니다."
        alert.alertStyle = .warning
        alert.addButton(withTitle:"진단 에이전트 등록")
        alert.addButton(withTitle:"취소")
        guard alert.runModal() == .alertFirstButtonReturn else {return}
        do {
            try service.register()
            report.string="진단 전용 등록 요청 완료. 시스템 설정에서 백그라운드 허용 상태를 확인하세요."
        } catch {
            report.string="등록 요청 실패. 서비스 등록 상태 및 macOS 승인 여부를 확인하세요.\n오류 분류: \(type(of:error))"
        }
        status.stringValue="등록 명령 실행 후 상태: \(service.status) · 자동 백업은 DISARMED"
    }
    @objc func unregisterAgent() {
        let alert=NSAlert()
        alert.messageText="라우터블 진단 에이전트를 등록 해제할까요?"
        alert.informativeText="라우터블 백업의 기존 성공 보관본이나 암호화 이미지는 변경하지 않습니다."
        alert.addButton(withTitle:"등록 해제")
        alert.addButton(withTitle:"취소")
        guard alert.runModal() == .alertFirstButtonReturn else {return}
        do {
            try service.unregister()
            report.string="진단 에이전트 등록 해제 요청 완료"
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
