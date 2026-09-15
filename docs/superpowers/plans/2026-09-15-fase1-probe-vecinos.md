# Fase 1, paso 1: probe por etapa del vecino del foco (VIIRS 375 m) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** saber, pasada por pasada, en qué etapa del pipeline se pierden los píxeles vecinos del foco que MIROVA sí suma, y cuánto aportarían con fondo local, antes de diseñar el A/B de la Fase 1.

**Architecture:** probe de sólo lectura (A75) que corre en GitHub Actions: reutiliza los monkeypatch del probe S135 sobre `pipeline.process_viirs`, agrega la captura de los índices del cúmulo final, y un módulo de análisis puro (numpy) decide por vecino la etapa de pérdida y su aporte con fondo del anillo y con fondo local. Un selector toma la muestra del OSF v2.5 con el pareo que ya usa `scripts/descomponer_magnitud_osf.py`.

**Tech Stack:** Python 3.11, numpy, pandas, earthaccess (sólo en CI), pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md` §4 (Fase 1, probe) y §5 (criterios). Fundamento físico: §1.4 (F_n 0,553: los vecinos tibios del foco se pierden en la detección) y la lectura S141 (`docs/audit_s139/LECTURA_PDF_SEGUNDA_PASADA.md`, V-07: MIROVA calcula el fondo por píxel alertado como media de sus vecinos no alertados).

---

## Por qué este probe y no un A/B directo

La magnitud VIIRS 375 m queda en ~0,66 de MIROVA porque sumamos 1 píxel donde MIROVA suma 3 (S139). Hay cuatro candidatos a culpable: el primer pase no ve al vecino, el segundo pase no lo recupera, `keep_peak` lo recorta, o el fondo del anillo es tan tibio que su exceso sale cero. Tres veces una atribución sin mirar la etapa siguiente resultó equivocada (S137, S138). El probe dice cuál es, y con eso se eligen los brazos del A/B.

## Límite del instrumento (se escribe antes de correr)

- MIROVA remuestrea a una grilla de 375 m; nosotros vemos píxeles nativos. **No se puede saber cuáles de nuestros píxeles son los `Npix` de MIROVA.** Se miran los 8 vecinos nativos del píxel nuestro más cercano al `LAT/LON` del OSF (el píxel más caliente de MIROVA). Es una aproximación; la distancia al punto del OSF se registra por pasada.
- El OSF está supervisado a mano: se usa sólo pasada contra pasada (fórmula, `Npix`, `Tot_Lmir_bk`), nunca para conteos. ⚠️ Corrección S142 (A105): la v2.5 no tuvo revisión manual; la filtran una clase automática y umbrales VRP por sensor (Coppola et al. 2026, Scientific Data, p. 7, p. 8 Tabla 1, p. 10 a 12). La regla de uso se mantiene.
- **P1 (¿vería una pérdida si existiera?)**: pasadas control donde publicamos tantos píxeles como MIROVA; ahí la mayoría de los vecinos debe salir "incluido". Si no, el instrumento no sirve y el veredicto es INDETERMINADO.
- **P2 (¿mide lo que dice?)**: por pasada se verifica que todas las máscaras capturadas tienen la misma forma que la escena de BT; si no, la pasada se descarta con `grilla_distinta`.
- **P3 (¿la muestra sigue siendo la que dice?, agregado S141 por pregunta de Nicolás)**: el OSF no se cruza con el NRT (no hay solape de fechas, spec §7.1), pero sí con nuestros records de 2025 del backfill, pasada contra pasada, sólo para fórmula, `Npix` y fondo. Esos records se procesaron con el código del backfill y el probe reprocesa con el de hoy. Por pasada se guarda el cúmulo de hoy (`hoy.pc_n`) y el criterio reporta cuántos candidatos siguen publicando 1 píxel; los que hoy publican otro conteo se leen aparte y no se atribuyen al código actual.

## Criterio pre-registrado (no se cambia después de ver datos)

Sobre pasadas `candidato` con `ok` y grilla consistente, n ≥ 10; vecino perdido = no está en el cúmulo final.

1. **Etapa**: si una etapa concentra ≥ 50 % de los vecinos perdidos, es la palanca del primer brazo (`PALANCA:<etapa>`); si no, `DISPERSA`. Si `nunca_candidato` concentra ≥ 50 %, la detección no ve a los vecinos: palanca = umbral o fondo de la detección, no ensamblado.
2. **Fondo local**: mediana por pasada de (aporte de los vecinos perdidos con fondo local) / (VRP OSF − VRP publicado). ≥ 0,5 → `FONDO_LOCAL_CIERRA_BRECHA` (el brazo D25 va primero); < 0,2 → `NO_CIERRA`; si no, `PARCIAL`.
3. **Control**: en pasadas `control`, ≥ 50 % de los vecinos `incluido`. Si falla → `INDETERMINADO` para todo.
4. Todo se reporta además por estrato focal/nevado (`scripts/build_c2ab_windows.py:41-42`).

## File Structure

| archivo | responsabilidad |
|---|---|
| `scripts/descomponer_magnitud_osf.py` (modificar `build`) | agregar `t_osf` y `t_ours` a cada par, para poder ubicar la pasada |
| `experiments/_s141_fase1_probe/seleccionar_pasadas.py` | muestra determinista de candidatos y controles, a `pasadas.json` |
| `experiments/_s141_fase1_probe/analisis_vecinos.py` | funciones puras: vecinos, etapa de pérdida, aporte con fondo, criterio |
| `experiments/_s141_fase1_probe/probe_vecinos.py` | runner en CI: importa los wrappers de S135, captura índices del cúmulo, llama al análisis |
| `.github/workflows/probe-s141-vecinos.yml` | workflow_dispatch, matriz por volcán, sin push |
| `tests/test_probe_vecinos_s141.py` | tests del selector, del análisis y del yml |

---

### Task 1: el pareo expone las horas de la pasada

**Files:**
- Modify: `scripts/descomponer_magnitud_osf.py` (función `build`)
- Test: `tests/test_probe_vecinos_s141.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_probe_vecinos_s141.py
"""S141, Fase 1: tests del probe por etapa del vecino del foco (VIIRS 375 m).

Lo que tiene que ser verdad antes de gastar una corrida en CI: el pareo OSF expone las horas,
la muestra es determinista, el análisis clasifica bien la etapa de pérdida sobre escenas
sintéticas construidas a mano, el criterio pre-registrado da cada veredicto en su caso, los
nombres parcheados existen en process_viirs (A89) y el yml no pushea (A43).
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROBE_DIR = os.path.join(ROOT, "experiments", "_s141_fase1_probe")
sys.path.insert(0, ROOT)
sys.path.insert(0, PROBE_DIR)


def test_build_expone_horas_de_la_pasada():
    import scripts.descomponer_magnitud_osf as m
    if not m.OSF_DEFECTO.exists():
        pytest.skip("OSF no disponible en este entorno")
    m.cargar(str(m.OSF_DEFECTO))
    d = m.build(0)
    assert {"t_osf", "t_ours"} <= set(d.columns)
    delta = (d.t_ours - d.t_osf).dt.total_seconds() / 60
    assert np.allclose(delta, d.dt_min)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_probe_vecinos_s141.py::test_build_expone_horas_de_la_pasada -q -p no:cacheprovider`
Expected: FAIL con `AssertionError` (faltan las columnas).

- [ ] **Step 3: Write minimal implementation** (en `build`, dentro del `dict(...)` de cada fila, agregar dos claves)

```python
                 test1=r.get('final_hotspot_source') == 'test1_roi', single=pc.get('single_pixel_mode'),
                 t_osf=x.t.to_pydatetime(), t_ours=m[0])
```

- [ ] **Step 4: Run test to verify it passes** (mismo comando). Expected: PASS. Correr también `python scripts/descomponer_magnitud_osf.py --out "$TMP/mag.json"` y comprobar que `R_gm` V375 sigue en 0,659.

- [ ] **Step 5: Commit** `git commit -m "feat(magnitud): el pareo OSF expone las horas de la pasada (Fase 1, probe)"`

---

### Task 2: selector determinista de la muestra

**Files:**
- Create: `experiments/_s141_fase1_probe/seleccionar_pasadas.py`
- Test: `tests/test_probe_vecinos_s141.py`

- [ ] **Step 1: Write the failing test** (agregar al archivo)

```python
def _pares_sinteticos():
    t = pd.date_range("2025-03-01 05:00", periods=12, freq="3D")
    return pd.DataFrame({
        "vol": ["Lascar"] * 8 + ["Villarrica"] * 4, "res": [375] * 12,
        "Npix": [4, 3, 5, 3, 6, 3, 3, 4, 3, 3, 1, 3], "pub_n": [1, 1, 1, 1, 1, 1, 6, 4, 1, 1, 1, 3],
        "t_osf": t, "t_ours": t + pd.Timedelta(minutes=2), "sensor": ["VIIRS_SNPP"] * 12,
        "osf_mw": 1.0, "pub_mw": 0.5, "satzen": 20.0, "pc_n": 1, "t_bg": 260.0,
    })


def test_selector_toma_candidatos_y_controles_deterministas():
    from seleccionar_pasadas import seleccionar
    d = _pares_sinteticos()
    a = seleccionar(d, por_volcan=2, controles_por_volcan=1)
    b = seleccionar(d, por_volcan=2, controles_por_volcan=1)
    assert a == b, "la muestra debe ser determinista"
    cand = [x for x in a if x["clase"] == "candidato"]
    ctl = [x for x in a if x["clase"] == "control"]
    assert all(x["osf"]["Npix"] >= 3 and x["persistido"]["pub_n"] == 1 for x in cand)
    assert all(x["persistido"]["pub_n"] >= x["osf"]["Npix"] >= 3 for x in ctl)
    assert sum(x["volcan"] == "Lascar" for x in cand) == 2
    assert {x["regimen"] for x in a} <= {"focal", "nevado"}
    assert all(x["pasada_utc"].count(":") == 1 for x in a), "formato YYYY-MM-DD HH:MM del probe S135"
```

- [ ] **Step 2: Run** `python -m pytest tests/test_probe_vecinos_s141.py::test_selector_toma_candidatos_y_controles_deterministas -q -p no:cacheprovider`. Expected: FAIL `ModuleNotFoundError: seleccionar_pasadas`.

- [ ] **Step 3: Write implementation**

```python
# experiments/_s141_fase1_probe/seleccionar_pasadas.py
# -*- coding: utf-8 -*-
"""S141, Fase 1: muestra de pasadas VIIRS 375 m para el probe del vecino del foco.

