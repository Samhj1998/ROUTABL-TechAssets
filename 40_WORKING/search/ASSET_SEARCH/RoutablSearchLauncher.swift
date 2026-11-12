import AppKit
import Foundation

// A user-clicked launcher. Never installs LaunchAgents, invokes Terminal.app,
// or changes source code, backups, GitHub, or Firebase.
private let store = FileManager.default.homeDirectoryForCurrentUser
    .appendingPathComponent("Library/Application Support/ROUTABL-AssetSearch")
private let service = store.appendingPathComponent("routabl_search_v1_4_service.py")
private let index = store.appendingPathComponent("assets_v1_4.sqlite")
private let base = "http://127.0.0.1:8768"

private func serviceReady() -> Bool {
    let probe = Process()
    probe.executableURL = URL(fileURLWithPath: "/usr/bin/curl")
    probe.arguments = ["--silent", "--fail", "--max-time", "1", "--noproxy", "*",
                       "--url", base + "/api/status"]
    let output = Pipe()
    probe.standardOutput = output
    probe.standardError = FileHandle.nullDevice
    do {
        try probe.run()
        probe.waitUntilExit()
        let bytes = output.fileHandleForReading.readDataToEndOfFile()
        let str = String(data: bytes, encoding: .utf8) ?? ""
        return probe.terminationStatus == 0 &&
               str.contains("ROUTABL_ASSET_SEARCH_V1_4")
    } catch {
        return false
    }
}

private func launch() throws {
    let python = Process()
    python.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
    python.arguments = [service.path, "serve"]
    python.standardInput = FileHandle.nullDevice
    python.standardOutput = FileHandle.nullDevice
    python.standardError = FileHandle.nullDevice
    try python.run()
    // Python has an exclusive flock on startup. A second Finder click cannot
    // start a second service even if both launches race.
}

private func showError(_ explanation: String) {
    NSApplication.shared.setActivationPolicy(.regular)
    let box = NSAlert()
    box.messageText = "라우터블 검색을 열지 못했습니다"
    box.informativeText = explanation
    box.alertStyle = .warning
    box.addButton(withTitle: "확인")
    box.runModal()
}

if CommandLine.arguments.contains("--self-test") {
    let ok = FileManager.default.fileExists(atPath: service.path) &&
             FileManager.default.fileExists(atPath: index.path)
    print(ok ? "ROUTABL_LAUNCHER_SELF_TEST_OK" : "ROUTABL_LAUNCHER_SELF_TEST_FAILED")
    exit(ok ? 0 : 1)
}

if !FileManager.default.fileExists(atPath: service.path) {
    showError("검색 서비스 파일을 찾을 수 없습니다. 개발 기록을 확인하세요.")
    exit(2)
}

// No Dock icon or terminal window for the normal click operation.
NSApplication.shared.setActivationPolicy(.accessory)
if !serviceReady() {
    do {
        try launch()
    } catch {
        showError("로컬 검색 서비스를 시작할 수 없습니다.")
        exit(3)
    }
}
var ready = false
for _ in 0..<60 {
    if serviceReady() {
        ready = true
        break
    }
    Thread.sleep(forTimeInterval: 0.15)
}
if ready, let page = URL(string: base + "/") {
    if CommandLine.arguments.contains("--integration-test") {
        // Exercise the packaged app launch path without modifying the user's browser.
        print("ROUTABL_LAUNCHER_INTEGRATION_OK")
    } else if !NSWorkspace.shared.open(page) {
        showError("기본 브라우저에서 검색 화면을 열지 못했습니다.")
        exit(4)
    }
} else {
    showError("검색 서버 준비 상태를 확인하지 못했습니다. 8768 포트 상태를 점검하세요.")
    exit(5)
}
