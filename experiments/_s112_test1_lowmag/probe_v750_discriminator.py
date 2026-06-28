"""S112 — Discriminante VIIRS750: artefacto topografico (nevados) vs cluster REAL (Lascar).

POR QUE (fenomeno fisico): en volcanes con cumbre nevada/glaciar el campo MIR (I04/M13)
absoluto esta dominado por el gradiente de altitud crater-frio vs valle-tibio, NO por lava.
El Test1 integrado (compute_test1_mir, MIR ABSOLUTO) suma ese exceso sobre pixeles GRANDES
(750m) -> VRP infla con el area. MIROVA detecta por NTI (cancela topografia) -> inmune al
artefacto. Lascar (crater real) tiene NTI elevado real; el artefacto tiene NTI plano (-0.93..-0.96).

OBJETIVO: encontrar la variable (o combinacion) que mejor separa el grupo ARTEFACTO
(Tupungatito/Isluga/NdC/Copahue/Llaima/Chaiten/PP) del grupo REAL (Lascar) en VIIRS750
summit desde 2026-05-01, con pc.vrp_mw>=0.5.

Read-only sobre data/mirova_equivalent/*.json. No toca pipeline (A45).
"""
import io
import json
import sys
import statistics as st
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "mirova_equivalent"
SINCE = "2026-05-01"
VRP_MIN = 0.5

ARTIFACT_VOLS = ["Tupungatito", "Isluga", "NevadosDeChillan", "Copahue",
                 "Llaima", "Chaiten", "PlanchonPeteroa"]
REAL_VOLS = ["Lascar"]

# Variables a perfilar. (clave_legible, extractor) — extractor devuelve float o None.
def _pc(r):
    return r.get("primary_cluster") or {}

def _delta_t(r):
    tmax, tbg = r.get("t_max_k"), r.get("t_bg_k")
    if tmax is None or tbg is None:
        return None
    return tmax - tbg

# nti_max preferir top-level, fallback diag_nti_max
def _nti_max(r):
    v = r.get("nti_max")
    if v is None:
        v = r.get("diag_nti_max")
    return v

# NTI excess sobre el fondo: nti_max - nti_bg (cuanto sobresale del background NTI).
def _nti_excess(r):
    nmax = _nti_max(r)
    nbg = r.get("nti_bg")
    if nbg is None:
        nbg = r.get("diag_nti_bg")
    if nmax is None or nbg is None:
        return None
    return nmax - nbg

VARS = [
    ("nti_max",            _nti_max),
    ("nti_bg",             lambda r: r.get("nti_bg") if r.get("nti_bg") is not None else r.get("diag_nti_bg")),
    ("nti_excess",         _nti_excess),
    ("n_dnti_ctx_path",    lambda r: r.get("n_dnti_ctx_path")),
    ("n_nti_rel_path",     lambda r: r.get("n_nti_rel_path")),
    ("n_nti_path",         lambda r: r.get("n_nti_path")),
    ("n_bt_path",          lambda r: r.get("n_bt_path")),
    ("pc_n_pixels",        lambda r: _pc(r).get("n_pixels")),
    ("delta_t_k",          _delta_t),
    ("t_max_k",            lambda r: r.get("t_max_k")),
    ("t_bg_k",             lambda r: r.get("t_bg_k")),
    ("pc_vrp_mw",          lambda r: _pc(r).get("vrp_mw")),
    ("triggered_test1",    lambda r: 1.0 if r.get("triggered_test1") else 0.0),
]


def collect(vols):
    """Devuelve lista de records VIIRS750 summit since SINCE con pc.vrp>=VRP_MIN."""
    out = []
    for vol in vols:
        f = DATA / f"{vol}.json"
        if not f.exists():
            print(f"  WARN: no existe {f}", flush=True)
            continue
        doc = json.loads(f.read_text(encoding="utf-8"))
        recs = doc["records"] if isinstance(doc, dict) else doc
        for r in recs:
            sensor = r.get("sensor", "")
            if "750" not in sensor:
                continue
            if (r.get("datetime_utc", "") or "") < SINCE:
                continue
            if r.get("distance_class") != "summit":
                continue
            pc = _pc(r)
            if (pc.get("vrp_mw") or 0) < VRP_MIN:
                continue
            r["_vol"] = vol
            out.append(r)
    return out


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    vals_sorted = sorted(vals)
    n = len(vals_sorted)
    def q(p):
        idx = max(0, min(n - 1, int(round(p * (n - 1)))))
        return vals_sorted[idx]
    return {
        "n": n,
        "median": st.median(vals_sorted),
        "p10": q(0.10),
        "p90": q(0.90),
        "min": vals_sorted[0],
        "max": vals_sorted[-1],
    }


