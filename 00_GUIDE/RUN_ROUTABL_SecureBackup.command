#!/bin/zsh
set -euo pipefail
echo "라우터블 기술자산 안전 백업 시작 (Mac 키체인 자동 잠금 해제)"
/usr/bin/python3 '/Users/yongho/ROUTABL-TechAssets/00_GUIDE/ROUTABL_SecureBackup_v1_0.py'
echo "백업 성공 메시지와 자동 추출 결과를 확인하세요."
