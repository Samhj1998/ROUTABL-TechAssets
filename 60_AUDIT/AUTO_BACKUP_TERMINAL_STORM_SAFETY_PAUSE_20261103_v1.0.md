# 120. Terminal 반복 창 사고 — 긴급 중지 및 검증
작성일: 2026-11-03 KST
사건: 임시 launchctl 제출 테스트의 반복 실행으로 Terminal 창이 수십 개 쌓이고 macOS의 osascript/Terminal/Google Drive/제거 가능한 볼륨/Node 권한 팝업이 반복됨.
사용자 스크린샷에서 TEST_LAUNCHD_TERMINAL_ACCESS_20261103.command (및 _v2) 제목의 다중 Terminal 창, 종료된 Python FileExistsError, [프로세스 완료됨] 확인.
사용자는 팝업 '허용'을 이미 선택했다고 설명함. 현재 재승인을 요구하지 말 것.

## 이번 응급 조치 (실제 적용)
1. gui/501/com.routabl.assetbackup.daily: launchctl bootout 성공.
2. gui/501/com.routabl.assetbackup.nas.daily: launchctl bootout 성공.
3. gui/501/com.routabl.assetbackup.drive.daily: launchctl bootout 성공.
4. 추가로 launchctl disable gui/501/<위 세 레이블> 각각 성공. print-disabled에서 세 항목 모두 disabled 확인.
5. 임시 작업 com.routabl.assetbackup.openprobe, hiddenprobe, tccprobe는 launchctl 목록에 없음.
6. ps에서 TEST_LAUNCHD_TERMINAL_ACCESS/ROUTABL_ScheduledBackup/NASReplication/DriveUpload 관련 실행 중인 프로세스 없음.
7. Terminal.app 메인 프로세스 자체는 존재하지만 기존 개인 터미널 세션 보호를 위해 강제 종료하지 않음.
8. /Volumes/ROUTABL-Secure는 마운트 해제된 상태 확인. 기존 암호화 이미지, NAS·Drive 사본, 모든 원본 보존.

## 주의
- macOS Terminal 창 여러 개는 실제 실행 중인 Python 프로세스가 아니라 완료된 테스트 창의 잔여물일 수 있음.
- 테스트 open -gj -a Terminal은 Terminal 앱을 화면 앞으로 가져오지 않도록 요청할 뿐, 새 터미널 '창'을 생성하지 않는다는 뜻이 아님. 이 설계를 무인 백업 안전성 완료라고 판단했던 것은 오류.
- 임시 launchctl submit 테스트의 KeepAlive/재실행 성질은 장기 유지 안전성을 보장하지 않음.
- macOS TCC 개인정보 보호 팝업의 허용을 반복 요청하는 구성은 폐기할 것.
- 현재 세 예약이 비활성화 상태이므로 2026-11-04 자동 백업이 수행되지 않음. 이전에 생성된 ChatGPT 점검 예약은 이러한 중지를 정확히 보고해야 함.
- 기존 .plist 파일은 삭제하지 않고 보존하되 launchctl에서 disable 상태임.
- 다음 작업은 Terminal GUI를 열지 않고, 명시적 허용된 범위에서 파일을 처리하는 검증된 단일 백그라운드 실행구조로 재설계. 비밀키/계정 토큰을 AI에게 보내거나 로그에 저장하지 않음.
- 그 전에는 GUI Terminal 경유 .command 예약을 재활성화하지 말 것.

## 사용자 화면 정리
수동으로 진행 중인 중요한 Terminal 작업이 없는 경우 Terminal 앱의 Command+Q로 완료된 창을 한꺼번에 닫아도 됨.
맥 계정 내 다른 Terminal 작업이 있다면 그 창은 보존하고 완료된 시험 창만 닫을 것.