def overlap_score(art_vals, real_vals):
    """Separacion simple: cuantos artefacto caen por encima del min real (si real es 'alto'),
    y cuantos real caen por debajo del max artefacto. Devuelve fraccion de error de clasificacion
    con el mejor umbral entre medianas (clasificador de 1 variable, threshold = punto medio
    entre medianas)."""
    a = [v for v in art_vals if v is not None]
    rr = [v for v in real_vals if v is not None]
    if not a or not rr:
        return None
    ma, mr = st.median(a), st.median(rr)
    thr = (ma + mr) / 2.0
    real_high = mr >= ma  # real tiende a ser mayor que artefacto
    # mejor accuracy con threshold = thr
    if real_high:
        # predecir REAL si val >= thr
        tp = sum(1 for v in rr if v >= thr)
        tn = sum(1 for v in a if v < thr)
    else:
        tp = sum(1 for v in rr if v < thr)
        tn = sum(1 for v in a if v >= thr)
    acc = (tp + tn) / (len(a) + len(rr))
    return {"threshold": round(thr, 4), "real_high": real_high, "accuracy": round(acc, 3),
            "real_correct": tp, "real_n": len(rr), "art_correct": tn, "art_n": len(a)}


def main():
    art = collect(ARTIFACT_VOLS)
    real = collect(REAL_VOLS)
    print("=" * 78)
    print(f"DISCRIMINANTE VIIRS750 — summit since {SINCE}, pc.vrp_mw>={VRP_MIN}")
    print(f"  ARTEFACTO ({','.join(ARTIFACT_VOLS)}): n={len(art)}")
    print(f"  REAL ({','.join(REAL_VOLS)}): n={len(real)}")
    print("=" * 78)

    # desglose por volcan artefacto
    print("\n[Desglose ARTEFACTO por volcan]")
    from collections import Counter
    c = Counter(r["_vol"] for r in art)
    for v, n in sorted(c.items()):
        print(f"   {v:24s} {n}")

    print("\n[Distribucion por variable — mediana (p10..p90) [min..max] n]")
    header = f"{'variable':18s} | {'ARTEFACTO':>34s} | {'REAL (Lascar)':>34s}"
    print(header)
    print("-" * len(header))
    sep_results = {}
    for name, fn in VARS:
        sa = stats([fn(r) for r in art])
        sr = stats([fn(r) for r in real])
        def fmt(s):
            if s is None:
                return f"{'(sin datos)':>34s}"
            return (f"med={s['median']:>8.4g} ({s['p10']:.3g}..{s['p90']:.3g}) "
                    f"[{s['min']:.3g}..{s['max']:.3g}] n={s['n']}").rjust(34)
        print(f"{name:18s} | {fmt(sa)} | {fmt(sr)}")
        ov = overlap_score([fn(r) for r in art], [fn(r) for r in real])
        if ov is not None:
            sep_results[name] = ov

    print("\n[Poder separador 1-variable — clasificador threshold = punto medio de medianas]")
    print(f"{'variable':18s} | acc   | thr      | real_high | real ok | art ok")
    print("-" * 72)
    for name, ov in sorted(sep_results.items(), key=lambda kv: -kv[1]["accuracy"]):
        print(f"{name:18s} | {ov['accuracy']:.3f} | {ov['threshold']:>8.4g} | "
              f"{str(ov['real_high']):>9s} | {ov['real_correct']}/{ov['real_n']:<4d} | "
              f"{ov['art_correct']}/{ov['art_n']}")

    # Combinacion explicita testeada en la hipotesis:
    # artefacto: NTI plano + 0 paths contextuales; Lascar: NTI elevado / paths>0.
    print("\n[Hipotesis combinada: 'tiene paths contextuales' = (n_dnti_ctx + n_nti_rel + n_nti) > 0]")
    def has_ctx(r):
        return ((r.get("n_dnti_ctx_path") or 0) + (r.get("n_nti_rel_path") or 0)
                + (r.get("n_nti_path") or 0)) > 0
    art_ctx = sum(1 for r in art if has_ctx(r))
    real_ctx = sum(1 for r in real if has_ctx(r))
    print(f"   ARTEFACTO con paths>0: {art_ctx}/{len(art)} ({100*art_ctx/max(1,len(art)):.1f}%)")
    print(f"   REAL con paths>0:      {real_ctx}/{len(real)} ({100*real_ctx/max(1,len(real)):.1f}%)")

    print("\n[Hipotesis combinada: nti_max >= -0.6 (NTI 'elevado real')]")
    for thr in (-0.9, -0.8, -0.7, -0.6, -0.5):
        a = sum(1 for r in art if (_nti_max(r) or -99) >= thr)
        rr = sum(1 for r in real if (_nti_max(r) or -99) >= thr)
        print(f"   thr nti_max>={thr:+.2f}: artefacto {a}/{len(art)} ({100*a/max(1,len(art)):.0f}%) | "
              f"real {rr}/{len(real)} ({100*rr/max(1,len(real)):.0f}%)")

    # Dump JSON para verificacion programatica (no transcribir numeros a mano).
    out = {
        "since": SINCE, "vrp_min": VRP_MIN,
        "n_artifact": len(art), "n_real": len(real),
        "artifact_breakdown": dict(c),
        "var_stats": {name: {"artifact": stats([fn(r) for r in art]),
                             "real": stats([fn(r) for r in real])}
                      for name, fn in VARS},
        "separation": sep_results,
    }
    jf = Path(__file__).resolve().parent / "probe_v750_discriminator_result.json"
    jf.write_text(json.dumps(out, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nJSON -> {jf}")


if __name__ == "__main__":
    main()
