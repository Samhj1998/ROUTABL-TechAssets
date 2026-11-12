# B6-R1 cause diagnosis

Prior B6 observed TimeoutExpired followed by a PermissionError in B4 cleanup. This instrumented copy records the startup/communicate duration, ready marker, PID/PGID/SID and errno of the call. Its result is separate from the unchanged B4 regression.

B4 starts a 1.5 second communicate budget immediately, including interpreter/fixture startup and the deliberate 0.8 second sleep. The cleanup sends SIGTERM, waits 0.12 seconds and sends group SIGKILL without checking the direct child's exit first. Only ProcessLookupError is ignored; a PermissionError bypasses the intended timeout classification and escapes as ADAPTER_ERROR. The outer supervisor releases flock without a durable unresolved admission fence. These control-flow defects are confirmed by the preserved source. Timing and error details of this run are in LEGACY_DIAGNOSTIC.json.

- Observation label: EPERM_ON_ZOMBIE_ONLY_GROUP_REPRODUCED_OS_POLICY_NOT_PROVEN.
- Legacy owner: FAILED_SAFE, ADAPTER_ERROR.
- Legacy contender: SKIPPED_LOCK_HELD.
- Owned unreaped zombie signal-zero probe: {'pid': 89151, 'pgid': 89151, 'pre_reap_state': 'Z', 'errno': 1, 'name': 'EPERM', 'exit': 0}.
- Error trace: [{'event': 'communicate_timeout', 'monotonic': 2.20279625, 'elapsed': 1.502474625, 'timeout': 1.5, 'stdout_bytes': 0, 'ready_seen': True, 'pid': 89137, 'pgid': 89137, 'sid': 89137, 'supervisor_uid': 501}, {'event': 'killpg_error', 'monotonic': 2.50725925, 'signal': 9, 'errno': 1, 'name': 'EPERM', 'pid': 89137, 'lookup_errno': 3}, {'event': 'killpg_zero_after_error', 'monotonic': 2.507428333, 'errno': 1, 'name': 'EPERM', 'pid': 89137, 'lookup_errno': 3}, {'event': 'group_status_after_error', 'monotonic': 2.648261666, 'rows': [['89137', '89137', 'Z']], 'probe_exit': 0}].

This investigation does not assign an unproven OS security-policy cause. R1 starts the active deadline after READY, has its own cleanup budget, never sends a group signal in the new candidate, verifies direct-child completion and leaves a durable fence for incomplete or escaped work. Original behavior and adjusted candidate behavior are recorded separately.

Timing rerun trace: []
