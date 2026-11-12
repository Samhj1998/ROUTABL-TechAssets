import AppKit
import Foundation
import ServiceManagement

final class BackupDiagnosticDelegate: NSObject, NSApplicationDelegate {
    private var window: NSWindow!
    private let output = NSTextView(frame: .zero)
    private let status = NSTextField(labelWithString: "안전 상태: 예약 백업 중지 / 진단 전용")
    private var diagnosisButton: NSButton!

    func applicationDidFinishLaunching(_ notification: Notification) {
        let frame = NSRect(x:0,y:0,width:750,height:515)
        window=NSWindow(contentRect:frame,styleMask:[.titled,.closable,.miniaturizable],
                        backing:.buffered,defer:false)
        window.title="라우터블 백업 진단 v0.1"
        window.center()
        window.isReleasedWhenClosed=false
        let content=NSView(frame:frame)
        window.contentView=content
        let title=NSTextField(labelWithString:"라우터블 기술자산 백업 · 안전 진단")
        title.font=NSFont.boldSystemFont(ofSize:23)
        title.frame=NSRect(x:28,y:452,width:680,height:36)
        content.addSubview(title)

        status.font=NSFont.systemFont(ofSize:13)
        status.textColor = .secondaryLabelColor
        status.frame=NSRect(x:30,y:418,width:682,height:24)
        content.addSubview(status)

        diagnosisButton=NSButton(title:"13단계 읽기 전용 진단 실행",target:self,action:#selector(runDiagnosis))
        diagnosisButton.bezelStyle = .rounded
        diagnosisButton.frame=NSRect(x:26,y:370,width:235,height:34)
        content.addSubview(diagnosisButton)

        let settings=NSButton(title:"macOS 백그라운드 설정 확인",target:self,action:#selector(openBackgroundSettings))
        settings.bezelStyle = .rounded
        settings.frame=NSRect(x:266,y:370,width:250,height:34)
        content.addSubview(settings)

        let notes=NSTextField(wrappingLabelWithString:
            "이 앱은 접근 상태 확인만 수행합니다. AES 이미지 마운트·복호화·NAS 복제·예약 설치·권한 변경은 하지 않습니다. " +
            "진단 성공은 무인 실행 권한을 보증하지 않으며, 예약 활성화는 별도 승인과 실환경 시험이 필요합니다.")
        notes.font=NSFont.systemFont(ofSize:12)
        notes.textColor = .secondaryLabelColor
        notes.frame=NSRect(x:30,y:312,width:690,height:49)
        content.addSubview(notes)

        let scroll=NSScrollView(frame:NSRect(x:30,y:32,width:690,height:268))
        scroll.borderType = .bezelBorder
        scroll.hasVerticalScroller=true
        output.isEditable=false
        output.isSelectable=true
        output.font=NSFont.monospacedSystemFont(ofSize:11,weight:.regular)
        output.string="상단 '13단계 읽기 전용 진단 실행'을 클릭하면 접근 단계별 결과가 여기에 표시됩니다.\n\n" +
            "기존 로컬/NAS/Google Drive 백업 예약은 이 앱으로 켤 수 없습니다."
        scroll.documentView=output
        content.addSubview(scroll)
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps:true)
    }

    @objc private func openBackgroundSettings() {
        SMAppService.openSystemSettingsLoginItems()
    }

    @objc private func runDiagnosis() {
        diagnosisButton.isEnabled=false
        status.stringValue="진단 중... 실제 백업은 실행하지 않습니다."
        let helper=Bundle.main.bundleURL.appendingPathComponent("Contents/MacOS/RoutablNativeAccessProbe")
        DispatchQueue.global(qos:.userInitiated).async { [weak self] in
            let task=Process()
            task.executableURL=helper
            let stdout=Pipe()
            let stderr=Pipe()
            task.standardOutput=stdout
            task.standardError=stderr
            task.standardInput=FileHandle.nullDevice
            var result="진단 실행 실패. 앱에 파일 접근 권한이 있는지 확인하십시오."
            var passed=false
            do {
                try task.run()
                task.waitUntilExit()
                let data=stdout.fileHandleForReading.readDataToEndOfFile()
                if let text=String(data:data,encoding:.utf8),!text.isEmpty {
                    result=text
                }
                passed=(task.terminationStatus==0 && result.contains("PASS_MANUAL_CONTEXT_ONLY"))
            } catch {
                result="진단 도구 실행 실패 (구체적 경로·인증정보 비출력)."
            }
            DispatchQueue.main.async {
                self?.diagnosisButton.isEnabled=true
                self?.status.stringValue=passed
                    ? "읽기 전용 접근 통과 · 무인 백업 권한은 아직 별도 검증 필요"
                    : "접근 항목 오류 · 자동 백업 활성화 금지"
                self?.output.string=result
            }
        }
    }
}
let app=NSApplication.shared
let delegate=BackupDiagnosticDelegate()
app.delegate=delegate
app.setActivationPolicy(.regular)
app.run()
