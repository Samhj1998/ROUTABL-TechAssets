# CW-01 Step 3 PoC verification

KST: 2026-11-07T00:17:25+09:00
Path: /Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_HANDOFF_POC_V01

## Tests

~~~~text
Command: handoff.py render chat_to_work.json work_to_chat.json | exit=0
MOCK-CW01-C2W-001: PASS; simulated execution PASS
MOCK-CW01-W2C-001: PASS; simulated execution BLOCKED
Command: handoff.py verify chat_to_work.json work_to_chat.json | exit=0
MOCK-CW01-C2W-001: PASS; simulated execution PASS
MOCK-CW01-W2C-001: PASS; simulated execution BLOCKED
Command: verify_poc.py | exit=1
PASS | 01 Chat to Work | expected outcome observed
PASS | 02 Work to Chat | expected outcome observed
PASS | 03 required field | expected Invalid: record.next: missing=['completion'], extra=[]
PASS | 04 direction and target | expected Invalid: record.to.chat: unexpected value
PASS | 05 missing reference | expected Invalid: asset missing or outside reference root: missing-fixture.md
PASS | 06 altered hash | expected Invalid: asset checksum mismatch: 00_GUIDE/DIGITOPIA_CHAT_WORK_PROTOCOL_v1.0.md
PASS | 07 altered Markdown | expected Invalid: Markdown differs from canonical JSON rendering
PASS | 08 altered JSON | expected Invalid: Markdown differs from canonical JSON rendering
PASS | 09 duplicate ID | expected Invalid: duplicate handoff ID: MOCK-CW01-C2W-001
PASS | 10 permitted test action | expected outcome observed
PASS | 11 pending approval | expected outcome observed
PASS | 12 attempted scope expansion | expected outcome observed
PASS | 13 prohibition overrides allowance | expected outcome observed
FAIL | 14 all evidence states and origins preserved | AssertionError
PASS | 15 unknown status | expected Invalid: record.evidence[0].status: invalid status or classification
PASS | 16 external target | expected Blocked: external delivery is disabled
PASS | 17 restricted classification | expected Blocked: restricted content or a credential marker cannot be rendered
PASS | 18 sample secret | expected Blocked: restricted content or a credential marker cannot be rendered
PASS | 19 path outside root | expected Invalid: asset path must be inside the reference root
PASS | 20 independent package | expected outcome observed
PASS | 21 historical evidence without reference | expected Invalid: historical evidence must reference a verified asset
~~~~

## Repository invariance

PASS | inventory, file bytes (SHA-256), file modes and symlink targets, excluding only the PoC directory.
Before: 386 entries | 80da914d7cefae082353fc19aa6e09c481459a73a2e965a2246c4bb0aec6306d
After: 386 entries | 80da914d7cefae082353fc19aa6e09c481459a73a2e965a2246c4bb0aec6306d
Latest manifest before work: 30_REGISTRY/asset_manifest_v0.27.json. Number of manifest versions: 27.
Changed paths: []

00_GUIDE/DIGITOPIA_CHAT_WORK_PROTOCOL_v1.0.md: 7b48c1deb08ab1c8904541f7c9acedbf2406e51f510fbccf0d7ae17609d585d1
60_AUDIT/120-2-W_CW01_STEP2_VERIFICATION_v1.0.md: ab56b5518120d93a300549757eb6f8c854989b339622367b73907d320a25e56d
30_REGISTRY/asset_manifest_v0.27.json: afe17adb54103952c0e84d296ded42a478fca49f25bd53f1f87dc0c73e1ce244
00_GUIDE/ROUTABL_3TIER_ASSET_PROTECTION_AND_RESTORATION_PRINCIPLE_TI01_v1.0_20261106.md: 21833f37c1c0e686743dca77a341577db9b2f0e97d93a8773a25fc8955711132
00_GUIDE/ROUTABL_VERSION_INDEPENDENCE_PRINCIPLE_v1.0_20261106.md: 86c79cd8cc11aac2aed2054c9f92ad445050ce5cfb6f17f17b355f75b4c4eb54

## Out of scope

NOT_TESTED | Runtime state outside the repository, including Firebase, GitHub, deployed apps, SSD/NAS restore, schedules and other AI/project settings.
NOT_TESTED | ChatGPT/Claude automatic linking, operational ID issuance/sealing/registry updates and Step 4 operations.
BLOCKED | External delivery, production access and any unapproved execution.

## PoC file checksums

6bfd6da70b9bddc5c81e012a4a085bd654475a015c63e6932a76a11321fd4937  README.md
3fecfbe830df7789b64f6b7d765ba7f96bedbba5cbb6a31f1f4fec3ef3b3d551  chat_to_work.json
a15ccb82974e511eb131752413c0cc192528ee0248e71953bf7a0f7ea02fbdca  chat_to_work.md
054226f8b8d9febf62e448ac4654ae6ad9509900bfc54447816ac7a5193fa292  handoff.py
37e85af63b965853d0977476cb9af09423a04ad79c2a2c146640740deacdcf43  schema.json
386b164a5dbf26a68bcca165ebcca5e4916dc6354468ddb449e3b45eca902ae7  verify_poc.py
2380edff116df3c98e23d68a76469968aaac451f3d83886fa7647017c18af159  work_to_chat.json
8768e30bf2f8e260ee37458f0811ac388601f5ac4e3ad5439429f6af9fecf909  work_to_chat.md
