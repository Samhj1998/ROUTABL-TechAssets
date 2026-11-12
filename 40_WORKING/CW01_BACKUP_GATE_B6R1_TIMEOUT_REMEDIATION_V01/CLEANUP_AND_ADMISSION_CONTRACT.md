# B6-R1 timeout cleanup and admission contract

The candidate only launches the pinned synthetic worker in this directory. Its command-line production entrypoint is disabled. The original B4, B5 and B6 tests run from verified, disposable copies. None of their assertions or timeout constants are changed.

| State | Meaning |
| --- | --- |
| FIXTURE_COMPLETED / FIXTURE_COMPLETED_DELAYED | The current token-bound completion event arrived, the process exited with zero, the output channel closed, tracked fixtures were absent or zombies, and the lock, media predicate and pins still matched. This is fixture evidence only. |
| TIMEOUT_CLEANED | The active-work deadline expired and cleanup was observed. It is a failed work attempt even though the admission fence can be resolved. |
| CLEANUP_PERMISSION_DENIED / CLEANUP_UNCONFIRMED | Signal refusal or lack of termination proof. Preserve the unresolved run and block subsequent runs even after flock release. |
| BLOCKED_UNRESOLVED_RUN | Admission stopped before launching a child. |
| BLOCKED_LOCK_REPLACED / BLOCKED_PIN_CHANGED | The lock inode or policy/program fingerprint changed. Preserve the pending state. |
| RECONCILED | A reviewed fixture run has no live tracked PIDs and the media predicate is explicitly clear. Retain original failure evidence and record review before reopening admission. |

A startup handshake has a separate deadline. Active work has a soft-delay threshold and hard deadline. Cleanup uses a separate bounded budget. The work budget starts with the fixture's READY event. A healthy delay under the hard deadline can complete; an overrun stays failed. On cleanup the candidate first closes the control pipe, then may terminate only its own direct, unreaped Popen child. It sends no signal to an escaped child. The controlled escaped fixture has a bounded self-exit. Unknown descendant identity, incomplete observations and uncertain media block successful completion.

Before child launch, the candidate atomically publishes pending.json. Under the original lock inode, result files use the run ID and are published with fsync, replace and directory fsync. Terminal proof precedes removal of the admission fence. The lock inode is pinned at fixture setup. A supervisor crash can leave ACTIVE with incomplete PID evidence, which requires manual review and stays blocked. Existing success receipts are never a substitute for the current run. PID reuse can cause conservative refusal. The cooperative fixture protocol and process observations do not establish containment for untrusted production descendants.

## Production acceptance still required

Confirm signal policy and provenance on the signed production runner with launch-domain isolation. Require stable process identity, independently track descendants and media state, persist unresolved runs across restarts, and verify atomic publication with approved storage. Establish authorization for any later real cleanup, never infer permission from an old receipt. Verify exclusive write capability, actual backup and linked CAS evidence, final v043 signing and pins, and rollback. Real backup, restore and deployment are NOT_TESTED. Step 5-C remains BLOCKED.

The final candidate records token-bound worker active duration separately from the supervisor's elapsed wait. The observer hard deadline is unchanged; its reaping/scheduling latency is not counted as simulated work when labeling a completed fixture delayed. The final test also observes SIGTERM on a direct non-cooperative fixture with exit -15. No group signal is used by the new candidate.
