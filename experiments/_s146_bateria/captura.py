"""S146 - captura de TODOS los cumulos y de los pixeles alertados del procesador MODIS (patron A75).

POR QUE. La bateria del Apendice A guardaba un solo cumulo por pasada, el primario, que el pipeline
elige anclado al crater. Con eso un nulo espacial ("la misma caja en otro rumbo debe quedar vacia")
esta vacio por construccion: lo que el brazo alerto lejos de la cumbre nunca quedo escrito. Para que
el nulo tenga poder hay que guardar lo que el procesador calcula y descarta: la lista completa de
cumulos y la mascara de alerta pixel por pixel, con el camino que marco cada uno.

COMO. Solo lectura, sin editar pipeline/. Se envuelven cuatro funciones EN EL NAMESPACE de
pipeline.process_modis, que es de donde calculate_vrp las lee:
  combine_hot_paths          -> mascaras de los caminos legado (bt, nti, dnti_ctx, test1, eti)
  first_pass_tests_2_and_3   -> mascara del primer pase (Tests 2 y 3)
  second_pass_adjacent       -> mascara tras la recaptura del segundo pase
  cluster_hotspots           -> mascara FINAL, lat/lon, VRP por pixel y la lista de cumulos
Los envoltorios devuelven exactamente lo que devuelve la funcion original: no cambian el resultado.

LAS DOS PREGUNTAS DEL INSTRUMENTO
(1) Si lo que mide estuviera roto (se pierden pixeles o cumulos), fallaria? Si: `extraer` compara
    la suma de n_pixels de los cumulos contra los pixeles listados y el primario capturado contra el
    primary_cluster del record, y devuelve la lista de discrepancias; el probe termina con error si
    hay alguna. prueba_local.py lo ejercita con calculate_vrp real sobre una escena sintetica con
    dos focos a distancia conocida.
(2) Si el instrumento estuviera muerto (los envoltorios no enganchan), se veria distinto? Si:
    `instalar` levanta AttributeError si alguna de las cuatro funciones no existe con ese nombre en
    el modulo (A89: un parche que no engancha no da error, da cero), y `extraer` marca como
    discrepancia un record con pixeles anomalos y ninguna llamada capturada.

LIMITE DECLARADO. La magnitud de cada cumulo es la suma cruda de sus pixeles tal como la entrega
cluster_hotspots (`vrp_mw_crudo`). El pipeline aplica despues, SOLO al primario, el nucleo focal, el
tope de 5 MW del camino D y el modo de un pixel; por eso el primario trae ademas `vrp_mw_publicado`,
que es el del record. Para los cumulos no primarios no existe una magnitud "publicada".
"""
import math

import numpy as np

FUNCIONES = ("combine_hot_paths", "first_pass_tests_2_and_3", "second_pass_adjacent",
             "cluster_hotspots")


