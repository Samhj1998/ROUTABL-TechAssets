# Backup Gate B6-R2 verification

- Device: MacStudioui-MacStudio.local, c377300b-a710-43a6-8169-f17e87175403.
- KST: 2026-11-08T02:34:57+09:00 to 2026-11-08T02:36:19+09:00.
- Original SHA-256 inventories: B4 22/22, B5 11/11, B6 20/20, R1 15/15.
- R2 candidate: PASS.
- B4 historical result: 19/20 FAIL. Retained in the unchanged R1 source record.
- B5/B6 unchanged regressions: PASS. R1 was run twice without changing source, thresholds or assertions.
- R2_INTEGRATION: 45/45, exit 0.
- B4_REGRESSION: 19/20, exit 1.
- B5_REGRESSION: 23/23, exit 0.
- B6_REGRESSION: 33/33, exit 0.
- R1_REGRESSION initial: 30/32, exit 1. Two fixtures completed with exit 0 and verified cleanup; soft-delay labels differed from expectations.
- R1_REGRESSION_RETRY: 29/32, exit 1. Initial failure retained. Retry protected scope unchanged: True.
- Protected: True; metadata entries 518; SHA paths 130.
- Production substitution: NOT_APPROVED. Actual backup, restore and v043 deployment: NOT_TESTED.
- Investigation B is the separate read-only determination of the Nov 8 scheduled job. Step 5-C: BLOCKED.

## SHA-256
- B4_REGRESSION.json: 88b7c7e00f8b4f0de75346504303437478cc34249a1ef468773bbc24a21a72e7
- B5_REGRESSION.json: 35553426bac8a502a5ef75f3a28db1460ec1879800cafefaa247f9c6ce463629
- B6_REGRESSION.json: 6c7d6bf1cffcd3320f4ac5ddaca1a594c35108bdc8f22e66fe52c59b5d5033da
- INTEGRATION_CONTRACT.md: 2ad202ac46bf2421d14c6f41de5da156b5adf956b0b8a9e1ecb3b99b6bdb833c
- PROTECTED_SCOPE.json: 24363f8d169ec478a135e726b0932b7b18c238c01a09ced26a45a2186610db6d
- R1_REGRESSION.json: e58a17eae1a426bd8c7f2fe60960e2d35dbd9d8b3a25e56f04b6ba0a427fd7e0
- R2_INTEGRATION.json: 8991fe1fc3f5f4da695e95aedd7c74e061607a893c558b73882d1ee46d77eff1
- ROUTABL_BackupEvidenceNormalizer_v0_1.py: 3fb5482c3da20aac42dcb4a638e78262d5b8a0eda3cc4625f96b827a3046dd51
- SOURCE_PROVENANCE.json: 8b58aaec8b216cbe6c2ae8f49bda9ac8c540304439eaa24d4170b9b69c3390aa
- b4_evidence.py: c0ba66a5c2f3781e006db5ddec4b34629c739d9774a823274b2b492c44b7cb1e
- b6_evidence.py: 8ad3e95a9dba518b44384145354468b5339f452128780385bd138f1ee0c083af
- backup_runner_candidate.py: ced384e9890a30f504a1babd5d9cc9e2b4733b127d41d763446498c273dbcd92
- r2_lifecycle.py: 5b516464b5c4eac5f300eead3717e31e066b71991baec4ef405437e53f17595a
- r2_oneshot.py: ea043bb0f75b84ad500bf4d8a98ab10f20d006caf6022f963e03324986a2924c
- r2_supervisor.py: ccf82bcc3914a3a0ccf05ebd03e167ed5dd9e82ded0b3f26f1fb5941b1eeffee
- r2_worker.py: b99970165f0654ec74375b778a0535718bc55d3936be103cded5d5252eb87e37
- test_r2.py: 556f4d8be7d617231b26f1a86e7c12c2deb2d701880271432d531c731217b4d6
- R1_REGRESSION_RETRY.json: ed805c92480a41b892b3a802c1749c821d7dfa8fbd2e5d2fb2e49ca4b52bcd7c
