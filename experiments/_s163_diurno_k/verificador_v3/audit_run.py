import sys, os
root = os.path.abspath(sys.argv[1]).lower().replace("\\","/")
seen = set()
def hook(ev, args):
    if ev == "open":
        p = args[0]
        if isinstance(p, (str, bytes, os.PathLike)):
            try:
                q = os.path.abspath(os.fsdecode(p)).lower().replace("\\","/")
            except Exception:
                return
            if q.startswith(root) and os.path.isfile(q) and "__pycache__" not in q:
                seen.add(q[len(root)+1:])
sys.addaudithook(hook)
import pytest
rc = pytest.main(["-q", "-p", "no:cacheprovider", "-x", "experiments/_s163_diurno_k/test_evaluar_diurno_k.py"])
open(sys.argv[2], "w").write("\n".join(sorted(seen)))
print("rc", rc)
