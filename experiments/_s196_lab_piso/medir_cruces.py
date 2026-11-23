# -*- coding: utf-8 -*-
"""S196: cuántas pasadas nocturnas tienen una celda de la zona A que cruzaría cada piso candidato del umbral
contextual, medido sobre records ya publicados (sin reprocesar). Sólo lectura.

POR QUÉ existe. El barrido del factor s (S195, run 45114681532) se aplanó: de s = 5 a s = 1 aparecen 5 publicaciones
nuevas en un mes de tres volcanes, porque en la región sensible el umbral nocturno es max(mu + s * sd, piso) y con
s bajo manda el piso de 0,003 (experiments/_s195_lab_paso3/salida_cuanto_manda_el_piso.txt). Antes de sellar una
grilla de pisos hay que saber cuántas pasadas se mueven con cada piso, para que los brazos se separen.

QUÉ MIDE. Cada record de la vía guarda, por pase, mu y sd del contraste NTI y ETI de toda la grilla, y la «celda
decisiva» del 7 x 7 alrededor del cráter: la que más cerca estuvo de alertar con los umbrales de producción, con sus
contrastes c_nti y c_eti (pipeline/mirova_v750_codigo.py::celda_decisiva). Para esa celda, si está en la zona A
(región sensible BOX == 2 a <= inner_radius_km del cráter, mascara_zona_a) y no alertó en producción (margen <= 1),
se calcula si alertaría con el umbral u(p, s) = max(mu + s * sd, p) en NTI y en ETI a la vez (la regla del .m, l.
397-399), para cada piso p y s en (5, 1, 0). s = 5 es el de producción; s = 1 y s = 0 dicen cuánto queda escondido
detrás del término mu + s * sd.

LÍMITES (escritos antes de mirar la salida):
  - Es una ESTIMACIÓN por pasada, de signo incierto, no un conteo de celdas: el record guarda una sola celda por
    pasada. Subestima porque otra celda de la zona A podría cruzar (la decisiva se elige con el umbral de producción,
    y con otro umbral el orden puede cambiar; en VIIRS 375 y en la caja sens de Tupungatito muchas celdas de la zona
    A caen fuera del 7 x 7, la salida dice cuántas). Sobrestima porque una celda que alerta no siempre publica: si
    su VRP sale negativo el record queda con vrp_mw 0 (verificador S196: Chillán MODIS_TERRA 2026-03-07 02:15 alerta
    en el barrido de s con VRP -0,498 MW y no publica). La primera versión de este texto la llamaba «cota inferior»;
    la validación de abajo la desmiente en los dos sentidos.
  - Ignora el efecto del primer pase sobre el segundo (una alerta nueva del pase 1 sale del fondo del pase 2).
  - La sección 7 compara la predicción para el barrido de s ya corrido (p = 0,003 y s de 4,5 a 1,0) con las
    publicaciones nuevas reales de ese barrido: es el control de que el instrumento puede dar distinto de cero y
    acierta donde se puede comprobar (A116).

Uso (desde la raíz del worktree; el argumento es una carpeta temporal para la referencia de MIROVA, que se baja
fresca como en el banco; sin él se salta la sección 8):
  python experiments/_s196_lab_piso/medir_cruces.py <carpeta_temporal> > experiments/_s196_lab_piso/salida_medir_cruces.txt
"""
from __future__ import annotations

import collections
import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline.geo_utils import get_detection_anchor  # noqa: E402

ZONA = ("Lascar", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica",
        "Copahue", "Chaiten", "Lastarria")
INICIO = "2026-03-01"
PISO_PROD = 0.003           # n2 = e2 nocturnos de la región 2 (.m l. 177-199; detectar_mirova)
S_PROD = 5.0
PISOS = (0.003, 0.00275, 0.0025, 0.00225, 0.002, 0.00175, 0.0015, 0.00125, 0.001, 0.0005, 0.0)
S_VARIANTES = (5.0, 3.0, 2.0, 1.0, 0.0)
RUN_BARRIDO = "45114681532"
RAMA_BARRIDO = "origin/s195-lab-barrido/%s" % RUN_BARRIDO
BASE_BARRIDO = "experiments/_s195_lab_paso3/salidas/%s" % RUN_BARRIDO
BRAZOS_S = {"_s195_lab_s45": 4.5, "_s195_lab_s40": 4.0, "_s195_lab_s35": 3.5, "_s195_lab_s30": 3.0,
            "_s195_lab_s25": 2.5, "_s195_lab_s20": 2.0, "_s195_lab_s15": 1.5, "_s195_lab_s10": 1.0}


