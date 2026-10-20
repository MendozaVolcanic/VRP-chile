# Verificador S157: F exacto por pixel desde anomaly_pixels (bt_k y vrp_mw guardados), sin suponer n_eff
# ni fondo. Para cada pixel: L_bg_i = Planck21(bt) - vrp*1e6/(k*A)  (fondo efectivamente restado, incluye
# kernel local); T_bk_i = inv21(L_bg_i); F_i = (P22(bt)-P22(T_bk_i)) / (P21(bt)-L_bg_i).
import json, math, sys, os, statistics as st
sys.path.insert(0, r"D:/vrp-trabajo/s157-lambda-b22"); sys.path.insert(0, r"D:/vrp-trabajo/s157-lambda-b22/scripts")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.constants import C1, C2
import banco_paridad as bp
from auto_audit_weekly import detector_de_record, leer_frontera_k
L21, L22, K, A = 3.929, 3.959, 18.9, 1e6
P = lambda t, l: C1 / (l**5 * (math.exp(C2 / (l * t)) - 1))
inv = lambda L, l: C2 / (l * math.log(C1 / (L * l**5) + 1))
fr = leer_frontera_k()
filas = []
for vol in bp.VOLS:
    recs = json.load(open(bp.DATA / f"{vol}.json", encoding="utf-8"))["records"]
    for r in recs:
        if "MODIS" not in (r.get("sensor") or ""): continue
        if (r.get("datetime_utc") or "")[:10] < fr: continue
        if detector_de_record(r, fr) != "K": continue
        pc = r.get("primary_cluster") or {}
        if (pc.get("vrp_mw") or 0) <= 0: continue
        Fs, ws, tbks, sat = [], [], [], 0
        for p in r.get("anomaly_pixels") or []:
            v, bt = p["vrp_mw"], p["bt_k"]
            if v < 0.005: continue
            Lbg = P(bt, L21) - v * 1e6 / (K * A)
            if Lbg <= 0: continue
            tbk = inv(Lbg, L21)
            lp = L22 if bt < 331 else L21
            if bt >= 331: sat += 1
            Fi = (P(bt, lp) - P(tbk, L22)) / (P(bt, L21) - Lbg)
            Fs.append(Fi); ws.append(v); tbks.append(tbk)
        if not Fs: continue
        Fw = sum(f * w for f, w in zip(Fs, ws)) / sum(ws)
        filas.append(dict(vol=vol, dt=r["datetime_utc"], pc=pc.get("vrp_mw"), npix=pc.get("n_pixels"),
                          spm=bool(pc.get("single_pixel_mode")), focal=pc.get("focal_magnitude"),
                          d9=bool(pc.get("d9_capped")), kl=r.get("diag_L_bg_local_w_m2_sr_um") is not None,
                          t_bg=r.get("t_bg_k"), tbk_min=min(tbks), tbk_max=max(tbks), F_top=Fs[0],
                          F_w=Fw, F_min=min(Fs), F_max=max(Fs), n_ap=len(Fs), n_sat=sat,
                          vrp_scene=r.get("vrp_mw")))
for f in filas:
    print(f"{f['vol'][:10]:10s} {f['dt'][:16]} pc={f['pc']:7.3f} n={f['npix']} spm={int(f['spm'])} kl={int(f['kl'])} d9={int(f['d9'])} "
          f"tbg={f['t_bg']} tbk=[{f['tbk_min']:.1f},{f['tbk_max']:.1f}] Ftop={f['F_top']:.4f} Fw={f['F_w']:.4f} "
          f"F=[{f['F_min']:.4f},{f['F_max']:.4f}] nap={f['n_ap']} sat={f['n_sat']}")
ok = [f for f in filas if not f["d9"]]
print("n", len(filas), "sin d9", len(ok))
print("F_top mediana", round(st.median(f["F_top"] for f in ok), 4), "min", round(min(f["F_top"] for f in ok), 4), "max", round(max(f["F_top"] for f in ok), 4))
print("F_w   mediana", round(st.median(f["F_w"] for f in ok), 4), "min", round(min(f["F_w"] for f in ok), 4), "max", round(max(f["F_w"] for f in ok), 4))
print("F pixel global min/max", round(min(f["F_min"] for f in ok), 4), round(max(f["F_max"] for f in ok), 4))
json.dump(filas, open(r"D:/vrp-trabajo/temporales/s157-lambda/verificador/f_por_pixel.json", "w"), indent=1)
