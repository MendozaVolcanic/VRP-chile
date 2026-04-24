"""reprocess_bbox_beneficiarios.py — reproceso Llaima + Copahue con bbox ROI.

Corre en paralelo al daytime_p31 que procesa PCC/Lastarria/Lascar.
Llaima y Copahue tienen 80% y 69% de refs MIROVA a >25 km del vent —
circle ROI los perdia; bbox los captura.

Ventana 2026-04-01 -> 2026-04-22 (paridad temporal con daytime_p31).

Timeouts: Llaima 2.5h, Copahue 2.5h. Total 5h aprox.
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG = ROOT / "logs" / "reprocess_bbox.log"


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_stage(name, cmd, timeout_sec):
    log(f"=== BEGIN {name} (timeout {timeout_sec/3600:.1f}h) ===")
    log(f"    cmd: {' '.join(cmd)}")
    t0 = time.time()
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        start = time.time()
        while True:
            if proc.poll() is not None:
                break
            if time.time() - start > timeout_sec:
                log(f"    TIMEOUT, killing {name}")
                proc.kill()
                proc.wait(timeout=30)
                return 124
            line = proc.stdout.readline()
            if line:
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(f"    | {line.rstrip()}\n")
            else:
                time.sleep(1)
        for line in proc.stdout:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"    | {line.rstrip()}\n")
        rc = proc.returncode
    except Exception as e:
        log(f"    EXCEPTION: {e}")
        rc = -1
    log(f"=== END {name} rc={rc} elapsed={(time.time()-t0)/60:.1f} min ===")
    return rc


def main():
    log("Reproceso bbox beneficiarios (Llaima + Copahue) starting.")
    py = sys.executable
    stages = [
        ("Llaima 2026-04-01 -> 2026-04-22",
         [py, "-u", "scripts/run_pipeline.py",
          "--volcano", "Llaima", "--start", "2026-04-01", "--end", "2026-04-22",
          "--overwrite"],
         int(2.5 * 3600)),
        ("Copahue 2026-04-01 -> 2026-04-22",
         [py, "-u", "scripts/run_pipeline.py",
          "--volcano", "Copahue", "--start", "2026-04-01", "--end", "2026-04-22",
          "--overwrite"],
         int(2.5 * 3600)),
    ]
    t0 = time.time()
    for name, cmd, to in stages:
        run_stage(name, cmd, to)
    log(f"DONE total {(time.time()-t0)/60:.1f} min")


if __name__ == "__main__":
    main()