def familia(sensor):
    if sensor.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if sensor.endswith("_750") else "VIIRS375"


def mascaras_zona_a():
    """{(volcán, familia): (zona_a, celda_crater)} con las mismas funciones que usa calcular_vrp_granulo."""
    vols = {v["name"]: v for v in yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    out = {}
    for nombre in ZONA:
        v = vols[nombre]
        lat, lon = get_detection_anchor(v)
        inner = float(v["inner_radius_km"])
        for fam in ("VIIRS750", "MODIS", "VIIRS375"):
            cfg = MV.FAMILIAS[fam]
            g = MV.grilla_del_volcan(nombre, paso_m=cfg["paso_m"], clave_roi=cfg["clave_roi"])
            if g is None:
                continue
            if cfg.get("roi1_half_m") is not None:
                box = MV.caja_v375(g, lat, lon, lado_sensible=cfg["lado_sensible"], half_roi1_m=cfg["roi1_half_m"])
            else:
                box = MV.caja_roi(g.get("roi", "def"), n=g["n"], celda_crater=MV.celda_de(g, lat, lon),
                                  inner_km=inner, lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"],
                                  paso_m=g["paso"])
            box = np.array(box, float)
            box[:, [0, -1]] = np.nan
            box[[0, -1], :] = np.nan
            za = MV.mascara_zona_a(box, MV.posicion_de(g, lat, lon), float(g["paso"]), inner)
            out[(nombre, fam)] = (za, MV.celda_de(g, lat, lon))
    return out


def umbral(mu, sd, s, p):
    """max(mu + s * sd, p) con la misma regla de NaN del .m (sin término finito manda el piso)."""
    if mu is None or sd is None or not np.isfinite(mu + s * sd):
        return p
    return max(mu + s * sd, p)


def evaluar_record(r, masks):
    """None si el record no entra; si entra, dict con la clase de la pasada y, si es candidata, la celda."""
    if str(r.get("datetime_utc", "")) < INICIO or not r.get("via_codigo_mirova"):
        return None
    dg = r.get("diag_codigo_mirova") or {}
    if dg.get("dayflag") != 0 or dg.get("motivo_vacio"):
        return None
    s1 = dg.get("s1") or {}
    cd = s1.get("celda_decisiva")
    fam = familia(r.get("sensor", ""))
    sin_alertas = (dg.get("n_abs") or 0) + (dg.get("n_p1") or 0) + (dg.get("n_p2") or 0) == 0
    base = {"fam": fam, "sin_alertas": sin_alertas, "p1": s1.get("pasada1")}
    if not cd:
        return dict(base, clase="sin_celda")
    if cd["margen"] > 1:
        return dict(base, clase="ya_alerta")
    za = masks[r["_vol"], fam][0]
    if za is None or not za[cd["fila"], cd["col"]]:
        return dict(base, clase="fuera_zona_a")
    dp = s1.get("pasada%d" % cd["pase"]) or {}
    return dict(base, clase="candidata", cd=cd, dp=dp)


def _u(dp, campo, s, p):
    """Umbral de la región 2 con factor s y piso p. Con s = 5 (el de producción) y p <= 0,003 se parte del umbral
    guardado u2 = max(mu + 5 sd, 0,003): si es mayor que 0,003 manda el término y no depende de p; si es 0,003, el
    término es <= 0,003 y el umbral es max(término, p). POR QUÉ no recalcular siempre mu + 5 sd: mu y sd están
    redondeados a 6 decimales en el record y el recálculo puede quedar 3e-6 bajo el umbral real, lo que en la primera
    corrida dio 1 cruce falso con el piso de producción (Láscar MODIS_AQUA 2026-06-26 07:40, margen 0,99945)."""
    mu, sd, u2 = dp.get("mu_" + campo), dp.get("sd_" + campo), dp.get("u_%s2" % campo)
    if s == S_PROD and p <= PISO_PROD and u2 is not None:
        if u2 > PISO_PROD:
            return u2
        return max(min(umbral(mu, sd, s, 0.0), PISO_PROD), p) if mu is not None and sd is not None else p
    return umbral(mu, sd, s, p)


def cruza(e, s, p, solo=None):
    """¿La celda decisiva de una candidata alerta con piso p y factor s? solo = "nti" o "eti" baja un solo piso."""
    dp, cd = e["dp"], e["cd"]
    pn = p if solo in (None, "nti") else PISO_PROD
    pe = p if solo in (None, "eti") else PISO_PROD
    return cd["c_nti"] > _u(dp, "nti", s, pn) and cd["c_eti"] > _u(dp, "eti", s, pe)


def cargar(ruta_o_texto):
    d = json.loads(ruta_o_texto)
    return d["records"] if isinstance(d, dict) else d


def git_show(ruta):
    r = subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (RAMA_BARRIDO, ruta)], capture_output=True)
    return None if r.returncode else r.stdout.decode("utf-8")


