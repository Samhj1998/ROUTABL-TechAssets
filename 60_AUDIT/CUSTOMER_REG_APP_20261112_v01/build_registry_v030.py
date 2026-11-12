#!/usr/bin/env python3
"""v0.30 등록부·v0.16 색인 만들기 (2026-11-12 고객등록앱·행정동 작업 등록).
- v0.29 등록부·v0.15 색인은 읽기만 함. 새 파일은 로컬 작업 폴더에서 만든 뒤 30_REGISTRY로 복사(덮어쓰기 없음)는 셸에서 cp -n.
- 사용: python3 build_registry_v030.py <tech-assets 루트(마운트 경로)> <mac 경로 접두 매핑 json> <출력 폴더>
"""
import hashlib, json, os, shutil, sqlite3, sys, datetime
from pathlib import Path

root = Path(sys.argv[1]); mapping = json.loads(sys.argv[2]); out = Path(sys.argv[3]); out.mkdir(parents=True, exist_ok=True)
reg = root / '30_REGISTRY'
KST = datetime.timezone(datetime.timedelta(hours=9))
SRC = 'CLAUDE_SESSION_20261112_CUSTOMER_REG_STAGE5'

def local(mac_path):
    for mac, mnt in mapping.items():
        if mac_path.startswith(mac): return Path(mnt + mac_path[len(mac):])
    raise KeyError(mac_path)

def meta(mac_path):
    p = local(mac_path); b = p.read_bytes()
    return {'observed_original_path': mac_path, 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest(),
            'mtime_utc': datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc).isoformat()}

CR = '/Users/yongho/StudioProjects/ROUTABL-CustomerRegistration-Android'
CRJ = CR + '/app/src/main/java/com/routivel/customerreg'
DR = '/Users/yongho/StudioProjects/DISPATCH-One-Android'
SR = '/Users/yongho/StudioProjects/ROUTABL-Senior-Driver'
TA = '/Users/yongho/ROUTABL-TechAssets'

