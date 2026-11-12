# 신규 AI 채팅용 기술자산 검색 지침 v0.3
프로젝트: 120. 라우터블(ROUTABL) 기술자산 통합관리
검증 기준: 2026-11-03. 데이터베이스: ~/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.3.json

1. 라우터블 개발 질문이면 기존 성공사례/실행경로/증거를 먼저 검색한다.
2. Mac Studio가 연결되면 위 자산대장을 읽고 현재 파일 해시를 재검증한다.
3. Mac이 접근 불가하면 ChatGPT Library와 과거 보고서를 찾아야 한다. 자산 부재로 단정하지 않는다.
4. 이전 성공과 현재 재실행 성공은 구분한다. 수정·배포·운영 쓰기는 명시적 승인 후 진행한다.
5. 민감한 원본 코드는 인덱스에 통째로 저장하거나 외부로 전송하지 않는다.

핵심 자산:
- TA-CASE-20261102-01: Firebase 고객 등록 사례. Mac Studio StudioProjects의 cloud_access.py.
  등록 성공의 과거 증거와 실제 파일 해시 확인; Firebase 현재 인증/운영 실행 시험은 미실시.
  사례 PDF Library: libfile_aae40558a6ec819189990681d3e6f4b2.
- INTEGRATION-E04: 2026-10-19 과거 통합점검 HTML 원본.
  Library: libfile_1348cf4cf49c8191af70ae0162dffe99; 아직 Mac 실물 해시 검증 없음.
- ROUTABL-97-1-V4.1: NAS 봉인 내부 기준판. Mac 내부 SSD에 PDF/ZIP/영수증 검증 사본 있음:
  ~/ROUTABL-TechAssets/20_ORIGINALS/NAS-Imported/ROUTABL-97-1-V4.1
  Library의 백서 PDF: libfile_72a4f0a4043c819192d8967951f680a1 (NAS와 바이트 대조는 미실시).

주의: 기존 ASSET-SEARCH-01 v1.1은 NAS 전용 색인이며, StudioProjects의 cloud_access.py가 자동으로 색인되지 않음.
Mac 내 새 자산대장은 검색용 메타데이터이며, 전체 라이브러리 자동 동기화 프로그램이 아님.
SSD2TB가 비암호화 상태이므로 백서 본문·인증 소스 백업을 확대하지 말 것.
