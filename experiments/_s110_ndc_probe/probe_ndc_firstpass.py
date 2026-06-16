"""S110 — Probe de atribución del first-pass MODIS en NdC (frente D11, A65).

Pregunta decisiva (AUDIT_S110_NDC_PATH_DIAGNOSTIC §gap): los píxeles-semilla del
first-pass (Coppola 2016a Tests 2∧3) que generan el artefacto topográfico A69 en
Nevados de Chillán, ¿pasan por la rama del PISO ABSOLUTO C1 (0.003 summit / 0.010
scene) o por la rama ESTADÍSTICA μ+C2·σ (background contaminado por la cumbre fría)?
Y ¿están en el cráter (summit) o en el valle tibio (scene)?

La respuesta decide el candidato D11 correcto (no apuntar al path equivocado por 4ª vez):
  - rama C1  -> el piso absoluto es demasiado permisivo en escenas de alto rango
    dinámico (nevados); candidato = C1 régimen-dependiente / escalado por σ_NTI escena.
  - rama μ+C2σ -> el background μ/σ está contaminado por la cumbre nevada fría;
    candidato = pool de background que excluya la cumbre / fondo local (con cuidado:
    fondo-local fue refutado S106 — ver D11).

MÉTODO (A45 read-only sobre pipeline): NO edita pipeline. Monkeypatch del probe que
envuelve first_pass_tests_2_and_3, captura sus inputs/outputs REALES, y reconstruye la
atribución por píxel reusando las MISMAS funciones building-block del pipeline
(_nanmean_8neighbors_fast, compute_eti_scene_quadratic, build_unsuitable_mask). Así
reusa el 100% del preámbulo real de calculate_vrp sin reproducir 340 líneas.

Corre en GitHub Actions (pyhdf/MODIS solo en Linux; secrets EARTHDATA). Espejo de los
probes ground-truth S104. Vuelca JSON + reporte de texto + PNG por noche. Archivar tras usar.
"""
import sys, io, os, json, math
from pathlib import Path
from datetime import datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

from pipeline.fetch import search_granules, download_granules, auth
import pipeline.process_modis as pm
import pipeline.detection_context as dc

# --- NdC config (volcanoes.yaml) ---
VLAT, VLON = -36.863, -71.377
RADIUS_KM = 25.0
VENT_RADIUS_KM = 2.0
INNER_KM = 5.0

# --- Targets: 5 ARTEFACTO (VIIRS no vio nada, ΔT~4-5K) + 5 REAL (VIIRS summit, ΔT~19-23K) ---
# Extraídos de data/mirova_equivalent/NevadosDeChillan.json (S110 diagnóstico JSON-level).
TARGETS = [
    # (date YYYY-MM-DD, sensor, granule, label, dT_json, pcvrp_json)
    ("2026-04-10", "MODIS_TERRA", "MOD021KM.A2026100.0130.061.2026100131437.hdf", "ARTEFACTO", 4.5, 0.30),
    ("2026-03-08", "MODIS_TERRA", "MOD021KM.A2026067.0250.061.2026067131051.hdf", "ARTEFACTO", 4.8, 0.12),
    ("2026-02-08", "MODIS_AQUA",  "MYD021KM.A2026039.0645.061.2026039192119.hdf", "ARTEFACTO", 4.8, 0.33),
    ("2026-02-26", "MODIS_AQUA",  "MYD021KM.A2026057.0650.061.2026057191350.hdf", "ARTEFACTO", 4.8, 0.07),
    ("2026-03-06", "MODIS_TERRA", "MOD021KM.A2026065.0135.061.2026065131325.hdf", "ARTEFACTO", 5.1, 0.42),
    ("2026-05-01", "MODIS_TERRA", "MOD021KM.A2026121.0205.061.2026121132049.hdf", "REAL", 22.9, 5.00),
    ("2026-06-10", "MODIS_TERRA", "MOD021KM.A2026161.0155.061.2026161131743.hdf", "REAL", 22.7, 5.00),
    ("2026-05-04", "MODIS_TERRA", "MOD021KM.A2026124.0225.061.2026124131532.hdf", "REAL", 21.3, 3.93),
    ("2026-03-17", "MODIS_TERRA", "MOD021KM.A2026076.0210.061.2026076131830.hdf", "REAL", 20.3, 3.87),
    ("2026-04-18", "MODIS_TERRA", "MOD021KM.A2026108.0145.061.2026108131726.hdf", "REAL", 18.9, 5.00),
]
PRODUCT_KEY = {"MODIS_TERRA": "MODIS_TERRA_L1B", "MODIS_AQUA": "MODIS_AQUA_L1B"}

