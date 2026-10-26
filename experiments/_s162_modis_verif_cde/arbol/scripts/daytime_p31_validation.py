"""daytime_p31_validation.py — reproceso diurno combinado P3.2 + P3.1.

Ventana reducida 2026-03-01 -> 2026-04-22 (52 dias) para que quepa en el
dia. Volcanes: Lastarria (critico, ratio 19.87), Lascar (canary). Chaitén
queda opcional.

Dado el rate de download observado (~1h por dia de datos en overnight
previo), 52 dias en 1 volcan son ~52h — no caben. Pero:
- Si el download falla/timeouts prematuramente, aun asi tenemos mas masa
  que los 4 dias del overnight anterior.
- Los 4 dias Lastarria ya reprocesados con P3.2 solo seran sobreescritos
  con P3.2+P3.1 via --overwrite.

Timeouts mas largos: Lastarria 6h, Lascar 4h, Chaiten 2h. Total 12h.
Si no todo termina, crossmatch final corre sobre lo que haya.

Uso:
  nohup python scripts/daytime_p31_validation.py > logs/daytime_p31_wrapper.log 2>&1 &
  disown
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOG = ROOT / "logs" / "daytime_p31.log"


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_stage(name: str, cmd: list, timeout_sec: int) -> int:
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
    log("Daytime P3.2 + P3.1 validation starting.")
    log("Profile: mirova_equivalent (dnti_contextual=ON + dual_roi=ON).")
    total_t0 = time.time()

    py = sys.executable

    # S15 ajuste: usuario apagara PC ~16:00. Re-plan para caber:
    # ventana abril-only (22 dias) + PCC primero (familiar para geologo)
    # + Lastarria segundo (P3.1 validation critical) + Lascar canary.
    stages = [
        ("PCC 2026-04-01 -> 2026-04-22 (familiar)",
         [py, "-u", "scripts/run_pipeline.py",
          "--volcano", "PuyehueCordonCaulle",
          "--start", "2026-04-01", "--end", "2026-04-22",
          "--overwrite"],
         3 * 3600),
        ("Lastarria 2026-04-01 -> 2026-04-22 (P3.1 CRITICO)",
         [py, "-u", "scripts/run_pipeline.py",
          "--volcano", "Lastarria",
          "--start", "2026-04-01", "--end", "2026-04-22",
          "--overwrite"],
         int(2.5 * 3600)),
        ("Lascar 2026-04-01 -> 2026-04-22 (canary)",
         [py, "-u", "scripts/run_pipeline.py",
          "--volcano", "Lascar",
          "--start", "2026-04-01", "--end", "2026-04-22",
          "--overwrite"],
         int(1.5 * 3600)),
        ("Crossmatch post-P3.1",
         [py, "experiments/27_crossmatch_vs_consolidado.py",
          "--out", "experiments/27_crossmatch_post_p31.json"],
         10 * 60),
        ("Delta report P3.1 (comparar contra P3.2 post y baseline)",
         [py, "experiments/33_p31_delta_report.py"],
         2 * 60),
    ]

    results = []
    for name, cmd, to in stages:
        rc = run_stage(name, cmd, to)
        results.append((name, rc))

    total_min = (time.time() - total_t0) / 60.0
    log("")
    log("=" * 60)
    log(f"DAYTIME RUN DONE. Total elapsed: {total_min:.1f} min")
    for name, rc in results:
        status = "OK" if rc == 0 else f"FAIL rc={rc}"
        log(f"  [{status}] {name}")
    log("=" * 60)


if __name__ == "__main__":
    main()