POR QUÉ. Sumamos 1 píxel donde MIROVA suma 3 o más (S139, F_n 0,553). Se eligen pasadas OSF
pareadas con nuestro record donde pasa eso (candidatos) y, como control del instrumento, pasadas
donde publicamos tantos píxeles como MIROVA (controles). El OSF está supervisado a mano: se usa
pasada contra pasada, nunca para conteos. (Corrección S142, A105: filtrado por clase automática y
umbrales, no supervisado a mano; la regla de uso no cambia.)

INSTRUMENTO. P1: los controles deben salir con los vecinos incluidos; P2: la muestra es
determinista (mismo resultado dos veces) y se reparte parejo en el tiempo dentro de cada volcán.

USO: python experiments/_s141_fase1_probe/seleccionar_pasadas.py [--por-volcan 4] [--controles 2]
Salida: experiments/_s141_fase1_probe/pasadas.json
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
sys.path.insert(0, str(R / "scripts"))

from build_c2ab_windows import FOCAL  # noqa: E402

OUT = Path(__file__).resolve().parent / "pasadas.json"


def _espaciados(g, k):
    g = g.sort_values("t_osf")
    if len(g) <= k:
        return g
    idx = sorted(set(np.linspace(0, len(g) - 1, k).round().astype(int)))
    return g.iloc[idx]


