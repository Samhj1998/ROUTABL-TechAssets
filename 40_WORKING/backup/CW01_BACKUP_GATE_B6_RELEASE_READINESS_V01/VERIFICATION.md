# Backup Gate B6 verification

- Device: MacStudioui-MacStudio.local, c377300b-a710-43a6-8169-f17e87175403.
- KST: 2026-11-07T19:16:29+09:00 to 2026-11-07T19:17:01+09:00.
- B5 originals pinned: 11/11. B4 originals pinned: 22/22.
- B4_REGRESSION initial: 19/20; exit 1. lock_owner_finishes ended FAILED_SAFE / ADAPTER_ERROR; the exact cause is not established.
- B4_REGRESSION_RETRY: 19/20; exit 1. Original test and timing unchanged.
- Targeted instrumented B4 diagnostic is separate from both regression results. Trace: B4_DIAG ROUTABL_MacToNasOneShot_v0_2.py child 62 TimeoutExpired, B4_DIAG ROUTABL_MacToNasOneShot_v0_2.py cleanup 27 PermissionError, B4_DIAG ROUTABL_MacToNasOneShot_v0_2.py child 64 PermissionError, B4_DIAG backup_runner_candidate.py stage 65 PermissionError, B4_DIAG backup_runner_candidate.py stage 71 Stop.
- Retry protected scope: unchanged=True; 2026-11-07T19:17:53+09:00 to 2026-11-07T19:18:25+09:00.
- B5_REGRESSION: 23/23; exit 0.
- B6_INTEGRATION: 33/33; exit 0.
- B6 isolated integration: PASS. Combined regression gate: FAIL. Actual backup and production deployment: NOT_TESTED.
- Actual legacy bypass prevention: BYPASS_NOT_BLOCKED. Team ID and final signed v043 binary: pending.
- Metadata checked: 475; content SHA-256 paths checked: 95; invariance: True.
- v0.27 protection: NOT_VERIFIED. Investigation B on Nov 8 04:30 is independent.
- Step 5-C: BLOCKED.

## SHA-256
- B4_REGRESSION.json: eace58f2219f6ccbf577aa2e39e96dc7c37fad322346ed5d22b8225581871d2a
- B5_REGRESSION.json: 35553426bac8a502a5ef75f3a28db1460ec1879800cafefaa247f9c6ce463629
- B6_INTEGRATION.json: 6c7d6bf1cffcd3320f4ac5ddaca1a594c35108bdc8f22e66fe52c59b5d5033da
- ENVIRONMENT_READONLY.json: 7a36aaffb4d77dbd105f0f1e0c8da69ad7c6de4c06469d15a248375746175c86
- PROTECTED_SCOPE.json: e7f78fe17bd65ad292585bda6a7e398e7790f62d62a484db84534b3fb9269b30
- RELEASE_AND_EVIDENCE_CONTRACT.md: d3fddd2fed5f9f2c4e9e3cec64fa4066b351f5868eda9e843d6395ce3b255847
- RELEASE_PINS.json: c87a84720ad196ee0a5509c6920817a37c3c09871106689bd6e462f08fb81c86
- ROUTABL_BackupEvidenceAdapter_v0_1.py: 8ad3e95a9dba518b44384145354468b5339f452128780385bd138f1ee0c083af
- ROUTABL_BackupEvidenceNormalizer_v0_1.py: 3fb5482c3da20aac42dcb4a638e78262d5b8a0eda3cc4625f96b827a3046dd51
- ROUTABL_BackupHeadlessSupervisor_v0_3.py: 187f8bb4d168d2d77344d032a391e3792baf646dd5117a1bf410b2efd59d91a5
- ROUTABL_MacToNasOneShot_v0_2.py: 334e38c1e0cf991cfef28d9c07f70faffdae360a2fa0d467bdf4a04875af8b8f
- STATUS_EVIDENCE.schema.json: 16557ffd5e00e6f30ffa10aee54ae18a30607f44ba90274d6c3e5a87700ca45e
- WRITE_CAPABILITY_DESIGN.md: 0d9717fb3baaed5722834936d069f8ae0aa7f8f50f73024bcb339545b2bf94b3
- _regression/b5/ROUTABL_BackupEvidenceNormalizer_v0_1.py: 3fb5482c3da20aac42dcb4a638e78262d5b8a0eda3cc4625f96b827a3046dd51
- _regression/b5/test_backup_gate_b5.py: 599d93bff04a3992e046c7c0f92c70c4bcc6c5aee3b348de0e81c307beb83373
- approval_v043.schema.json: 936f4a1f8d73cbad517f1288957ad9e66aad17bb2e1d90868e680dd2097e96b4
- test_backup_gate_b6.py: 99370e9bc07457bba8c4af0e560041b2c03ae6faf388286ba5534875b114dbc1
- B4_REGRESSION_RETRY.json: 307652f2f63e214927a34ed7424fbd5a409bacfe8d28eb6ffad6ad2a51ca2299
- B4_LOCK_OWNER_DIAGNOSTIC.json: 85bb49f9070ceb4481c9f7fe43eefb9dcdd3cb5917e439fd7c588079cb8e9a83
