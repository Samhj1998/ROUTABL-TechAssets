# Backup Gate B6-R1 verification

- Device: MacStudioui-MacStudio.local, c377300b-a710-43a6-8169-f17e87175403.
- Original B4/B5/B6 pins: 22/22, 11/11, 20/20.
- Candidate tests: [32, 32, 0]; candidate verdict: PASS.
- First candidate run: [26, 30, 1]. Host scheduling/reaping was included in the soft-delay label, and the pin-test helper eagerly generated unused approval. Both were corrected. First output retained.
- Unmodified B4/B5/B6 regressions: [19, 20, 1], [23, 23, 0], [33, 33, 0].
- B4 legacy timeout/EPERM reproduced. Immediate mechanism observed; underlying OS permission policy remains unverified.
- Protected metadata and SHA paths: 498, 115. Revision unchanged: True.
- Combined release gate: FAIL while original B4 remains 19/20. Real backup, restore, production deployment: NOT_TESTED. Step 5-C: BLOCKED.
- Revision time: 2026-11-08T01:45:11+09:00 to 2026-11-08T01:45:27+09:00.

## SHA-256
- B4_REGRESSION.json: 275c48c883292b3296dc3d4917738cd7df6e646a921e03a017704a17a6e912d1
- B5_REGRESSION.json: 35553426bac8a502a5ef75f3a28db1460ec1879800cafefaa247f9c6ce463629
- B6_REGRESSION.json: 6c7d6bf1cffcd3320f4ac5ddaca1a594c35108bdc8f22e66fe52c59b5d5033da
- CAUSE_DIAGNOSIS.md: 3d1641f016c020585a04bb27ef27e0e0faf99f0d5da361d3f647ff1b5c07d393
- CLEANUP_AND_ADMISSION_CONTRACT.md: 7df7b1f0ac52dbe8920801ce1141f91df3f93c887170822c0677b03d613f916f
- LEGACY_DIAGNOSTIC.json: 182183383282972d8ff21206ea9e637e9e44f400c33257121267e9fbaad753c1
- LEGACY_TIMING_DIAGNOSTIC.json: e6ad8cd76a141138040bec4f731053531757e0434b45195d51f6beb74b577cde
- PROTECTED_SCOPE.json: e93b4b00eb06d57db3f147f0d33e5516238fe55d833b4fcd40e359e41f98e808
- R1_INTEGRATION.json: 58187cafdd1c7c9eb55143c009e9b188dbf7379c105a96eb96be70917216ca93
- R1_INTEGRATION_ATTEMPT_01.json: f69108fe2ad7aba66ca99533e5db570e0ffc1b33bb6a83d6e055666b9477b643
- legacy_diagnostic.py: a0de8ce8b22e7fc90d3eaddaa9a82dd7b0451044bed0f724165ebe75e717c839
- test_timeout_supervisor.py: 96f3c981c9df0de287b307b88ab5ad1b17833d41dfc97c6bd7c0ac7192299960
- timeout_fixture.py: 4de4071746a6604e4cb4c55326c07eeb6071719770b96f6f1686ee28866c311d
- timeout_supervisor.py: dc101cc3ea12eae8cbc0764364841907eaacfd26142279e0144eb79174a81f3a
