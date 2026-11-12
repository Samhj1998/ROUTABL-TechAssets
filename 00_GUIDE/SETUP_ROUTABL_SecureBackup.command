#!/bin/zsh
# ROUTABL encrypted backup: one-time interactive creation only.
# Never passes secrets on command line or stores passwords in files.
set -euo pipefail
umask 077

ROOT="/Volumes/SSD2TB/ROUTABL-TechAssets-Backup"
IMAGE="$ROOT/ROUTABL-SecureBackup.sparsebundle"
VOLUME="ROUTABL-Secure"

echo "ROUTABL 기술자산 암호화 백업 공간 최초 설정"
echo "대상: SSD2TB 의 독립적인 20GB AES-256 APFS Sparse Bundle"
echo "기존 SSD 데이터와 파티션은 변경하지 않습니다."
echo

if [[ "$(id -un)" != "yongho" ]]; then
  echo "중단: Mac 계정 yongho로 실행해야 합니다."
  exit 20
fi
if ! /sbin/mount | /usr/bin/grep -Fq " on /Volumes/SSD2TB ("; then
  echo "중단: SSD2TB 마운트를 확인할 수 없습니다."
  exit 21
fi
if [[ ! -d "$ROOT" || -L "$ROOT" ]]; then
  echo "중단: 백업 대상 디렉터리가 없거나 심볼릭 링크입니다."
  exit 22
fi
if [[ -e "$IMAGE" || -L "$IMAGE" ]]; then
  echo "중단: 같은 이름의 이미지가 존재합니다. 덮어쓰지 않습니다."
  exit 23
fi
echo "Mac의 암호 입력 창에 새로운 백업 비밀번호를 직접 설정하세요."
echo "ChatGPT에는 암호를 보내거나 복사하지 마세요."
echo "중요: Mac 키체인 외에 안전한 오프라인 복구 방법도 마련하세요."
echo

/usr/bin/hdiutil create \
  -type SPARSEBUNDLE \
  -size 20g \
  -fs APFS \
  -layout GPTSPUD \
  -volname "$VOLUME" \
  -encryption AES-256 \
  -agentpass \
  "$IMAGE"

if [[ ! -d "$IMAGE" ]]; then
  echo "암호화 이미지 생성 결과를 확인할 수 없습니다. 완료로 간주하지 않습니다."
  exit 24
fi

echo
echo "암호화 이미지 생성 명령이 완료되었습니다."
echo "이어서 마운트 비밀번호 창이 나타나면 '나의 키체인에 암호 저장'을 선택하세요."
echo "최초 마운트에는 암호를 한 번 더 요구할 수 있습니다."
echo "Mac 로그인 계정이 탈취되면 키체인 자동 접근도 위험해질 수 있습니다."
echo "백업과 검증이 끝나면 Finder에서 ROUTABL-Secure를 추출하여 잠그세요."
echo
/usr/bin/open "$IMAGE"
echo "설정 창을 열었습니다. 실제 마운트·키체인·복원 시험은 별도로 확인해야 합니다."
