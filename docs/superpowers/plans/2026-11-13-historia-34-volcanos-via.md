# Historia de los 34 volcanes sin MIROVA con la vía «código MIROVA»: plan por etapas

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** que el tablero pueda mostrar, para cada uno de los 34 volcanes fuera del NRT, su serie con la vía desde el
2025-02-15, reprocesada en tandas que no estorben al NRT de los 11 y sin poner en riesgo lo que la sombra diaria ya
publica.

**Architecture:** la historia (2025-02-15 a 2026-11-02) se reprocesa con las mismas piezas del reemplazo de los 11
(`reproc-historia-via.yml`, `unir_trozos.py`, `aplicar-reemplazo.yml`, #987 y #994). Se guarda en archivos PROPIOS,
`data/historia_34/<Volcan>.json`, que se escriben una vez y nadie reescribe. La sombra diaria sigue escribiendo
`data/sombra_34/<Volcan>.json` desde el 2026-11-03. El tablero lee los dos desde el repo público
(`raw.githubusercontent.com`), igual que hoy lee la sombra, y la historia sólo cuando se pide un período largo.

**Tech Stack:** Python 3.11/3.12, pytest, GitHub Actions (`workflow_dispatch`), JSON, gzip.

Escrito el 2026-11-13 a pedido de Nicolás («se podría hacer pausado y por etapas para tener hacia atrás?»). Sólo el
plan: nada de esto está ejecutado.

---

## 1. Por qué así (lo que se midió el 2026-11-13 sobre main `46b2d0b5e`)

**El fenómeno.** Los 34 no tienen referencia de MIROVA. Su historia no sirve para medir paridad; sirve para saber
cómo es cada volcán en una noche normal (fondo, artefactos recurrentes, estaciones) antes de leer una anomalía nueva.
Eso pide la misma vía en toda la serie, igual que en los 11.

**Hechos que fijan el diseño:**

| hecho | evidencia |
|---|---|
| Los 34 ya tienen grilla de MIROVA (regla GEO con el lat/lon del yaml) | `pipeline/grillas_mirova.yaml`, bloque S172; 45 entradas |
| La vía ya corre sobre ellos cada día desde el 2026-11-03 | `sombra-34.yml`; `data/sombra_34/`: 2.713 records, 100 % `via_codigo_mirova: true`; primer record 2026-11-03 01:55 |
| El tablero ya los muestra y los lee desde el repo, no desde Pages | `frontend/index.html`: `SOMBRA_34_BASE = "https://raw.githubusercontent.com/.../data/sombra_34/"`; `pages-deploy.yml` borra `data/sombra_34` del sitio |
| El tablero baja el archivo COMPLETO de cada uno de los 34 al cargar | `frontend/index.html`, `loadVolcano`: para `fuente === "sombra_34"` no hay `_recent` |
| La sombra empuja con `git pull --rebase -X theirs` | `.github/workflows/sombra-34.yml:149`; en un rebase, «theirs» es el commit propio que se reaplica (lección S181) |
| Costo medido de la vía por volcán | Tupungatito, 2025-02-15 a 2026-02-22 (373 días): 9,1 h de runner, 2 h de reloj, 20 trozos (run 43146587816) |
| Peso por record | ~2,2 KB (`data/sombra_34`: 5,7 MB en 2.713 records; `mirova_equivalent`: 163 MB) |

**Consecuencias:**

1. **La historia NO va al archivo de la sombra.** Dos razones medidas. (a) Con 626 días cada archivo pasaría de unos
   170 KB a unos 14 MB, y el tablero bajaría los 34 completos en cada visita (~475 MB). (b) Si el reemplazo entra a
   main mientras corre la sombra, el rebase con `-X theirs` hace ganar el archivo de la sombra, que no tiene la
   historia, y la borra sin error. Con un archivo aparte que la sombra nunca toca, ninguna de las dos cosas pasa.
2. **El techo de 1 GB de Pages no aplica**: los 34 se sirven desde el repo. Sacar de Pages las carpetas que nadie lee
   (~590 MB) es una limpieza útil para los 11, pero independiente de este plan (§7).
3. **Por etapas.** El planificador sellado admite 256 trozos por despacho y el grupo de concurrencia guarda UN solo
   despacho pendiente (S152: un tercero desplaza al segundo). Por eso, tandas de 5 volcanes, despachadas de a una.

**Costo estimado** (escalado de Tupungatito, ESTIMACIÓN): por volcán, 626 días ≈ 15,3 h de runner y 32 trozos.

| | volcanes | trozos | runner | reloj con `max-parallel: 6` |
|---|---|---|---|---|
| piloto | 2, un mes | ~4 | ~1,5 h | <1 h |
| una tanda | 5 | ~165 | ~77 h | ~13 h |
| todo | 34 | ~1.120 | ~520 h | 7 tandas, una por día: ~1 semana |

El repo es público: los minutos no se cobran. El NRT de los 11 recibe despachos a las :10 de 01 a 12 UTC con 8 en
paralelo; 6 más del reproceso quedan bajo el tope de 20 simultáneos. El peso en el repo (no en Pages) sube ~475 MB una
sola vez: la historia no se reescribe después.

## 2. Decisiones que necesita Nicolás antes de la Tarea 6

| # | pregunta | recomendación |
|---|---|---|
| H1 | ¿Qué volcanes? (D1 del plan de los 34: los 34 de hoy, o la lista de la RNVV) | Los 34 de `data/sombra_34/`: es lo que ya muestra el tablero. Si D1 saca alguno, se salta su tanda |
| H2 | Orden de las tandas | Por región de norte a sur (vecinos con la misma escena juntos, se revisan juntos). Sin datos de actividad para ordenar por prioridad |
| H3 | Aprobación por tanda o una sola vez | Una sola para las 7 (A45 con tag por tanda), y cada tanda se aplica sólo si su ensayo da 0 huecos y 0 caídas a K |

## 3. Coordinación con la sesión «Los 34 al tablero y fuera la pestaña preliminar»

Esa sesión trabaja en el frontend de los 34. Este plan **no toca `frontend/`**. Le deja un contrato (Tarea 8):
`data/historia_34/<Volcan>.json` con la forma `{"volcano", "perfil", "hasta_utc", "records": [...]}`. Sus records
tienen la misma forma que los de `data/sombra_34/` y todos son anteriores al 2026-11-03 00:00 UTC, así que la unión
por clave `(datetime_utc, sensor)` nunca choca. Se carga sólo cuando el período pedido empieza antes del primer record
de la sombra.

**Respuesta de esa sesión (S183, rama `feat/s183-tablero-absorbe-preliminar34`, 2026-11-13):**
- Su alcance es `frontend/index.html`, `vista_volcan.css`, sus pruebas y una fila de la ficha.
- Sigue leyendo los 34 desde `data/sombra_34/` (`SOMBRA_34_BASE`), sin cargar `historia_34`.
- No toca `pages-deploy.yml` ni `data/`, ni archiva los JSON de abril.
- No decidió D1 ni D5: usa el radio de cumbre de 5 km que ya existía (`RADIO_CUMBRE_SOMBRA_KM`).
- Agrega el rótulo «píxel a X km de la cumbre», la marca «también visto desde X» y los filtros «sólo los 34» y «sólo los 11».
- Retira `preliminar_34.html` y `.js`.

Ojo para la Tarea 8: `focosCompartidosSombra` y `pixelEnCumbreSombra` recorren todos los records cargados de los 34.
Con la historia unida funcionan igual, si los records tienen la misma forma, pero recorren unas 75 veces más records (unos 6.000 de historia por volcán contra unos 80 de la sombra hoy).
Hay que medir el tiempo de la página con la historia cargada de un volcán antes de cargarla para varios a la vez.

---

## 4. Mapa de archivos

| archivo | qué | tarea |
|---|---|---|
| `experiments/_s180_reemplazo_via/plan_trozos_historia.py` | acepta también una lista de sólo los 34 (nunca mezclada con los 11) | 1 |
| `tests/test_reproc_historia_via_s180.py` | pruebas del planificador con los 34 | 1 |
| `experiments/_historia_34/aplicar_historia_34.py` | escribe `data/historia_34/<V>.json` desde la unión, con sus reglas | 3 |
| `experiments/_historia_34/aplicar_historia_34.sh` | envoltorio para `aplicar-reemplazo.yml` | 3 |
| `tests/test_historia_34.py` | reglas del aplicador y guard de los datos | 3 y 7 |
| `experiments/_historia_34/union/<V>.json.gz` | la unión de cada tanda, commiteada (los artifacts vencen a los 30 días) | 5 |
| `experiments/_historia_34/TANDAS.md` | bitácora: run, trozos, huecos, ensayo y commit de cada tanda | 4 a 6 |

`unir_trozos.py` y `aplicar-reemplazo.yml` se usan tal cual: ninguno depende de la lista de los 11.

---

## 5. Tareas

### Tarea 1: el planificador acepta los 34

**Files:**
- Modify: `experiments/_s180_reemplazo_via/plan_trozos_historia.py`
- Test: `tests/test_reproc_historia_via_s180.py`

POR QUÉ: el sellado (`experiments/_s172_retro_paquete/plan_trozos.py`) rehúsa todo volcán fuera de su `TIER_A`. No se
toca: el envoltorio cambia `PT.TIER_A` dentro de `try/finally`, como ya hace con `INICIO_TUPUNGATITO`.

- [ ] **Step 1: escribir las pruebas que fallan**

```python
# al final de tests/test_reproc_historia_via_s180.py
def test_los_34_salen_de_la_grilla_menos_los_11():
    PH = _ph()
    assert len(PH.LOS_34) == 34 and not set(PH.LOS_34) & set(PT.TIER_A)
    assert "Calbuco" in PH.LOS_34 and "Lascar" not in PH.LOS_34


def test_planifica_los_34_y_deja_el_sellado_como_estaba():
    PH = _ph()
    antes = PT.TIER_A
    jobs, _ = PH.planificar(PH.PERFIL_VIA, "Calbuco,Osorno", "2025-03-01:2025-03-31")
    assert jobs and {j["vol"] for j in jobs} == {"Calbuco", "Osorno"}
    assert PT.TIER_A == antes


def test_rehusa_mezclar_los_11_con_los_34():
    PH = _ph()
    with pytest.raises(SystemExit):
        PH.planificar(PH.PERFIL_VIA, "Calbuco,Lascar", "2025-03-01:2025-03-31")


def test_rehusa_un_volcan_que_no_es_de_ningun_grupo():
    PH = _ph()
    with pytest.raises(SystemExit):
        PH.planificar(PH.PERFIL_VIA, "Calbuco,Etna", "2025-03-01:2025-03-31")
```

(`PT` y `_ph()` ya están en ese archivo de pruebas: `PT` es el planificador sellado y `_ph()` importa el de la
historia. Cada trozo trae el volcán en la clave `vol`.)

- [ ] **Step 2: correrlas y verlas fallar**

Run: `python -m pytest tests/test_reproc_historia_via_s180.py -q -k "34 or mezclar or ningun"`
Expected: FAIL con `AttributeError: module 'plan_trozos_historia' has no attribute 'LOS_34'`

- [ ] **Step 3: implementar**

```python
# experiments/_s180_reemplazo_via/plan_trozos_historia.py, después de INICIO_SERIE
import yaml

_GRILLAS = RAIZ / "pipeline" / "grillas_mirova.yaml"
# Los 34 sin MIROVA: los volcanes con grilla que no son de los 11 (S172). Se leen de la grilla, no de una lista
# escrita a mano, para que la lista no se desvíe de lo que la vía puede correr.
LOS_34 = tuple(v for v in yaml.safe_load(_GRILLAS.read_text(encoding="utf-8"))["volcanes"] if v not in PT.TIER_A)


def planificar(perfil, volcanes_txt, ventanas_txt, max_dias=20, max_dias_chillan=10):
    if perfil.strip() != PERFIL_VIA:
        raise PT.Rehusado(f"REHUSADO: este despacho es sólo del brazo de la vía ({PERFIL_VIA}), no de {perfil!r}")
    # Un despacho es de los 11 o de los 34: si la lista es toda de los 34 se planifica contra los 34; si mezcla, se
    # planifica contra los 11 y el sellado rehúsa el primer volcán de los 34 (no hace falta otra regla).
    pedidos = {v.strip() for v in volcanes_txt.split(",") if v.strip()}
    grupo = LOS_34 if pedidos and pedidos <= set(LOS_34) else PT.TIER_A
    previo_ini, previo_tier = PT.INICIO_TUPUNGATITO, PT.TIER_A
    PT.INICIO_TUPUNGATITO, PT.TIER_A = INICIO_SERIE, grupo
    try:
        return PT.planificar(perfil, volcanes_txt, ventanas_txt, max_dias, max_dias_chillan)
    finally:
        PT.INICIO_TUPUNGATITO, PT.TIER_A = previo_ini, previo_tier
```

Actualizar el docstring del módulo: un párrafo «S180 (2026-11-13): los 34», con el porqué de arriba.

- [ ] **Step 4: correr el archivo entero**

Run: `python -m pytest tests/test_reproc_historia_via_s180.py -q`
Expected: todo PASS, incluidas las 8 pruebas previas (el job del workflow sigue idéntico al de la retrospectiva)

- [ ] **Step 5: mutaciones de control** (en el árbol, restaurando con `git checkout --` el archivo al terminar; lección
  S180: leer y escribir en bytes, el repo tiene CRLF): `<= set(LOS_34)` → `>= set(LOS_34)`; quitar la restauración
  de `PT.TIER_A` en el `finally`. Las dos deben dar al menos una prueba roja (comprobado el 2026-11-13 en una copia
  fuera del repo, junto con las cinco de la Tarea 3: 7 de 7 atrapadas).

- [ ] **Step 6: commit**

```bash
git add experiments/_s180_reemplazo_via/plan_trozos_historia.py
git add tests/test_reproc_historia_via_s180.py
git commit -m "historia 34: el planificador de la vía acepta los 34 sin mezclarlos con los 11"
```

### Tarea 2: PR de las Tareas 1 y 3 y merge

`workflow_dispatch` sólo corre con el yml y el planificador en `main` (S73). PR con las Tareas 1 y 3. Recién con CI
verde (`gh pr checks <N> --watch`; un PR sin checks no es verde) se le pide a Nicolás «mergea #N», y se mergea con
`gh pr merge <N> --merge --match-head-commit <sha>`.

### Tarea 3: aplicador de la historia de los 34

**Files:**
- Create: `experiments/_historia_34/aplicar_historia_34.py`
- Create: `experiments/_historia_34/aplicar_historia_34.sh`
- Test: `tests/test_historia_34.py`

REGLAS y por qué:
- sólo records con `datetime_utc` anterior a `CORTE = "2026-11-03 00:00"` (desde ahí manda la sombra; su primer record
  es del 2026-11-03 01:55);
- todos con `via_codigo_mirova is True` y perfil `_s172_retro_paquete` (una caída a K no se publica como vía, A118);
- sólo volcanes de `LOS_34`;
- un archivo de historia que ya existe se UNE por clave (gana el que ya estaba): así se pueden aplicar las tandas de a
  una y repetir una sin duplicar;
- nunca escribe en `data/sombra_34/` ni en `data/mirova_equivalent/`.

- [ ] **Step 1: escribir las pruebas que fallan**

```python
# tests/test_historia_34.py
# -*- coding: utf-8 -*-
"""Reglas de experiments/_historia_34/aplicar_historia_34.py (historia de los 34 con la vía)."""
import gzip
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "_historia_34"))
import aplicar_historia_34 as A  # noqa: E402


def _r(dt, sensor="VIIRS_NOAA20", via=True, perfil="_s172_retro_paquete", vrp=0.0):
    return {"datetime_utc": dt, "sensor": sensor, "via_codigo_mirova": via, "vrp_mw": vrp,
            "regimen": {"perfil": perfil}}


def _union(tmp_path, v, recs):
    d = tmp_path / "union"
    d.mkdir(exist_ok=True)
    (d / f"{v}.json.gz").write_bytes(gzip.compress(json.dumps({"volcano": v, "records": recs}).encode()))
    return d


def test_escribe_solo_lo_anterior_al_corte(tmp_path):
    u = _union(tmp_path, "Calbuco", [_r("2026-11-02 23:59"), _r("2026-11-03 00:00"), _r("2025-02-15 05:00")])
    inf = A.aplicar(u, tmp_path / "hist", aplicar=True)
    s = json.loads((tmp_path / "hist" / "Calbuco.json").read_text(encoding="utf-8"))
    assert [r["datetime_utc"] for r in s["records"]] == ["2025-02-15 05:00", "2026-11-02 23:59"]
    assert s["hasta_utc"] == A.CORTE and inf["Calbuco"]["tras_corte"] == 1


def test_rehusa_caida_a_k_y_otro_perfil(tmp_path):
    for malo in (_r("2025-03-01 05:00", via="sin_grilla"), _r("2025-03-01 05:00", perfil="_s172_retro_k")):
        u = _union(tmp_path, "Calbuco", [malo])
        with pytest.raises(A.Rehusado):
            A.aplicar(u, tmp_path / "hist", aplicar=True)
    assert not (tmp_path / "hist").exists()


def test_rehusa_un_volcan_de_los_11(tmp_path):
    u = _union(tmp_path, "Lascar", [_r("2025-03-01 05:00")])
    with pytest.raises(A.Rehusado):
        A.aplicar(u, tmp_path / "hist", aplicar=True)


def test_ensayo_no_escribe(tmp_path):
    u = _union(tmp_path, "Calbuco", [_r("2025-03-01 05:00")])
    inf = A.aplicar(u, tmp_path / "hist", aplicar=False)
    assert inf["Calbuco"]["nuevos"] == 1 and not (tmp_path / "hist").exists()


def test_una_tanda_repetida_no_duplica_y_gana_lo_que_estaba(tmp_path):
    u = _union(tmp_path, "Calbuco", [_r("2025-03-01 05:00", vrp=1.0)])
    A.aplicar(u, tmp_path / "hist", aplicar=True)
    u = _union(tmp_path, "Calbuco", [_r("2025-03-01 05:00", vrp=9.0), _r("2025-03-02 05:00")])
    inf = A.aplicar(u, tmp_path / "hist", aplicar=True)
    s = json.loads((tmp_path / "hist" / "Calbuco.json").read_text(encoding="utf-8"))
    assert [r["vrp_mw"] for r in s["records"]] == [1.0, 0.0] and inf["Calbuco"]["ya_estaban"] == 1


def test_orden_cronologico_y_sin_claves_repetidas(tmp_path):
    u = _union(tmp_path, "Calbuco", [_r("2025-03-02 05:00"), _r("2025-03-01 05:00"),
                                     _r("2025-03-01 05:00", "MODIS_AQUA")])
    A.aplicar(u, tmp_path / "hist", aplicar=True)
    s = json.loads((tmp_path / "hist" / "Calbuco.json").read_text(encoding="utf-8"))
    fechas = [r["datetime_utc"] for r in s["records"]]
    assert fechas == sorted(fechas) and len(s["records"]) == 3
```

- [ ] **Step 2: correrlas y verlas fallar**

Run: `python -m pytest tests/test_historia_34.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'aplicar_historia_34'`

- [ ] **Step 3: implementar**

```python
# experiments/_historia_34/aplicar_historia_34.py
# -*- coding: utf-8 -*-
"""Escribe la historia de los 34 volcanes sin MIROVA con la vía en data/historia_34/<V>.json.

POR QUÉ. Nicolás pidió el 2026-11-13 tener hacia atrás los 34 que el tablero ya muestra desde la sombra diaria
(data/sombra_34/, desde el 2026-11-03). La historia va en archivos PROPIOS y no en los de la sombra: el tablero baja
completo el archivo de la sombra al cargar, y la sombra empuja con `git pull --rebase -X theirs`, que borraría la
historia si este commit entra mientras ella corre (plan docs/superpowers/plans/2026-11-13-historia-34-volcanos-via.md, §1).

REGLAS: sólo antes del CORTE (desde ahí manda la sombra); todo record con la vía y el perfil del brazo; sólo los 34;
un archivo existente se une por clave y gana lo que ya estaba (las tandas se aplican de a una y se pueden repetir).
Por defecto es ENSAYO. Lo llama aplicar_historia_34.sh desde .github/workflows/aplicar-reemplazo.yml.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "_s180_reemplazo_via"))
from plan_trozos_historia import LOS_34  # noqa: E402

PERFIL = "_s172_retro_paquete"
CORTE = "2026-11-03 00:00"   # primer día de data/sombra_34 (scripts/ventana_sombra.py no devuelve nada antes)
UNION = RAIZ / "experiments" / "_historia_34" / "union"
DESTINO = RAIZ / "data" / "historia_34"


class Rehusado(Exception):
    pass


def _clave(r):
    return (r.get("datetime_utc"), r.get("sensor"))


def _minuto(dt):
    return (dt or "").replace("T", " ")[:16]


def aplicar(union: Path, destino: Path, aplicar: bool) -> dict:
    """Calcula todo antes de escribir: si un volcán se rehúsa, no se escribe ninguno."""
    informe, salida = {}, {}
    for gz in sorted(union.glob("*.json.gz")):
        v = gz.name[:-len(".json.gz")]
        if v not in LOS_34:
            raise Rehusado(f"REHUSADO: {v} no es de los 34")
        recs = json.loads(gzip.decompress(gz.read_bytes())).get("records", [])
        nuevos, tras = {}, 0
        for r in recs:
            if _minuto(r.get("datetime_utc")) >= CORTE:
                tras += 1
                continue
            if r.get("via_codigo_mirova") is not True:
                raise Rehusado(f"REHUSADO: {v} {_clave(r)} no es de la vía ({r.get('via_codigo_mirova')!r})")
            if (r.get("regimen") or {}).get("perfil") != PERFIL:
                raise Rehusado(f"REHUSADO: {v} {_clave(r)} no viene de {PERFIL}")
            nuevos[_clave(r)] = r
        previo = destino / f"{v}.json"
        ya = {}
        if previo.exists():
            ya = {_clave(r): r for r in json.loads(previo.read_text(encoding="utf-8"))["records"]}
        repetidos = sum(1 for k in nuevos if k in ya)
        todos = {**nuevos, **ya}   # gana lo que ya estaba
        lista = sorted(todos.values(), key=lambda r: (r.get("datetime_utc", ""), r.get("sensor", "")))
        salida[v] = {"volcano": v, "perfil": PERFIL, "hasta_utc": CORTE, "records": lista}
        informe[v] = {"en_union": len(recs), "tras_corte": tras, "nuevos": len(nuevos) - repetidos,
                      "ya_estaban": repetidos, "total": len(lista)}
    if aplicar:
        destino.mkdir(parents=True, exist_ok=True)
        for v, s in salida.items():
            with open(destino / f"{v}.json", "w", encoding="utf-8", newline="\n") as f:
                json.dump(s, f, indent=1, ensure_ascii=False)
    return informe


def main(argv=None) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--union", default=str(UNION))
    ap.add_argument("--destino", default=str(DESTINO))
    ap.add_argument("--informe", required=True)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args(argv)
    try:
        inf = aplicar(Path(a.union), Path(a.destino), a.aplicar)
    except Rehusado as e:
        print(e, file=sys.stderr)
        return 2
    Path(a.informe).parent.mkdir(parents=True, exist_ok=True)
    Path(a.informe).write_text(json.dumps(inf, indent=1, ensure_ascii=False), encoding="utf-8")
    for v, i in inf.items():
        print(f"{v:22s} en la unión {i['en_union']:5d}  nuevos {i['nuevos']:5d}  ya estaban {i['ya_estaban']:5d}  "
              f"tras el corte {i['tras_corte']:3d}  total {i['total']:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

```bash
# experiments/_historia_34/aplicar_historia_34.sh
#!/usr/bin/env bash
# Lo despacha .github/workflows/aplicar-reemplazo.yml (plan 2026-11-13-historia-34-volcanos-via.md, Tarea 6).
set -euo pipefail
python experiments/_historia_34/aplicar_historia_34.py \
  --informe experiments/_historia_34/aplicado/informe.json --aplicar
```

- [ ] **Step 4: correr las pruebas**

Run: `python -m pytest tests/test_historia_34.py -q`
Expected: 6 passed

- [ ] **Step 5: mutaciones de control** (en bytes, restaurando al terminar): `>= CORTE` → `> CORTE`;
  `is not True` → `is False`; `{**nuevos, **ya}` → `{**ya, **nuevos}`; quitar el `sorted`; quitar el chequeo de
  `LOS_34`. Las cinco deben dar al menos una prueba roja.

- [ ] **Step 6: commit**

```bash
git add experiments/_historia_34/aplicar_historia_34.py
git add experiments/_historia_34/aplicar_historia_34.sh
git add tests/test_historia_34.py
git commit -m "historia 34: aplicador a data/historia_34 (antes del corte de la sombra, sólo la vía)"
```

### Tarea 4: piloto barato antes de la primera tanda (lección S170: ensayar antes del paso caro)

- [ ] **Step 1:** despachar 2 volcanes, un mes:

```bash
gh workflow run reproc-historia-via.yml --ref main -f profile=_s172_retro_paquete -f volcanoes=Calbuco,Parinacota -f ventanas=2025-03-01:2025-03-31
```

  Uno del sur y uno del Altiplano, para ver dos fondos distintos.
- [ ] **Step 2:** esperar el run (`gh run watch <id>` en segundo plano) y bajarlo con `gh run download <id>` a
  `D:\vrp-trabajo\temporales\historia_34\piloto\` (carpeta nueva y vacía, fuera del repo).
- [ ] **Step 3:** unir con `python -I experiments/_s180_reemplazo_via/unir_trozos.py --salida <dir>/union --informe <dir>/informe.json <dir>`
  y exigir: 0 huecos, todas las marcas `true`, trozos con intento 1.
- [ ] **Step 4:** anotar en `experiments/_historia_34/TANDAS.md` las horas de runner reales
  (`gh api repos/MendozaVolcanic/VRP-chile/actions/runs/<id>/jobs?per_page=100`, suma de `completed_at - started_at`) y
  corregir la tabla de costo del §1 si se aleja más de 30 %.

### Tarea 5: cada tanda (repetir 7 veces, de a una)

Tandas propuestas (H2, de norte a sur; ajustar con D1):

| tanda | volcanes |
|---|---|
| 1 | Taapaca, Parinacota, Guallatiri, Irruputuncu, OlcaParuma |
| 2 | Ollague, SanPedro, Putana, SanJose, Tinguiririca |
| 3 | DescabezadoGrande, CerroAzulQuizapu, LagunaDelMaule, NevadoDeLongavi, Antuco |
| 4 | Callaqui, Lonquimay, Tolhuaca, Sollipulli, Quetrupillan |
| 5 | Lanin, MochoChoshuenco, CarranLosVenados, AntillancaCasablanca, Osorno |
| 6 | Calbuco, YateHornopiren, Huequi, Michinmahuida, CorcovadoYanteles |
| 7 | Melimoyu, MacaCay, Mentolat, Hudson |

- [ ] **Step 1:** comprobar que no hay otro despacho del grupo en cola
  (`gh run list -w reproc-historia-via.yml --status queued`); si hay, esperar (un tercero desplazaría al segundo).
- [ ] **Step 2:** despachar después de las 13 UTC (el NRT de los 11 ya terminó su ciclo de 01 a 12 UTC):

```bash
gh workflow run reproc-historia-via.yml --ref main -f profile=_s172_retro_paquete -f volcanoes=<los 5 de la tanda> -f ventanas=2025-02-15:2025-12-31,2026-01-01:2026-01-31,2026-02-01:2026-03-31,2026-04-01:2026-09-30,2026-10-01:2026-10-16,2026-10-17:2026-11-02
```

  Las ventanas siguen los tramos del planificador sellado (R25, F26, DM y OTRO en
  `experiments/_s172_retro_paquete/plan_trozos.py::tramo_de`): un trozo que cruza de tramo se rehúsa. Con esas
  ventanas, 5 volcanes dan 165 trozos (comprobado el 2026-11-13 con 5 de los 11). Comprobar que el job `plan` pase y
  que el número de trozos sea ≤ 256.
- [ ] **Step 3:** al terminar, relanzar sólo los trozos rojos con su ventana (el intento más alto gana en la unión).
  Un trozo que falla dos veces se anota como hueco y NO se aplica esa tanda hasta cerrarlo.
- [ ] **Step 4:** bajar a `D:\vrp-trabajo\temporales\historia_34\tanda<N>\` (parada si C: o D: baja de 3 GB) y unir:

```bash
python -I experiments/_s180_reemplazo_via/unir_trozos.py --salida experiments/_historia_34/union --informe experiments/_historia_34/union/informe_tanda<N>.json D:/vrp-trabajo/temporales/historia_34/tanda<N>
```

- [ ] **Step 5:** exigir en el informe, por volcán: `desde` 2025-02-15, `hasta` 2026-11-02, `huecos: []`, marcas sólo
  `:true`. Ensayo: `python -I experiments/_historia_34/aplicar_historia_34.py --informe <tmp>/ensayo.json` (sin
  `--aplicar`) y anotar sus conteos en `TANDAS.md`.
- [ ] **Step 6:** commitear los `.json.gz` de la tanda y su informe en una rama, PR, CI verde, «mergea #N» de Nicolás.

### Tarea 6: aplicar una tanda (A45)

- [ ] **Step 1:** con el «sí» de Nicolás para esa tanda (o el de H3 para las 7), verificar que `sombra-34.yml` no está
  corriendo (`gh run list -w sombra-34.yml --status in_progress`); el archivo de historia no lo toca, pero el tag
  defensivo debe marcar un main quieto.
- [ ] **Step 2:** despachar:

```bash
gh workflow run aplicar-reemplazo.yml --ref main -f confirmacion=si -f script=experiments/_historia_34/aplicar_historia_34.sh -f tag=pre-historia-34-tanda<N> -f pruebas="tests/test_historia_34.py tests/test_sombra_34_s172.py" -f mensaje="historia 34: tanda <N> con la vía en data/historia_34"
```

- [ ] **Step 3:** comprobar en `origin/main` (no en el checkout local) que aparecieron los 5 archivos
  `data/historia_34/<V>.json` y que `data/sombra_34/` no cambió en ese commit (`git show --stat <sha>`).

### Tarea 7: guard de los datos publicados

**Files:**
- Modify: `tests/test_historia_34.py`

- [ ] **Step 1: agregar la prueba sobre los datos reales**

```python
DATOS = ROOT / "data" / "historia_34"


@pytest.mark.skipif(not DATOS.exists(), reason="sin historia aplicada todavía")
def test_historia_publicada_es_toda_de_la_via_y_anterior_a_la_sombra():
    for f in sorted(DATOS.glob("*.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        assert f.stem in A.LOS_34 and s["volcano"] == f.stem
        recs = s["records"]
        assert all(r.get("via_codigo_mirova") is True for r in recs), f.stem
        assert all(A._minuto(r["datetime_utc"]) < A.CORTE for r in recs), f.stem
        claves = [A._clave(r) for r in recs]
        assert len(claves) == len(set(claves)), f.stem
```

- [ ] **Step 2:** correrla con la carpeta ausente (SKIP) y después de la primera tanda (PASS); commit junto con la
  Tarea 3 o en el PR de la primera tanda.

### Tarea 8: contrato para el frontend (lo implementa la sesión del tablero de los 34, no este plan)

Escribir en el PR de la Tarea 2, para esa sesión:
- **Dónde:** `https://raw.githubusercontent.com/MendozaVolcanic/VRP-chile/main/data/historia_34/<V>.json`. No está en
  Pages, igual que la sombra.
- **Cuándo cargarlo:** sólo si el período pedido empieza antes del primer record de la sombra. Pesa unos 14 MB por
  volcán; cargar los 34 al abrir la página serían ~475 MB.
- **Cómo unirlo:** por clave `(datetime_utc, sensor)`; nunca chocan, porque la historia termina antes del 2026-11-03
  00:00 UTC y la sombra empieza después.
- **Qué mostrar:** un volcán sin `historia_34` (tanda pendiente) se ve como hoy.

### Tarea 9: cierre

- [ ] Las 7 tandas aplicadas y `TANDAS.md` completo (run, trozos, horas de runner reales, huecos, conteos del ensayo,
  commit de aplicación).
- [ ] Verificador limpio de otro modelo sobre el aplicador y una tanda (ensayo independiente, sin llamadas a NASA).
- [ ] Ficha SDA: una línea en el historial de versiones (`docs/FICHA_SDA_VRP_CHILE.md`) sobre la historia de los 34.

---

## 6. Riesgos y qué los ataja

| riesgo | ataja |
|---|---|
| Borrar historia por el rebase de la sombra | archivo propio que la sombra no toca (§1) |
| Página que baja 475 MB | historia sólo a pedido (Tarea 8) |
| Un despacho desplaza a otro en el grupo | de a uno, revisando la cola (Tarea 5, Step 1) |
| Trozo perdido que se publica como «sin pasadas» | `huecos: []` exigido y prueba de racha (Tarea 5, Step 5) |
| Caída a K publicada como vía | el aplicador rehúsa todo `via_codigo_mirova` distinto de `true` (Tarea 3) |
| Artifacts que vencen a los 30 días | la unión de cada tanda se commitea en cuanto se baja (Tarea 5, Step 6) |
| NRT de los 11 más lento | despacho después de las 13 UTC; `max-parallel: 6` |
| Repo más pesado | ~475 MB una sola vez; el repo ya pesa 12,8 GB (§7) |

## 7. Fuera de este plan (anotado para no perderlo)

- **Pages, lista explícita:** hoy `pages-deploy.yml` copia `data/` entera menos las sombras y guardias. De lo que se
  copia, las páginas leen unos 280 MB (`mirova_equivalent`, `mirova`, `experimental`, `experimental_v2`, `alerts`,
  `_s99_test1_eq16`, `mirova_reference`, `_c0_residuales`) y van unos 500 MB que nadie lee (medido con
  `git ls-tree -r -l origin/main data` el 2026-11-13). Pasar a una lista explícita,
  con una prueba que la saque del código del frontend, devuelve margen al techo de 1 GB para los 11.
- **Peso del repo (12,8 GB):** crece sobre todo porque el NRT reescribe JSON de ~15 MB cada 2 horas. Un repo de datos
  aparte, o un formato que no reescriba toda la serie, se evalúa por separado.
- **`_recent` para la sombra de los 34:** su archivo crece ~0,1 MB por semana; en un año el tablero bajaría ~200 MB al
  abrir. Hace falta el mismo `_recent` que tienen los 11 antes de mediados de 2027.
