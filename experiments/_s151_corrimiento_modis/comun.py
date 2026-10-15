# Utilidades comunes del estudio del corrimiento MODIS (tarea 1.15). Solo lectura: no toca pipeline/.
#
# POR QUE este modulo: el corrimiento del pixel MODIS del crater puede salir de tres lugares distintos
# (la interpolacion 5 km -> 1 km de `_interp_geo`, el paralaje de la cumbre, o una convencion mal
# aplicada). Cada uno predice una FORMA distinta del corrimiento en funcion del angulo de vision, del
# lado del barrido y de la altura del volcan. Aca viven los modelos de esas formas, para que todos los
# scripts usen la misma geometria.
import math
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]
SALIDAS = Path(__file__).resolve().parent / "salidas"

TIER_A = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
          "Copahue", "Llaima", "Villarrica", "PuyehueCordonCaulle", "Chaiten"]

R_TIERRA_KM = 6371.0
H_MODIS_KM = 705.0          # Terra y Aqua, orbita nominal
H_VIIRS_KM = 829.0          # Suomi NPP y NOAA-20/21, orbita nominal
N_FRAMES = 1354             # MOD021KM: Max_EV_frames (Data Dictionary C7, p. 66)
N_GEO = 271                 # 1KM_geo_dim = Max_EV_frames/5 + 1 (idem)
GEO_OFFSET = 2              # DimensionMap: offset 2, increment 5 (idem, figura 2.1.1)
GEO_INC = 5
# Paso angular de un frame de 1 km: IFOV de 1 km a 705 km. 1354 frames x 0,0813 deg = 110 deg (+-55 deg).
DELTA_FRAME_RAD = 1.0 / H_MODIS_KM


def vents():
    """vent_lat/vent_lon de volcanoes.yaml para los 11 Tier A."""
    d = yaml.safe_load(open(RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]
    if isinstance(d, list):
        d = {x["name"]: x for x in d}
    out = {}
    for k in TIER_A:
        x = d[k]
        out[k] = (float(x.get("vent_lat", x["lat"])), float(x.get("vent_lon", x["lon"])))
    return out


def cargar_records(vol, brazo=None, cache=None):
    """Records de un volcan. Sin `brazo`: produccion (data/mirova_equivalent). Con `brazo`: el brazo de un
    A/B bajado de GitHub Actions a `cache/<run_id>/<brazo>/<vol>.json`, sin duplicar pasadas entre runs.

    POR QUE los brazos sin Test 1: en produccion el Test 1 integrado marca pixeles dentro de un circulo
    alrededor del crater calculado con la geolocalizacion MODIS; ese patron viaja CON el error de
    geolocalizacion y esconde el corrimiento. Sin Test 1 los pixeles los marcan los tests contextuales."""
    import glob
    import json as _json
    if brazo is None:
        return _json.load(open(RAIZ / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    vistos = {}
    for f in sorted(glob.glob(str(Path(cache) / "*" / brazo / f"{vol}.json"))):
        try:
            recs = _json.load(open(f, encoding="utf-8"))["records"]
        except Exception:
            continue
        for r in recs:
            vistos.setdefault((r["sensor"], r["datetime_utc"]), r)
    return list(vistos.values())


def ne_km(lat0, lon0, lat, lon):
    """Desplazamiento (norte, este) en km de (lat, lon) respecto de (lat0, lon0). Plano local."""
    dn = (lat - lat0) * 111.32
    de = (lon - lon0) * 111.32 * math.cos(math.radians((lat + lat0) / 2))
    return dn, de


def hacia_sensor(dn, de, az_deg):
    """Componentes del desplazamiento: u hacia el sensor (az = acimut del sensor visto desde el pixel),
    v perpendicular (90 deg a la derecha de u)."""
    a = math.radians(az_deg)
    u = dn * math.cos(a) + de * math.sin(a)
    v = -dn * math.sin(a) + de * math.cos(a)
    return u, v


# ------------------------------------------------------------------ posicion del Sol (NOAA, ~0,1 deg)
def sol_az_zen(dt, lat, lon):
    """Acimut (desde el norte, horario, del punto hacia el Sol) y cenit solar, algoritmo NOAA."""
    import datetime as _dt
    jd = (dt - _dt.datetime(2000, 1, 1, 12)).total_seconds() / 86400.0 + 2451545.0
    jc = (jd - 2451545.0) / 36525.0
    l0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360
    m = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    mr = math.radians(m)
    c = (math.sin(mr) * (1.914602 - jc * (0.004817 + 0.000014 * jc)) + math.sin(2 * mr) * (0.019993 - 0.000101 * jc)
         + math.sin(3 * mr) * 0.000289)
    tl = l0 + c
    om = 125.04 - 1934.136 * jc
    lam = tl - 0.00569 - 0.00478 * math.sin(math.radians(om))
    eps0 = 23 + (26 + ((21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813)))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(math.radians(om))
    dec = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam))))
    y = math.tan(math.radians(eps / 2)) ** 2
    l0r = math.radians(l0)
    eqt = 4 * math.degrees(y * math.sin(2 * l0r) - 2 * e * math.sin(mr) + 4 * e * y * math.sin(mr) * math.cos(2 * l0r)
                           - 0.5 * y * y * math.sin(4 * l0r) - 1.25 * e * e * math.sin(2 * mr))
    minutos = dt.hour * 60 + dt.minute + dt.second / 60
    tst = (minutos + eqt + 4 * lon) % 1440
    ha = tst / 4 - 180
    la, de_, har = math.radians(lat), math.radians(dec), math.radians(ha)
    cz = math.sin(la) * math.sin(de_) + math.cos(la) * math.cos(de_) * math.cos(har)
    zen = math.degrees(math.acos(max(-1, min(1, cz))))
    az = math.degrees(math.atan2(math.sin(har), math.cos(har) * math.sin(la) - math.tan(de_) * math.cos(la))) + 180
    return az % 360, zen


