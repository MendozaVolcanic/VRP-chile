"""S94 — guardián de disco para el reproc VIIRS local (red de seguridad).

Chequea el disco C: cada 2 min. Si baja de THRESHOLD_GB, MATA todos los procesos
run_pipeline _s94_reproc_viirs (Stop-Process) para no llenar el disco y romper el
sistema. Sale solo cuando ya no hay reproc corriendo o cuando dispara el corte.

NO se commitea (utilitario de sesión). Uso (background):
  python experiments/_s94_audit/disk_guard.py
"""
import time, shutil, subprocess, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

THRESHOLD_GB = 8.0
MATCH = "_s94_reproc_viirs"
PS_COUNT = ("(Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
            f"Where-Object {{ $_.CommandLine -like '*{MATCH}*' }}).Count")
PS_KILL = ("Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | "
           f"Where-Object {{ $_.CommandLine -like '*{MATCH}*' }} | "
           "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }")


def n_running():
    r = subprocess.run(["powershell", "-NoProfile", "-Command", PS_COUNT],
                       capture_output=True, text=True)
    s = (r.stdout or "").strip()
    try:
        return int(s)
    except ValueError:
        return -1


time.sleep(30)  # dar tiempo a que arranquen los reproc
while True:
    free = shutil.disk_usage("C:/").free / 1e9
    n = n_running()
    if n == 0:
        print(f"[guard] no quedan reproc corriendo — salgo. libre={free:.1f} GB")
        break
    if free < THRESHOLD_GB:
        subprocess.run(["powershell", "-NoProfile", "-Command", PS_KILL])
        print(f"[guard] ⚠️ DISCO BAJO {free:.1f} GB < {THRESHOLD_GB} — reproc MATADO")
        break
    print(f"[guard] OK libre={free:.1f} GB, reproc activos={n}", flush=True)
    time.sleep(120)
