# Flag de geolocalización MxD03 para MODIS: plan de implementación (para cuando Nicolás dé el sí)

> **Para agentes:** SUB-SKILL REQUERIDA: superpowers:executing-plans o subagent-driven-development, tarea por tarea.
> Los pasos usan casillas (`- [ ]`). **Nada de este plan se ejecuta sin el tag defensivo y el sí explícito de Nicolás
> para este cambio (A45).** El plan no toca `pipeline/` por sí mismo: es el guion para cuando llegue el sí.

**Objetivo:** que MODIS ubique cada píxel con el producto de geolocalización MxD03 (que el pipeline ya baja y no usa),
que una pasada en que el cráter no tiene posición no se guarde como «noche observada sin anomalía», y que la distancia
que decide la etiqueta `summit`/`far` se mida desde el cráter y no desde el centro del volcán.

**Arquitectura:** tres flags del perfil, apagados por defecto y leídos desde `pipeline.profile` (A89), en un solo PR
dentro del paquete MODIS (decisión 1 del bloque 0 de `tasks/LOOP_MODIS.md`, aplicada con D-48):
`enable_modis_geo_mxd03` (posición por píxel), `enable_modis_crater_sin_dato` (estado «sin dato», sólo con el
primero encendido) y `enable_modis_dist_desde_crater` (distancia de la etiqueta). Cada uno se mide por separado.

**Stack:** Python 3.11, numpy, pyhdf (sólo en Linux: las pruebas con HDF corren en GitHub Actions), pytest, node para
el predicado del tablero.

---

## 0. Por qué (el fenómeno antes que el código)

