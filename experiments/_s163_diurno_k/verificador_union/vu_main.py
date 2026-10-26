# main() de evaluar_con_exclusion vs main() sellado (mismos datos), y con lista vs main() sellado con excluir_dias inyectado.
import os, sys, json, pathlib, io, contextlib, time
os.environ["VRP_PROFILE"]="mirova_equivalent"
AQ=os.path.dirname(os.path.abspath(__file__)); CAR=os.path.dirname(AQ); ROOT=os.path.dirname(os.path.dirname(CAR))
sys.path[:0]=[ROOT, os.path.join(ROOT,"scripts"), CAR]
import evaluar_diurno_k as ev, evaluar_con_exclusion as ex, sustrato_k as sk
raiz, ref, tmp = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]); VOLS=set(sys.argv[4].split(","))
tmp.mkdir(exist_ok=True)
_cr=sk.cargar_ref
sk.cargar_ref=lambda r:[f for f in _cr(r) if f["volcano"] in VOLS]       # sólo para acelerar; igual en los dos lados
import banco_paridad as bp
_vols=list(bp.VOLS)
bp.VOLS=[v for v in _vols if v in VOLS]                                  # idem: sólo cargamos los records de esos volcanes
class Buf(io.StringIO):
    def reconfigure(self,**k): pass
def corre(fn, args):
    buf=Buf(); t=time.time()
    with contextlib.redirect_stdout(buf):
        rc=fn(args)
    return rc, buf.getvalue(), time.time()-t
def juzga(js):
    d=json.loads(pathlib.Path(js).read_text(encoding="utf-8"))
    return json.dumps({k:d[k] for k in ("principal","variantes","final","motivo")}, sort_keys=True, default=str)
def lineas(txt): return [l for l in txt.splitlines() if l.startswith(("COMPUERTAS","VIIRS375:","VIIRS750:","GLOBAL","VARIANTES","VEREDICTO","cobertura diurna","R1","noche, records en un solo"))]
comun=["--raiz",raiz,"--ref",ref,"--sha-codigo","a"*40,"--opcion-e","e-ii"]
(tmp/"vacia.json").write_text(json.dumps({"excluir_dias":[],"consulta_cmr_utc":"vu","evidencia":{}}),encoding="utf-8")
(tmp/"dos.json").write_text(json.dumps({"excluir_dias":["2026-06-24","2026-10-13"],"consulta_cmr_utc":"vu","evidencia":{}}),encoding="utf-8")
fase=sys.argv[5]
if fase=="vacia":
    rc1,o1,t1=corre(ev.main, comun+["--salida",str(tmp/"s_sellado.json")])
    rc2,o2,t2=corre(ex.main, comun+["--excluidos",str(tmp/"vacia.json"),"--salida",str(tmp/"s_union_vacia.json")])
    print("rc",rc1,rc2,"t %.0f %.0f"%(t1,t2))
    print("JSON principal/variantes/final/motivo iguales:", juzga(tmp/"s_sellado.json")==juzga(tmp/"s_union_vacia.json"))
    print("lineas comunes iguales:", lineas(o1)==lineas(o2), len(lineas(o1)), len(lineas(o2)))
    only1=[l for l in o1.splitlines() if l not in o2.splitlines()]; only2=[l for l in o2.splitlines() if l not in o1.splitlines()]
    print("--- lineas que imprime sólo el main sellado:"); [print("  ",l[:160]) for l in only1]
    print("--- lineas que imprime sólo la union:"); [print("  ",l[:260]) for l in only2]
else:
    rc3,o3,t3=corre(ex.main, comun+["--excluidos",str(tmp/"dos.json"),"--salida",str(tmp/"s_union_dos.json")])
    _orig=ev.evaluar
    def par(pasadas, recs, c, b, *a, excluir_dias=(), **kw): return _orig(pasadas, recs, c, b, *a, excluir_dias=set(excluir_dias)|{"2026-06-24","2026-10-13"}, **kw)
    ev.evaluar=par
    rc4,o4,t4=corre(ev.main, comun+["--salida",str(tmp/"s_sellado_dos.json")])
    print("rc",rc3,rc4,"t %.0f %.0f"%(t3,t4))
    print("JSON principal/variantes/final/motivo iguales:", juzga(tmp/"s_union_dos.json")==juzga(tmp/"s_sellado_dos.json"))
    print("lineas comunes iguales:", lineas(o3)==lineas(o4), len(lineas(o3)))
    print(o3.splitlines()[1:6])
    d=json.loads(pathlib.Path(tmp/"s_union_dos.json").read_text(encoding="utf-8"));
    print("principal global:", d["principal"]["global"], "| pasadas", d["principal"]["pasadas"])
    d0=json.loads(pathlib.Path(tmp/"s_union_vacia.json").read_text(encoding="utf-8")) if (tmp/"s_union_vacia.json").exists() else None
    if d0: print("sin lista pasadas", d0["principal"]["pasadas"])
