"""e1_reprocess.py — S16 E1 reproceso con profile s9_vent_permissive.

Lanza secuencialmente reproceso Tupungatito + Chaiten + Lascar para
validar H1 (vent-path sigma gating S12 mato TPs sub-pixel).

Ventana: 2026-04-08 -> 2026-04-22 (~15 dias). Suficiente para masa
estadistica comparable con abril fixes S15 (ventana 2026-04-01 -> 04-22).

Timeouts por volcan: 3h. Total max 9h pero tipicamente menos (paraleliza).

Output a data/s9_vent_permissive/. NO toca data/mirova_equivalent/
(asi podemos comparar lado a lado).
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG = ROOT / "logs" / "e1_reprocess.log"


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
    log("S16 E1 reproceso con profile s9_vent_permissive.")
    log("H1: verificar que vent-path threshold fijo 1K (n_sigma_vent=0)")
    log("recupera recall Tupungatito y Chaiten a niveles S9.")
    py = sys.executable

    stages = [
        # Tupungatito primero — es el caso crítico, 77 refs MIROVA
        ("Tupungatito 2026-04-08 -> 2026-04-22 (H1 critical)",
         [py, "-u", "scripts/run_pipeline.py",
          "--profile", "s9_vent_permissive",
          "--volcano", "Tupungatito",
          "--start", "2026-04-08", "--end", "2026-04-22",
          "--overwrite"],
         3 * 3600),
        ("Chaiten 2026-04-08 -> 2026-04-22 (H1 secondary)",
         [py, "-u", "scripts/run_pipeline.py",
          "--profile", "s9_vent_permissive",
          "--volcano", "Chaiten",
          "--start", "2026-04-08", "--end", "2026-04-22",
          "--overwrite"],
         3 * 3600),
        ("Lascar 2026-04-08 -> 2026-04-22 (canary)",
         [py, "-u", "scripts/run_pipeline.py",
          "--profile", "s9_vent_permissive",
          "--volcano", "Lascar",
          "--start", "2026-04-08", "--end", "2026-04-22",
          "--overwrite"],
         3 * 3600),
    ]

    t0 = time.time()
    for name, cmd, to in stages:
        run_stage(name, cmd, to)
    log(f"")
    log(f"E1 REPROCESO DONE. Total elapsed: {(time.time()-t0)/60:.1f} min")
    log(f"Output en data/s9_vent_permissive/")
    log(f"Siguiente: correr experiments/34_e1_delta_report.py para comparar")
    log(f"   s9_vent_permissive vs mirova_equivalent en la misma ventana.")


if __name__ == "__main__":
    main()