def _fila(x, clase):
    return {
        "volcan": x.vol, "pasada_utc": x.t_ours.strftime("%Y-%m-%d %H:%M"), "sensor": x.sensor,
        "clase": clase, "regimen": "focal" if x.vol in FOCAL else "nevado",
        "osf": {"Npix": int(x.Npix), "vrp_mw": float(x.osf_mw), "satzen": float(x.satzen),
                "t_osf": x.t_osf.strftime("%Y-%m-%d %H:%M"),
                "lat": float(x.lat) if "lat" in x and x.lat == x.lat else None,
                "lon": float(x.lon) if "lon" in x and x.lon == x.lon else None},
        "persistido": {"pub_n": int(x.pub_n), "pub_mw": float(x.pub_mw), "pc_n": int(x.pc_n),
                       "t_bg_k": float(x.t_bg) if x.t_bg == x.t_bg else None},
    }


def seleccionar(d, por_volcan=4, controles_por_volcan=2):
    v = d[d.res == 375]
    cand = v[(v.Npix >= 3) & (v.pub_n == 1)]
    ctl = v[(v.Npix >= 3) & (v.pub_n >= v.Npix)]
    filas = []
    for clase, base, k in (("candidato", cand, por_volcan), ("control", ctl, controles_por_volcan)):
        for vol in sorted(base.vol.unique()):
            for x in _espaciados(base[base.vol == vol], k).itertuples():
                filas.append(_fila(x, clase))
    return filas


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--por-volcan", type=int, default=4)
    ap.add_argument("--controles", type=int, default=2)
    a = ap.parse_args(argv)
    import descomponer_magnitud_osf as m
    m.cargar(str(m.OSF_DEFECTO))
    d = m.build(0)
    osf = m.o.set_index("t")[["vol", "LAT", "LON"]]
    d = d.merge(m.o[["t", "vol", "LAT", "LON"]].rename(columns={"t": "t_osf", "LAT": "lat", "LON": "lon"}),
                on=["t_osf", "vol"], how="left").drop_duplicates(subset=["t_osf", "vol", "sensor"])
    filas = seleccionar(d, a.por_volcan, a.controles)
    OUT.write_text(json.dumps(filas, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(filas)} pasadas -> {OUT}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test** (PASS) y luego `python experiments/_s141_fase1_probe/seleccionar_pasadas.py`. Expected: ~40 pasadas; comprobar a ojo que cada candidato tiene `Npix ≥ 3`, `pub_n = 1` y `lat/lon` no nulos.

- [ ] **Step 5: Commit** `git commit -m "feat(probe): muestra determinista de pasadas para el probe del vecino (Fase 1)"`

---

### Task 3: análisis puro del vecindario

**Files:**
- Create: `experiments/_s141_fase1_probe/analisis_vecinos.py`
- Test: `tests/test_probe_vecinos_s141.py`

- [ ] **Step 1: Write the failing tests**

```python
from analisis_vecinos import (ORDEN, aporte_mw, etapa_de_perdida, evaluar_criterio,  # noqa: E402
                              fondo_local_k, resumir_vecindario)


def test_etapa_de_perdida_en_cada_caso():
    assert etapa_de_perdida({"first_pass": True, "second_pass": True, "test1": True,
                             "ctx_filter_out": True, "cluster": True}) == "incluido"
    assert etapa_de_perdida({e: False for e in ORDEN}) == "nunca_candidato"
    assert etapa_de_perdida({"first_pass": False, "second_pass": False, "test1": True,
                             "ctx_filter_out": False, "cluster": False}) == "perdido_en_ctx_filter_out"
    assert etapa_de_perdida({"first_pass": True, "second_pass": None, "test1": None,
                             "ctx_filter_out": None, "cluster": False}) == "perdido_en_cluster"


def test_aporte_y_fondo_local():
    assert aporte_mw(300.0, 300.0) == 0.0
    assert aporte_mw(310.0, 300.0) > 0
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 300.0
    bt[2, 3] = 290.0            # vecino alertado: no entra al fondo
    alertado = np.zeros((5, 5), bool)
    alertado[2, 2] = alertado[2, 3] = True
    assert fondo_local_k(bt, alertado, 2, 2) == pytest.approx(270.0, abs=0.01)


def test_resumir_vecindario_escena_sintetica():
    bt = np.full((7, 7), 260.0)
    bt[3, 3], bt[3, 4], bt[2, 3] = 300.0, 275.0, 272.0
    lat, lon = np.meshgrid(np.linspace(-23.30, -23.40, 7), np.linspace(-67.70, -67.80, 7), indexing="ij")
    z = np.zeros((7, 7), bool)
    fp = z.copy(); fp[3, 3] = True
    t1 = z.copy(); t1[3, 3] = t1[3, 4] = True
    ctx = z.copy(); ctx[3, 3] = True
    cl = z.copy(); cl[3, 3] = True
    r = resumir_vecindario(bt, lat, lon, {"first_pass": fp, "second_pass": fp, "test1": t1,
                                          "ctx_filter_out": ctx, "cluster": cl},
                           osf_lat=lat[3, 3], osf_lon=lon[3, 3], t_bg_anillo=268.0)
    assert r["grilla_ok"] is True
    assert r["centro"] == [3, 3]
    assert r["conteo"]["perdido_en_ctx_filter_out"] == 1      # (3,4): Test 1 lo tenía, keep_peak lo sacó
    assert r["conteo"]["nunca_candidato"] == 7
    assert r["aporte_perdidos_fondo_local_mw"] > r["aporte_perdidos_fondo_anillo_mw"]


def test_grilla_distinta_se_marca():
    bt = np.full((5, 5), 260.0)
    lat = lon = np.zeros((5, 5))
    r = resumir_vecindario(bt, lat, lon, {"first_pass": np.zeros((4, 4), bool)}, 0.0, 0.0, 260.0)
    assert r["grilla_ok"] is False


def _fila(clase, conteo, cierre, regimen="focal"):
    return {"ok": True, "clase": clase, "regimen": regimen,
            "resumen": {"grilla_ok": True, "conteo": conteo, "fraccion_brecha_fondo_local": cierre}}


def test_criterio_palanca_fondo_y_control():
    cand = [_fila("candidato", {"perdido_en_ctx_filter_out": 3, "nunca_candidato": 1, "incluido": 0}, 0.6)
            for _ in range(10)]
    ctl = [_fila("control", {"incluido": 6, "nunca_candidato": 2}, None) for _ in range(2)]
    c = evaluar_criterio(cand + ctl)
    assert c["etapa"] == "PALANCA:perdido_en_ctx_filter_out"
    assert c["fondo"] == "FONDO_LOCAL_CIERRA_BRECHA"
    assert c["control"] == "OK"


def test_criterio_indeterminado_si_control_falla_o_n_chico():
    cand = [_fila("candidato", {"nunca_candidato": 8}, 0.1) for _ in range(10)]
    ctl = [_fila("control", {"nunca_candidato": 8}, None)]
    assert evaluar_criterio(cand + ctl)["veredicto"] == "INDETERMINADO"
    assert evaluar_criterio(cand[:5] + [_fila("control", {"incluido": 8}, None)])["veredicto"] == "INDETERMINADO"
```

- [ ] **Step 2: Run** `python -m pytest tests/test_probe_vecinos_s141.py -q -p no:cacheprovider -k "etapa or aporte or vecindario or grilla or criterio"`. Expected: FAIL `ModuleNotFoundError: analisis_vecinos`.

- [ ] **Step 3: Write implementation**

```python
# experiments/_s141_fase1_probe/analisis_vecinos.py
# -*- coding: utf-8 -*-
"""S141, Fase 1: análisis puro del vecindario del foco (sin red, sin pipeline).

POR QUÉ. MIROVA suma los píxeles tibios que rodean al foco y calcula el fondo de cada píxel
alertado como la media de sus vecinos no alertados (Campus et al. 2024, Bull. Volcanol. 86:25,
p. 3, ec. 1 y 2; verificado S141). Nosotros publicamos 1 píxel. Este módulo dice, para cada uno
de los 8 vecinos nativos del foco, en qué etapa del ensamblado se perdió y cuánto habría aportado
con el fondo del anillo y con fondo local.

ETAPAS, en el orden del ensamblado VIIRS 375 m: primer pase (Tests 2 y 3), segundo pase
(adyacencia), Test 1, filtro contextual con keep_peak, cúmulo final.
"""
import math
import statistics

import numpy as np

ORDEN = ("first_pass", "second_pass", "test1", "ctx_filter_out", "cluster")
LAMBDA_I04_UM = 3.74
C1, C2 = 1.191042e8, 14388.0
KA_375 = 18.0 * 140625          # coeficiente de Wooster por área nadir, igual que el pipeline
UMBRAL_CONCENTRA = 0.5
N_MIN = 10


def planck(t_k, lam=LAMBDA_I04_UM):
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * t_k)) - 1))


def aporte_mw(bt_k, fondo_k):
    """VRP de un píxel con ese fondo, en MW; nunca negativo (así lo publica el pipeline)."""
    if bt_k is None or fondo_k is None or not np.isfinite(bt_k) or not np.isfinite(fondo_k):
        return 0.0
    return max(planck(bt_k) - planck(fondo_k), 0.0) * KA_375 / 1e6


def _vecinos(shape, i, j):
    return [(i + di, j + dj) for di in (-1, 0, 1) for dj in (-1, 0, 1)
            if (di or dj) and 0 <= i + di < shape[0] and 0 <= j + dj < shape[1]]


def fondo_local_k(bt, alertado, i, j):
    """BT equivalente a la radiancia media de los vecinos no alertados del píxel (i, j)."""
    ls = [planck(bt[a, b]) for a, b in _vecinos(bt.shape, i, j)
          if not alertado[a, b] and np.isfinite(bt[a, b])]
    if not ls:
        return None
    lm = sum(ls) / len(ls)
    return C2 / (LAMBDA_I04_UM * math.log(1 + C1 / (LAMBDA_I04_UM ** 5 * lm)))


def etapa_de_perdida(estado):
    if estado.get("cluster"):
        return "incluido"
    vistos = [e for e in ORDEN if estado.get(e)]
    if not vistos:
        return "nunca_candidato"
    for e in ORDEN[ORDEN.index(vistos[-1]) + 1:]:
        if estado.get(e) is False:
            return f"perdido_en_{e}"
    return f"perdido_despues_de_{vistos[-1]}"


def resumir_vecindario(bt, lat, lon, mascaras, osf_lat, osf_lon, t_bg_anillo):
    bt = np.asarray(bt, dtype=float)
    formas = {k: np.asarray(v).shape for k, v in mascaras.items() if v is not None}
    if any(s != bt.shape for s in formas.values()) or np.asarray(lat).shape != bt.shape:
        return {"grilla_ok": False, "formas": {k: list(s) for k, s in formas.items()},
                "forma_bt": list(bt.shape)}
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    d2 = (lat - osf_lat) ** 2 + ((lon - osf_lon) * math.cos(math.radians(osf_lat))) ** 2
    i, j = np.unravel_index(np.nanargmin(d2), d2.shape)
    dist_km = float(math.sqrt(d2[i, j]) * 111.195)
    alertado = np.zeros(bt.shape, bool)
    for v in mascaras.values():
        if v is not None:
            alertado |= np.asarray(v, bool)
    conteo, vecinos = {}, []
    perd_anillo = perd_local = 0.0
    for a, b in _vecinos(bt.shape, i, j):
        estado = {e: (bool(mascaras[e][a, b]) if mascaras.get(e) is not None else None) for e in ORDEN}
        etapa = etapa_de_perdida(estado)
        conteo[etapa] = conteo.get(etapa, 0) + 1
        fl = fondo_local_k(bt, alertado, a, b)
        ap_anillo, ap_local = aporte_mw(bt[a, b], t_bg_anillo), aporte_mw(bt[a, b], fl)
        if etapa != "incluido":
            perd_anillo += ap_anillo
            perd_local += ap_local
        vecinos.append({"ij": [int(a), int(b)], "bt_k": round(float(bt[a, b]), 2), "etapa": etapa,
                        "fondo_local_k": None if fl is None else round(fl, 2),
                        "aporte_fondo_anillo_mw": round(ap_anillo, 4), "aporte_fondo_local_mw": round(ap_local, 4)})
    return {"grilla_ok": True, "centro": [int(i), int(j)], "dist_centro_a_osf_km": round(dist_km, 3),
            "bt_centro_k": round(float(bt[i, j]), 2), "conteo": conteo, "vecinos": vecinos,
            "aporte_perdidos_fondo_anillo_mw": round(perd_anillo, 4),
            "aporte_perdidos_fondo_local_mw": round(perd_local, 4)}


def _dominante(filas):
    total = {}
    for f in filas:
        for k, v in f["resumen"]["conteo"].items():
            if k != "incluido":
                total[k] = total.get(k, 0) + v
    n = sum(total.values())
    if not n:
        return None, 0.0, total
    k = max(total, key=total.get)
    return k, total[k] / n, total


def evaluar_criterio(filas, regimen=None):
    buenas = [f for f in filas if f.get("ok") and f.get("resumen", {}).get("grilla_ok")
              and (regimen is None or f.get("regimen") == regimen)]
    cand = [f for f in buenas if f["clase"] == "candidato"]
    ctl = [f for f in buenas if f["clase"] == "control"]
    out = {"n_candidatos": len(cand), "n_controles": len(ctl)}
    inc = sum(f["resumen"]["conteo"].get("incluido", 0) for f in ctl)
    tot = sum(sum(f["resumen"]["conteo"].values()) for f in ctl)
    out["control"] = "OK" if tot and inc / tot >= UMBRAL_CONCENTRA else "FALLA"
    k, frac, total = _dominante(cand)
    out["perdidas_por_etapa"] = total
    out["etapa"] = (f"PALANCA:{k}" if k and frac >= UMBRAL_CONCENTRA else "DISPERSA")
    fr = [f["resumen"].get("fraccion_brecha_fondo_local") for f in cand]
    fr = [x for x in fr if x is not None]
    med = statistics.median(fr) if fr else None
    out["mediana_fraccion_brecha_fondo_local"] = med
    out["fondo"] = (None if med is None else "FONDO_LOCAL_CIERRA_BRECHA" if med >= 0.5
                    else "NO_CIERRA" if med < 0.2 else "PARCIAL")
    if len(cand) < N_MIN or out["control"] != "OK":
        out["veredicto"] = "INDETERMINADO"
    else:
        out["veredicto"] = f"{out['etapa']} | {out['fondo']}"
    return out
```

- [ ] **Step 4: Run** los tests del Step 2. Expected: PASS (7 tests).
- [ ] **Step 5: Commit** `git commit -m "feat(probe): analisis puro del vecindario del foco (Fase 1)"`

---

### Task 4: runner en CI y workflow

**Files:**
- Create: `experiments/_s141_fase1_probe/probe_vecinos.py`
- Create: `.github/workflows/probe-s141-vecinos.yml`
- Test: `tests/test_probe_vecinos_s141.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_a89_nombres_parcheados_existen():
    os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
    import pipeline.process_viirs as pv
    for n in ("compute_test1_mir", "apply_contextual_test1_filter", "first_pass_tests_2_and_3",
              "second_pass_adjacent", "cluster_hotspots", "read_viirs_l1b", "calculate_vrp"):
        assert callable(getattr(pv, n, None)), n


def test_yml_no_pushea_y_on_entre_comillas():
    p = os.path.join(ROOT, ".github", "workflows", "probe-s141-vecinos.yml")
    txt = open(p, encoding="utf-8").read()
    d = yaml.safe_load(txt)
    assert "on" in d and True not in d, "A43: la clave on debe ir entre comillas"
    assert "git push" not in txt and "contents: write" not in txt
    assert "pyhdf" not in txt
```

- [ ] **Step 2: Run** `python -m pytest tests/test_probe_vecinos_s141.py -q -p no:cacheprovider -k "a89 or yml"`. Expected: el de A89 PASA (ya existen) y el del yml FALLA (archivo no existe).

- [ ] **Step 3a: runner**

```python
# experiments/_s141_fase1_probe/probe_vecinos.py
# -*- coding: utf-8 -*-
"""S141, Fase 1: probe por etapa del vecino del foco, VIIRS 375 m (A75, sólo lectura, sólo CI).

Reutiliza los monkeypatch del probe S135 (`experiments/_s135_probe_etapas/probe_etapas.py`, que
parchea en el namespace de pipeline.process_viirs al importarse, A89) y agrega la captura de los
índices del cúmulo final. No escribe en data/, no hace push. Plan:
docs/superpowers/plans/2026-09-15-fase1-probe-vecinos.md (criterio pre-registrado ahí).

Env: PROBE_VOL filtra volcán; PROBE_PASADAS ruta al JSON (por defecto pasadas.json de esta carpeta).
Salida: out/<vol>_<fecha>_<hhmm>.json + out/criterio.json
"""
import io
import json
import os
import sys
import traceback
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S135 = ROOT / "experiments" / "_s135_probe_etapas"
for p in (ROOT, ROOT / "scripts", S135, HERE):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_etapas as s135  # noqa: E402  (aplica los parches de S135 al importarse)
from analisis_vecinos import evaluar_criterio, resumir_vecindario  # noqa: E402

pv = s135.pv
OUT = HERE / "out"
s135.OUT = OUT
s135.DEST = HERE / "granules"

_REAL_CL = pv.cluster_hotspots


def _cl_con_indices(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw):
    cl = _REAL_CL(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw)
    s135._CAP.setdefault("cluster_indices", []).append(
        {"shape": list(np.asarray(hot_mask_2d).shape),
         "primario": [list(ij) for ij in (cl[0].get("pixel_indices") or [])] if cl else []})
    return cl


pv.cluster_hotspots = _cl_con_indices


def mascaras_de(cap, forma):
    def m(x):
        return None if x is None else np.asarray(x, bool)
    sp = cap.get("second_pass") or []
    sp_union = None
    for s in sp:
        o = np.asarray(s["out"], bool)
        sp_union = o if sp_union is None else (sp_union | o if sp_union.shape == o.shape else sp_union)
    cl = np.zeros(forma, bool)
    ci = cap.get("cluster_indices") or []
    if ci and ci[-1]["shape"] == list(forma):
        for a, b in ci[-1]["primario"]:
            cl[a, b] = True
    elif ci:
        cl = np.zeros(tuple(ci[-1]["shape"]), bool)
    return {"first_pass": m((cap.get("first_pass") or {}).get("hot")),
            "second_pass": sp_union,
            "test1": m((cap.get("test1") or {}).get("mask_contributing")),
            "ctx_filter_out": m((cap.get("ctx_filter") or {}).get("mask_out")),
            "cluster": cl}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s135.DEST.mkdir(parents=True, exist_ok=True)
    ruta = os.environ.get("PROBE_PASADAS", "").strip() or str(HERE / "pasadas.json")
    f_vol = os.environ.get("PROBE_VOL", "").strip()
    lista = [x for x in json.loads(Path(ruta).read_text(encoding="utf-8"))
             if not f_vol or x["volcan"] == f_vol]
    print(f"Probe S141 vecinos: {len(lista)} pasadas (perfil {os.environ['VRP_PROFILE']})", flush=True)
    s135.auth()
    vols = {v["name"]: v for v in s135.load_volcanoes()}
    filas = []
    for x in lista:
        try:
            fila = s135.correr_pasada(vols[x["volcan"]], x["pasada_utc"], x["sensor"], x["clase"], x.get("persistido"))
            fila.update({"regimen": x["regimen"], "osf": x["osf"], "persistido": x["persistido"]})
            t1 = s135._CAP.get("test1") or {}
            if fila.get("ok") and t1.get("bt") is not None and x["osf"].get("lat") is not None:
                forma = np.asarray(t1["bt"]).shape
                res = resumir_vecindario(t1["bt"], t1["lat"], t1["lon"], mascaras_de(s135._CAP, forma),
                                         x["osf"]["lat"], x["osf"]["lon"], fila["record"].get("t_bg_k"))
                brecha = x["osf"]["vrp_mw"] - x["persistido"]["pub_mw"]
                if res.get("grilla_ok") and brecha > 0:
                    res["fraccion_brecha_fondo_local"] = round(res["aporte_perdidos_fondo_local_mw"] / brecha, 4)
                fila["resumen"] = res
            else:
                fila["ok"] = False
                fila.setdefault("error", "sin BT del Test 1 o sin lat/lon OSF")
        except Exception as e:
            fila = {**x, "ok": False, "error": str(e), "traceback": traceback.format_exc()}
        filas.append(fila)
        nombre = f"{x['volcan']}_{x['pasada_utc'].replace(' ', '_').replace(':', '')}.json"
        (OUT / nombre).write_text(json.dumps(s135.a_json(fila), indent=1, ensure_ascii=False), encoding="utf-8")
        for p in s135.DEST.glob("*"):
            try:
                p.unlink()
            except OSError:
                pass
    crit = {"total": evaluar_criterio(filas), "focal": evaluar_criterio(filas, "focal"),
            "nevado": evaluar_criterio(filas, "nevado")}
    (OUT / "criterio.json").write_text(json.dumps(s135.a_json(crit), indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(s135.a_json(crit), indent=1, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3b: workflow** (copiado de `.github/workflows/_archive/probe-s135-etapas.yml`)

```yaml
name: Probe S141 vecinos del foco (Fase 1, VIIRS 375)

# A43: "on" entre comillas. One-off, READ-ONLY (A75): monkeypatch en pipeline.process_viirs.
# NO empuja commits ni toca data/. Plan y criterio pre-registrado:
# docs/superpowers/plans/2026-09-15-fase1-probe-vecinos.md. Archivar en _archive/ al terminar.
"on":
  workflow_dispatch:
    inputs:
      vol:
        description: "Volcán (vacío = matriz completa)"
        required: false
        default: ""

jobs:
  probe:
    runs-on: ubuntu-latest
    timeout-minutes: 120
    strategy:
      fail-fast: false
      max-parallel: 4
      matrix:
        vol: [Chaiten, Isluga, Lascar, Lastarria, NevadosDeChillan, PlanchonPeteroa, PuyehueCordonCaulle, Villarrica]
    steps:
      - uses: actions/checkout@v4
        if: github.event.inputs.vol == '' || github.event.inputs.vol == matrix.vol
      - uses: actions/setup-python@v5
        if: github.event.inputs.vol == '' || github.event.inputs.vol == matrix.vol
        with:
          python-version: "3.11"
      - name: Install deps
        if: github.event.inputs.vol == '' || github.event.inputs.vol == matrix.vol
        run: |
          pip install --upgrade pip
          pip install earthaccess numpy h5py scipy pyyaml pandas
      - name: Run probe (read-only)
        if: github.event.inputs.vol == '' || github.event.inputs.vol == matrix.vol
        env:
          EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}
          EARTHDATA_USERNAME: ${{ secrets.EARTHDATA_USERNAME }}
          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}
          VRP_PROFILE: mirova_equivalent
          PROBE_VOL: ${{ matrix.vol }}
        run: |
          mkdir -p experiments/_s141_fase1_probe/out
          python experiments/_s141_fase1_probe/probe_vecinos.py | tee experiments/_s141_fase1_probe/out/report_${{ matrix.vol }}.txt
      - name: Upload artifact
        if: always() && (github.event.inputs.vol == '' || github.event.inputs.vol == matrix.vol)
        uses: actions/upload-artifact@v4
        with:
          name: s141-probe-vecinos-${{ matrix.vol }}
          path: experiments/_s141_fase1_probe/out/
