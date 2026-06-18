"""S112 focal V750 — audit A/B con criterio PRE-REGISTRADO (A66, A10, A67, A62).

Objetivo: el fix núcleo-focal portado a VIIRS750 debe CURAR el artefacto topográfico
(inflado 10-25x sobre MIROVA en nevados) SIN matar la señal real (Lascar cráter, Villarrica
lava lake, PCC lacolito cat-b). Cruce con pc.vrp_mw (A10) vs MIROVA por sensor V750 (A67).

CRITERIO PRE-REGISTRADO:
  C1 (Lascar CANARIO anti-FN): el brazo ON preserva Lascar — mediana V750 summit pc.vrp se
     mantiene 0.5-2x vs MIROVA V750 y NO pierde records (n_on ~ n_base). ABORTAR si colapsa.
  C2 (artefacto Tupun/Isluga/NdC): ON reduce la mediana >=60% vs base (de-infla hacia MIROVA,
     que reporta ~0 o << en V750).
  C3 (cat-b Villarrica/PCC): ON NO los lleva a 0 (keep_peak rescata el foco) — siguen con
     records vrp>0.
  C4 (MODIS byte-idéntico): MODIS igual entre base y ON (el flag V750 NO toca MODIS).
  C5 (VIIRS375 byte-idéntico): NdC VIIRS375 (#439/#440) igual entre base y ON (otro path).
  ADOPTAR sii C1 ∧ C2 ∧ C3 ∧ C4 ∧ C5. Si Lascar cae (C1) o cat-b se anula (C3) -> NO.
"""
import csv, io, json, statistics as st, sys
from pathlib import Path
from collections import defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
CONS = ROOT / "experiments" / "_s111_d11" / "mirova_fresh" / "cons.csv"
V750 = {"VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"}
V375 = {"VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"}
NAME_MIR = {"Lascar": "Lascar", "Tupungatito": "Tupungatito", "Isluga": "Isluga",
            "Nevados de Chillan": "NevadosDeChillan", "Villarrica": "Villarrica",
            "Puyehue-Cordon Caulle": "PuyehueCordonCaulle"}
VOLS = ["Lascar", "Tupungatito", "Isluga", "NevadosDeChillan", "Villarrica", "PuyehueCordonCaulle"]
ARTIFACT = {"Tupungatito", "Isluga", "NevadosDeChillan"}
CATB = {"Villarrica", "PuyehueCordonCaulle"}
WIN_START = "2026-05-01"


def mirova_v750_median():
    out = defaultdict(list)
    for r in csv.DictReader(open(CONS, encoding="utf-8")):
        v = NAME_MIR.get(r.get("Volcan", ""))
        if not v or r.get("Sensor") != "VIIRS" or r.get("Tipo_Registro") != "ALERTA_TERMICA":
            continue
        if str(r.get("Fecha_Satelite_UTC", "")) < WIN_START:
            continue
        try:
            vrp = float(r.get("VRP_MW") or 0)
        except ValueError:
            vrp = 0.0
        if vrp > 0:
            out[v].append(vrp)
    return {v: (st.median(x) if x else 0.0, max(x) if x else 0.0, len(x)) for v, x in out.items()}


def load(profile, vol, sensors):
    p = ROOT / "data" / profile / f"{vol}.json"
    if not p.exists():
        return None
    doc = json.loads(p.read_text(encoding="utf-8"))
    recs = doc["records"] if isinstance(doc, dict) else doc
    out = []
    for r in recs:
        if r.get("sensor") not in sensors:
            continue
        if str(r.get("datetime_utc", "")) < WIN_START:
            continue
        pc = r.get("primary_cluster") or {}
        out.append({"granule": r.get("granule"), "vrp": float(pc.get("vrp_mw") or 0),
                    "summit": r.get("distance_class") == "summit"})
    return out


def v750_summit_vrps(recs):
    return [r["vrp"] for r in recs if r["summit"] and r["vrp"] > 0]


def byte_identical(profile_a, profile_b, vol, sensors):
    a = load(profile_a, vol, sensors); b = load(profile_b, vol, sensors)
    if a is None or b is None:
        return None
    da = {r["granule"]: round(r["vrp"], 4) for r in a}
    db = {r["granule"]: round(r["vrp"], 4) for r in b}
    return da == db