def medir_produccion(masks):
    print("== 1. Producción (data/mirova_equivalent, vía, nocturnas válidas, desde %s, 10 volcanes de la zona A)"
          % INICIO)
    tot = collections.Counter()
    ult = ""
    evs = []
    for v in ZONA:
        for r in cargar((ROOT / "data" / "mirova_equivalent" / ("%s.json" % v)).read_text(encoding="utf-8")):
            r["_vol"] = v
            e = evaluar_record(r, masks)
            if e is None:
                continue
            e["vol"], e["sensor"], e["dt"] = v, r.get("sensor"), r.get("datetime_utc")
            ult = max(ult, str(r.get("datetime_utc", "")))
            evs.append(e)
            tot[(e["fam"], e["clase"])] += 1
    print("última pasada leída:", ult)
    print("familia | pasadas | ya_alerta | sin_celda | celda decisiva fuera de zona A | candidatas (zona A, sin alerta)")
    for fam in ("MODIS", "VIIRS750", "VIIRS375"):
        n = sum(c for (f, _), c in tot.items() if f == fam)
        print("%s | %d | %d | %d | %d | %d" % (fam, n, tot[(fam, "ya_alerta")], tot[(fam, "sin_celda")],
                                              tot[(fam, "fuera_zona_a")], tot[(fam, "candidata")]))

    print("\n== 2. ¿Cuándo manda el piso con s = 5? Pasadas (pase 1) con mu + 5 sd < p, por familia")
    print("familia | p | NTI manda el piso | ETI manda el piso | n")
    for fam in ("MODIS", "VIIRS750", "VIIRS375"):
        ps = [e["p1"] for e in evs if e["fam"] == fam and e["p1"] and e["p1"].get("sd_nti") is not None]
        for p in PISOS:
            nn = sum(1 for x in ps if umbral(x["mu_nti"], x["sd_nti"], S_PROD, 0.0) < p)
            ne = sum(1 for x in ps if x.get("sd_eti") is not None and umbral(x["mu_eti"], x["sd_eti"], S_PROD, 0.0) < p)
            print("%s | %.5f | %d | %d | %d" % (fam, p, nn, ne, len(ps)))
        qn = np.percentile([x["mu_nti"] + 5 * x["sd_nti"] for x in ps], [10, 25, 50, 75, 90])
        qe = np.percentile([x["mu_eti"] + 5 * x["sd_eti"] for x in ps if x.get("sd_eti") is not None],
                           [10, 25, 50, 75, 90])
        print("%s cuantiles 10/25/50/75/90 de mu + 5 sd: NTI %s | ETI %s"
              % (fam, " ".join("%.5f" % q for q in qn), " ".join("%.5f" % q for q in qe)))

    print("\n== 3. Candidatas cuya celda decisiva alertaría (estimación de pasadas con alerta nueva en la zona A)")
    print("s | p | MODIS | VIIRS750 | VIIRS375 | total | de ellas en escenas sin ninguna alerta en producción")
    cand = [e for e in evs if e["clase"] == "candidata"]
    for s in S_VARIANTES:
        for p in PISOS:
            c = collections.Counter(e["fam"] for e in cand if cruza(e, s, p))
            n0 = sum(1 for e in cand if e["sin_alertas"] and cruza(e, s, p))
            print("%.1f | %.5f | %d | %d | %d | %d | %d" % (s, p, c["MODIS"], c["VIIRS750"], c["VIIRS375"],
                                                         sum(c.values()), n0))

    print("\n== 4. Bajar un solo piso (NTI o ETI) contra los dos, con s = 5, 3 y 1")
    print("s | p | sólo NTI | sólo ETI | los dos")
    for s in (5.0, 3.0, 1.0):
        for p in PISOS:
            print("%.1f | %.5f | %d | %d | %d" % (s, p, sum(1 for e in cand if cruza(e, s, p, "nti")),
                                                  sum(1 for e in cand if cruza(e, s, p, "eti")),
                                                  sum(1 for e in cand if cruza(e, s, p))))

    print("\n== 5. Con s = 5, por volcán (los dos pisos), pasadas nuevas en la zona A")
    print("volcán | " + " | ".join("%.5f" % p for p in PISOS))
    for v in ZONA:
        print("%s | %s" % (v, " | ".join(str(sum(1 for e in cand if e["vol"] == v and cruza(e, 5.0, p)))
                                         for p in PISOS)))
    return evs


