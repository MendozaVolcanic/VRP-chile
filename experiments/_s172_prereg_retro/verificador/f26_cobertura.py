# VPR172 V-3 (A108): alertas de la tabla en F26 sin pasada de K a +-120 s. P1: control positivo: ventana V2 reproduce el '1 alerta sin record' de S158 (Lascar 2026-03-11 06:18 OCR) solo en union.
import sys, os, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXP = r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\export_main"
sys.path.insert(0, EXP); sys.path.insert(0, EXP + r"\scripts"); os.chdir(EXP)
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR
coords=bp._coords_por_volcan(); inner=bp.inner_desde_html()
fa=cargar_referencia_unificada(SNAP_CONS,SNAP_OCR); fc=[f for f in fa if f["source"]=="CONS"]
for nom,(d,h) in {"F26":("2026-02-01","2026-03-31"),"V2":("2026-03-01","2026-10-16")}.items():
    recs=bp.cargar_nuestros(coords,inner,(d,h))
    for canal,fl in (("tabla",fc),("union",fa)):
        por_vb,ns,nv,n=bp.indexar_referencia(fl,coords,(d,h),regla_minimas="SN")
        sr=bp.alertas_sin_record(por_vb,recs)
        print(nom,canal,"alertas sin record nuestro a +-2min:",dict(sr),"total",sum(sr.values()))
