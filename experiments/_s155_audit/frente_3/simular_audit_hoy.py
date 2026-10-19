"""F3: corre scripts/auto_audit_weekly.main() SIN TOCAR data/: redirige OUTDIR a D:\vrp-trabajo\temporales\frente_3\audit_hoy.
Es la predicción de lo que el cron de hoy (lunes 2026-10-19, programado 09:00 UTC, histórico de llegada 15-18 UTC)
va a escribir con el corpus de cb90031a. P1: es el mismo código; P2: si el banco falla queda 'error' en el bloque."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, ROOT)
import auto_audit_weekly as aw
aw.OUTDIR = r"D:\vrp-trabajo\temporales\frente_3\audit_hoy"
aw.main()