items = [
 ('CUSTOMER-REG-APP-01-CONSENSUS-V05', '고객등록앱 합의안 v0.5 — 1차 즉시 저장, 2차 여유 있을 때 정리 / 공유 빠른 경로 / 정식 경로',
  TA + '/40_WORKING/CUSTOMER_REG_APP_PREP_20261111/CUSTOMER_REG_APP_CONSENSUS_v0.5.md', 'USER_CONFIRMED_CONSENSUS_ALL_5_STAGES_IMPLEMENTED_20261112', ['ASSET-120-ADDR-REGISTRATION-RUNBOOK-V01']),
 ('CUSTOMER-REG-APP-01-CAPTURE-PARSER', '캡처·사진 글자 인식 칸 나누기 CaptureParser (인성데이타 정형·카톡 비정형, 업체명 규칙, 메모 뒤 주소 줄 인식)',
  CRJ + '/capture/CaptureParser.kt', 'DEVICE_S25_VERIFIED__PHOTO_3000x4000_KAB_ADDRESS_LINE_FIX_6B6531C__PUSHED', ['CUSTOMER-REG-APP-01-CONSENSUS-V05']),
 ('CUSTOMER-REG-APP-01-FIRST-REGISTRATION', '1차 등록 규칙 FirstRegistration (중복·지번/도로명 선택·행정동 우선 동명·확인 필요 표시)',
  CRJ + '/register/FirstRegistration.kt', 'DEVICE_S25_VERIFIED_DUPLICATE_BY_NAME_AND_PHONE__ADMIN_DONG_6B6531C__PUSHED', ['CUSTOMER-REG-APP-01-CONSENSUS-V05']),
 ('CUSTOMER-REG-APP-01-SHARE-QUICK-PATH', '공유 빠른 경로 ShareRegisterWorker (갤러리·카톡 공유 → 화면 없이 백그라운드 1차 등록 → 묶음 알림)',
  CRJ + '/share/ShareRegisterWorker.kt', 'DEVICE_S25_VERIFIED_STAGE4_0F0C1A7__PUSHED', ['CUSTOMER-REG-APP-01-CONSENSUS-V05']),
 ('CUSTOMER-REG-APP-01-REVIEW-QUEUE', '정리 목록 저장소 ReviewQueue (폰 안 review-queue.json, 확인 필요·보완 후보·등록 못 함, 계정 구분)',
  CRJ + '/register/ReviewQueue.kt', 'DEVICE_S25_VERIFIED_STAGE5_6C73C97__PUSHED', ['CUSTOMER-REG-APP-01-CONSENSUS-V05']),
 ('CUSTOMER-REG-APP-01-REVIEW-EDIT', '수정 화면 ReviewEditActivity (기사앱 CustomerEditActivity와 같은 칸·주소 확인·저장 경로, 보완은 바뀐 칸만, 다른 업체로 신규 등록)',
  CRJ + '/review/ReviewEditActivity.kt', 'DEVICE_S25_VERIFIED_D6CC4FD__PUSHED', ['CUSTOMER-REG-APP-01-REVIEW-QUEUE']),
 ('CUSTOMER-REG-APP-01-HOME', '첫 화면 HomeActivity (고객 목록·초성 검색·정리 배너·직접 입력·캡처로 등록, 화면 구성안 ①)',
  CRJ + '/HomeActivity.kt', 'DEVICE_S25_VERIFIED_9BD6757_D6CC4FD__PUSHED', ['CUSTOMER-REG-APP-01-CONSENSUS-V05']),
 ('CUSTOMER-REG-APP-01-UI-COMMON', '고객등록앱 공통 화면 모양 Ui.kt (남색 머리·카드·큰 버튼, 화면 구성안 ③④⑤)',
  CRJ + '/ui/Ui.kt', 'DEVICE_S25_VERIFIED_SCREENS_1_3_5__SCREEN_4_PENDING_D6CC4FD__PUSHED', ['CUSTOMER-REG-APP-01-HOME']),
 ('CUSTOMER-REG-APP-01-HANDOFF-STAGE5', '고객등록앱 5단계 인계 기록 (결정·구현·실기기 시험·행정동·보류·남은 일)',
  CR + '/docs/HANDOFF_STAGE5_20261111.md', 'DOCUMENT_COMMITTED_D6CC4FD__PUSHED', ['CUSTOMER-REG-APP-01-CONSENSUS-V05']),
 ('SERVER-ADDR-SEARCH-ADMIN-DONG', '주소 검색 서버 함수 routablCustomerAddressSearch 행정동(adminDong = 카카오 region_3depth_h_name) 추가',
  DR + '/server/control-routing/customer-address-policy.js', 'NODE_TEST_68_PASS__DEPLOYED_ROUTIVEL_PROD_20261112_0012__EA537FE_PUSHED', ['CUSTOMER-REG-APP-01-FIRST-REGISTRATION']),
 ('DRIVER-APP-ADDR-LOOKUP-ADMIN-DONG', '기사앱 고객 수정 "주소 확인" 동명 = 행정동 우선 (1.0.69)',
  DR + '/app/src/main/java/com/routivel/driver/CustomerEditActivity.kt', 'DEVICE_S25_VERIFIED_BEOMEO_TO_BEOMEO2_DA31932_F245A74__PUSHED', ['SERVER-ADDR-SEARCH-ADMIN-DONG']),
 ('SENIOR-APP-ADDR-LOOKUP-ADMIN-DONG', '시니어 기사앱 고객 수정 "주소 확인" 동명 = 행정동 우선 (1.0.21, 기사앱과 같은 코드)',
  SR + '/app/src/main/java/com/routivel/driver/CustomerEditActivity.kt', 'COMMITTED_BE52144_766E658__PUSHED__BUILD_NOT_YET_RUN', ['DRIVER-APP-ADDR-LOOKUP-ADMIN-DONG']),
 ('CUSTOMER-DONG-NORMALIZE-TOOL', '기존 주소록 동명 행정동 일괄 정리 도구 normalize_dongs.py (plan → apply CAS → verify)',
  DR + '/tools/customer-dong/normalize_dongs.py', 'UNIT_TEST_5_PASS__PLAN_RUN_20261112_0047__APPLY_ON_HOLD_USER_DECISION__CE85D7A_PUSHED', ['SERVER-ADDR-SEARCH-ADMIN-DONG']),
]