def medir_cobertura(masks):
    print("\n== 6. Celdas de la zona A dentro y fuera del 7 x 7 de la celda decisiva")
    print("volcán familia | celdas zona A | fuera del 7 x 7")
    for (v, fam), (za, cc) in sorted(masks.items()):
        if za is None:
            continue
        r, q = np.indices(za.shape)
        dentro = (abs(r - cc[0]) <= 3) & (abs(q - cc[1]) <= 3)
        print("%s %s | %d | %d" % (v, fam, int(za.sum()), int((za & ~dentro).sum())))


def validar(masks):
    print("\n== 7. Validación del instrumento contra el barrido de s ya corrido (run %s, p = 0,003)" % RUN_BARRIDO)
    print("brazo s | predichas (celda decisiva del control) | nuevas reales (vrp_mw > 0 en el brazo y 0 en el "
          "control) | predichas y reales | reales no predichas | predichas no reales")
    lista = subprocess.run(["git", "-C", str(ROOT), "ls-tree", "--name-only",
                            "%s:%s/_s195_lab_control" % (RAMA_BARRIDO, BASE_BARRIDO)],
                           capture_output=True, text=True).stdout.split()
    vols = sorted(x[:-5] for x in lista if x.endswith(".json"))
    control = {}
    for v in vols:
        for r in cargar(git_show("%s/_s195_lab_control/%s.json" % (BASE_BARRIDO, v))):
            control[(v, r.get("sensor"), r.get("datetime_utc"))] = r
    for brazo, s in BRAZOS_S.items():
        reales = set()
        for v in vols:
            for r in cargar(git_show("%s/%s/%s.json" % (BASE_BARRIDO, brazo, v))):
                k = (v, r.get("sensor"), r.get("datetime_utc"))
                if (r.get("vrp_mw") or 0) > 0 and not ((control.get(k) or {}).get("vrp_mw") or 0) > 0:
                    reales.add(k)
        pred = set()
        for k, r in control.items():
            if (r.get("vrp_mw") or 0) > 0:
                continue
            r = dict(r, _vol=k[0])
            e = evaluar_record(r, masks)
            if e and e["clase"] == "candidata" and cruza(e, s, PISO_PROD):
                pred.add(k)
        print("%.1f | %d | %d | %d | %s | %s" % (s, len(pred), len(reales), len(pred & reales),
                                                 sorted(reales - pred), sorted(pred - reales)))
    print("volcanes del barrido:", vols)


