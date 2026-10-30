# -*- coding: utf-8 -*-
"""S168, P2-01: prueba sin red de la descarga del arnés de MOD-D fase 4 (probe_f4.bajar_por_nombre y
probe_f4.recorrer_granulos) contra el circuit-breaker REAL de pipeline/fetch.py.

POR QUÉ. El breaker de descarga de fetch.py guarda los hosts caídos en el proceso, y en el arnés el proceso es la parte
entera. La auditoría S169 (experiments/_s169/audit_patrones/f2/INFORME.md P2-01) y su verificador (m01b_simular_breaker.py)
midieron que un solo ConnectTimeout, con el host ya recuperado, hacía perder 6 de 6 gránulos con 400 s de espera cada
uno. El arreglo resetea el breaker antes de cada intento de descarga y corta la parte tras TOPE_CAIDAS gránulos
seguidos sin bajar por caída de host. Lo único falso aquí es earthaccess (search y download), el probe TCP del host
(siempre False: el host «no responde» al probe, el peor caso de fetch.py) y time.sleep (se suma, no se duerme).
download_granules, reset_transient_breakers y _DOWN_DOWNLOAD_HOSTS son los de pipeline/fetch.py sin tocar.

ESCENARIOS
  M01B      el caso del verificador: 6 gránulos (L1B + MxD03), ConnectTimeout sólo en la primera descarga; tienen que
            bajar todos menos, a lo sumo, el gránulo de la caída; sin tope.
  M01B_CTRL control de que el instrumento puede fallar: el mismo caso SIN reset (reset que no hace nada) pierde los
            gránulos siguientes, como el arnés viejo. Si este control bajara todo, la prueba de arriba no probaría nada.
  TOPE      host caído de verdad: 6 gránulos de 2 pasadas; tras 3 gránulos seguidos sin bajar la parte se corta, las 12
            pasadas tienen fila no_bajado escrita con flush (se leen del disco antes de cerrar el archivo), las 6 de los
            gránulos no intentados con falta no_intentado, no se intenta ninguna descarga después del tope, el código
            de salida es SALIDA_TOPE, y evaluar_f4 las cuenta como falla del arnés en cobertura (no como faltantes).
  CADENA    una falla que no es caída de host (CMR no sirve el gránulo) corta la racha: caída, ausente, caída, caída no
            llega al tope.
  BREAKER   un RuntimeError del propio breaker no duerme y cuenta como caída de host; un ReadTimeout duerme y no cuenta.
Los cinco escenarios corren también dentro de la batería del arnés (probar_probe_f4.py, t_descarga_*), donde las
mutaciones MA17 a MA20 los ejercitan sobre copias del arnés; cada función recibe el módulo del arnés como A.
Uso: python probar_descarga_f4.py   (sale 1 si algo falla; sin red, unos segundos)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import traceback
import types
from pathlib import Path
from unittest.mock import patch

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (RAIZ, RAIZ / "scripts", AQUI):
    sys.path.insert(0, str(_p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import requests  # noqa: E402

import evaluar_f4 as E  # noqa: E402
import probe_f4 as A  # noqa: E402
from pipeline import fetch as F  # noqa: E402


class G(dict):
    def __init__(self, n):
        super().__init__(umm={"GranuleUR": n})
        self.n = n

    def data_links(self):
        return [f"https://ladsweb.modaps.eosdis.nasa.gov/x/{self.n}"]


class Red:
    """earthaccess falso. fallar(n) decide si la descarga número n (desde 1) lanza ConnectTimeout."""

    def __init__(self, fallar, ausentes=()):
        self.fallar, self.ausentes, self.n, self.pedidos = fallar, set(ausentes), 0, []

    def search_data(self, short_name, version, granule_name):
        if granule_name.endswith("*") or granule_name in self.ausentes:
            return []
        return [G(granule_name)]

    def download(self, gs, local_path):
        self.n += 1
        self.pedidos.append(gs[0].n)
        if self.fallar(self.n):
            raise requests.exceptions.ConnectTimeout("simulado")
        p = Path(local_path) / gs[0].n
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
        return [str(p)]


def grupos_de(n_gran, n_pas=1):
    g = {}
    for i in range(n_gran):
        clave = f"MOD021KM.A2026100.{1000 + i}"
        g[clave] = [{"vol": "Lascar", "dt": f"2026-04-10 {i:02d}:{j:02d}", "l1b": f"MOD021KM.A2026100.{1000 + i}.061.x.hdf",
                     "geo": f"MOD03.A2026100.{1000 + i}.061.x.hdf"} for j in range(n_pas)]
    return g


def correr_parte(A, red, grupos, reset=None):
    """Corre recorrer_granulos con la red falsa; devuelve (filas leídas del disco ANTES de cerrar, errores, terminada,
    segundos dormidos, medidos)."""
    dormido, medidos = [], []

    def medir(clave, ps, l1b, geo, otro, escribir):
        for p in ps:
            medidos.append(clave)
            escribir({"tipo": "record", "vol": p["vol"], "dt": p["dt"], "clave": clave, "estado": "ok"})
        return 0

    F.reset_transient_breakers()
    with tempfile.TemporaryDirectory() as d, \
            patch.object(F, "earthaccess", types.SimpleNamespace(download=red.download)), \
            patch.object(F, "_probe_download_host", lambda h, timeout=5.0: False), \
            patch.object(F, "_diag", lambda *a, **k: None), \
            patch.object(F, "_escribir_resumen", lambda *a, **k: None), \
            patch("time.sleep", lambda s: dormido.append(s)):
        ruta = Path(d) / "f4_parte00.jsonl"
        salida = open(ruta, "w", encoding="utf-8")
        try:
            bajar = (lambda n, info: A.bajar_por_nombre(n, Path(d) / "hdf", red.search_data, F.download_granules,
                                                        reset=reset, info=info))
            errores, terminada = A.recorrer_granulos(grupos, salida, bajar, medir)
            with open(ruta, encoding="utf-8") as lect:          # lo que ya llegó al disco (flush), sin cerrar
                filas = [json.loads(x) for x in lect if x.strip()]
        finally:
            salida.close()
    F.reset_transient_breakers()
    return filas, errores, terminada, sum(dormido), medidos


def t_m01b(A=A):
    red = Red(lambda n: n == 1)
    filas, errores, terminada, dormido, medidos = correr_parte(A, red, grupos_de(6))
    ok = sorted({f["clave"] for f in filas if f["estado"] == "ok"})
    assert len(ok) >= 5, f"con el host recuperado bajaron sólo {len(ok)} de 6 gránulos: {ok}"
    assert terminada is None and len(filas) == 6, (terminada, len(filas))
    perdidos = [f["clave"] for f in filas if f["estado"] != "ok"]
    assert not perdidos or perdidos == ["MOD021KM.A2026100.1000"], perdidos
    return f"bajaron {len(ok)} de 6 gránulos, {dormido:.0f} s de espera, perdidos {perdidos or 'ninguno'}"


def t_m01b_control(A=A):
    red = Red(lambda n: n == 1)
    filas, errores, terminada, dormido, medidos = correr_parte(A, red, grupos_de(6), reset=lambda: None)
    ok = {f["clave"] for f in filas if f["estado"] == "ok"}
    assert len(ok) <= 1, f"sin reset tenían que perderse los gránulos tras la caída y bajaron {len(ok)}"
    return f"sin reset bajaron {len(ok)} de 6 (el instrumento ve la falla del arnés viejo); terminada {terminada}"


def t_tope(A=A):
    red = Red(lambda n: True)
    grupos = grupos_de(6, n_pas=2)
    filas, errores, terminada, dormido, medidos = correr_parte(A, red, grupos)
    esperadas = [(p["vol"], p["dt"]) for ps in grupos.values() for p in ps]
    assert terminada == "tope_caidas_host" and A.codigo_salida(errores, terminada) == A.SALIDA_TOPE != 0, terminada
    assert sorted((f["vol"], f["dt"]) for f in filas) == sorted(esperadas), "faltan filas o hay repetidas"
    assert all(f["estado"] == "no_bajado" for f in filas) and errores == 12 and not medidos
    no_int = [f for f in filas if f.get("falta") == "no_intentado"]
    assert len(no_int) == 6 and all(f["motivo_arnes"] == "tope_caidas_host" for f in no_int)
    assert {f["clave"] for f in no_int} == set(list(grupos)[3:]), "los no intentados no son los 3 últimos gránulos"
    assert all(f["falta"] == "L1B" for f in filas if f not in no_int)
    pedidos = set(red.pedidos)
    assert all(n.startswith("MOD021KM") for n in pedidos) and len(pedidos) == 3, \
        f"después del tope se pidieron descargas o se pidió el MxD03 sin L1B: {sorted(pedidos)}"
    assert red.n == 3 * 4, red.n                           # 4 intentos por L1B, un ConnectTimeout cada uno
    for f in filas:              # evaluar_f4.main mezcla los campos de la población (lab) en cada fila antes de evaluar
        f.update({"lab": "neg_limpio", "_evaluable": E.evaluable(f)[0], "_motivo": E.evaluable(f)[1]})
    cob = E.control_cobertura(filas, esperadas, [], predicado=lambda casos: [(0, 0.0)] * len(casos))
    assert cob["estado"] == "INDECIDIBLE" and cob["n_faltan"] == 0 and cob["n_fallas"] == 12, \
        (cob["estado"], cob["n_faltan"], cob["n_fallas"])
    assert all(x["motivo"] == "falla_arnes_no_bajado" for x in cob["fallas"])
    return f"cortó tras 3 gránulos, 12 filas no_bajado (6 no_intentado), código {A.codigo_salida(errores, terminada)}, " \
           f"cobertura INDECIDIBLE con 12 fallas y 0 faltantes, {dormido:.0f} s de espera"


def t_cadena(A=A):
    g = grupos_de(4)
    l1bs = [ps[0]["l1b"] for ps in g.values()]
    red = Red(lambda n: True, ausentes={l1bs[1]})
    filas, errores, terminada, dormido, medidos = correr_parte(A, red, g)
    assert terminada is None and len(filas) == 4 and all(f["estado"] == "no_bajado" for f in filas), terminada
    return "caída, ausente, caída, caída: sin tope"


def t_breaker(A=A):
    dormido = []
    info = {}

    def desc_breaker(res, dest):
        raise RuntimeError(f"{A.MENSAJE_BREAKER}: ['ladsweb.modaps.eosdis.nasa.gov']")
    with patch("time.sleep", lambda s: dormido.append(s)):
        r = A.bajar_por_nombre("MOD021KM.A2026100.1000.061.x.hdf", Path(tempfile.gettempdir()),
                               lambda **k: [G(k["granule_name"])], desc_breaker, reset=lambda: None, info=info)
    assert r == (None, None) and sum(dormido) == 0 and info["caida_host"] is True, (r, dormido, info)
    dormido.clear()

    def desc_read(res, dest):
        raise requests.exceptions.ReadTimeout("lento")
    with patch("time.sleep", lambda s: dormido.append(s)):
        r = A.bajar_por_nombre("MOD021KM.A2026100.1000.061.x.hdf", Path(tempfile.gettempdir()),
                               lambda **k: [G(k["granule_name"])], desc_read, reset=lambda: None, info=info)
    assert r == (None, None) and sum(dormido) == 20 + 40 + 60 + 80 and info["caida_host"] is False, (dormido, info)
    return "breaker: 0 s y caída; ReadTimeout: 200 s y no caída"


ESCENARIOS = [t_m01b, t_m01b_control, t_tope, t_cadena, t_breaker]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("prueba de la descarga del arnés (probe_f4.py sha256 LF %s, pipeline/fetch.py sha256 LF %s)"
          % (A.sha256_lf(AQUI / "probe_f4.py"), A.sha256_lf(RAIZ / "pipeline/fetch.py")))
    res = {}
    for t in ESCENARIOS:
        try:
            res[t.__name__] = ("OK", t())
        except AssertionError as e:
            res[t.__name__] = ("FALLA", str(e)[:300])
        except Exception as e:  # noqa: BLE001
            res[t.__name__] = ("CAE", f"{type(e).__name__}: {e} | {traceback.format_exc()[-400:]}")
        print(f"  {res[t.__name__][0]:5s} {t.__name__:16s} {res[t.__name__][1]}", flush=True)
    n_ok = sum(v[0] == "OK" for v in res.values())
    print(f"RESUMEN: {n_ok} de {len(res)} OK")
    sys.exit(0 if n_ok == len(res) else 1)


if __name__ == "__main__":
    main()