HERE = Path(__file__).parent
DEST = HERE / "granules"; DEST.mkdir(parents=True, exist_ok=True)
OUT = HERE / "out"; OUT.mkdir(parents=True, exist_ok=True)

# --- Monkeypatch capture: envuelve el first-pass real, guarda inputs+outputs ---
_REAL_FP = dc.first_pass_tests_2_and_3
_CAP = {}

def _wrapped_fp(*args, **kwargs):
    hot, diag = _REAL_FP(*args, **kwargs)
    # process_modis llama por keyword (verificado process_modis.py:695)
    _CAP["kwargs"] = dict(kwargs)
    _CAP["hot"] = np.array(hot, dtype=bool)
    _CAP["diag"] = diag
    return hot, diag

pm.first_pass_tests_2_and_3 = _wrapped_fp  # process_modis lo importó por nombre


def gname(g):
    try:
        return g["umm"]["DataGranule"]["Identifiers"][0]["Identifier"]
    except Exception:
        return str(g)[:60]


def attribute(kw, hot):
    """Reconstruye dNTI/dETI/μ/σ EXACTO como first_pass_tests_2_and_3 y atribuye
    por píxel-semilla: rama (C1 vs μ+C2σ), región (summit/scene), valores."""
    nti = kw["nti"]; nti_app = kw["nti_app"]; bt = kw["bt"]
    roi = kw["roi_mask"]; dist = kw["dist_km"]; t_bg = kw["t_bg"]
    inner = kw["inner_km"]
    c1_dnti_sum = kw["c1_dnti_summit"]; c1_deti_sum = kw["c1_deti_summit"]
    c2_dnti_sum = kw["c2_dnti_summit"]; c2_deti_sum = kw["c2_deti_summit"]
    c1_dnti_sce = kw.get("c1_dnti_scene"); c1_deti_sce = kw.get("c1_deti_scene")
    c2_dnti_sce = kw.get("c2_dnti_scene"); c2_deti_sce = kw.get("c2_deti_scene")
    dual = c1_dnti_sce is not None

    mask_valid = roi & np.isfinite(nti) & np.isfinite(nti_app)
    eti = dc.compute_eti_scene_quadratic(nti, nti_app, mask_valid)
    dnti = nti - dc._nanmean_8neighbors_fast(nti)
    deti = eti - dc._nanmean_8neighbors_fast(eti)
    bg_mask = dc.build_unsuitable_mask(
        roi_mask=roi, dnti=dnti, deti=deti, test1_mask=kw.get("test1_mask"),
        dnti_floor=kw["unsuitable_dnti_floor"], deti_floor=kw["unsuitable_deti_floor"],
    )
    mu_dnti = float(np.mean(dnti[bg_mask])); sd_dnti = float(np.std(dnti[bg_mask]))
    mu_deti = float(np.mean(deti[bg_mask])); sd_deti = float(np.std(deti[bg_mask]))

    # threshold efectivo por región = min(C1, μ+C2σ); rama "binding" = la menor
    def branch(c1, mu, c2, sd):
        stat = mu + c2 * sd
        return ("C1" if c1 <= stat else "STAT"), min(c1, stat), c1, stat

    b_dnti_sum = branch(c1_dnti_sum, mu_dnti, c2_dnti_sum, sd_dnti)
    b_deti_sum = branch(c1_deti_sum, mu_deti, c2_deti_sum, sd_deti)
    b_dnti_sce = branch(c1_dnti_sce, mu_dnti, c2_dnti_sce, sd_dnti) if dual else b_dnti_sum
    b_deti_sce = branch(c1_deti_sce, mu_deti, c2_deti_sce, sd_deti) if dual else b_deti_sum

    ys, xs = np.where(hot)
    pixels = []
    for y, x in zip(ys.tolist(), xs.tolist()):
        is_sum = bool(dist[y, x] <= inner)
        bd = b_dnti_sum if is_sum else b_dnti_sce
        be = b_deti_sum if is_sum else b_deti_sce
        pixels.append({
            "dist_km": round(float(dist[y, x]), 2),
            "region": "summit" if is_sum else "scene",
            "bt_k": round(float(bt[y, x]), 2),
            "bt_excess_k": round(float(bt[y, x] - t_bg), 2),
            "nti": round(float(nti[y, x]), 5),
            "dnti": round(float(dnti[y, x]), 5),
            "deti": round(float(deti[y, x]), 5),
            "thr_dnti": round(bd[1], 5), "branch_dnti": bd[0],
            "thr_deti": round(be[1], 5), "branch_deti": be[0],
            # rama que efectivamente dejó pasar dNTI: pasó C1 y/o STAT
            "dnti_pass_C1": bool(float(dnti[y, x]) > bd[2]),
            "dnti_pass_STAT": bool(float(dnti[y, x]) > bd[3]),
        })
    return {
        "t_bg": round(float(t_bg), 3), "inner_km": inner, "dual_roi": dual,
        "mu_dnti": round(mu_dnti, 6), "sd_dnti": round(sd_dnti, 6),
        "mu_deti": round(mu_deti, 6), "sd_deti": round(sd_deti, 6),
        "n_bg_used": int(np.count_nonzero(bg_mask)),
        "thr_summit_dnti": {"C1": c1_dnti_sum, "stat": round(mu_dnti + c2_dnti_sum * sd_dnti, 5),
                            "binding": b_dnti_sum[0], "eff": round(b_dnti_sum[1], 5)},
        "thr_scene_dnti": ({"C1": c1_dnti_sce, "stat": round(mu_dnti + c2_dnti_sce * sd_dnti, 5),
                            "binding": b_dnti_sce[0], "eff": round(b_dnti_sce[1], 5)} if dual else None),
        "pixels": pixels,
    }


