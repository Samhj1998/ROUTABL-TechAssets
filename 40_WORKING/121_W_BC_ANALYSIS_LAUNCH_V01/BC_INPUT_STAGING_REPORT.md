# B/C 공통 입력 배치 결과

2026-11-08 KST. MacStudioui-MacStudio.local, 장치 c377300b-a710-43a6-8169-f17e87175403.

| 대상 | 실제 검증 |
|---|---|
| 기준 매니페스트 | b65db09df1012b5ef05c520157af2ff954fd71258256475a0b6be5b5089307d1 일치 |
| 원본 4개 | 해시와 크기 일치. 배치 후 재확인 |
| B input | /Users/yongho/121_CHATGPT_B_V01/input, 정확히 4개, 각 0400, 디렉터리 0500 |
| C input | /Users/yongho/121_CLAUDE_ISOLATED_V01/input, 정확히 4개, 각 0400, 디렉터리 0500 복구 |
| 양측 사본 | BC_INPUT_SHA256SUMS 8/8 검증 PASS |
| 공통 프롬프트 | 31b8f06de5a141c948efdcc3408051b4348ff2309a90042eeea4c85f25474f08 일치. B용 독립 사본은 B 루트에 별도로 저장 |

| 파일 | 공통 SHA-256 |
|---|---|
| COMMON_ANALYSIS_PACKET_V01.md | d88a5a12e4a814105991fce95391079e7cdd22cddee0296d5ad33d3812c69bba |
| SYNTHETIC_CORPUS_V01.json | 840ecf1ea98a59fa20d499e559205ceae130c513aa68531e295cb129e01a7b8b |
| SYNTHETIC_DEV_V01.json | db2fca0951c1c43d30da560d7ecafd6c967e7ff9389c21c773b347714a93f3a1 |
| COMMON_TEST_SPEC.md | 552bb8111f703048e657a26922954f2739156362efa37f54f5f7e5cf1e254f6d |

B output은 /Users/yongho/121_CHATGPT_B_V01/output. C output은 /Users/yongho/121_CLAUDE_ISOLATED_V01/output. 두 input 사본은 실파일이며 심볼릭 링크·하드링크는 사용하지 않았다. 소스, 실제 질의, 운영 DB 및 보류시험은 배치 대상에서 제외했다.
