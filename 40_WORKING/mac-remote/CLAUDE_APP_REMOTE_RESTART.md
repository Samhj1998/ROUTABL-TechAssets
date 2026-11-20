# Claude 앱 원격 재시작 (MAC-CLAUDE-RESTART-01)

## 왜
Claude 채팅이 Mac에 닿는 길은 Mac의 Claude 데스크톱 앱 하나다. 앱이 죽거나 멈추면 Claude는 스스로 앱을 다시 켤 수 없다.
밖(휴대폰)에서 이런 일이 생기면 Claude 앱과 무관한 길(ChatGPT + Desktop Commander Remote)로 다시 켠다.
2026-11 실제로 이 방법으로 재시작에 성공함(당시 명령 원문은 기록 없음 — 아래가 표준 절차).

## 경로 정리 (2026-11-21 확인)
- 평소 Mac 작업: Claude 앱 경로. Desktop Commander Remote 한도를 쓰지 않음(Remote 사용량 3,960 그대로 확인).
- 비상: ChatGPT + Remote. 매달 Remote 한도 일부를 이 용도로 남겨 둔다.

## 비상 재시작 절차 (ChatGPT + Remote에게 그대로 지시)
```
osascript -e 'quit app "Claude"'; sleep 5
pkill -f "/Applications/Claude.app/Contents/MacOS/Claude"; sleep 2
open -a "Claude"; sleep 10
ps -axo comm | grep -x "/Applications/Claude.app/Contents/MacOS/Claude" && echo 켜짐
```
- 1줄: 정상 종료 요청 / 2줄: 멈춰서 안 꺼질 때 강제 종료 / 3줄: 다시 켜기 / 4줄: 켜졌는지 확인
- 확인: 휴대폰 Claude 앱에서 Mac 연결된 채팅에 아무 말이나 보내 응답이 오면 성공

## 감시 장치 (자동, 2026-11-21)
- `claude_watchdog.sh` + `com.digitopia.claude-watchdog.plist`(~/Library/LaunchAgents에 설치)
- 5분마다 Claude 앱이 꺼져 있으면 다시 켬. 켜진 채 멈춘 경우는 못 잡음 → 그때는 위 비상 절차
- 잠시 끄기: `touch ~/.claude_watchdog_off` / 다시 켜기: `rm ~/.claude_watchdog_off`
- 기록: `~/Library/Logs/claude_watchdog.log` (다시 켤 때만 한 줄)
- 설치: `cp com.digitopia.claude-watchdog.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.digitopia.claude-watchdog.plist`
- 제거: `launchctl unload ~/Library/LaunchAgents/com.digitopia.claude-watchdog.plist` 후 파일 삭제(승인 후)
