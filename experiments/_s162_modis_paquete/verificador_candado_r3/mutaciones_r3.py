# Verificador r3: mutaciones propias sobre copia en memoria de evaluar_paquete.py; corre solo las pruebas indicadas
import sys, os, time, tempfile, shutil, importlib.util, traceback
from pathlib import Path
AQUI = Path(r"C:/vrp-trabajo/s162-modd/experiments/_s162_modis_paquete")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
os.environ["MODD_RAIZ"] = str(AQUI.parents[1])
sys.path.insert(0, str(AQUI))
import probar_evaluar_paquete as T
src0 = (AQUI / "evaluar_paquete.py").read_text(encoding="utf-8")
MUT = {
 "ok_sin_len40": ('and len(str(commit_esperado)) == 40 and commits == [commit_esperado]', 'and commits == [commit_esperado]'),
 "sin_blob_manifiesto": ('    ext["manifiesto"]["blob_manifiesto"] = blob(MC.MANIFIESTO) if Path(MC.MANIFIESTO).exists() else None\n', ''),
 "falla_solo_si_pub_mayor": ('        if pub != runner:', '        if pub > runner:'),
 "falla_solo_si_runner_mayor": ('        if pub != runner:', '        if pub < runner:'),
 "sel_usa_k33": ('pk = predicado([(f.get("k_slim"), f["inner"]) for f in sel])', 'pk = predicado([(f.get("k33_slim"), f["inner"]) for f in sel])'),
 "commit_mayusculas_normaliza": ('commits == [commit_esperado]', 'commits == [str(commit_esperado).lower()]'),
 "prot_sin_k_publica_en_veredicto": ('b["m"]["regla"] == "EMPEORA" or prot_k:', 'b["m"]["regla"] == "EMPEORA":'),
 "manifiesto_fuera_de_controles": ('    ctl.update(externos)', '    ctl.update({k: v for k, v in externos.items() if k != "manifiesto"})'),
 "procedencia_fuera_de_controles": ('    ctl.update(externos)', '    ctl.update({k: v for k, v in externos.items() if k != "procedencia"})'),
 "blobs_fuera_de_controles": ('    ctl.update(externos)', '    ctl.update({k: v for k, v in externos.items() if k != "blobs"})'),
 "fuera_protegida_o_bajo1": ('if not f["_evaluable"] and f.get("lab") == "protegida" and f["_motivo"] in MOTIVOS_SELLADOS]', 'if not f["_evaluable"] and f.get("lab") in ("protegida", "bajo1") and f["_motivo"] in MOTIVOS_SELLADOS]'),
 "motivo_extra_grilla_incompleta": ('MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo", "escena_invalida")', 'MOTIVOS_SELLADOS = ("volcan_fuera_del_granulo", "escena_invalida", "falla_port_grilla_incompleta")'),
}
sel = sys.argv[1:] or list(MUT)
PRU = [t for t in T.PRUEBAS if t.__name__[:3] in ("t01","t11","t12","t17","t20","t21","t22","t33","t34","t35","t36","t37")]
for nombre in sel:
    a, b = MUT[nombre]
    n = src0.count(a)
    if n != 1:
        print(nombre, "SUSTITUCION INVALIDA", n); continue
    td = Path(tempfile.mkdtemp())
    for f in ("evaluar_d25_ded217af4.py", "grillas.json"):
        shutil.copy2(AQUI / f, td / f)
    (td / "evaluar_paquete.py").write_text(src0.replace(a, b), encoding="utf-8")
    t0 = time.time()
    E = T.cargar(str(td / "evaluar_paquete.py"))
    falla, cae = [], []
    for t in PRU:
        try:
            t(E)
        except T.Falla:
            falla.append(t.__name__)
        except Exception as e:
            cae.append((t.__name__, type(e).__name__))
    print("%-34s %s; caen %s  (%.0f s)" % (nombre, ("ATRAPADA por " + ", ".join(falla)) if falla else "VIVA", cae, time.time() - t0), flush=True)
    shutil.rmtree(td, ignore_errors=True)
