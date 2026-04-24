"""overnight_p32_validation.py — Reproceso nocturno P3.2 autonomo.

Ejecuta secuencialmente 3 reprocesos VIIRS (Lastarria, Lascar, Chaiten) con
timeouts per-etapa, luego re-corre el crossmatch vs CSV consolidado y
genera un delta report comparando pre/post P3.2.

Todo se loguea a logs/overnight_p32.log con timestamps. Si una etapa falla
o se pasa del timeout, se mata y continua con la siguiente.

Disenado para correr sin intervencion humana (5h de ventana overnight).

Uso:
  python scripts/overnight_p32_validation.py &
  # revisar luego:
  tail -f logs/overnight_p32.log
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG = ROOT / "logs" / "overnight_p32.log"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_stage(name: str, cmd: list, timeout_sec: int) -> int:
    log(f"=== BEGIN {name} (timeout {timeout_sec//60} min) ===")
    log(f"    cmd: {' '.join(cmd)}")
    t0 = time.time()
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(ROOT),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
        # Stream output to log
        start = time.time()
        while True:
            if proc.poll() is not None:
                break
            if time.time() - start > timeout_sec:
                log(f"    TIMEOUT reached, killing {name}")
                proc.kill()
                proc.wait(timeout=30)
                return 124
            line = proc.stdout.readline()
            if line:
                with open(LOG, "a", encoding="utf-8") as f:
                    f.write(f"    | {line.rstrip()}\n")
            else:
                time.sleep(1)
        # Drain remaining
        for line in proc.stdout:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(f"    | {line.rstrip()}\n")
        rc = proc.returncode
    except Exception as e:
        log(f"    EXCEPTION {name}: {e}")
        rc = -1
    dt = time.time() - t0
    log(f"=== END {name} rc={rc} elapsed={dt/60:.1f} min ===")
    return rc


def main():
    log("Overnight P3.2 validation starting.")
    log(f"Profile activa: mirova_equivalent (Path D dNTI contextual ON).")
    log(f"MODIS local falla por pyhdf (Windows); solo VIIRS se procesa.")
    total_t0 = time.time()

    py = sys.executable

    stages = [
        ("Lastarria Feb-Apr 2026",
         [py, "-u", "scripts/run_pipeline.py",
          "--volcano", "Lastarria",
          "--start", "2026-02-01", "--end", "2026-04-22",
          "--overwrite"],
         2 * 3600),  # 2h max
        ("Lascar Feb-Apr 2026 (canary)",
         [py, "-u", "scripts/run_pipeline.py",
          "--volcano", "Lascar",
          "--start", "2026-02-01", "--end", "2026-04-22",
          "--overwrite"],
         int(1.5 * 3600)),  # 1.5h max
        ("Chaiten Feb-Apr 2026 (0pct recall case)",
         [py, "-u", "scripts/run_pipeline.py",
          "--volcano", "Chaiten",
          "--start", "2026-02-01", "--end", "2026-04-22",
          "--overwrite"],
         3600),  # 1h max
        ("Crossmatch post-P3.2",
         [py, "experiments/27_crossmatch_vs_consolidado.py",
          "--out", "experiments/27_crossmatch_post_p32.json"],
         5 * 60),
        ("Delta report pre/post P3.2",
         [py, "experiments/30_p32_delta_report.py"],
         2 * 60),
    ]

    results = []
    for name, cmd, to in stages:
        rc = run_stage(name, cmd, to)
        results.append((name, rc))

    total_min = (time.time() - total_t0) / 60.0
    log("")
    log("=" * 60)
    log(f"OVERNIGHT RUN DONE. Total elapsed: {total_min:.1f} min")
    for name, rc in results:
        status = "OK" if rc == 0 else f"FAIL rc={rc}"
        log(f"  [{status}] {name}")
    log("=" * 60)
    log("Resultados:")
    log("  - JSONs reprocesados en data/mirova_equivalent/")
    log("  - Crossmatch: experiments/27_crossmatch_post_p32.json")
    log("  - Delta report: experiments/30_p32_delta_report.md")


if __name__ == "__main__":
    main()