```

- [ ] **Step 4: Run** todo `tests/test_probe_vecinos_s141.py` y la suite completa. Expected: PASS, suite sin regresiones. Humo local sin red: `python -c "import sys; sys.path.insert(0,'experiments/_s141_fase1_probe'); import probe_vecinos"` debe importar sin error (no llama a `main`).
- [ ] **Step 5: Commit** `git commit -m "feat(probe): runner y workflow del probe del vecino del foco (Fase 1)"`

---

### Task 5: pre-registro, corrida, lectura y verificación

- [ ] **Step 1**: antes de despachar, anotar en `docs/HYPOTHESIS_LOG.md` la hipótesis, el criterio de este plan y la fecha (spec §5.6).
- [ ] **Step 2**: PR con Tasks 1 a 4 + `pasadas.json`; merge (el `workflow_dispatch` sólo existe en `main`, S73).
- [ ] **Step 3**: `gh workflow run probe-s141-vecinos.yml --ref main`; esperar con un monitor; bajar los artefactos con `gh run download <id> -D experiments/_s141_fase1_probe/artefactos`.
- [ ] **Step 4**: juntar los JSON de las 8 corridas y recalcular `evaluar_criterio` sobre el total, focal y nevado con un script `experiments/_s141_fase1_probe/juntar.py` que lea `artefactos/*/*.json` (las filas) y escriba `criterio_total.json`. Ningún número a mano (S91).
- [ ] **Step 5**: escribir `experiments/_s141_fase1_probe/RESULTADOS.md`: veredicto, pérdidas por etapa, fracción de la brecha, controles, pasadas descartadas y por qué; fenómeno físico primero.
- [ ] **Step 6**: verificador con contexto limpio sobre RESULTADOS.md (recibe sólo título, ruta y scripts; re-corre `juntar.py`).
- [ ] **Step 7**: anotar el resultado en `docs/HYPOTHESIS_LOG.md`, archivar el yml en `.github/workflows/_archive/`, y proponer los brazos del A/B de la Fase 1 a Nicolás según el veredicto. **No se toca `pipeline/` en este plan.**

---

## Self-review

- Spec §4 Fase 1 probe: muestra OSF con MIROVA ≥ 3 y nosotros 1 (Task 2), registro por etapa (Tasks 3 y 4), aporte con fondo local (Task 3). §5: pre-registro y verificador (Task 5); estratos focal/nevado (criterio punto 4).
- Nombres consistentes: `ORDEN`, `resumir_vecindario`, `evaluar_criterio`, `mascaras_de`, `fraccion_brecha_fondo_local` iguales en tests, análisis y runner.
- Riesgo conocido: que las máscaras del Test 1 no compartan grilla con la del primer pase. Queda cubierto por `grilla_ok` (P2) y se reporta, no se adivina.
