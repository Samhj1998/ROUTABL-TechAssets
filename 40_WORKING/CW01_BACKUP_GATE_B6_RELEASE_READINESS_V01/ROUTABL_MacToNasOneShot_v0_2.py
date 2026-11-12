"""B6 OneShot candidate. Runs only an injected fixture, never a command."""
from ROUTABL_BackupEvidenceAdapter_v0_1 import evaluate

class FixtureEngine:
    def __init__(self, call):
        self._call = call

    def capture(self):
        return self._call()

def collect(engine, started, clock):
    if type(engine) is not FixtureEngine:
        return "BLOCKED_ENGINE_UNAPPROVED", {}
    try:
        bundle, child = engine.capture()
        ended = clock()
        if ended < started:
            return "EVIDENCE_INVALID", {"reason":"CLOCK_REVERSED"}
        status, report = evaluate(bundle, child, started, ended)
        return status, {"child":child,"evidence":report}
    except TimeoutError:
        return "FAILED_CHILD", {"reason":"FIXTURE_TIMEOUT"}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return "EVIDENCE_INVALID", {}
