"""Casos sinteticos contra scripts/revisar_sombra.py de f743d7b8f (arbol/). Cada caso declara el veredicto esperado.
P1 (si estuviera roto, lo veria?): si, cada caso tiene control positivo y negativo del mismo eje.
P2 (instrumento muerto): sale con exit 1 si algun esperado no coincide; imprime el resumen real de los casos clave.
Denominador: casos sinteticos (no hay datos reales de la sombra: no se abrio data/sombra_codigo_mirova/)."""
import sys, json, os, tempfile, subprocess
sys.dont_write_bytecode = True
ARBOL = "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/arbol"
sys.path.insert(0, ARBOL + "/scripts")
import revisar_sombra as rs

SHA = "abc123"
DESDE = "2026-11-06T15:00:05Z"
FIN, INI = "2026-11-06", "2026-10-30"


def rec(sensor, dia, hora="05:30:00", via=True, proc="2026-11-06T15:10:00Z", sha=SHA):
    return {"sensor": sensor, "datetime_utc": f"{dia}T{hora}Z", "via_codigo_mirova": via, "processed_utc": proc,
            "regimen": {"codigo_sha": sha}}


S3 = ("MODIS_AQUA", "VIIRS_NOAA20_750", "VIIRS_NOAA20")


def sanos(dia):
    return [rec(s, dia) for s in S3]


COB_BASE = {"fallas": [], "plataformas": {"MODIS_AQUA": {}, "MODIS_TERRA": {}, "VIIRS_NOAA20_750": {},
            "VIIRS_NOAA21_750": {}, "VIIRS_NOAA20": {}, "VIIRS_NOAA21": {}}, "incidencias": []}


def cob(fallas=(), vacias=()):
    c = json.loads(json.dumps(COB_BASE))
    c["fallas"] = list(fallas)
    c["incidencias"] = [{"tipo": "sin_granulos", "fecha": FIN, "plataforma": p} for p in vacias]
    return c


V750 = ["VIIRS_NOAA20_750", "VIIRS_NOAA21_750"]
V375 = ["VIIRS_NOAA20", "VIIRS_NOAA21"]
MOD = ["MODIS_AQUA", "MODIS_TERRA"]
casos = []


def caso(n, recs, c, esperado_ok, subcad=None, log=""):
    ok, res = rs.revisar(recs, log, INI, FIN, DESDE, c, sha=SHA)
    casos.append((n, ok, esperado_ok, res, subcad))


# --- R1
caso("R1 control: 3 sensores con pasada de fin", sanos(FIN), cob(), True)
caso("R1 3 sensores con pasada de la vispera escrita hoy", sanos("2026-11-05"), cob(), True)
caso("R1 3 sensores con pasada de fin-2 escrita hoy (reemplazo NRT->std)", sanos("2026-11-04"), cob(), False,
     "ningún record de la vía de 2026-11-05 o 2026-11-06")
caso("R1 un sensor solo con fin-3, los otros con fin", sanos(FIN)[:2] + [rec("VIIRS_NOAA20", "2026-11-03")], cob(),
     False, "VIIRS375")
caso("R1 datetime_utc 'AAAA-MM-DD HH:MM:SS' (sin T)",
     [dict(r, datetime_utc=r["datetime_utc"].replace("T", " ").rstrip("Z")) for r in sanos(FIN)], cob(), True)
caso("R1 datetime_utc None en los 3 (cae de la ventana)", [dict(r, datetime_utc=None) for r in sanos(FIN)], cob(), False)
# --- R2
caso("R2 tres sensores vacios en todas las plataformas (catalogo vacio)", [], cob(vacias=MOD + V750 + V375), False,
     "catálogo de CMR vacío")
caso("R2 V750 y V375 vacios, MODIS con pasada", [rec("MODIS_AQUA", FIN)], cob(vacias=V750 + V375), False,
     "catálogo de CMR vacío")
caso("R2 solo V750 vacio (NOTA)", [rec("MODIS_AQUA", FIN), rec("VIIRS_NOAA20", FIN)], cob(vacias=V750), True,
     "NOTA VIIRS750")
caso("R2 solo V375 vacio (NOTA)", [rec("MODIS_AQUA", FIN), rec("VIIRS_NOAA20_750", FIN)], cob(vacias=V375), True,
     "NOTA VIIRS375")
