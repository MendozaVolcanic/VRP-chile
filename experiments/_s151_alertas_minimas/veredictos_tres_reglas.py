# -*- coding: utf-8 -*-
"""Decision D-9 (issue #811): los veredictos ya publicados, re-corridos con las tres reglas de las alertas minimas
y con la funcion UNICA que quedo en el repo (scripts/clase_mirova.py::aplicar_regla_minimas, a traves de
scripts/banco_paridad.py::indexar_referencia(regla_minimas=...)).

POR QUE. Nicolas aprobo SN ("MIROVA no vio nada") con la condicion de probar todas las opciones. Este script no
mide nada nuevo: vuelve a contar, sobre las MISMAS publicaciones de cada brazo, los tres resultados que cita el
estudio (meses de S150 en VIIRS 375, VIIRS 750 y Chillan) y el techo del A/B de D22, con cada regla:
  original  la etiqueta del scraper (control: reproduce los totales publicados);
  SN        la decidida, umbral 0,05 MW (0,05 exacto cuenta como "MIROVA no vio nada");
  SE        estrato aparte, umbral 0,05;
  SN_004 y SE_004  la variante que deja 0,05 exacto como alerta (el estudio no pudo decidir 0,05: 5 NONE y 5
                   VERY LOW en la muestra con banner).
Y dos controles de que la funcion unica es la del estudio: con SN y SE a 0,05, los totales tienen que ser los de
suma_salida.txt, que salieron de una implementacion propia del estudio (suma_errores.py), escrita aparte.

La regla toca solo VIIRS 375 (la frontera de VIIRS 750 descansa en una imagen por lado). Por eso en VIIRS 750 las
cinco reglas dan lo mismo por construccion; la sensibilidad con un umbral de 0,15 MW en VIIRS 750 se lee de
suma_salida.txt, que es donde se midio.

Uso: python veredictos_tres_reglas.py --congelado-meses DIR > veredictos_tres_reglas_salida.txt
     (DIR: carpeta con <mes>/registro_vrp_*.csv; en .gitignore, se verifica contra el manifiesto)
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import suma_errores as se  # deja sys.stdout en utf-8 y trae los mismos lectores y contadores del estudio

bp, ev = se.bp, se.ev
from comun import RAIZ  # noqa: E402
sys.path.insert(0, str(RAIZ / "scripts"))
import clase_mirova as cm  # noqa: E402

AQUI = Path(__file__).resolve().parent
REGLAS = (("original", "original", None), ("SN", "SN", cm.UMBRAL_MINIMA_MW), ("SE", "SE", cm.UMBRAL_MINIMA_MW),
          ("SN_004", "SN", cm.UMBRAL_MINIMA_VARIANTE_MW), ("SE_004", "SE", cm.UMBRAL_MINIMA_VARIANTE_MW))


def etiquetar(filas, claves, ventana, modo, umbral):
    """Etiqueta del evaluador con la regla D-9 aplicada por la funcion unica. "minima" (SE) no cuenta en contar()."""
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, bp._coords_por_volcan(), tuple(ventana),
                                              regla_minimas=modo, umbral_minima_mw=umbral)
    recs = []
    for c in claves:
        vol, b, t = c.split("|")
        dt = datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        recs.append({"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"), "clave": c})
    bp.etiquetar(recs, por_vb, ns, nv)
    ev.anotar_vrp_mirova(recs, por_vb)
    return {r["clave"]: (r["lab"], r.get("vrp_ref")) for r in recs}


def sumas(pas, filas, ventana, brazos, sensores):
    """{regla: {brazo: Counter}} y las pasadas cuya etiqueta original no reproduce la tabla."""
    claves = sorted(pas)
    out, malas = {}, None
    for nombre, modo, umbral in REGLAS:
        etq = etiquetar(filas, claves, ventana, modo, umbral)
        if nombre == "original":
            malas = sum(1 for k in claves if (pas[k]["lab"], pas[k]["vrp_ref"]) != etq[k])
        out[nombre] = {b: se.contar(pas, b, etq, sensores) for b in brazos}
    return out, malas


def ganador(res_regla):
    m = min(c["suma"] for c in res_regla.values())
    return "=".join(b for b, c in res_regla.items() if c["suma"] == m)


def leer_estudio():
    """Totales de suma_salida.txt (implementacion propia del estudio) para el control de igualdad."""
    txt = (AQUI / "suma_salida.txt").read_text(encoding="utf-8")
    meses = txt.split("## TOTAL abril a agosto, VIIRS 375, umbral 0,05")[1].split("##")[0]
    out = {"meses": {}, "ndc": {}}
    for esc, b, s in re.findall(r"^\s+(S0|SE|SN) (B|F)\s+.*?SUMA\s+(\d+)", meses, re.M):
        out["meses"][(esc, b)] = int(s)
    ndc = txt.split("== 2. CHILLAN")[1].split("== 3.")[0]
    esc = None
    for linea in ndc.splitlines():
        m = re.match(r"\s+(S0|SE|SN) \(", linea)
        if m:
            esc = m.group(1); continue
        m = re.match(r"\s+(\w+)\s+alertas Muy Bajo.*SUMA\s+(\d+)", linea)
        if m and esc:
            out["ndc"][(esc, m.group(1))] = int(m.group(2))
    v750 = txt.split("## TOTAL abril a agosto, VIIRS 750, SENSIBILIDAD con umbral 0,15")[1].split("==")[0]
    out["v750_015"] = {(e, b): int(s) for e, b, s in re.findall(r"^\s+(S0|SE|SN) (B|F)\s+.*?SUMA\s+(\d+)", v750, re.M)}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--congelado-meses", required=True)
    a = ap.parse_args()
    est = leer_estudio()
    filas_tabla = []   # (resultado, regla, sumas por brazo, ganador)

    print("== 1. MESES de S150, abril a agosto (control B sin Test 1, brazo F = max)")
    for sensor in ("VIIRS375", "VIIRS750"):
        grupos = se.leer_pasadas(AQUI / "pasadas_meses_B_F.csv", ["B", "F"], lambda r, s=sensor: f"|{s}|" in r["clave"])
        tot = defaultdict(lambda: defaultdict(Counter))
        for mes in se.MESES:
            pas = grupos[mes]
            ventana = se.verificar_congelado(Path(a.congelado_meses) / mes, se.CONG_MESES_MANIF / mes / "MANIFIESTO.json")
            res, malas = sumas(pas, se.cargar_ref(Path(a.congelado_meses) / mes, historico=False), ventana, ["B", "F"], (sensor,))
            print(f"   {sensor} {mes}: control, etiqueta original igual a la tabla salvo en {malas} de {len(pas)} pasadas")
            for regla, d in res.items():
                for b, c in d.items():
                    tot[regla][b].update(c)
        for regla in tot:
            for b in tot[regla]:
                tot[regla][b]["suma"] = tot[regla][b]["perdidas"] + tot[regla][b]["fp"]
            print(f"   {sensor} TOTAL regla {regla:8s} " + " | ".join(
                f"{b}: perdidas {c['perdidas']} de {c['pos']}, negativos publicados {c['fp']} de {c['neg']}, suma {c['suma']}"
                + (f", fuera de la cuenta {c['excluidas']}" if c['excluidas'] else "")
                for b, c in tot[regla].items()) + f" | gana {ganador(tot[regla])}")
            filas_tabla.append((f"meses, {sensor}", regla, {b: c["suma"] for b, c in tot[regla].items()}, ganador(tot[regla])))
        if sensor == "VIIRS375":
            ok = all(tot[r][b]["suma"] == est["meses"][(e, b)] for r, e in (("original", "S0"), ("SN", "SN")) for b in "BF")
            print(f"   control: original y SN reproducen suma_salida.txt (implementacion del estudio): {'OK' if ok else 'FALLA'}")
            # SE: el estudio saca de la cuenta las alertas minimas por pareo; aqui salen como etiqueta "minima"
            ok_se = all(tot["SE"][b]["suma"] == est["meses"][("SE", b)] for b in "BF")
            print(f"   control: SE reproduce suma_salida.txt: {'OK' if ok_se else 'FALLA'}")
    print("   VIIRS 750, sensibilidad con umbral 0,15 MW (suma_salida.txt; la regla decidida no toca VIIRS 750): "
          + " | ".join(f"{e} {b} {s}" for (e, b), s in sorted(est["v750_015"].items())))
    for e in ("S0", "SE", "SN"):
        d = {b: est["v750_015"][(e, b)] for b in "BF"}
        filas_tabla.append(("meses, VIIRS 750, sensibilidad 0,15 MW (del estudio)", {"S0": "original", "SE": "SE", "SN": "SN"}[e], d,
                            "=".join(b for b in d if d[b] == min(d.values()))))

    print("\n== 2. CHILLAN (run 38560317428), los tres sensores")
    ventana = se.verificar_congelado(se.CONG_NDC, se.CONG_NDC / "MANIFIESTO.json")
    pas = se.leer_pasadas(AQUI / "pasadas_ndc.csv", se.BRAZOS_NDC)["ndc"]
    res, malas = sumas(pas, se.cargar_ref(se.CONG_NDC, historico=True), ventana, se.BRAZOS_NDC, ("MODIS", "VIIRS375", "VIIRS750"))
    print(f"   control: etiqueta original igual a la tabla salvo en {malas} de {len(pas)} pasadas")
    for regla, d in res.items():
        for c in d.values():
            c["suma"] = c["perdidas"] + c["fp"]
        print(f"   regla {regla:8s} " + " | ".join(f"{b} {c['suma']}" for b, c in d.items()) + f" | gana {ganador(d)}")
        filas_tabla.append(("Chillan, tres sensores", regla, {b: c["suma"] for b, c in d.items()}, ganador(d)))
    ok = all(res[r][b]["suma"] == est["ndc"][(e, b)] for r, e in (("original", "S0"), ("SN", "SN"), ("SE", "SE")) for b in se.BRAZOS_NDC)
    print(f"   control: original, SN y SE reproducen suma_salida.txt (implementacion del estudio): {'OK' if ok else 'FALLA'}")

    print("\n== 3. D22, techo de ganancia (perdidas confiables de max por el camino D22)")
    vrps = [float(m.group(1)) for m in re.finditer(r"VRP MIROVA\s+([0-9.]+) MW", se.D22.read_text(encoding="utf-8"))]
    for nombre, modo, umbral in REGLAS:
        techo = len(vrps) if modo == "original" else sum(not cm.es_alerta_minima(v, "VIIRS375", umbral) for v in vrps)
        print(f"   regla {nombre:8s} techo {techo} de {len(vrps)}")
        filas_tabla.append(("techo del A/B de D22 (perdidas recuperables)", nombre, {"techo": techo}, ""))

    print("\n== TABLA (va a veredictos_tres_reglas.md)")
    for res_, regla, d, g in filas_tabla:
        print(f"   {res_} | {regla} | " + " ".join(f"{b} {s}" for b, s in d.items()) + (f" | gana {g}" if g else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