Un píxel MODIS no trae su posición: el archivo de radiancias (MOD021KM) sólo lleva la latitud y longitud de uno de
cada cinco píxeles por lado, y el pipeline estira esa grilla con una interpolación lineal (`_interp_geo`,
`pipeline/process_modis.py:385-396`) que la trata como si estuviera muestreada en el píxel 5i cuando lo está en el 5i+2.
Cada píxel recibe así la posición de su vecino: el cráter de Láscar aparece corrido 1 a 3 km hacia el sensor cerca del
nadir y hasta 11,5 km en el borde del barrido (A61 de S162, H2, verificada). El producto MxD03 trae la posición de cada
píxel con corrección de terreno; Coppola et al. 2026 (Scientific Data, p. 4) lo nombra como insumo de MIROVA (MOD-A,
PR #902). El A/B de S162 (MOD-B, 5.465 pasadas nocturnas) dio **CUMPLE SIN DAÑO**: con MxD03 no se pierde ninguna de
las 48 protegidas y las 48 quedan más cerca del cráter (mediana 0,34 km contra 1,58), con el mismo calor (46 de 48 son
los mismos píxeles; verificador de la A61).

Dos defectos que la A61 encontró en el camino y que este plan arregla en el mismo paquete:

1. **Una pasada sin cráter se guarda como negativo** (H1 y VA61-01). Cuando el cráter cae en un bloque de relleno de
   geolocalización (−999, escaneos enteros sin efemérides) o en la primera o última línea o frame del gránulo (el
   volcán quedó en el borde de la franja), el pipeline igual escribe un record con 0 píxeles anómalos: en el tablero es
   una noche tranquila, y en toda evaluación es un «negativo limpio» que en realidad no miró el cráter. Son unos 215 de
   5.465 records (3,9 %), 16 a 20 veces lo que daría el azar (verificador de la A61, VA61-01; que el cráter quede
   realmente fuera es SOSPECHA hasta medirlo en el censo de MOD-D, que ya guarda `crater_mxd03.dist_km` y
   `vecinos_validos`).
2. **La etiqueta mide desde el centro del volcán** (H5). `dist` se calcula desde `volcano_lat/lon`
   (`process_modis.py:560`); de ahí sale el `dist_km` de cada píxel anómalo (`:1143`), el `hotspot_dist_km` (`:1151`)
   y el `final_hotspot_dist_km` (`:1363`), que decide `summit`/`far` (`:1382-1384`). En Láscar el centro está 0,68 km
   al sur del cráter: una alerta de 2,19 MW a 4,4 km al NE del cráter queda a 5,05 km del centro y sale `far`
   (Láscar 2026-03-12 07:25 en 5 de 20 brazos R). El cúmulo (`primary_cluster.centroid_dist_km`) ya se mide desde el
   cráter, así que hoy el mismo record tiene dos distancias desde dos puntos distintos (A46).

Lo que este plan **no** cambia: el anillo de fondo de 5 a 25 km sigue centrado donde está (es la geometría del ROI,
D17, y cambiarla es otro A/B); los ángulos del sensor siguen saliendo de la grilla de 5 km (no entran en detección y
así se reproduce el brazo X de MOD-B); VIIRS tiene el mismo patrón de distancia (`process_viirs.py:780`) y queda como
seguimiento aparte.

## 1. Qué tiene que pasar antes del primer edit

- [ ] MOD-D (paquete MODIS) despachado y leído, o pasado el 2026-11-24 sin paquete (entonces el flag entra solo).
- [ ] El censo de MOD-D midió `crater_mxd03.dist_km` y `vecinos_validos` en las 5.465 pasadas: la regla de «sin
      dato» de la Tarea 3 se confirma o se corrige con ese dato, no antes (A115). Si alguna alerta de MIROVA (protegida
      o bajo 1 MW) cae en «sin dato», se lista y decide Nicolás.
- [ ] Medición sin red del efecto de la Tarea 5 sobre `data/` (Tarea 5, paso 1).
- [ ] Sí explícito de Nicolás, por escrito, para este cambio.
- [ ] Tag defensivo empujado: `git tag pre-s16x-mxd03-modis <sha> && git push origin pre-s16x-mxd03-modis`.

## 2. Archivos

| archivo | qué |
|---|---|
| `pipeline/profiles/mirova_equivalent.yaml` | tres claves nuevas en `thresholds:`, todas `false` |
| `pipeline/profile.py` | lectura de las tres claves (junto a `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`, `:658`) |
| `pipeline/process_modis.py` | `leer_mxd03` (nueva), `crater_cubierto` (nueva), uso en `calculate_vrp` (`:547`, `:560`, `:1143`) |
| `tests/test_modis_geo_mxd03_s16x.py` | pruebas sin HDF (lector parchado) de las tres piezas |
| `tests/test_guard_mxd03_flags_s16x.py` | guard: los tres flags se leen desde `pipeline.profile` y llegan a todos sus consumidores (A118) |
| `.github/workflows/probe-mxd03-equivalencia.yml` | reproduce el brazo X de MOD-B record por record sobre los 5 gránulos del humo (pyhdf) |
| `docs/FICHA_SDA_VRP_CHILE.md`, `docs/MIROVA_DIVERGENCES.md` (D35), `frontend/index.html`, `diario.html`, `mosaico.html` | marca de régimen y texto para OVDAS (Tarea 7) |

## Tarea 1: los flags, apagados

**Files:** Modify `pipeline/profiles/mirova_equivalent.yaml`, `pipeline/profile.py:658`. Test
`tests/test_guard_mxd03_flags_s16x.py`.

- [ ] **Paso 1: prueba que falla**

```python
# tests/test_guard_mxd03_flags_s16x.py
import importlib
import os


def _perfil():
    os.environ["VRP_PROFILE"] = "mirova_equivalent"
    import pipeline.profile as p
    return importlib.reload(p)


def test_flags_mxd03_existen_y_estan_apagados():
    p = _perfil()
    for nombre in ("ENABLE_MODIS_GEO_MXD03", "ENABLE_MODIS_CRATER_SIN_DATO", "ENABLE_MODIS_DIST_DESDE_CRATER"):
        assert getattr(p, nombre) is False, nombre


def test_process_modis_lee_los_flags_del_perfil():
    import pipeline.process_modis as pm
    for nombre in ("ENABLE_MODIS_GEO_MXD03", "ENABLE_MODIS_CRATER_SIN_DATO", "ENABLE_MODIS_DIST_DESDE_CRATER"):
        assert hasattr(pm, nombre), nombre
```

- [ ] **Paso 2:** `pytest tests/test_guard_mxd03_flags_s16x.py -v`. Esperado: FAIL, `AttributeError`.
- [ ] **Paso 3: implementación mínima.** En el YAML, dentro de `thresholds:` (no en la raíz: A89, la clave se lee de
  esa sección):

```yaml
    enable_modis_geo_mxd03: false          # S16x, D35: posicion por pixel del MxD03 en vez de _interp_geo
    enable_modis_crater_sin_dato: false    # S16x, A61 H1/VA61-01: crater sin posicion -> sin record (no negativo)
    enable_modis_dist_desde_crater: false  # S16x, A61 H5: dist_km del pixel anomalo desde el crater
```

  En `pipeline/profile.py`, junto a la línea 658, con el mismo patrón:

```python
ENABLE_MODIS_GEO_MXD03: bool = bool(_cfg.get("enable_modis_geo_mxd03", _p.get("enable_modis_geo_mxd03", False)))
ENABLE_MODIS_CRATER_SIN_DATO: bool = bool(_cfg.get("enable_modis_crater_sin_dato",
                                                   _p.get("enable_modis_crater_sin_dato", False)))
ENABLE_MODIS_DIST_DESDE_CRATER: bool = bool(_cfg.get("enable_modis_dist_desde_crater",
                                                     _p.get("enable_modis_dist_desde_crater", False)))
```

  y en el bloque `from pipeline.profile import (...)` de `process_modis.py` (`:173`) los tres nombres.
- [ ] **Paso 4:** la prueba pasa. **Paso 5:** suite completa sobre árbol quieto (A112):
  `python -m pytest -q -p no:cacheprovider` sin fallas nuevas contra `origin/main` (A50).
- [ ] **Paso 6:** `git add` por archivo y commit «S16x MxD03: tres flags apagados».

## Tarea 2: posición por píxel del MxD03

**Files:** Modify `pipeline/process_modis.py` (función nueva `leer_mxd03` antes de `calculate_vrp`, y `:547-558`).
Test `tests/test_modis_geo_mxd03_s16x.py`.

- [ ] **Paso 1: pruebas que fallan** (sin HDF: el lector se parcha, igual que el arnés de MOD-B)

```python
# tests/test_modis_geo_mxd03_s16x.py
import numpy as np
import pytest
from unittest.mock import patch

import pipeline.process_modis as pm


def test_leer_mxd03_limpia_el_relleno():
    lat = np.array([[-23.0, -999.0], [-23.1, -23.2]], np.float32)
    lon = np.array([[-67.0, -999.0], [-67.1, -67.2]], np.float32)
    la, lo = pm.limpiar_relleno_geo(lat, lon)
    assert np.isnan(la[0, 1]) and np.isnan(lo[0, 1])
    assert la[1, 1] == pytest.approx(-23.2)


def test_latlon_de_calculo_con_flag_es_mxd03():
    datos = {"lat": np.zeros((4, 4), np.float32), "lon": np.zeros((4, 4), np.float32)}
    mxd = (np.full((4, 4), -23.0, np.float32), np.full((4, 4), -67.0, np.float32))
    with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True), patch.object(pm, "leer_mxd03", lambda _p: mxd):
        lat, lon, fuente = pm.posicion_de_calculo(datos, "geo.hdf")
    assert fuente == "mxd03" and np.all(lat == -23.0)


def test_latlon_de_calculo_sin_flag_es_la_de_siempre():
    datos = {"lat": np.ones((4, 4), np.float32), "lon": np.ones((4, 4), np.float32)}
    lat, lon, fuente = pm.posicion_de_calculo(datos, "geo.hdf")
    assert fuente == "interp_5km" and lat is datos["lat"]


def test_mxd03_que_no_calza_cae_a_la_interpolada_y_lo_dice():
    datos = {"lat": np.ones((4, 4), np.float32), "lon": np.ones((4, 4), np.float32)}
    malo = (np.zeros((3, 3), np.float32), np.zeros((3, 3), np.float32))
    with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True), patch.object(pm, "leer_mxd03", lambda _p: malo):
        lat, lon, fuente = pm.posicion_de_calculo(datos, "geo.hdf")
    assert fuente == "interp_5km_mxd03_no_calza" and lat is datos["lat"]
```

- [ ] **Paso 2:** `pytest tests/test_modis_geo_mxd03_s16x.py -v`. Esperado: FAIL (`limpiar_relleno_geo` no existe).
- [ ] **Paso 3: implementación**, antes de `calculate_vrp`:

```python
RELLENO_GEO_MXD03 = -999.0   # MOD03/MYD03: _FillValue de Latitude y Longitude (escaneos sin efemerides)


def limpiar_relleno_geo(lat, lon):
    """POR QUE: el relleno -999 interpolado o usado como posicion produce latitudes de cientos de grados (A61 H1). Un
    pixel sin posicion se marca NaN y no entra a ningun ROI ni anillo: se pierde, que es lo honesto."""
    lat = np.asarray(lat, np.float32).copy()
    lon = np.asarray(lon, np.float32).copy()
    malo = (lat < -90) | (lat > 90) | (lon < -180) | (lon > 180)
    lat[malo] = np.nan
    lon[malo] = np.nan
    return lat, lon


def leer_mxd03(geo_path):
    """Latitude y Longitude por pixel del MxD03 (1 km), sin interpolar."""
    from pyhdf.SD import SD, SDC
    sd = SD(str(geo_path), SDC.READ)
    try:
        return limpiar_relleno_geo(sd.select("Latitude").get(), sd.select("Longitude").get())
    finally:
        sd.end()


def posicion_de_calculo(data, geo_path):
    """(lat, lon, fuente) que usa calculate_vrp. Con ENABLE_MODIS_GEO_MXD03 apagado, la de siempre. Si el MxD03 no se
    puede leer o no calza con el L1B, se usa la interpolada y el record lo declara (no se pierde la pasada)."""
    if not ENABLE_MODIS_GEO_MXD03:
        return data["lat"], data["lon"], "interp_5km"
    try:
        lat_m, lon_m = leer_mxd03(geo_path)
    except Exception:
        return data["lat"], data["lon"], "interp_5km_mxd03_ilegible"
    if lat_m.shape != np.shape(data["lat"]):
        return data["lat"], data["lon"], "interp_5km_mxd03_no_calza"
    return lat_m, lon_m, "mxd03"
```

  y en `calculate_vrp`, reemplazando `lat = data["lat"]` / `lon = data["lon"]` (`:557-558`, después de la rama de
  `ENABLE_UTM_REGRID`, que con MxD03 queda fuera de alcance):

```python
    lat, lon, geo_fuente = posicion_de_calculo(data, geo_path)
```

  y `"geo_fuente": geo_fuente` en el dict del resultado. Actualizar el docstring («geo_path ... not used») y la
  cabecera FICHA del archivo.
- [ ] **Paso 4:** pasan las 4. **Paso 5:** suite completa, árbol quieto. **Paso 6:** commit por archivo.

## Tarea 3: cráter sin posición, sin record

**Files:** Modify `pipeline/process_modis.py` (función nueva `crater_cubierto` y uso al inicio de `calculate_vrp`).
Test: el mismo archivo de la Tarea 2.

- [ ] **Paso 0 (no se salta):** leer en el censo de MOD-D la distribución de `crater_mxd03.dist_km` y
  `vecinos_validos` en las pasadas con `borde` falso, y confirmar que la regla de abajo no deja fuera ninguna pasada
  normal (cero con `vecinos_validos` falso fuera del borde y del relleno) y sí deja fuera las de H1 y VA61-01. Si el
  dato contradice la regla, se corrige la regla aquí, por escrito, antes de seguir (A115).
- [ ] **Paso 1: pruebas que fallan**

```python
def _grilla(n=9):
    i = np.arange(n)
    lat, lon = np.meshgrid(-23.0 - i * 0.009, -67.0 + i * 0.0098, indexing="ij")
    return lat.astype(np.float32), lon.astype(np.float32)


def test_crater_cubierto_en_el_interior():
    lat, lon = _grilla()
    assert pm.crater_cubierto(lat, lon, float(lat[4, 4]), float(lon[4, 4])) is True


def test_crater_en_un_bloque_de_relleno_no_esta_cubierto():
    lat, lon = _grilla()
    lat[3:6, :], lon[3:6, :] = np.nan, np.nan
    assert pm.crater_cubierto(lat, lon, -23.036, -66.9608) is False


def test_crater_en_la_primera_linea_no_esta_cubierto():
    lat, lon = _grilla()
    assert pm.crater_cubierto(lat, lon, float(lat[0, 4]), float(lon[0, 4])) is False


def test_calculate_vrp_sin_cobertura_devuelve_none_con_flags():
    lat, lon = _grilla()
    lat[:], lon[:] = np.nan, np.nan
    with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True), patch.object(pm, "ENABLE_MODIS_CRATER_SIN_DATO", True), \
            patch.object(pm, "crater_cubierto", lambda *a: False):
        assert pm.sin_dato_de_geolocalizacion(lat, lon, -23.0, -67.0, "mxd03") is True
    assert pm.sin_dato_de_geolocalizacion(lat, lon, -23.0, -67.0, "interp_5km") is False
```

- [ ] **Paso 2:** FAIL. **Paso 3: implementación**

```python
def crater_cubierto(lat, lon, vent_lat, vent_lon):
    """POR QUE: si el pixel con posicion mas cercano al crater esta en el borde del granulo o le falta posicion a
    algun vecino, el crater puede no estar en la imagen (A61 H1, VA61-01). Una pasada asi no es una noche observada sin
    anomalia: es una noche sin dato, y no debe contarse como negativo."""
    d = haversine_km(vent_lat, vent_lon, lat, lon)
    if not np.isfinite(d).any():
        return False
    i, j = np.unravel_index(np.nanargmin(d), d.shape)
    n_l, n_f = d.shape
    if i in (0, n_l - 1) or j in (0, n_f - 1):
        return False
    return bool(np.isfinite(lat[i - 1:i + 2, j - 1:j + 2]).all())


def sin_dato_de_geolocalizacion(lat, lon, vent_lat, vent_lon, geo_fuente):
    """Solo con MxD03 (donde el relleno ya es NaN) y con el flag del estado encendido."""
    if not (ENABLE_MODIS_CRATER_SIN_DATO and geo_fuente == "mxd03"):
        return False
    return not crater_cubierto(lat, lon, vent_lat, vent_lon)
```

  y en `calculate_vrp`, después de `posicion_de_calculo`:

```python
    _ancla = (vent_lat, vent_lon) if vent_lat is not None else (volcano_lat, volcano_lon)
    if sin_dato_de_geolocalizacion(lat, lon, _ancla[0], _ancla[1], geo_fuente):
        print(f"  MODIS {hdf_path.name}: crater sin posicion en el granulo (sin dato, no se escribe record)")
        return None
```

  POR QUÉ `None` y no un record marcado: es lo que el pipeline ya hace cuando el volcán no está en el gránulo
  (`:584-585`); un record nuevo con estado obligaría a cambiar las tres vistas y el etiquetador. Si después se quiere
  ver «pasó el satélite y no miró el cráter», va como campo en un PR propio.
- [ ] **Paso 4:** pasan. **Paso 5:** suite completa. **Paso 6:** commit.

## Tarea 4: equivalencia con el brazo X de MOD-B, record por record

**Files:** Create `.github/workflows/probe-mxd03-equivalencia.yml` y
`experiments/_s16x_mxd03_flag/equivalencia.py`.

- [ ] **Paso 1:** `equivalencia.py` corre `calculate_vrp` + `store.append_record` con
  `ENABLE_MODIS_GEO_MXD03 = True` (y los otros dos apagados) sobre los 5 gránulos del humo de MOD-B
  (`MYD021KM.A2026073.0705`, `MYD021KM.A2026086.0710`, `MYD021KM.A2026283.0740`, `MOD021KM.A2026284.0140` y uno con
  relleno, `MOD021KM.A2026113.0150`) y compara cada record con el del brazo X de los artefactos de MOD-B (runs
  40112510038, 40122029477, 40126381034): misma publicación con el predicado del tablero y `pc.vrp_mw` a 0,001 MW, en
  el 100 % (sin tolerancia: es la misma función con el mismo insumo). Control negativo: con el flag apagado tiene que
  reproducir el brazo K, y no el X, en los gránulos donde K y X difieren.
- [ ] **Paso 2:** el workflow (`"on":` entre comillas, `EARTHDATA_TOKEN` que falla vacío, `ubuntu-24.04`, pyhdf, sólo
  lectura). Lo despacha la coordinadora.
- [ ] **Paso 3:** con la Tarea 3 encendida, el mismo script cuenta cuántos records pasan a «sin dato» en esos 5
  gránulos: el de relleno (`MOD021KM.A2026113.0150`, Lastarria) tiene que dar «sin dato»; los otros cuatro, record.

## Tarea 5: distancia de la etiqueta desde el cráter

**Files:** Modify `pipeline/process_modis.py:1143`. Test `tests/test_modis_geo_mxd03_s16x.py`.

- [ ] **Paso 1 (sin red, antes de tocar nada):** sobre los records MODIS de `data/mirova_equivalent/` desde la marca
  del régimen K (2026-09-18), recalcular la distancia del `final_hotspot` desde `get_detection_anchor(volcan)` y
  contar cuántas etiquetas cambian de `far` a `summit` y al revés, cuántas cambian la publicación con el predicado del
  tablero (node), y cuáles de esas son alertas de MIROVA o negativos limpios (A94: contarlo en noches). Escribirlo en
  `experiments/_s16x_mxd03_flag/medir_dist_crater.py` con su salida. Sin este número no se enciende (A116).
- [ ] **Paso 2: prueba que falla**

```python
def test_dist_km_del_pixel_anomalo_desde_el_crater_con_flag():
    dist_centro = np.array([[5.05]])
    dist_crater = np.array([[4.40]])
    with patch.object(pm, "ENABLE_MODIS_DIST_DESDE_CRATER", True):
        assert pm.dist_de_etiqueta(dist_centro, dist_crater)[0, 0] == pytest.approx(4.40)
    assert pm.dist_de_etiqueta(dist_centro, dist_crater)[0, 0] == pytest.approx(5.05)
```

- [ ] **Paso 3:**

```python
def dist_de_etiqueta(dist, vent_dist_per_pixel):
    """POR QUE: el cumulo ya se mide desde el crater; la etiqueta, desde el centro del volcan. En Lascar los dos puntos
    estan a 0,68 km y una alerta real queda 'far' por eso (A61 H5, A46). El anillo de fondo NO cambia: sigue usando
    `dist` (geometria del ROI, D17)."""
    return vent_dist_per_pixel if ENABLE_MODIS_DIST_DESDE_CRATER else dist
```

  y en `:1143`, `"dist_km": round(float(dist_etiqueta[r, c]), 2)` con `dist_etiqueta = dist_de_etiqueta(dist,
  vent_dist_per_pixel)` calculado una vez junto a `:566`. Con eso `hotspot_dist_km` y `final_hotspot_dist_km` quedan
  desde el cráter. Revisar con `grep -n "dist\[" pipeline/process_modis.py` cada otro uso de `dist` y dejar escrito
  por qué se queda (A118: el flag tiene que llegar a todos sus consumidores o decir por qué no).
- [ ] **Paso 4:** pasan. **Paso 5:** relación con `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` (decisión S134-D3,
  abierta): con este flag la etiqueta del hotspot y la del cúmulo miden desde el mismo punto; el flip de S134 sigue
  siendo otra decisión y no se toca aquí.

## Tarea 6: guard de cableado (A118)

- [ ] `tests/test_guard_mxd03_flags_s16x.py`: con los tres flags encendidos en memoria y la escena sintética de la
  1.17 (`experiments/_s151_mxd03_etiquetas/probar_probe_mxd03.py::escena`), `calculate_vrp` con un lector parchado
  devuelve `geo_fuente == "mxd03"`, `final_hotspot_dist_km` desde el cráter, y `None` con el cráter en un bloque NaN.
  Con los tres apagados, el record es idéntico al de hoy (`registros_iguales`, salvo marcas de hora). Mutaciones con
  control de caída: cada flag sin efecto tiene que hacer fallar una aserción.

## Tarea 7: adopción (sólo con el sí)

- [ ] Encender en `mirova_equivalent.yaml` los flags que el sí de Nicolás cubra; FICHA SDA a la versión siguiente;
  marca A113 al inicio de D35; marca de régimen en las tres vistas con la fecha de los DATOS (S155).
- [ ] Texto para OVDAS, con los números verificados (no los de la A61 sin verificar): «el punto MODIS se corre al
  cráter: 1 a 3 km cerca del nadir y hasta 11,5 km en el borde del barrido; la magnitud de una alerta individual puede
  cambiar de −27 % a +48 % por el fondo, sin que cambie la alerta; las pasadas en que el cráter no tiene posición dejan
  de aparecer como noches observadas».
- [ ] Reproceso del histórico MODIS sólo con decisión aparte (A104: una serie que cruce la fecha mezcla regímenes).

## 3. Autorrevisión

- Cubre lo pedido: MxD03 (Tareas 2 y 4), estado «sin dato» (Tarea 3, con su medición previa), distancia desde el
  cráter (Tarea 5, con su medición previa), TDD en cada una, A45 en la §1.
- Riesgos declarados: la regla de «sin dato» es una hipótesis hasta el Paso 0 de la Tarea 3; el efecto de la Tarea 5
  sobre la publicación no está medido; el remuestreo UTM (D17) queda fuera.
