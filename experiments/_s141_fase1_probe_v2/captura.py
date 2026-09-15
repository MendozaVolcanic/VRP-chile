# -*- coding: utf-8 -*-
"""S141, Fase 1 (v2): envoltorios que registran las llamadas por etapa del ensamblado VIIRS 375 m.

POR QUÉ. El v1 infería qué etapa había corrido a partir de un None y ponía en fila dos rutas que en
el pipeline corren en paralelo (VERIFICADOR.md V2, V9). Aquí cada llamada queda como un evento con
número de orden, y la ruta del cúmulo se lee de cómo la llama el código (A89): la llamada del Test 1
pasa `connectivity=8` (process_viirs.py:1910-1914) y la contextual no (:1467-1472). El segundo pase
de la ruta contextual es la única llamada con `active_mask=` por nombre (:1287).

Rediseño por H3 (VERIFICADOR_V2_PRE_CORRIDA.md): los eventos de los tests de detección guardan los
argumentos con que se llamaron (referencias, sin copiar los arreglos grandes) para que
`margenes.py` recalcule el margen de cada vecino a cada test contra la firma real de la función.

Funciones puras sobre el callable real: no importan el pipeline y se prueban sin red.
"""
import numpy as np


def _bool(x):
    return None if x is None else np.array(x, dtype=bool)


class Captura:
    def __init__(self):
        self.reset()

    def reset(self):
        self.eventos = []
        self.record = None
        self._seq = 0

    def _add(self, ev):
        self._seq += 1
        ev["seq"] = self._seq
        self.eventos.append(ev)
        return ev

    def de_tipo(self, tipo):
        return [e for e in self.eventos if e["tipo"] == tipo]

    def ultimo(self, tipo, cond=None):
        for e in reversed(self.de_tipo(tipo)):
            if cond is None or cond(e):
                return e
        return None

    def corrio(self):
        """Booleano por etapa: True si la función fue llamada (aunque devolviera vacío)."""
        cl = self.de_tipo("cluster")
        return {
            "first_pass": bool(self.de_tipo("first_pass")),
            "second_pass_por_nombre": any(e["via_kw"] for e in self.de_tipo("second_pass")),
            "dnti_ctx": bool(self.de_tipo("dnti_ctx")),
            "test1": bool(self.de_tipo("test1")),
            "test1_disparo": any(e["triggered"] for e in self.de_tipo("test1")),
            "filtro_contextual": bool(self.de_tipo("ctx_filter")),
            "cumulo_contextual": any(e["ruta"] == "contextual" for e in cl),
            "cumulo_test1": any(e["ruta"] == "test1" for e in cl),
        }

    def test1_gana(self):
        """Último valor de resolve_test1_source_priority; None si no se llamó (process_viirs.py:1712
        no la llama cuando test1_centroid_lat es None). Evidencia parcial de la fuente interna."""
        ev = self.ultimo("prioridad")
        return None if ev is None else ev["valor"]

    def lbg_test1(self):
        ev = self.ultimo("lbg_test1")
        return None if ev is None else ev["valor"]

    # -------------------------------------------------------------- envoltorios

    def envolver_calcular(self, real):
        def calculate_vrp(*a, **kw):
            self.reset()
            rec = real(*a, **kw)
            self.record = rec
            return rec
        return calculate_vrp

    def envolver_cluster(self, real):
        def cluster_hotspots(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw):
            cl = real(hot_mask_2d, lat, lon, vent_lat, vent_lon, **kw)
            vpp = kw.get("vrp_per_pixel")
            self._add({
                "tipo": "cluster", "ruta": "test1" if "connectivity" in kw else "contextual",
                "entrada": _bool(hot_mask_2d), "lat": lat, "lon": lon,
                "vrp_per_pixel": None if vpp is None else np.array(vpp, dtype=float),
                "clusters": [{"n_pixels": c.get("n_pixels"), "centroid_lat": c.get("centroid_lat"),
                              "centroid_lon": c.get("centroid_lon"), "vrp_mw": c.get("vrp_mw"),
                              "pixel_indices": [tuple(int(t) for t in ij) for ij in (c.get("pixel_indices") or [])]}
                             for c in (cl or [])],
            })
            return cl
        return cluster_hotspots

    def envolver_first_pass(self, real):
        def first_pass_tests_2_and_3(*a, **kw):
            hot, diag = real(*a, **kw)
            d = diag or {}
            self._add({"tipo": "first_pass", "hot": _bool(hot), "bt": kw.get("bt"), "a": a, "kw": kw,
                       "diag": {k: d.get(k) for k in ("mu_dnti", "sd_dnti", "mu_deti", "sd_deti", "n_bg_used", "eti")}})
            return hot, diag
        return first_pass_tests_2_and_3

    def envolver_second_pass(self, real):
        def second_pass_adjacent(*a, **kw):
            out = real(*a, **kw)
            entrada = kw.get("active_mask", a[2] if len(a) > 2 else None)
            self._add({"tipo": "second_pass", "via_kw": "active_mask" in kw, "entrada": _bool(entrada),
                       "salida": _bool(out), "a": a, "kw": kw})
            return out
        return second_pass_adjacent

    def envolver_dnti_ctx(self, real):
        def dual_roi_contextual_dnti_hot_mask(*a, **kw):
            out = real(*a, **kw)
            self._add({"tipo": "dnti_ctx", "salida": _bool(out), "a": a, "kw": kw})
            return out
        return dual_roi_contextual_dnti_hot_mask

    def envolver_test1(self, real):
        def compute_test1_mir(*a, **kw):
            res = real(*a, **kw)
            self._add({"tipo": "test1", "bt": kw.get("bt"), "lat": kw.get("lat"), "lon": kw.get("lon"),
                       "mask_contributing": _bool(res.get("mask_contributing")),
                       "triggered": bool(res.get("triggered"))})
            return res
        return compute_test1_mir

    def envolver_ctx(self, real):
        def apply_contextual_test1_filter(test1_mask, dnti_ctx_mask, keep_peak_rc=None):
            out = real(test1_mask, dnti_ctx_mask, keep_peak_rc=keep_peak_rc)
            self._add({"tipo": "ctx_filter", "test1_in": _bool(test1_mask), "dnti_ctx": _bool(dnti_ctx_mask),
                       "keep_peak_rc": None if keep_peak_rc is None else [int(t) for t in keep_peak_rc],
                       "salida": _bool(out)})
            return out
        return apply_contextual_test1_filter

    def envolver_prioridad(self, real):
        def resolve_test1_source_priority(*a, **kw):
            v = real(*a, **kw)
            self._add({"tipo": "prioridad", "valor": bool(v)})
            return v
        return resolve_test1_source_priority

    def envolver_lbg(self, real):
        def select_test1_effective_lbg(*a, **kw):
            v = real(*a, **kw)
            self._add({"tipo": "lbg_test1", "valor": None if v is None else float(v)})
            return v
        return select_test1_effective_lbg