caso("R2 MODIS y V750 vacios, V375 con pasada (OK por diseno)", [rec("VIIRS_NOAA20", FIN)], cob(vacias=MOD + V750),
     True)
caso("R2 MODIS y V375 vacios, V750 con pasada (OK por diseno)", [rec("VIIRS_NOAA20_750", FIN)],
     cob(vacias=MOD + V375), True)
caso("R2 MASCARA: los 3 vacios en fin pero con records de la vispera reescritos hoy", sanos("2026-11-05"),
     cob(vacias=MOD + V750 + V375), True, "")
caso("R2 V750 vacio y V375 sin vacia ni record (FALLA por V375)", [rec("MODIS_AQUA", FIN)], cob(vacias=V750), False,
     "VIIRS375: ningún record")
# --- R3
caso("R3 falla de busqueda del dia fin -> FALLA", sanos(FIN),
     cob([{"fecha": FIN, "producto": "x", "etapa": "busqueda"}]), False, "del 2026-11-06")
caso("R3 falla de dia anterior (fin-1) -> NOTA y verde", sanos(FIN), cob([{"fecha": "2026-11-05", "producto": "x"}]),
     True, "día anterior al último")
caso("R3 falla sin fecha -> FALLA", sanos(FIN), cob([{"producto": "x"}]), False, "cobertura incompleta")
caso("R3 falla con fecha ISO con hora de fin", sanos(FIN), cob([{"fecha": FIN + "T05:00:00Z"}]), False)
caso("R3 falla 'fecha' vacia", sanos(FIN), cob([{"fecha": ""}]), False)
caso("R3 HUECO: dia X=fin-1 perdido (sin records de X), 3 fallas de X, hoy sano -> verde", sanos(FIN),
     cob([{"fecha": "2026-11-05", "producto": "x", "etapa": "descarga"}] * 3), True, "día anterior al último")
caso("R3 log 'Cobertura INCOMPLETA' con fallas solo viejas", sanos(FIN), cob([{"fecha": "2026-11-05"}]), True, None,
     log="Cobertura INCOMPLETA: 1 búsquedas")
caso("R3 log 'Cobertura INCOMPLETA' y fallas vacias", sanos(FIN), cob([]), False, "Cobertura INCOMPLETA",
     log="Cobertura INCOMPLETA: 1")
# --- R5
caso("R5 sano, 0 K", sanos(FIN), cob(), True, "K caídos en la ventana: 0")
caso("R5 sano con K escrito ayer -> verde, linea K=1",
     sanos(FIN) + [rec("MODIS_AQUA", "2026-11-04", via="geo_distinta", proc="2026-11-05T15:10:00Z")], cob(), True,
     "K caídos en la ventana: 1")
caso("R5 K de hoy -> FALLA y linea K=1", sanos(FIN) + [rec("MODIS_AQUA", "2026-11-04", via="geo_distinta")], cob(),
     False, "K caídos en la ventana: 1")
caso("R5 via None (campo ausente) escrito ayer",
     sanos(FIN) + [dict(rec("MODIS_AQUA", "2026-11-04", proc="2026-11-05T15:10:00Z"), via_codigo_mirova=None)], cob(),
     True, "K caídos en la ventana: 1")
caso("R5 FALLA por sensor, la linea K igual aparece", [], cob(), False, "K caídos en la ventana: 0")
mal = 0
for n, ok, esp, res, sub in casos:
    bien = (ok == esp) and (sub is None or sub == "" or sub in res)
    mal += (not bien)
    print(("OK   " if bien else "MAL  ") + f"{n} -> ok={ok}")
    if not bien or "MASCARA" in n or "HUECO" in n:
        print("      " + res.replace("\n", "\n      "))
# cambio de mes
ok, res = rs.revisar([rec(s, "2026-11-30", proc="2026-12-01T15:10:00Z") for s in S3], "", "2026-11-24", "2026-12-01",
                     "2026-12-01T15:00:00Z", cob(), sha=SHA)
print("OK   " if ok else "MAL  ", "R1 cambio de mes: vispera 30-nov cuenta con fin 01-dic -> ok=", ok)
mal += (not ok)
ok, res = rs.revisar([rec(s, "2026-11-29", proc="2026-12-01T15:10:00Z") for s in S3], "", "2026-11-24", "2026-12-01",
                     "2026-12-01T15:00:00Z", cob(), sha=SHA)
