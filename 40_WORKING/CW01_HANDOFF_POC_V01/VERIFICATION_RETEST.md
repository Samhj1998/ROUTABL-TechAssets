# CW-01 Step 3 retest

KST: 2026-11-07T00:18:15+09:00
Initial audit retained as VERIFICATION.md.
Only the PoC assertion was corrected to normalize Markdown's escaped underscore in NOT_TESTED. JSON, rendered Markdown, and renderer are byte-identical to the initial run.

~~~~text
Command: handoff.py verify chat_to_work.json work_to_chat.json | exit=0
MOCK-CW01-C2W-001: PASS; simulated execution PASS
MOCK-CW01-W2C-001: PASS; simulated execution BLOCKED
Command: verify_poc.py | exit=0
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
PASS | 14 all evidence states and origins preserved | expected outcome observed
PASS | 15 unknown status | expected Invalid: record.evidence[0].status: invalid status or classification
PASS | 16 external target | expected Blocked: external delivery is disabled
PASS | 17 restricted classification | expected Blocked: restricted content or a credential marker cannot be rendered
PASS | 18 sample secret | expected Blocked: restricted content or a credential marker cannot be rendered
PASS | 19 path outside root | expected Invalid: asset path must be inside the reference root
PASS | 20 independent package | expected outcome observed
PASS | 21 historical evidence without reference | expected Invalid: historical evidence must reference a verified asset
~~~~

PASS | Protected repository compared with pre-creation baseline. Entries: 386.
Before: 80da914d7cefae082353fc19aa6e09c481459a73a2e965a2246c4bb0aec6306d
After: 80da914d7cefae082353fc19aa6e09c481459a73a2e965a2246c4bb0aec6306d

NOT_TESTED | External service configuration, actual approval, issuance, sealing, linking, deployment, registry registration, SSD/NAS restore and Step 4/5 operations.
BLOCKED | External delivery and unapproved actions.

## Checksums

6bfd6da70b9bddc5c81e012a4a085bd654475a015c63e6932a76a11321fd4937  README.md
ab0327da31617d3eaf38b3981d56aae885a9d5b027b46c0b2d2089fcbadec819  VERIFICATION.md
3fecfbe830df7789b64f6b7d765ba7f96bedbba5cbb6a31f1f4fec3ef3b3d551  chat_to_work.json
a15ccb82974e511eb131752413c0cc192528ee0248e71953bf7a0f7ea02fbdca  chat_to_work.md
054226f8b8d9febf62e448ac4654ae6ad9509900bfc54447816ac7a5193fa292  handoff.py
37e85af63b965853d0977476cb9af09423a04ad79c2a2c146640740deacdcf43  schema.json
b08f9192874aa5301a32769587acc7cb27ef86ad92461b5b0ad94861949dfbf1  verify_poc.py
2380edff116df3c98e23d68a76469968aaac451f3d83886fa7647017c18af159  work_to_chat.json
8768e30bf2f8e260ee37458f0811ac388601f5ac4e3ad5439429f6af9fecf909  work_to_chat.md
