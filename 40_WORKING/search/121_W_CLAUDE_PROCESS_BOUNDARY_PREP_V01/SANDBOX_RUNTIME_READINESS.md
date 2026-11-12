# @anthropic-ai/sandbox-runtime 준비 상태

공식 GitHub 릴리스와 공개 npm latest 메타데이터에서 v0.0.81을 확인했다. npm 배포 무결성 값은 `sha512-bjHDu87gjIR7+Oxy9jPiK3v8CvSELCzfpXa3fjqfSKdvlZET2iF51xcXILWPayTpowB3xtZeQVf2JR916nVW/w==`이다. 공개 메타데이터 조회는 Work 환경에서 수행했고 Mac 시험은 로컬에 한정했다.

공식 메타데이터는 Node >=22.12.0과 srt 실행 항목 dist/cli.js를 명시한다. 운영 의존성은 zod, commander, node-forge, @pondwader/socks5-server다. Mac에서 Node v24.21.0 arm64, npm 11.19.0, /usr/bin/sandbox-exec 실행 가능을 확인했다. PATH, 대표 prefix와 npm global root에 srt 또는 npm 패키지가 없었다. macOS Seatbelt 기반 설계와 설치본 아키텍처는 부합한다. 실제 설치, 초기화, 네이티브 Claude 2.1.309와 Pro OAuth/Keychain 호환은 NOT_TESTED.

공식 README의 전역 설치 예시는 global prefix, bin 링크, cache를 변경한다. 제안은 전역 설치 대신 /Users/yongho/121_CLAUDE_ISOLATED_V01/config/runtime-v0.0.81/의 전용 npm prefix와 전용 cache를 쓰는 방식이다. 별도 승인 후보 명령은 `/usr/local/bin/npm --prefix <전용-prefix> --cache <전용-prefix>/.npm-cache install --ignore-scripts --no-audit --no-fund --save-exact @anthropic-ai/sandbox-runtime@0.0.81`이다. 실행 전 prefix 충돌, 배포 integrity, 전이 의존성과 잠금 파일을 검토한다. 설치 시 전용 package manifest·lock·node_modules·npm 캐시·다운로드가 생길 수 있다. 예상 밖 lifecycle 작업 또는 전역 변경이 필요하면 중단한다. 제거는 이번에 승인된 전용 경로에서만 정리하며 실제 제거는 별도 범위로 정한다.

공식 설정은 network 및 filesystem 정책을 담은 JSON이다. 읽기는 기본 허용에서 denyRead 후 필요한 경로만 allowRead로 되돌린다. 쓰기는 명시 허용 중심이지만 기본 임시·로그 예외와 표준 입출력을 함께 확인해야 한다. macOS 네트워크는 Seatbelt와 로컬 프록시를 결합하며 일반 프록시 호환성과 Unix 소켓·Mach 서비스·Apple Events가 별도 경계다. 사용자 기본 설정에 의존하지 말고 검증된 설정 경로를 명시한다. 공식 문서는 베타이며 버전별 규칙과 한계가 달라질 수 있다.

[릴리스 v0.0.81](https://github.com/anthropics/sandbox-runtime/releases/tag/v0.0.81) · [패키지 manifest](https://github.com/anthropics/sandbox-runtime/blob/v0.0.81/package.json) · [npm 메타데이터](https://registry.npmjs.org/@anthropic-ai%2fsandbox-runtime/latest)
