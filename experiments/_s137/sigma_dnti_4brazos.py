"""S137 - cuanto cae el sigma del dNTI con la banda 22 y con el remuestreo.

POR QUE. El umbral efectivo de los Tests 2 y 3 es combinar(C1, mu + C2*sigma). Bajo la conectiva
`min` (la formula del paper, que es lo que corre hoy) el piso C1 gobierna el 100 % de los records
de MODIS y sigma no entra: de ahi el corolario de S136 que cerro estos frentes. Bajo `max` (la
prosa del mismo paper) el umbral ES mu + C2*sigma y sigma es lo unico que decide. Como S136 midio
que NINGUNA de las dos lecturas reproduce a MIROVA, el cierre de esos frentes quedo apoyado en una
lectura refutada. Ver experiments/_s137/EL_CIERRE_DE_S136_ES_CIRCULAR.md.

QUE MIDE. Por granule, pareado, el sigma y el mu del dNTI bajo cuatro configuraciones:

    base      lo que corre hoy (B21 primaria, sin remuestreo)
    b22       B22 primaria y B21 solo donde B22 satura  -> Coppola 2016a p.3, banda L21ok
    regrid    remuestreo a grilla equiespaciada de 1 km -> Coppola 2016a p.3, "requires
              homogenous pixel scale"
    ambos     las dos juntas

NO ES UN A/B DE ADOPCION y no lleva criterio de adopcion pre-registrado, porque no decide nada:
es la medicion del numero que falta. La decision, si el numero da, la toma despues la bateria del
Apendice A con su propio criterio (conservar los 6 positivos Y curar los 3 negativos).

Lo que S133 midio fue el sigma del fondo BT (`diag_sigma_bg_k`), que cae entre 23 y 43 %. Ese NO
es el sigma del dNTI que gobierna los Tests 2 y 3. Son objetos distintos y nadie midio el segundo.

READ-ONLY (A75): monkeypatchea los dos flags en el namespace del modulo y llama a calculate_vrp.
No escribe en data/, no toca pipeline/ ni ningun perfil, no empuja commits.
"""
import io
import json
import os
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import yaml  # noqa: E402
from pipeline.fetch import auth, download_granules, search_granules  # noqa: E402
import pipeline.process_modis as pm  # noqa: E402

DEST = Path(os.environ.get("VRP_DEST", "/tmp/sigma137"))
OUT = HERE / "out_sigma"
PARES = [("MODIS_TERRA_L1B", "MODIS_TERRA_GEO"), ("MODIS_AQUA_L1B", "MODIS_AQUA_GEO")]

# C1 y C2 de la Tabla 1, noche, ROI1. El piso contra el que se compara el contraste.
C1_SUMMIT = 0.003
C2_SUMMIT = 5.0

BRAZOS = {
    "base":   {"b22": False, "regrid": False},
    "b22":    {"b22": True,  "regrid": False},
    "regrid": {"b22": False, "regrid": True},
    "ambos":  {"b22": True,  "regrid": True},
}


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g)[:80]


def ginicio(g):
    try:
        s = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
        return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None


def volcan(nombre):
    d = yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))
    vs = d["volcanoes"] if isinstance(d, dict) and "volcanoes" in d else d
    for v in vs:
        if v.get("name") == nombre:
            return v
    raise SystemExit("volcan no encontrado: " + nombre)


def correr(l1b, geo, v, brazo):
    """Una pasada con los flags del brazo. Devuelve el diag, o None."""
    cfg = BRAZOS[brazo]
    prev = (pm.ENABLE_MODIS_B22_PRIMARY, pm.ENABLE_UTM_REGRID)
    pm.ENABLE_MODIS_B22_PRIMARY = cfg["b22"]
    pm.ENABLE_UTM_REGRID = cfg["regrid"]
    try:
        rec = pm.calculate_vrp(
            l1b, geo,
            v["lat"], v["lon"], float(v.get("radius_km", 25)),
            vent_lat=v.get("vent_lat", v["lat"]), vent_lon=v.get("vent_lon", v["lon"]),
            vent_radius_km=4.0, inner_radius_km=float(v.get("inner_radius_km", 5)),
            exclude_zones=v.get("exclude_zones"), active_water_bodies=None,
            lbg_global_compatible=False, local_kernel_bg_compatible=False,
        )
    except Exception as e:
        print("      " + brazo + ": EXCEPCION " + str(e), flush=True)
        traceback.print_exc()
        return None
    finally:
        pm.ENABLE_MODIS_B22_PRIMARY, pm.ENABLE_UTM_REGRID = prev
    if rec is None:
        return None
    return {
        "mu_dnti": rec.get("diag_mu_dnti"),
        "sd_dnti": rec.get("diag_sd_dnti"),
        "sd_deti": rec.get("diag_sd_deti"),
        "sigma_bg_k": rec.get("diag_sigma_bg_k"),
        "n_first_pass": rec.get("diag_n_first_pass_pixels"),
        "nti_max": rec.get("diag_nti_max"),
        "vrp_pc_mw": (rec.get("primary_cluster") or {}).get("vrp_mw"),
    }


