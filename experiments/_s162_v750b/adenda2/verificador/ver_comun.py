# -*- coding: utf-8 -*-
"""Constructor propio del verificador (no usa Pob del autor): poblaciones sinteticas en el formato del probe."""
import hashlib, json, subprocess, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
V750B = AQUI.parents[1]
ADENDA2 = AQUI.parent
EV = Path(r"C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs750-2-918174\0c1274cb-99b4-4a91-a624-a9ed2be04812\scratchpad\evaluar_d25.py")
TMP = Path(r"C:\vrp-trabajo\temporales\v750b_ver2")
SENSOR = "VIIRS_SNPP_750"
CAJAS = ("B0", "B1", "B2", "B3", "B5")
COB = {"nan_67": 0, "nan_21": 0, "nan_7": 0, "nan_centro": False, "nan_7_crater": 0, "nan_crater": False}


def caja(pix, vrp=0.5):
    if not pix:
        return {"motivo_vacio": None, "n_abs": 0, "n_p1": 0, "n_p2": 0, "npix": 0, "vrp_mw": None, "pixeles": []}
    return {"motivo_vacio": None, "n_abs": 0, "n_p1": len(pix), "n_p2": 0, "npix": len(pix), "vrp_mw": vrp,
            "pixeles": [[f, c, 2, round(((f - 33) ** 2 + (c - 33) ** 2) ** 0.5 * 0.75, 2), m] for f, c, m in pix]}


def k_record(pub):
    if not pub:
        return {"primary_cluster": None, "distance_class": None, "vrp_mw": 0.0, "vrp_mir_mw": 0.0,
                "discarded_reason": None, "triggered_test1": False, "vrp_vent_mw": None, "t_max_k": 290.0,
                "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}
    return {"primary_cluster": {"vrp_mw": 0.5, "n_pixels": 1, "centroid_dist_km": 0.5}, "distance_class": "summit",
            "vrp_mw": 0.5, "vrp_mir_mw": 0.5, "discarded_reason": None, "triggered_test1": False,
            "vrp_vent_mw": None, "t_max_k": 300.0, "sensor": SENSOR, "f5_core_vrp_mw": None, "anomaly_pixels": []}


class Pob:
    def __init__(self):
        self.sell, self.supl, self.res = [], [], []

    def pasada(self, hora, lab, pix_por_caja, vrp_mirova=0.0, volcan="Lascar", dist_mirova=None, crater=(33.0, 33.0),
               pub_prod=False, k_pub=None, filas=None, source="CONS", vrp_caja=0.5, estado="ok"):
        """pix_por_caja: lista (se usa para todas las cajas) o dict caja -> lista."""
        supl = lab == "far_ref"
        lista = self.supl if supl else self.sell
        i = (100000 if supl else 0) + len(lista)
        if filas is None:
            if lab == "pos":
                filas = [{"fecha_utc": hora + ":00", "tipo": "ALERTA_TERMICA", "vrp_mw": vrp_mirova,
                          "dist_km": dist_mirova, "source": source}]
            elif lab == "far_ref":
                filas = [{"fecha_utc": hora + ":00", "tipo": "FALSO_POSITIVO", "vrp_mw": vrp_mirova,
                          "dist_km": dist_mirova, "source": source}]
            else:
                filas = [{"fecha_utc": hora + ":00", "tipo": "RUTINA", "vrp_mw": 0.0, "dist_km": None, "source": "CONS"}]
        o = {"id": i, "volcan": volcan, "hora_utc": hora, "sensor": SENSOR, "lab": lab,
             "protegida": lab == "pos" and vrp_mirova >= 1.0, "alerta_tabla": lab == "pos" and source == "CONS",
             "decide": True, "mirova": filas, "mirova_vrp": vrp_mirova, "z": 30.0, "pub_prod": pub_prod,
             "dc": "summit" if pub_prod else None, "pc_vrp": 0.5 if pub_prod else 0.0, "pc_n": 1 if pub_prod else None,
             "granule": f"g{i}", "en_sc": False, "celda_crater": [int(x) for x in crater], "pos_crater": list(crater),
             "inner_km": 5.0}
        if supl:
            o["dist_ref"] = dist_mirova
        lista.append(o)
        kp = pub_prod if k_pub is None else k_pub
        cajas = {b: caja(pix_por_caja[b] if isinstance(pix_por_caja, dict) else pix_por_caja, vrp_caja) for b in CAJAS}
        self.res.append({"id": i, "volcan": volcan, "hora_utc": hora, "estado": estado, "dayflag": 0, "sunglint": 40.0,
                         "cobertura": COB, "brazos": {"K": {"record": k_record(kp), "pc_pix": []}}, "oraculo": cajas})
        return i

    def escribir(self, d, con_supl=True):
        d = Path(d)
        (d / "art").mkdir(parents=True, exist_ok=True)
        res = self.res if con_supl else [r for r in self.res if r["id"] < 100000]
        (d / "art" / "resultados_00.json").write_text(json.dumps(res), encoding="utf-8")
        ts = json.dumps(self.sell)
        (d / "objetivos.json").write_text(ts, encoding="utf-8")
        (d / "sin_granulo.json").write_text(json.dumps(
            {"objetivos_sha256": hashlib.sha256(ts.encode("utf-8")).hexdigest(), "pasadas": []}), encoding="utf-8")
        tp = json.dumps(self.supl)
        (d / "supl.json").write_text(tp, encoding="utf-8")
        (d / "sin_granulo_supl.json").write_text(json.dumps(
            {"objetivos_sha256": hashlib.sha256(tp.encode("utf-8")).hexdigest(), "pasadas": []}), encoding="utf-8")


def correr(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def lector(d, extra=()):
    return correr([sys.executable, ADENDA2 / "leer_posicion_v750b.py", "--art", d / "art", "--objetivos", d / "objetivos.json",
                   "--objetivos-supl", d / "supl.json", "--sin-granulo-supl", d / "sin_granulo_supl.json",
                   "--evaluador", EV, "--salida", d / "lector.txt", *extra])


def analizador(d, art=None, extra=()):
    return correr([sys.executable, V750B / "analizar_v750b.py", "--art", art or d / "art", "--objetivos", d / "objetivos.json",
                   "--evaluador", EV, "--sin-granulo", d / "sin_granulo.json", "--censo-omitido-solo-pruebas",
                   "--salida", d / "analizador.txt", *extra])
