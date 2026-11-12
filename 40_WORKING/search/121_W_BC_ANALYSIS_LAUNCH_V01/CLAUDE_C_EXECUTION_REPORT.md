# Claude C execution evidence

```json
{
  "start_kst": "2026-11-08T12:05:51+09:00",
  "process_launches": 1,
  "initial_prompt_count": 1,
  "auth": "claude.ai Pro firstParty target-match",
  "usage_credits": "disabled in verified Step 2-B record",
  "version": "2.1.309",
  "cwd": "/Users/yongho/121_CLAUDE_ISOLATED_V01/input",
  "format": "stream-json",
  "max_turns": 4,
  "stop_reason": null,
  "read_attempts": [
    {
      "file": "COMMON_ANALYSIS_PACKET_V01.md",
      "offset": 1,
      "limit": null,
      "result": "success"
    },
    {
      "file": "COMMON_TEST_SPEC.md",
      "offset": 1,
      "limit": null,
      "result": "success"
    },
    {
      "file": "SYNTHETIC_DEV_V01.json",
      "offset": 1,
      "limit": null,
      "result": "success"
    },
    {
      "file": "SYNTHETIC_CORPUS_V01.json",
      "offset": 1,
      "limit": 80,
      "result": "success"
    }
  ],
  "init_tools": [
    "Read"
  ],
  "mcp_count": 0,
  "model": "claude-opus-5-5",
  "exit_code": 0,
  "result_subtype": "success",
  "result_is_error": false,
  "num_turns": 5,
  "duration_ms": 137219,
  "duration_api_ms": 137038,
  "usage": {
    "input_tokens": 4,
    "cache_creation_input_tokens": 15975,
    "cache_read_input_tokens": 4927,
    "output_tokens": 13387
  },
  "usage_limit_signal": false,
  "billing_signal": false,
  "auth_error_signal": false,
  "init_seen": true,
  "read_ok": [
    "COMMON_ANALYSIS_PACKET_V01.md",
    "COMMON_TEST_SPEC.md",
    "SYNTHETIC_CORPUS_V01.json",
    "SYNTHETIC_DEV_V01.json"
  ],
  "missing_reads": [],
  "analysis_bytes": 9786,
  "analysis_sha256": "d534a406094e4e42d146fb0640d77e10b97667c72cf08452258f09244e0976c7",
  "result_shape": {
    "numbered_sections": 5,
    "bottleneck": true,
    "algorithm_or_pseudocode": true,
    "korean_initial_alias": true,
    "preservation": true,
    "evaluation": true,
    "risk_scope": true,
    "uncertainty": true
  },
  "verdict": "PASS",
  "end_kst": "2026-11-08T12:08:09+09:00"
}
```
