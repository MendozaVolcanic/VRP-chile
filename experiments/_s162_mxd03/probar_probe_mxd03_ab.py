# -*- coding: utf-8 -*-
"""Prueba sintetica del arnes del A/B de MxD03 sobre K (A116: el instrumento tiene que poder dar cada resultado).
Sin red ni HDF: escenas MODIS de 81 x 81 pixeles de la 1.17 (foco de 335 K a 6 km al norte del crater, inner 5 km) que
pasan por el pipeline REAL de este checkout (calculate_vrp + store.append_record + predicado del tablero con node).

Casos (cada uno con lo que el arnes TIENE que dar; si no, sale 1):
  PRESENTE  `_interp_geo` corrida 2 km al sur de MxD03 (la verdad). K publica (foco a 4 km, cumbre) y X no (6 km).
            K2 identico a K; hashes de grilla K != X; los 20 nulos con modulo aplicado de 2 km (+-10 m, control 2),
            rumbos cada 18 grados, y el nulo cambia la publicacion en los dos sentidos (al menos uno publica y uno no);
            como K y X difieren, corre la atribucion: XF_id == K y XD_id == X exactos, un solo reemplazo de la distancia
            al centro en cada brazo cruzado, y X_fondo cambia el fondo respecto de K (t_bg o n del anillo distintos:
            el cruce esta vivo).
  AUSENTE   las dos geolocalizaciones iguales: corrimiento 0, K = K2 = X, todos los nulos iguales a K en
            publicacion, sin atribucion.
  SIN_R     PRESENTE con cenit sobre 35 grados en la poblacion: no corre nulos.
  PURAS     `difiere_de_guardado` (publicacion distinta, magnitud a mas de 0,001 MW, None contra numero) y `decide`.
Ademas, MUTACIONES del arnes (cada una tiene que hacer fallar al menos una asercion; se cuentan solo si la falla es una
asercion de este archivo, no una excepcion, S156):
  M1  FondoCruzado no reemplaza nada            (la atribucion queda muerta)
  M2  los nulos usan la sal de la 1.23            (rumbos de otro pre-registro)
  M3  los nulos trasladan la mitad del modulo     (R no imita el tamano de X)
  M4  K2 se corre con la grilla de X              (el control de identidad no seria tal)
Uso: python probar_probe_mxd03_ab.py   (sale 1 si algo falla; necesita node)
"""
import hashlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for p in (RAIZ, RAIZ / "experiments/_s151_mxd03_etiquetas", AQUI):     # AQUI queda primero (VMX-06)
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import probe_mxd03_ab as A  # noqa: E402
import probar_probe_mxd03 as T  # noqa: E402  (escena de la 1.17)

CLAVE = "MYD021KM.A2026073.0705"


def fila_pob(z=20.0, lab="protegida", pub=1, vrp=1.234, expuesta=False):
    return {"vol": T.VOLCAN["name"], "dt": "2026-03-14 07:05", "sensor": "MODIS_AQUA", "z": z,
            "tramo": "<=25", "lado": "f0", "lab": lab, "pub_guardada": pub, "pc_vrp_guardada": vrp,
            "expuesta": expuesta, "r_nulos": z <= A.CENIT_R}


def caso(dn_km, z=20.0):
    verdad = T.escena()
    interp = dict(verdad)
    interp["lat"] = (verdad["lat"].astype(np.float64) + dn_km / 111.32).astype(np.float32)
    lat_m, lon_m = verdad["lat"].copy(), verdad["lon"].copy()
    f = fila_pob(z=z)
    return A.medir_record(T.L1B, Path("geo.hdf"), T.VOLCAN, None, interp, (lat_m, lon_m), f, CLAVE)