manifest = json.loads((reg / 'asset_manifest_v0.29.json').read_text())
prev_bytes = (reg / 'asset_manifest_v0.29.json').read_bytes()
existing = {a['asset_id'] for a in manifest['asset_files']}
added = []
for aid, title, path, validation, parents in items:
    assert aid not in existing, aid
    e = {'asset_id': aid, 'title': title, **meta(path), 'source_system': SRC, 'source_chat_number': 'CUSTOMER-REG-STAGE5',
         'execution_validation': validation, 'write_or_execution_approval_class': 'C' if aid.startswith('SERVER-') else 'B',
         'copy_in_managed_repository': 'NO_REFERENCED_ONLY', 'original_file_unchanged': True,
         'provenance_status': 'DIRECT_FILE_BYTES_SHA256_VERIFIED_AUTHORED_IN_THIS_SESSION', 'parent_asset_ids': parents,
         'registry_added_in': 'v0.30'}
    manifest['asset_files'].append(e); added.append(e)

dong = sys.argv[4] if len(sys.argv) > 4 else '{}'
manifest['schema_version'] = '0.30'
manifest['captured_at_kst'] = datetime.datetime.now(KST).replace(microsecond=0).isoformat()
manifest['previous_registry'] = {'path': 'asset_manifest_v0.29.json', 'bytes': len(prev_bytes), 'sha256': hashlib.sha256(prev_bytes).hexdigest()}
manifest['customer_reg_app_v030'] = {
    'status': 'CUSTOMER_REG_APP_STAGES_1_TO_5_AND_SCREEN_DESIGN_IMPLEMENTED_DEVICE_VERIFIED',
    'version': '0.6.1-ui (versionCode 15)',
    'repo': 'https://github.com/Samhj1998/ROUTABL-CustomerRegistration-Android (PRIVATE, first push 2026-11-12, origin/main d6cc4fd)',
    'consensus': 'v0.5: 1차 즉시 저장 → 2차 정리, 공유 빠른 경로 + 정식 경로 + 직접 입력',
    'screen_design_artifact': 'https://claude.ai/artifact/GrqffN8oRpUf2VZfg4JdE4 (라우터블고객등록 화면 구성안, 8 screens)',
    'decisions_20261112': ['수정 저장: 관리자 saveShared / 기사 submit', '되돌리기: 관리자만(저장 직후 그대로일 때 삭제), 기사 되돌리기 없음(firestore.rules 요청 삭제 금지)',
                           '정리 목록 무시 버튼', '알림 → 정리 목록', '동명은 행정동 우선', '기존 주소록 동명 일괄 정리 보류 (거리별 요금 계산 전)'],
    'admin_dong_chain': {'server': 'routablCustomerAddressSearch adminDong, deployed routivel-prod 2026-11-12 00:12, ea537fe',
                         'driver_app': '1.0.69 da31932', 'senior_app': '1.0.21 be52144', 'customer_reg_app': '6b6531c'},
    'customer_dong_plan_20261112': json.loads(dong),
    'pending': ['정리 목록(④) 실기기 모양 확인', '신규 등록 건 행정동 저장 실기기 확인', '고객등록앱 단위 시험 Android Studio 실행', '시니어앱 빌드',
                '동명 일괄 정리 apply 전 renamed 종류 표본 확인'],
}
mpath = out / 'asset_manifest_v0.30.json'
mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1))

db = out / 'asset_120_lookup_v0.16.sqlite'
shutil.copyfile(reg / 'asset_120_lookup_v0.15.sqlite', db)
c = sqlite3.connect(db)
for e in added:
    c.execute('insert into assets values (?,?,?,?,?,?,?,?)', (e['asset_id'], e['title'], e['observed_original_path'], e['sha256'],
              e['execution_validation'], 'P3', SRC, 'v0.30'))
c.execute("insert or replace into search_info values ('source_register','asset_manifest_v0.30.json')")
c.execute("insert or replace into search_info values ('20261112_customer_reg_app_v030', 'CUSTOMER_REG_APP_STAGE5_SCREEN_DESIGN_ADMIN_DONG_SERVER_DRIVER_SENIOR_13_ASSETS')")
c.commit()
ok = c.execute('pragma integrity_check').fetchone()[0]; rows = c.execute('select count(*) from assets').fetchone()[0]; c.close()
print(json.dumps({'added': len(added), 'rows': rows, 'integrity': ok,
                  'manifest_sha256': hashlib.sha256(mpath.read_bytes()).hexdigest(), 'db_sha256': hashlib.sha256(db.read_bytes()).hexdigest(),
                  'ids': [(e['asset_id'], e['sha256'][:12]) for e in added]}, ensure_ascii=False, indent=1))
