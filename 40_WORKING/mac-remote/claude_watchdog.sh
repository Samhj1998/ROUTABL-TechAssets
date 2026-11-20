#!/bin/zsh
# Claude 앱 감시 장치: 5분마다(launchd) Claude 앱이 떠 있는지 보고, 꺼져 있으면 다시 켠다.
# 잠시 끄기: touch ~/.claude_watchdog_off   다시 켜기: rm ~/.claude_watchdog_off
# 기록: ~/Library/Logs/claude_watchdog.log (다시 켤 때만 한 줄)
[ -e "$HOME/.claude_watchdog_off" ] && exit 0
APP="/Applications/Claude.app/Contents/MacOS/Claude"
if ! ps -axo comm | grep -qx "$APP"; then
  open -a "Claude"
  echo "$(date '+%Y-%m-%d %H:%M:%S') Claude 꺼져 있어 다시 켬" >> "$HOME/Library/Logs/claude_watchdog.log"
fi
exit 0