def aserciones(r_pres, r_aus, r_sinr):
    f = []

    def exige(cond, msg):
        if not cond:
            f.append(msg)

    p = r_pres
    exige(abs(p["desplazamiento"]["km"] - 2.0) < 0.05, "PRESENTE: corrimiento medido %s" % p["desplazamiento"]["km"])
    exige(p["pub"]["K"] == 1 and p["pub"]["X"] == 0, "PRESENTE: K/X publican %s/%s, esperado 1/0" %
          (p["pub"]["K"], p["pub"]["X"]))
    exige(p["k2_igual"] is True, "PRESENTE: K2 distinto de K")
    exige(p["hash_grilla"]["K"] != p["hash_grilla"]["X"], "PRESENTE: hash de X igual al de K (parche muerto)")
    exige(len(p["nulos"]) == 20, "PRESENTE: %d nulos" % len(p["nulos"]))
    exige(all(abs(n["km_aplicado"] - n["km_pedido"]) <= 0.010 for n in p["nulos"]),
          "PRESENTE: modulo aplicado distinto del pedido en algun nulo")
    exige(all(abs(n["km_pedido"] - 2.0) < 0.05 for n in p["nulos"]), "PRESENTE: modulo pedido no es el de X")
    ang = sorted(n["angulo_grados"] for n in p["nulos"])
    sep = [round((b - a) % 360, 4) for a, b in zip(ang, ang[1:] + ang[:1])]
    exige(all(abs(s - 18.0) < 1e-3 for s in sep), "PRESENTE: rumbos no equiespaciados cada 18 grados")
    # referencia independiente del arnes: la sal escrita en el §3 del pre-registro, calculada aqui
    u = int(hashlib.sha1(("s159-mxd03-r" + CLAVE).encode()).hexdigest()[:12], 16) / float(16 ** 12)
    esperado = sorted(round(360.0 * ((u + n / 20) % 1.0), 6) for n in range(20))
    exige(ang == esperado, "PRESENTE: rumbos no son los de la sal del pre-registro (s159-mxd03-r)")
    pubs_r = [p["pub"][b] for b in A.NULOS]
    exige(0 < sum(pubs_r) < 20, "PRESENTE: el nulo no cambia la publicacion en los dos sentidos (%d de 20)" % sum(pubs_r))
    exige(len(set(p["hash_grilla"][b] for b in A.NULOS)) == 20, "PRESENTE: hay nulos con la misma grilla")
    at = p.get("atribucion")
    exige(at is not None, "PRESENTE: K y X difieren y no corrio la atribucion")
    if at:
        exige(at["XF_id_igual_K"] is True, "PRESENTE: XF_id (fondo cruzado con la grilla de K) no reproduce K")
        exige(at["XD_id_igual_X"] is True, "PRESENTE: XD_id (fondo cruzado con la grilla de X) no reproduce X")
        exige(all(at[b]["reemplazos_fondo"] == 1 for b in ("X_fondo", "X_det", "XF_id", "XD_id")),
              "PRESENTE: reemplazos de la distancia al centro %s" %
              {b: at[b]["reemplazos_fondo"] for b in ("X_fondo", "X_det", "XF_id", "XD_id")})
        kf, xf = p["brazos"]["K"], at["X_fondo"]["rec"]
        exige(xf is not None and (xf["t_bg_k"] != kf["t_bg_k"] or xf["diag_n_bg_anillo"] != kf["diag_n_bg_anillo"]),
              "PRESENTE: X_fondo no cambio el fondo de K (cruce muerto)")
        kd, xd = p["brazos"]["X"], at["X_det"]["rec"]
        exige(xd is not None and (xd["t_bg_k"] != kd["t_bg_k"] or xd["diag_n_bg_anillo"] != kd["diag_n_bg_anillo"]),
              "PRESENTE: X_det no cambio el fondo de X (cruce muerto)")
    exige(p["pico"] is not None, "PRESENTE: sin pixel por indice para la vara")

    a = r_aus
    exige(a["desplazamiento"]["km"] < 1e-6, "AUSENTE: corrimiento %s" % a["desplazamiento"]["km"])
    exige(a["pub"]["K"] == a["pub"]["X"] == a["pub"]["K2"], "AUSENTE: K, K2 y X no publican igual")
    exige(a["brazos"]["K"] == a["brazos"]["X"], "AUSENTE: K y X distintos con la misma grilla")
    exige(all(a["pub"][b] == a["pub"]["K"] for b in A.NULOS), "AUSENTE: un nulo de 0 km cambio la publicacion")
    exige("atribucion" not in a, "AUSENTE: corrio la atribucion sin cambio")

    exige(r_sinr["nulos"] == [] and not any(b in r_sinr["pub"] for b in A.NULOS), "SIN_R: corrio nulos sobre 35 grados")

    base = fila_pob()
    exige(A.difiere_de_guardado(base, {"pc_vrp": 1.234}, 1) is False, "PURAS: igual marcado como distinto")
    exige(A.difiere_de_guardado(base, {"pc_vrp": 1.2345}, 1) is False, "PURAS: 0,0005 MW marcado como distinto")
    exige(A.difiere_de_guardado(base, {"pc_vrp": 1.236}, 1) is True, "PURAS: 0,002 MW no marcado")
    exige(A.difiere_de_guardado(base, {"pc_vrp": 1.234}, 0) is True, "PURAS: publicacion distinta no marcada")
    exige(A.difiere_de_guardado(base, None, 1) is True, "PURAS: record None contra numero no marcado")
    exige(A.decide(fila_pob(lab="bajo1")) and A.decide(fila_pob(lab="neg_limpio", pub=1)), "PURAS: decide falla en alerta/neg publicado")
    exige(not A.decide(fila_pob(lab="neg_limpio", pub=0)) and A.decide(fila_pob(lab="sin_info", expuesta=True)),
          "PURAS: decide falla en negativo no publicado o expuesta")
    return f


