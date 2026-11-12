# Backup Gate B4 verification

- Device: MacStudioui-MacStudio.local, 2026-11-07 KST.
- Window: 2026-11-07T17:12:28+09:00 to 2026-11-07T17:12:59+09:00.
- B3 originals: all nine verified against expected SHA-256. Three byte-identical copies used for B4 logic and regression.
- B3_REGRESSION: 22/22, exit 0
- B4_INTEGRATION: 20/20, exit 0
- Repo metadata: 440; changes outside the candidate: 0.
- Selected files with SHA-256: 49; changes: 0.
- Approval metadata, schedule registration projection and Step 5-C targets unchanged: True.
- Test subprocess commands: pinned fixture worker and process listing only. Audit probes denied outside read and unapproved process launch if the corresponding case passed.
- Real backup, operational adapters, signatures, registration, production deployment, and restore: NOT_TESTED. Step 5-C: BLOCKED.
- Attempt 01 stopped before the first case when macOS Python UUID generation opened /dev/urandom. The audit policy now permits read-only access to that device. Attempt 02 also denied the subprocess library opening /dev/null for redirected standard streams. The fence now allows that device in read/write mode. Both original test outputs are preserved.
- The November 8 regular run is independent of B4.
- Protection scope and exact before/after evidence: PROTECTED_SCOPE.json.
- The verification document's own digest is reported by the separate post-write hash calculation.

## SHA-256
- APPROVAL_PROPOSAL.schema.json: 5d7b3efcbafd4debe1efd1301d6334d7016311af915ac4bc2ebc67da81ef27d7
- B3_REGRESSION.json: cd49e26d96ec2087f4c485bd43c2deb658e8f7b4b257ee7f04852f29455ae3d1
- B4_INTEGRATION.json: 1b7ac572678d243a5578f67d436565fa3e5869cc188325571e310129fa9974d7
- B4_INTEGRATION_ATTEMPT_01.json: 8efbe5600114ef1a9f30f33b42b04bb0d672bb5f79a7d2aeee3fe5415c3e252b
- B4_INTEGRATION_ATTEMPT_02.json: 6ba7ccf6b2c7faee30fa2727da2e138b6e0241bb95cb073e518abb9ad3fbaf90
- ENGINE_COMPATIBILITY.md: 9fd73bb7f2af6ee024c6e6cfca79b6e673397be9fa9894ef3870f997d199a25b
- NATIVE_V043_CUTOVER.md: 45bb9d43b9bf96440a5e66be4c2d8f633a0a6a21b0110e8de1dd6d6d94c5ccfe
- PRE_DEPLOYMENT_ACCEPTANCE.md: 5a0fc79258d1b5c2a98f4523922cde991fe1b261b0db91a62426e6e2cff8615c
- PROTECTED_SCOPE.json: d6491687cbbf64103c996a146e488467e25ecaacc53eec73c5c7a1c6dde4922c
- ROUTABL_BackupEvidenceAdapter_v0_1.py: c0ba66a5c2f3781e006db5ddec4b34629c739d9774a823274b2b492c44b7cb1e
- ROUTABL_BackupHeadlessSupervisor_v0_3.py: 1935218efc6b2522c2d43991e3e0e6fd8c76108185318ee2b7afff0855f9db1d
- ROUTABL_MacToNasOneShot_v0_2.py: ece6b0085ffb0d7a36e84c6d4262cb0c799cb74034618df3ab8e05dfff10d219
- STATUS_EVIDENCE.schema.json: 4f3c96532ed0d09b45252faf13204eecb1fa8d33fb46d0cfe456cf2a418a35e2
- backup_runner_candidate.py: ced384e9890a30f504a1babd5d9cc9e2b4733b127d41d763446498c273dbcd92
- backup_supervisor_candidate.py: cf36c46dd3c391b5133f39f59f27ed42fcaa98b78de3eb0008628a3ee5feb972
- fixture_approval.json: 380550ffde0f12b46499ede974c0a4816f35b619a7ebbf2b2cc94ec762df4981
- fixture_approval_bad.json: b0de7af7e691533cef220b0a6026bf28a2650f29cfca903ebcbb3435914610f1
- fixture_boundary.py: 161ea3a6662bdd0344985938f8539f76f29c128137569d3933eb2f15e7b25ae4
- fixture_worker.py: 9ecd64e5ee5686473c005c2d5df13547cb20de5fac323044ae477f5a5a7e0cd8
- test_backup_gate_b3.py: 59f55b4f79fc02d6169a584fea9a47e5dd2d6d0a2227ffe868a67c1a2ae5ca10
- test_backup_gate_b4.py: c107fee4bcfdf2d699bfbd4bf097332d6852cf87a9f0cd4d77c505e5940fd87a