# ------------------------------------------------------------------ orbita y lado del barrido
def satelite(sensor):
    s = sensor.upper()
    for k in ("TERRA", "AQUA", "SNPP", "NOAA20", "NOAA21"):
        if k in s:
            return k
    return "?"


def ascendente(sat, dt, lon):
    """Terra cruza el ecuador descendiendo a las 10:30 y ascendiendo a las 22:30 hora solar local;
    Aqua y los VIIRS ascienden a las 13:30 y descienden a la 01:30."""
    lst = (dt.hour + dt.minute / 60 + lon / 15.0) % 24
    de_dia = 6 <= lst < 18
    if sat == "TERRA":
        return not de_dia
    return de_dia


def lado(sat, dt, lon, az_sensor):
    """'der' si el volcan queda a la derecha de la traza (mirando en el sentido de vuelo), 'izq' si no.
    Rumbo de la traza: ~348 deg ascendiendo, ~192 deg descendiendo (inclinacion 98,2 deg, latitudes medias
    del sur). El volcan esta a la derecha si el acimut hacia el sensor es ~ rumbo - 90."""
    rumbo = 348.0 if ascendente(sat, dt, lon) else 192.0
    return "der" if math.cos(math.radians(az_sensor - (rumbo - 90.0))) > 0 else "izq"


# ------------------------------------------------------------------ modelo de la interpolacion
def _x_suelo(beta, h):
    """Distancia sobre el suelo (km, con signo) desde el nadir para un angulo de barrido beta (rad)."""
    s = (R_TIERRA_KM + h) / R_TIERRA_KM * math.sin(beta)
    s = max(-1.0, min(1.0, s))
    return R_TIERRA_KM * (math.asin(s) - beta)


def beta_desde_cenit(z_deg, h=H_MODIS_KM):
    return math.asin(R_TIERRA_KM / (R_TIERRA_KM + h) * math.sin(math.radians(z_deg)))


def frame_desde_cenit(z_deg, lado_frame0):
    """Frame s (0..1353) que mira con cenit z. `lado_frame0` dice de que lado queda el frame 0:
    si el volcan esta de ese lado, s < 676,5."""
    b = beta_desde_cenit(z_deg) / DELTA_FRAME_RAD
    c = (N_FRAMES - 1) / 2.0
    s = c - b if lado_frame0 else c + b
    return min(max(s, 0.0), N_FRAMES - 1.0)     # un cenit apenas mayor que el del borde no sale del barrido


def frame_asignado(s):
    """El frame cuya posicion VERDADERA recibe el frame s con `_interp_geo` (zoom de extremos
    alineados): el zoom lleva s a la columna gruesa s*(N_GEO-1)/(N_FRAMES-1), y la columna gruesa j
    corresponde al frame 2 + 5 j (DimensionMap)."""
    j = s * (N_GEO - 1) / (N_FRAMES - 1)
    return GEO_OFFSET + GEO_INC * j


def pred_interp_km(z_deg, lado_frame0):
    """Corrimiento predicho por la interpolacion, en km, positivo HACIA EL SENSOR (hacia el nadir)."""
    s = frame_desde_cenit(z_deg, lado_frame0)
    t = frame_asignado(s)
    c = (N_FRAMES - 1) / 2.0
    xs = _x_suelo((s - c) * DELTA_FRAME_RAD, H_MODIS_KM)
    xt = _x_suelo((t - c) * DELTA_FRAME_RAD, H_MODIS_KM)
    d = xt - xs                                  # a lo largo de s creciente
    hacia_nadir = 1.0 if xs < 0 else -1.0
    return d * hacia_nadir
