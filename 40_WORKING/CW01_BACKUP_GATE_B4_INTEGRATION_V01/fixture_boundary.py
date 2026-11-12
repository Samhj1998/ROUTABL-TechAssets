"""Cooperative Python audit fence for the fixture entrypoints."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
RUNTIME = Path(sys.base_prefix).resolve()
WORKER = str(ROOT / "fixture_worker.py")
PS = ["/bin/ps", "-axo", "pid=,pgid=,stat="]

def install():
    def guard(event, args):
        if event in ("open", "os.listdir", "os.scandir", "os.mkdir", "os.remove", "os.rmdir"):
            if isinstance(args[0], int):
                return
            path = Path(os.fsdecode(args[0])).resolve()
            if path == ROOT or ROOT in path.parents:
                return
            flags = args[2] if event == "open" else 0
            if event == "open" and path == Path("/dev/null") and flags & os.O_ACCMODE == os.O_RDWR and not flags & (os.O_CREAT | os.O_TRUNC):
                return
            if event == "open" and path == Path("/dev/urandom") and not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
                return
            if (event in ("open", "os.listdir", "os.scandir") and RUNTIME in path.parents
                    and not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
                return
            raise PermissionError("FIXTURE_AUDIT_PATH_DENIED")
        if event == "subprocess.Popen":
            program, argv, cwd, _ = args
            if argv == PS and program == PS[0]:
                return
            if (program == sys.executable and argv[:4] == [sys.executable, "-I", "-B", WORKER]
                    and len(argv) == 6 and argv[5] in ("gate", "nas", "grandchild")
                    and cwd is not None and Path(cwd) == ROOT):
                return
            raise PermissionError("FIXTURE_AUDIT_PROCESS_DENIED")
        if event in ("os.system", "os.exec", "os.posix_spawn", "os.rename", "os.symlink", "os.link"):
            raise PermissionError("FIXTURE_AUDIT_OPERATION_DENIED")
    sys.addaudithook(guard)