def tasa_noche_predicha(evs_por_clave, dest, s_lab=S_PROD):
    """Tasa de publicación por noche negativa limpia de volcán (la unidad sellada del paso 2, §5 del pre-registro
    S194) que tendría cada brazo de piso con s = 5, si sólo se sumaran las pasadas que predice la celda decisiva.
    Es una estimación de signo incierto, como la celda decisiva (ver LÍMITES)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import banco_paridad as bp
    print("\n== 8. Tasa por noche negativa limpia (tres sensores) predicha por brazo, s = %.1f (estimación)" % s_lab)
    coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
    fin = max(k[2] for k in evs_por_clave)[:10]
    ventana = (INICIO, fin)
    info = bp.bajar_remoto(Path(dest))
    filas = bp.cargar_referencia_unificada(Path(info["registro_vrp_consolidado.csv"]["path"]),
                                           Path(info["registro_vrp_ocr.csv"]["path"]))
    por_vb, noche_sensor, noche_volcan, _ = bp.indexar_referencia(filas, coords, ventana, regla_minimas=bp.MODO_MINIMAS)
    recs = [r for r in bp.cargar_nuestros(coords, inner, ventana, excluir_escenas_invalidas=True) if r["vol"] in ZONA]
    bp.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    noches = collections.defaultdict(list)
    for r in recs:
        noches[(r["vol"], r["noche"])].append(r)
    neg = [v for v in noches.values() if any(r["lab"] == "neg_limpio" for r in v)
           and not any(r["lab"] in ("pos", "far_ref") for r in v)]
    print("ventana %s a %s; noches negativas limpias: %d; referencia de MIROVA: consolidado %s, OCR %s"
          % (INICIO, fin, len(neg), info["registro_vrp_consolidado.csv"]["sha"], info["registro_vrp_ocr.csv"]["sha"]))
    print("p | noches que publican | tasa | pasadas neg_limpio que publican / pasadas neg_limpio")
    npas = sum(1 for v in neg for r in v if r["lab"] == "neg_limpio")
    for p in PISOS:
        def pub(r):
            e = evs_por_clave.get((r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")))
            return r["pub"] or bool(e and e["clase"] == "candidata" and cruza(e, s_lab, p))
        n = sum(1 for v in neg if any(pub(r) for r in v))
        k = sum(1 for v in neg for r in v if r["lab"] == "neg_limpio" and pub(r))
        print("%.5f | %d | %.4f | %d / %d" % (p, n, n / len(neg), k, npas))


def unidades_predichas(evs_por_clave, nhi_dir, s_lab=S_PROD, bajar=True):
    """Cuántas unidades S y N tendría cada volcán con serie NHI en cada brazo de piso (s = 5), con el pareo sellado
    del pre-registro S194 (§3.2 a §3.4) y la estimación de la celda decisiva como laboratorio. POR QUÉ: dice antes de correr
    nada cuántos volcanes pueden votar (SIN PODER bajo 10 unidades S o N). NO lee ni imprime la alerta NHI de ninguna
    unidad: sólo cuenta unidades, para no mirar el resultado de la prueba (la verdad del veredicto)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("evaluar_s194", ROOT / "experiments" / "_s194_lab_zona_a" / "evaluar.py")
    E = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(E)
    fin = max(k[2] for k in evs_por_clave)[:10]
    if bajar:
        E.bajar_nhi(nhi_dir)
    nhi = E.cargar_nhi(nhi_dir)
    prod = E.cargar_pasadas(ROOT / "data" / "mirova_equivalent", E.VENTANA_INICIO, fin)
    print("\n== 9. Unidades S y N predichas por volcán NHI y brazo (s = %.1f; ventana NHI %s a %s; sin mirar alertas)"
          % (s_lab, E.VENTANA_INICIO, fin))
    print("volcán | " + " | ".join("%.5f S/N" % p for p in PISOS))
    filas = {v: [] for v in E.VOLCANES_NHI}
    for p in PISOS:
        lab = []
        for x in prod:
            e = evs_por_clave.get((x["vol"], x["sensor"], x["dt"].strftime("%Y-%m-%d %H:%M")))
            extra = bool(e and e["clase"] == "candidata" and not x["invalida"] and cruza(e, s_lab, p))
            lab.append(dict(x, pub=x["pub"] or extra))
        noches = E.clasificar_noches(lab, prod)
        for v in E.VOLCANES_NHI:
            nv = {n: info for (vv, n), info in noches.items() if vv == v}
            uni = E.parear_nhi(nhi.get(v, []), nv, fin=fin)
            filas[v].append("%d/%d" % (sum(1 for u in uni.values() if u["clase"] == "S"),
                                       sum(1 for u in uni.values() if u["clase"] == "N")))
    for v in E.VOLCANES_NHI:
        print("%s | %s" % (v, " | ".join(filas[v])))


def main():
    masks = mascaras_zona_a()
    evs = medir_produccion(masks)
    medir_cobertura(masks)
    validar(masks)
    if len(sys.argv) > 1:
        por_clave = {(e["vol"], e["sensor"], e["dt"]): e for e in evs}
        for i, s in enumerate((S_PROD, 3.0, 2.0, 1.0)):   # las s menores que 5 informan la pregunta 1 del pre-registro
            tasa_noche_predicha(por_clave, sys.argv[1], s_lab=s)
            unidades_predichas(por_clave, str(Path(sys.argv[1]) / "nhi"), s_lab=s, bajar=(i == 0))


if __name__ == "__main__":
    main()