def png_night(label, date, attr, path):
    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    except Exception:
        return
    px = attr["pixels"]
    if not px:
        return
    d = [p["dist_km"] for p in px]; dn = [p["dnti"] for p in px]
    col = ["#d62728" if p["region"] == "summit" else "#1f77b4" for p in px]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(d, dn, c=col, s=40, edgecolors="k", linewidths=0.4, zorder=3)
    ax.axhline(0.003, ls="--", c="#d62728", lw=1, label="C1 summit 0.003")
    ax.axhline(0.010, ls="--", c="#1f77b4", lw=1, label="C1 scene 0.010")
    ax.axvline(INNER_KM, ls=":", c="gray", lw=1, label=f"inner {INNER_KM}km")
    ax.set_xlabel("dist al cráter (km)"); ax.set_ylabel("dNTI (semilla)")
    ax.set_title(f"{label} {date} — semillas first-pass (rojo=summit, azul=scene)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)


def main():
    auth()
    print(f"NdC first-pass attribution probe — {len(TARGETS)} noches\n", flush=True)
    results = []
    for date, sensor, granule, label, dT, pcvrp in TARGETS:
        print(f"=== {label} {date} {sensor} ΔT_json={dT} pc.vrp_json={pcvrp} ===", flush=True)
        print(f"    {granule}", flush=True)
        dt = datetime.strptime(date, "%Y-%m-%d")
        try:
            grs = search_granules(PRODUCT_KEY[sensor], VLAT, VLON, RADIUS_KM, dt)
        except Exception as e:
            print(f"    SEARCH FAIL: {e}", flush=True); continue
        # Filtrar al granule objetivo ANTES de bajar (evita pasadas irrelevantes).
        stamp = ".".join(granule.split(".")[1:3])  # A2026100.0130
        grs_t = [g for g in grs if gname(g) == granule or stamp in gname(g)]
        if not grs_t:
            print(f"    target no en search (encontrados: {[gname(g) for g in grs][:6]})", flush=True)
            grs_t = grs  # fallback: intentar con todos
        paths = []
        try:
            paths = download_granules(grs_t, DEST)
        except Exception as e:
            print(f"    DOWNLOAD FAIL: {e}", flush=True)
        match = [p for p in paths if Path(p).name == granule]
        if not match:
            # fallback: cualquier L1B (no GEO) cuyo timestamp coincida con el granule
            stamp = ".".join(granule.split(".")[1:3])  # A2026100.0130
            match = [p for p in paths if stamp in Path(p).name and "021KM" in Path(p).name]
        if not match:
            print(f"    NO MATCH (bajados: {[Path(p).name for p in paths][:6]})", flush=True); continue
        hdf = Path(match[0])
        _CAP.clear()
        try:
            rec = pm.calculate_vrp(
                hdf, hdf, VLAT, VLON, RADIUS_KM,
                vent_lat=VLAT, vent_lon=VLON, vent_radius_km=VENT_RADIUS_KM,
                inner_radius_km=INNER_KM, exclude_zones=None, active_water_bodies=None,
                lbg_global_compatible=True, local_kernel_bg_compatible=False,
            )
        except Exception as e:
            print(f"    calculate_vrp FAIL: {e}", flush=True); continue
        if "hot" not in _CAP:
            print(f"    first-pass NO se ejecutó (gate previo o granule sin cobertura)", flush=True)
            results.append({"date": date, "label": label, "sensor": sensor,
                            "granule": granule, "first_pass_ran": False,
                            "record_vrp": (rec or {}).get("vrp_mw") if rec else None})
            continue
        attr = attribute(_CAP["kwargs"], _CAP["hot"])
        px = attr["pixels"]
        n = len(px); n_sum = sum(1 for p in px if p["region"] == "summit")
        n_sce = n - n_sum
        # de las semillas, ¿cuántas pasaron dNTI SOLO por C1 (no por stat)?
        only_c1 = sum(1 for p in px if p["dnti_pass_C1"] and not p["dnti_pass_STAT"])
        via_stat = sum(1 for p in px if p["dnti_pass_STAT"])
        dn_sum = [p["dnti"] for p in px if p["region"] == "summit"]
        print(f"    semillas={n} (summit={n_sum}, scene={n_sce}) | "
              f"dNTI solo-C1={only_c1}, vía-STAT={via_stat}", flush=True)
        print(f"    binding summit dNTI: {attr['thr_summit_dnti']['binding']} "
              f"(C1={attr['thr_summit_dnti']['C1']} vs stat={attr['thr_summit_dnti']['stat']})", flush=True)
        if attr["thr_scene_dnti"]:
            print(f"    binding scene  dNTI: {attr['thr_scene_dnti']['binding']} "
                  f"(C1={attr['thr_scene_dnti']['C1']} vs stat={attr['thr_scene_dnti']['stat']})", flush=True)
        if dn_sum:
            print(f"    dNTI semillas summit: min={min(dn_sum):.5f} max={max(dn_sum):.5f} "
                  f"(C1 summit=0.003)", flush=True)
        png_night(label, date, attr, OUT / f"{label}_{date}_{sensor}.png")
        out = {"date": date, "label": label, "sensor": sensor, "granule": granule,
               "first_pass_ran": True, "dT_json": dT, "pcvrp_json": pcvrp,
               "n_seed": n, "n_summit": n_sum, "n_scene": n_sce,
               "dnti_only_C1": only_c1, "dnti_via_STAT": via_stat,
               "record_vrp": (rec or {}).get("vrp_mw") if rec else None,
               **attr}
        results.append(out)
        print("", flush=True)

    (OUT / "ndc_firstpass_attribution.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    # --- Síntesis ARTEFACTO vs REAL ---
    print("\n" + "=" * 60, flush=True)
    print("SÍNTESIS ARTEFACTO vs REAL", flush=True)
    for lab in ("ARTEFACTO", "REAL"):
        rs = [r for r in results if r.get("label") == lab and r.get("first_pass_ran")]
        if not rs:
            print(f"  {lab}: sin datos", flush=True); continue
        tot = sum(r["n_seed"] for r in rs)
        tsum = sum(r["n_summit"] for r in rs); tsce = sum(r["n_scene"] for r in rs)
        tc1 = sum(r["dnti_only_C1"] for r in rs); tstat = sum(r["dnti_via_STAT"] for r in rs)
        all_dn_sum = [p["dnti"] for r in rs for p in r["pixels"] if p["region"] == "summit"]
        med_dn = float(np.median(all_dn_sum)) if all_dn_sum else float("nan")
        print(f"  {lab} (n={len(rs)} noches): semillas={tot} "
              f"summit={tsum} scene={tsce} | dNTI solo-C1={tc1} vía-STAT={tstat} | "
              f"mediana dNTI summit={med_dn:.5f}", flush=True)
    print("\nJSON: experiments/_s110_ndc_probe/out/ndc_firstpass_attribution.json", flush=True)


if __name__ == "__main__":
    main()