def hav(la1, lo1, la2, lo2):
    R = 6371.0088
    p = math.radians
    a = (math.sin(p(la2 - la1) / 2) ** 2
         + math.cos(p(la1)) * math.cos(p(la2)) * math.sin(p(lo2 - lo1) / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


class Captura:
    def __init__(self):
        self.reset()

    def reset(self):
        self.legado = None        # dict nombre -> mascara bool
        self.primer_pase = None   # mascara bool
        self.segundo_pase = []    # lista de mascaras bool (una por llamada)
        self.llamadas = []        # llamadas a cluster_hotspots


def _mascara(m):
    return None if m is None else np.array(m, dtype=bool, copy=True)


def instalar(pm):
    """Envuelve las cuatro funciones en el modulo `pm`. Devuelve la Captura compartida.

    Se llama DESPUES de los parches del brazo (por ejemplo el que quita la compuerta), para que el
    envoltorio vea la funcion que de verdad corre.
    """
    for nombre in FUNCIONES:
        if not callable(getattr(pm, nombre)):   # AttributeError si el nombre no existe (A89)
            raise AttributeError(f"{nombre} no es invocable en {pm.__name__}")
    cap = Captura()
    orig_combine = pm.combine_hot_paths
    orig_fp = pm.first_pass_tests_2_and_3
    orig_sp = pm.second_pass_adjacent
    orig_cl = pm.cluster_hotspots

    def combine(*args, **kw):
        nombres = ("bt_path_hot", "nti_path_hot", "dnti_ctx_hot", "test1_hot")
        leg = {n: _mascara(a) for n, a in zip(nombres, args)}
        for n in nombres + ("eti_path_hot", "nti_rel_hot"):
            if n in kw:
                leg[n] = _mascara(kw[n])
        cap.legado = leg
        return orig_combine(*args, **kw)

    def primer_pase(*args, **kw):
        res = orig_fp(*args, **kw)
        cap.primer_pase = _mascara(res[0])
        return res

    def segundo_pase(*args, **kw):
        res = orig_sp(*args, **kw)
        cap.segundo_pase.append(_mascara(res))
        return res

    def cumulos(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw):
        res = orig_cl(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw)
        vpp = kw.get("vrp_per_pixel")
        cap.llamadas.append({
            # La llamada del bloque del Test 1 es la unica que pasa `connectivity` explicito.
            "origen": "test1" if "connectivity" in kw else "contextual",
            "mascara": _mascara(hot_mask_2d),
            "lat": np.array(lat, dtype=np.float64, copy=True),
            "lon": np.array(lon, dtype=np.float64, copy=True),
            "vrp": None if vpp is None else np.array(vpp, dtype=np.float64, copy=True),
            "cumulos": [dict(c) for c in res],
        })
        return res

    pm.combine_hot_paths = combine
    pm.first_pass_tests_2_and_3 = primer_pase
    pm.second_pass_adjacent = segundo_pase
    pm.cluster_hotspots = cumulos
    return cap


def _caminos(cap, forma, i, j):
    """Caminos que marcaron el pixel (i, j). Los del legado se calculan siempre pero, con el primer
    pase encendido, NO forman la mascara final: se reportan porque dicen que mas vio ese pixel."""
    out = []
    if cap.primer_pase is not None and cap.primer_pase.shape == forma and cap.primer_pase[i, j]:
        out.append("primer_pase_t23")
    elif any(m is not None and m.shape == forma and m[i, j] for m in cap.segundo_pase):
        out.append("segundo_pase_recaptura")
    for n, m in (cap.legado or {}).items():
        if m is not None and m.shape == forma and m[i, j]:
            out.append("legado:" + n.replace("_path_hot", "").replace("_hot", ""))
    return out


def extraer(cap, rec, cumbre_lat, cumbre_lon):
    """Devuelve (cumulos, pixeles, llamada_publicada, discrepancias) para la pasada recien corrida.

    `llamada_publicada`: origen de la llamada cuyo primer cumulo es el primary_cluster del record
    (la del Test 1 pisa a la contextual cuando devuelve algo; ver process_modis.py, bloque S31+).
    """
    cumulos, pixeles, discrepancias = [], [], []
    publicada = None
    for ll in cap.llamadas:
        if ll["cumulos"] and (ll["origen"] == "test1" or publicada is None):
            publicada = ll["origen"]
    pc = (rec or {}).get("primary_cluster") or {}
    for ll in cap.llamadas:
        forma = ll["mascara"].shape
        n_listados = 0
        for orden, c in enumerate(ll["cumulos"]):
            es_primario = (orden == 0 and ll["origen"] == publicada)
            crudo = c.get("vrp_mw")
            cumulos.append({
                "origen": ll["origen"], "orden": orden, "es_primario_publicado": es_primario,
                "n_pixels": int(c["n_pixels"]),
                "lat": round(float(c["centroid_lat"]), 5), "lon": round(float(c["centroid_lon"]), 5),
                "dist_cumbre_km": round(hav(c["centroid_lat"], c["centroid_lon"],
                                            cumbre_lat, cumbre_lon), 3),
                "vrp_mw_crudo": None if crudo is None else round(float(crudo), 4),
                "vrp_mw_publicado": pc.get("vrp_mw") if es_primario else None,
            })
            if es_primario and pc:
                if (abs(round(float(c["centroid_lat"]), 5) - pc.get("centroid_lat", 1e9)) > 1e-4
                        or abs(round(float(c["centroid_lon"]), 5) - pc.get("centroid_lon", 1e9)) > 1e-4):
                    discrepancias.append(
                        f"primario capturado ({c['centroid_lat']:.5f},{c['centroid_lon']:.5f}) != "
                        f"primary_cluster del record ({pc.get('centroid_lat')},{pc.get('centroid_lon')})")
            for (i, j) in c["pixel_indices"]:
                n_listados += 1
                la, lo = float(ll["lat"][i, j]), float(ll["lon"][i, j])
                v = None if ll["vrp"] is None else float(ll["vrp"][i, j])
                pixeles.append({
                    "origen": ll["origen"], "cumulo_orden": orden, "fila": int(i), "col": int(j),
                    "lat": round(la, 5), "lon": round(lo, 5),
                    "dist_cumbre_km": round(hav(la, lo, cumbre_lat, cumbre_lon), 3),
                    "vrp_mw": None if v is None else round(v, 4),
                    "caminos": (["test1_integrado"] if ll["origen"] == "test1" else [])
                               + _caminos(cap, forma, int(i), int(j)),
                })
        n_mascara = int(ll["mascara"].sum())
        if n_listados != n_mascara:
            discrepancias.append(f"llamada {ll['origen']}: {n_listados} pixeles en cumulos != "
                                 f"{n_mascara} en la mascara")
    if pc and publicada is None:
        discrepancias.append("el record trae primary_cluster y no se capturo ninguna llamada a "
                             "cluster_hotspots con cumulos: los envoltorios no engancharon")
    if (rec or {}).get("n_anomalous_pixels") and not cap.llamadas:
        discrepancias.append("n_anomalous_pixels > 0 y ninguna llamada capturada")
    return cumulos, pixeles, publicada, discrepancias