def mediana(xs):
    xs = sorted(x for x in xs if isinstance(x, (int, float)))
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def resumen(filas):
    print("\n\n" + "=" * 84, flush=True)
    print("RESUMEN, sigma del dNTI por brazo", flush=True)
    print("=" * 84, flush=True)
    print("pares por granule: " + str(len(filas)))
    for nombre in sorted({f["volcan"] for f in filas}):
        sub = [f for f in filas if f["volcan"] == nombre]
        print("\n" + nombre + "  n=" + str(len(sub)))
        cab = "  {:8} {:>10} {:>10} {:>10} {:>14} {:>11}".format(
            "brazo", "sd_dNTI", "mu+5sd", "veces C1", "caida vs base", "n_1er_paso")
        print(cab)
        base_sd = mediana([f["base"]["sd_dnti"] for f in sub if f.get("base")])
        for brazo in BRAZOS:
            vals = [f[brazo] for f in sub if f.get(brazo)]
            if not vals:
                print("  {:8}  sin datos".format(brazo))
                continue
            sd = mediana([x["sd_dnti"] for x in vals])
            mu = mediana([x["mu_dnti"] for x in vals])
            npx = mediana([x["n_first_pass"] for x in vals])
            if sd is None or mu is None:
                print("  {:8}  sin sigma".format(brazo))
                continue
            thr = mu + C2_SUMMIT * sd
            veces = thr / C1_SUMMIT
            caida = (base_sd / sd) if (base_sd and sd) else None
            cs = "-" if caida is None else "{:.2f}x".format(caida)
            print("  {:8} {:10.6f} {:10.6f} {:10.2f} {:>14} {:>11}".format(
                brazo, sd, thr, veces, cs, str(npx)))
    print("\nLectura: 'veces C1' es cuanto excede el contraste al piso de 0,003. Bajo la conectiva")
    print("`max` ese numero ES el factor por el que el umbral supera al piso; con 1,0 las dos")
    print("lecturas del paper coinciden y la contradiccion del texto se vuelve inmaterial.")


def main():
    # El wrapper de UTF-8 va DENTRO de main, nunca a nivel de modulo: importar este
    # archivo desde un test no debe tocar el stdout del proceso que lo importa. A nivel
    # de modulo rompia la captura de pytest con "I/O operation on closed file", y el
    # guard de tests/test_sigma_dnti_s137.py ahora lo vigila.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    nombres = [s.strip() for s in os.environ.get("SIGMA_VOLCANES", "Lascar,Villarrica").split(",")]
    dias = int(os.environ.get("SIGMA_DIAS", "20"))
    fin = datetime.strptime(os.environ.get("SIGMA_FIN", "2026-08-31"), "%Y-%m-%d")
    OUT.mkdir(parents=True, exist_ok=True)
    auth()
    from run_pipeline import is_nighttime  # noqa: E402

    filas = []
    for nombre in nombres:
        v = volcan(nombre)
        print("\n" + "=" * 84, flush=True)
        print(nombre + ": " + str(dias) + " dias hasta " + str(fin.date()), flush=True)
        print("=" * 84, flush=True)
        for k in range(dias):
            dia = fin - timedelta(days=k)
            for l1b_key, geo_key in PARES:
                try:
                    grs = search_granules(l1b_key, v["lat"], v["lon"],
                                          float(v.get("radius_km", 25)), dia)
                except Exception as e:
                    print("  " + str(dia.date()) + " " + l1b_key + ": busqueda fallo, " + str(e),
                          flush=True)
                    continue
                for g in grs:
                    nom, ini = gname(g), ginicio(g)
                    if ini is None or not is_nighttime(v["lat"], v["lon"], ini):
                        continue
                    try:
                        paths = [Path(p) for p in download_granules([g], DEST)]
                        if not paths:
                            continue
                        gg = search_granules(geo_key, v["lat"], v["lon"],
                                             float(v.get("radius_km", 25)), dia)
                        sel = [x for x in gg if ini.strftime("%H%M") in gname(x)]
                        geo = ([Path(p) for p in download_granules(sel[:1], DEST)] or [None])[0]
                    except Exception as e:
                        print("  " + nom + ": descarga fallo, " + str(e), flush=True)
                        continue
                    fila = {"volcan": nombre, "granule": nom, "inicio": str(ini)}
                    for brazo in BRAZOS:
                        fila[brazo] = correr(paths[0], geo, v, brazo)
                    if fila.get("base") is None:
                        continue
                    filas.append(fila)
                    b, a = fila["base"], fila.get("ambos")
                    print("  " + nom + " " + str(ini) + "  sd_dnti base=" +
                          str(b.get("sd_dnti")) + "  ambos=" +
                          str(a.get("sd_dnti") if a else None), flush=True)
            json.dump(filas, open(OUT / "sigma_dnti_4brazos.json", "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)

    resumen(filas)
    json.dump(filas, open(OUT / "sigma_dnti_4brazos.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