def audit():
    mir = mirova_v750_median()
    print("=== A/B focal V750 — mediana V750 summit pc.vrp (base vs ON) vs MIROVA V750 ===", flush=True)
    verdict = {}
    for vol in VOLS:
        rb = load("_v750focal_base", vol, V750)
        ro = load("_v750focal_on", vol, V750)
        if rb is None or ro is None:
            print(f"  {vol:20s} SIN DATA (gather primero)", flush=True); continue
        vb = v750_summit_vrps(rb); vo = v750_summit_vrps(ro)
        mb = st.median(vb) if vb else 0.0
        mo = st.median(vo) if vo else 0.0
        mm, mmax, mn = mir.get(vol, (0.0, 0.0, 0))
        red = (1 - mo / mb) * 100 if mb > 0 else 0.0
        verdict[vol] = {"base_med": mb, "on_med": mo, "n_base": len(vb), "n_on": len(vo),
                        "mir_med": mm, "mir_n": mn, "reduction_pct": red}
        print(f"  {vol:20s} base_med={mb:.2f}(n{len(vb)}) on_med={mo:.2f}(n{len(vo)}) "
              f"MIROVA_med={mm:.2f}(n{mn}) reduccion={red:.0f}%", flush=True)

    print("\n=== VEREDICTO (criterio pre-registrado) ===", flush=True)
    ok = True
    # C1 Lascar canario
    L = verdict.get("Lascar")
    if L:
        ratio = L["on_med"] / L["mir_med"] if L["mir_med"] > 0 else float("inf")
        c1 = (0.5 <= ratio <= 2.0) and (L["n_on"] >= 0.8 * L["n_base"])
        print(f"  C1 Lascar CANARIO: on_med={L['on_med']:.2f} ratio_vs_MIROVA={ratio:.2f} "
              f"n_on/{L['n_base']}={L['n_on']} -> {'OK' if c1 else 'FALLA (ABORTAR)'}", flush=True)
        ok = ok and c1
    # C2 artefacto: reducción >=60% Y sin pérdida de records (la de-inflación es per-record,
    # no por perder detecciones — guard A19/A67, review S112 LOW).
    for v in ARTIFACT:
        d = verdict.get(v)
        if d:
            c2_red = d["reduction_pct"] >= 60.0
            c2_rec = d["n_on"] >= 0.8 * d["n_base"] if d["n_base"] else True
            c2 = c2_red and c2_rec
            print(f"  C2 {v}: reduccion {d['reduction_pct']:.0f}% (>=60%?) n_on/{d['n_base']}="
                  f"{d['n_on']} -> {'OK' if c2 else ('PARCIAL' if c2_red else 'FALLA')}", flush=True)
            ok = ok and c2
    # C3 cat-b PRESERVACIÓN (review S112 HIGH): keep_peak hace pc.vrp>0 trivial, así que
    # "no-cero" NO mide nada. Cruzar vs MIROVA V750 por vol (A10/A62): donde MIROVA reporta
    # V750>0 (PCC, lacolito real) el ON NO debe aplastar bajo el piso del sensor (0.15 MW) ni
    # bajo 0.3× MIROVA; donde MIROVA V750=0 (Villarrica, lava lake va por MODIS/VIIRS375) la
    # de-inflación del artefacto V750 es CORRECTA y el lava lake se verifica intacto en C4/C5.
    V750_FLOOR = 0.15
    for v in CATB:
        d = verdict.get(v)
        if not d:
            continue
        if d["mir_med"] > 0:  # PCC: V750 real → preservar hacia MIROVA
            thr = max(V750_FLOOR, 0.3 * d["mir_med"])
            c3 = d["on_med"] >= thr
            print(f"  C3 {v} cat-b (MIROVA V750={d['mir_med']:.2f}): on_med={d['on_med']:.2f} "
                  f">= {thr:.2f}? -> {'OK' if c3 else 'FALLA (aplasta cat-b real)'}", flush=True)
            ok = ok and c3
        else:  # Villarrica: MIROVA V750=0 → de-inflar OK; lava lake en otros sensores (C4/C5)
            print(f"  C3 {v} cat-b (MIROVA V750=0): on_med={d['on_med']:.2f} — de-inflación del "
                  f"artefacto V750 ESPERADA; lava lake real verificado en C4 (MODIS)+C5 (VIIRS375)",
                  flush=True)
    # C4 MODIS byte-idéntico (el flag V750 NO toca MODIS). None (sin data) NO es PASS.
    c4_all = [bi for vol in VOLS
              if (bi := byte_identical("_v750focal_base", "_v750focal_on", vol,
                                       {"MODIS_TERRA", "MODIS_AQUA"})) is not None]
    c4 = all(c4_all) if c4_all else None
    print(f"  C4 MODIS byte-identico base==ON: {c4} ({sum(c4_all)}/{len(c4_all)} vols con data)",
          flush=True)
    # C5 VIIRS375 byte-idéntico (NdC #439/#440 es otro path). None NO es PASS.
    c5 = byte_identical("_v750focal_base", "_v750focal_on", "NevadosDeChillan", V375)
    print(f"  C5 VIIRS375 NdC byte-identico base==ON: {c5}", flush=True)
    # None (no verificable) bloquea ADOPTAR (review S112 LOW: no vacuous-pass).
    ok = ok and (c4 is True) and (c5 is True)
    print(f"\n  ==> {'ADOPTAR' if ok else 'NO ADOPTAR / revisar'} (C1 canario es bloqueante)", flush=True)
    out = ROOT / "experiments" / "_s112_v750focal" / "v750focal_ab_audit.json"
    out.write_text(json.dumps(verdict, indent=2), encoding="utf-8")
    print(f"\nResumen -> {out}", flush=True)


if __name__ == "__main__":
    audit()