def correr():
    return caso(-2.0), caso(0.0), caso(-2.0, z=40.0)


def main():
    fallas = aserciones(*correr())
    print("caso base:", "OK" if not fallas else "FALLAS: " + " | ".join(fallas))
    if fallas:
        sys.exit(1)

    # mutaciones: cada una tiene que hacer fallar una asercion (no una excepcion)
    real_fc_call = A.FondoCruzado.__call__
    real_rumbos = A.rumbos
    real_vec = A.S.vector_nulo

    def m1(self, lat1, lon1, lat2, lon2):
        self.llamadas += 1
        return self.real(lat1, lon1, lat2, lon2)

    def m2(clave, k=A.K_NULOS):
        return A.S.rumbos(clave, k)

    def m3(km, ang):
        return real_vec(km / 2, ang)

    mutaciones = (("M1 FondoCruzado no reemplaza", patch.object(A.FondoCruzado, "__call__", m1)),
                  ("M2 sal de la 1.23", patch.object(A, "rumbos", m2)),
                  ("M3 mitad del modulo", patch.object(A.S, "vector_nulo", m3)),
                  ("M4 K2 con otra grilla", patch.object(A, "BRAZOS_BASE", (("K", "interp"), ("K2", "mxd03"),
                                                                             ("X", "mxd03")))))
    atrapadas = 0
    for nombre, parche in mutaciones:
        try:
            with parche:
                fm = aserciones(*correr())
            res = "ATRAPADA (%s)" % fm[0] if fm else "NO ATRAPADA"
            atrapadas += bool(fm)
        except Exception as e:  # noqa: BLE001  una excepcion no cuenta como atrapada (S156)
            res = "CAYO con %s: %s (no cuenta)" % (type(e).__name__, e)
        print(nombre + ":", res)
    assert real_fc_call is A.FondoCruzado.__call__ and real_rumbos is A.rumbos
    print("mutaciones atrapadas por asercion: %d de %d" % (atrapadas, len(mutaciones)))
    sys.exit(0 if atrapadas == len(mutaciones) else 1)


if __name__ == "__main__":
    main()