print("OK   " if not ok else "MAL  ", "R1 cambio de mes: 29-nov no cuenta -> ok=", ok)
mal += ok
for s, f in [("MODIS_AQUA", "MODIS"), ("MODIS_TERRA", "MODIS"), ("VIIRS_SNPP", "VIIRS375"), ("VIIRS_NOAA21", "VIIRS375"),
             ("VIIRS_NOAA20_750", "VIIRS750"), ("VIIRS_NOAA21_750", "VIIRS750"), ("VIIRS_SNPP_750", "VIIRS750"),
             ("GOES", None)]:
    b = rs.familia(s) == f
    mal += (not b)
    print("OK   " if b else "MAL  ", "familia", s, rs.familia(s))

# R5: main() con GITHUB_STEP_SUMMARY, y rutas de excepcion
d = tempfile.mkdtemp(dir="D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/medidas")
SUMM = os.path.join(d, "summary.md")


def main_con(jsonp, cobp, logp, summary=True, desde=DESDE):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    env.pop("GITHUB_STEP_SUMMARY", None)
    if os.path.exists(SUMM):
        os.remove(SUMM)
    if summary:
        env["GITHUB_STEP_SUMMARY"] = SUMM
    p = subprocess.run([sys.executable, "-B", ARBOL + "/scripts/revisar_sombra.py", "--json", jsonp, "--log", logp,
                        "--cobertura-json", cobp, "--ini", INI, "--fin", FIN, "--desde-utc", desde, "--sha", SHA],
                       capture_output=True, text=True, encoding="utf-8", env=env)
    s = open(SUMM, encoding="utf-8").read() if os.path.exists(SUMM) else None
    return p, s


J = os.path.join(d, "v.json")
C = os.path.join(d, "c.json")
L = os.path.join(d, "l.log")
open(J, "w", encoding="utf-8").write(json.dumps({"records": sanos(FIN)}))
open(C, "w", encoding="utf-8").write(json.dumps(cob()))
open(L, "w").write("")
p, s = main_con(J, C, L)
b = p.returncode == 0 and "K caídos en la ventana: 0" in p.stdout and s and "K caídos en la ventana: 0" in s
print("OK   " if b else "MAL  ", "R5 main verde: stdout y GITHUB_STEP_SUMMARY llevan la linea; rc=", p.returncode)
mal += (not b)
open(J, "w", encoding="utf-8").write(json.dumps({"records": []}))
p, s = main_con(J, C, L)
b = p.returncode == 1 and "K caídos en la ventana: 0" in p.stdout and s and "K caídos en la ventana: 0" in s and "FALLA" in s
print("OK   " if b else "MAL  ", "R5 main rojo: linea en ambos; rc=", p.returncode)
mal += (not b)
p, s = main_con(J, C, L, summary=False)
b = p.returncode == 1 and "K caídos" in p.stdout
print("OK   " if b else "MAL  ", "R5 main sin GITHUB_STEP_SUMMARY: solo stdout; rc=", p.returncode)
mal += (not b)
open(J, "w", encoding="utf-8").write("{no es json")
p, s = main_con(J, C, L)
print("INFO R5 json corrupto: rc=", p.returncode, "| linea K en stdout:", "K caídos" in p.stdout, "| summary:", s is not None,
      "| stderr:", p.stderr.strip().splitlines()[-1:])
open(J, "w", encoding="utf-8").write(json.dumps({"records": sanos(FIN)}))
open(C, "w", encoding="utf-8").write("{roto")
p, s = main_con(J, C, L)
print("INFO R5 cobertura corrupta: rc=", p.returncode, "| linea K en stdout:", "K caídos" in p.stdout, "| summary:", s is not None,
      "| stderr:", p.stderr.strip().splitlines()[-1:])
open(C, "w", encoding="utf-8").write(json.dumps(cob()))
p, s = main_con(J, C, L, desde="")
print("INFO R5 desde-utc vacio: rc=", p.returncode, "| linea K en stdout:", "K caídos" in p.stdout, "| summary:", s is not None,
      "| stderr:", p.stderr.strip().splitlines()[-1:])
print("FALLAN", mal)
sys.exit(1 if mal else 0)
