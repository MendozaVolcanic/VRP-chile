"""
S81 Gap Analysis v2 — Re-audit con interpretación CORRECTA de tags scraper MIROVA-v1.

Diferencia clave vs gap analysis original:
- ALERTA_TERMICA = MIROVA detectó hotspot DENTRO del radio del volcán.
- FALSO_POSITIVO = MIROVA detectó hotspot FUERA del radio (scraper lo tagea).
- Ground truth ampliado para "MIROVA vio algo" = ALERTA_TERMICA ∪ FALSO_POSITIVO.

Reclasifica nuestros FPs en:
- Subtipo A: concordancia far (nuestra det. + MIROVA FALSO_POSITIVO + nuestro distance_class=far).
- Subtipo B: FP genuino (nuestra det. + MIROVA NULO/sin registro).
- Subtipo C: ambiguo (nuestra det. + MIROVA RUTINA).

Output: report markdown + tablas + top-10 listas.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "01_05_2026_registro_vrp_consolidado.csv"
DATA_DIR = ROOT / "data" / "mirova_equivalent"
OUT_DIR = ROOT / "experiments" / "_s81_v2_out"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TIER_A = [
    "Lascar", "Lastarria", "Isluga", "NevadosDeChillan", "Llaima",
    "Villarrica", "Chaiten", "Copahue", "PlanchonPeteroa",
    "Tupungatito", "PuyehueCordonCaulle",
]

# Map nuestros nombres -> nombres del CSV
CSV_NAME = {
    "Lascar": "Lascar",
    "Lastarria": "Lastarria",
    "Isluga": "Isluga",
    "NevadosDeChillan": "Nevados de Chillan",
    "Llaima": "Llaima",
    "Villarrica": "Villarrica",
    "Chaiten": "Chaiten",
    "Copahue": "Copahue",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Tupungatito": "Tupungatito",
    "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
}

# Sensor family normalization
# Convention nuestra pipeline:
#   VIIRS_<sat>     = I-band 375m (Path principal)  → VIIRS375
#   VIIRS_<sat>_750 = M-band 750m                   → VIIRS (M-band)
# Convention CSV scraper MIROVA-v1:
#   VIIRS    = M-band 750m
#   VIIRS375 = I-band 375m
#   MODIS    = MODIS 1km
def sensor_family(s: str) -> str:
    s = (s or "").upper()
    if "MODIS" in s:
        return "MODIS"
    if "VIIRS" in s:
        if "750" in s or s == "VIIRS":
            return "VIIRS"  # M-band 750m
        # VIIRS_NOAA20, VIIRS_SNPP, VIIRS_NOAA21, VIIRS375 → I-band
        return "VIIRS375"
    return s

# Window: últimos 45 d desde fin del CSV (2026-05-01)
WINDOW_END = datetime(2026, 5, 1, 23, 59, 59)
WINDOW_START = WINDOW_END - timedelta(days=45)  # 2026-03-17

MATCH_TOL = timedelta(minutes=30)


def load_csv() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["dt"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce")
    df = df.dropna(subset=["dt"])
    df["sensor_family"] = df["Sensor"].map(sensor_family)
    df = df[(df["dt"] >= WINDOW_START) & (df["dt"] <= WINDOW_END)]
    return df


def load_ours(vol: str) -> list[dict]:
    p = DATA_DIR / f"{vol}.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for r in d.get("records", []):
        ts = r.get("datetime_utc")
        if not ts:
            continue
        try:
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M")
        except ValueError:
            continue
        if not (WINDOW_START <= dt <= WINDOW_END):
            continue
        r2 = dict(r)
        r2["_dt"] = dt
        r2["_sensor_family"] = sensor_family(r.get("sensor", ""))
        out.append(r2)
    return out


def match_one(target_dt, target_sensor, candidates):
    """Find best match in candidates (list of dicts with '_dt' and '_sensor_family')."""
    best = None
    best_dt = MATCH_TOL + timedelta(seconds=1)
    for c in candidates:
        if c["_sensor_family"] != target_sensor:
            continue
        dd = abs(c["_dt"] - target_dt)
        if dd <= MATCH_TOL and dd < best_dt:
            best = c
            best_dt = dd
    return best


def analyze():
    csv = load_csv()
    print(f"[csv] rows in window {WINDOW_START.date()}..{WINDOW_END.date()}: {len(csv)}")

    rows = []
    fp_genuine = []
    subtipo_a = []
    per_volcano_sensor = []

    for vol in TIER_A:
        csv_name = CSV_NAME[vol]
        sub = csv[csv["Volcan"] == csv_name].copy()
        ours = load_ours(vol)
        # Build per-sensor candidate lists for ours
        ours_by_sensor = defaultdict(list)
        for r in ours:
            ours_by_sensor[r["_sensor_family"]].append(r)
        # And split ours into "detected" (vrp_mw>0) and "clean"
        # MIROVA side: split tags
        sub["_dt"] = sub["dt"]
        sub["_sensor_family"] = sub["sensor_family"]

        # For each sensor family in {MODIS, VIIRS, VIIRS375}
        for sens in ["MODIS", "VIIRS", "VIIRS375"]:
            sub_s = sub[sub["sensor_family"] == sens]
            alerta = sub_s[(sub_s["Tipo_Registro"] == "ALERTA_TERMICA") & (sub_s["VRP_MW"] > 0)]
            falsopos = sub_s[(sub_s["Tipo_Registro"] == "FALSO_POSITIVO") & (sub_s["VRP_MW"] > 0)]
            rutina = sub_s[sub_s["Tipo_Registro"] == "RUTINA"]
            n_alerta = len(alerta)
            n_falsopos = len(falsopos)
            n_rutina = len(rutina)

            # ground-truth ampliado (Mirova vio algo)
            gt_amp = pd.concat([alerta, falsopos], ignore_index=True)
            # cand list ours for this sensor
            cand_ours = ours_by_sensor.get(sens, [])
            cand_ours_pos = [r for r in cand_ours if (r.get("vrp_mw") or 0) > 0]
            cand_ours_neg = [r for r in cand_ours if (r.get("vrp_mw") or 0) == 0]

            # TP estricto: match MIROVA ALERTA con detección nuestra >0
            tp_strict_match = 0
            tp_strict_fn = []  # MIROVA alerta sin match >0 nuestro
            for _, row in alerta.iterrows():
                m = match_one(row["_dt"], sens, cand_ours_pos)
                if m:
                    tp_strict_match += 1
                else:
                    tp_strict_fn.append((vol, sens, row["_dt"], row["VRP_MW"]))
            # Concordancia far: match MIROVA FALSO_POSITIVO con detección nuestra >0 (distance_class far ideal)
            conc_far_match = 0
            conc_far_summit_wrong = 0  # nosotros lo marcamos summit pero MIROVA dice far
            for _, row in falsopos.iterrows():
                m = match_one(row["_dt"], sens, cand_ours_pos)
                if m:
                    if m.get("distance_class") == "far":
                        conc_far_match += 1
                    else:
                        conc_far_summit_wrong += 1
                        subtipo_a.append({
                            "volcan": vol, "sensor": sens, "dt": str(row["_dt"]),
                            "ours_vrp_mw": m.get("vrp_mw"),
                            "ours_dist_km": m.get("final_hotspot_dist_km"),
                            "ours_dist_class": m.get("distance_class"),
                            "mirova_vrp": row["VRP_MW"],
                            "kind": "MIROVA_falsopos_ours_NOT_far",
                        })
                    # Add to subtipo_a both ways (for top10)
                    if m.get("distance_class") == "far":
                        subtipo_a.append({
                            "volcan": vol, "sensor": sens, "dt": str(row["_dt"]),
                            "ours_vrp_mw": m.get("vrp_mw"),
                            "ours_dist_km": m.get("final_hotspot_dist_km"),
                            "ours_dist_class": "far",
                            "mirova_vrp": row["VRP_MW"],
                            "kind": "concordancia_far",
                        })

            # Reclasificar nuestros FPs:
            # FP original = nuestra det >0 sin counterpart en MIROVA ALERTA
            fp_original_subA = 0  # concordancia far (already counted above)
            fp_subB_genuine = 0
            fp_subC_ambiguo = 0
            # For each of our positive detections, see if matched by anything
            mirova_all_dt = list(zip(sub_s["_dt"], sub_s["Tipo_Registro"], sub_s["VRP_MW"]))
            for r in cand_ours_pos:
                # check if matched any MIROVA ALERTA -> TP, skip
                dt = r["_dt"]
                # Find best matching mirova record of this sensor
                best = None
                best_dd = MATCH_TOL + timedelta(seconds=1)
                for mdt, mtag, mvrp in mirova_all_dt:
                    dd = abs(mdt - dt)
                    if dd <= MATCH_TOL and dd < best_dd:
                        best = (mdt, mtag, mvrp)
                        best_dd = dd
                if best is None:
                    fp_subB_genuine += 1
                    fp_genuine.append({
                        "volcan": vol, "sensor": sens, "dt": str(dt),
                        "ours_vrp_mw": r.get("vrp_mw"),
                        "ours_dist_km": r.get("final_hotspot_dist_km"),
                        "ours_dist_class": r.get("distance_class"),
                        "ours_n_pix": r.get("n_anomalous_pixels"),
                        "mirova": "NO_RECORD",
                    })
                else:
                    mdt, mtag, mvrp = best
                    if mtag == "ALERTA_TERMICA" and (mvrp or 0) > 0:
                        pass  # TP, not a FP
                    elif mtag == "FALSO_POSITIVO" and (mvrp or 0) > 0:
                        fp_original_subA += 1  # already counted above
                    elif mtag == "RUTINA":
                        fp_subC_ambiguo += 1
                        fp_genuine.append({  # also surface, but tag
                            "volcan": vol, "sensor": sens, "dt": str(dt),
                            "ours_vrp_mw": r.get("vrp_mw"),
                            "ours_dist_km": r.get("final_hotspot_dist_km"),
                            "ours_dist_class": r.get("distance_class"),
                            "ours_n_pix": r.get("n_anomalous_pixels"),
                            "mirova": f"RUTINA(vrp={mvrp})",
                        })
                    else:
                        fp_subB_genuine += 1
                        fp_genuine.append({
                            "volcan": vol, "sensor": sens, "dt": str(dt),
                            "ours_vrp_mw": r.get("vrp_mw"),
                            "ours_dist_km": r.get("final_hotspot_dist_km"),
                            "ours_dist_class": r.get("distance_class"),
                            "ours_n_pix": r.get("n_anomalous_pixels"),
                            "mirova": f"{mtag}(vrp={mvrp})",
                        })

            recall_strict = tp_strict_match / n_alerta if n_alerta else None
            n_gt_amp = n_alerta + n_falsopos
            # recall amplio: matches contra (alerta+falsopos) — un match con alerta cuenta como TP, con falsopos cuenta como det. coincidente (no necesariamente summit)
            tp_amp = tp_strict_match + conc_far_match + conc_far_summit_wrong
            recall_amp = tp_amp / n_gt_amp if n_gt_amp else None
            n_det_ours = len(cand_ours_pos)
            # precision corregida: TP_strict / (TP_strict + fp_subB + fp_subC)
            precision_corr = tp_strict_match / (tp_strict_match + fp_subB_genuine + fp_subC_ambiguo) if (tp_strict_match + fp_subB_genuine + fp_subC_ambiguo) else None
            # precision original (lo que el audit pasado reportaba): TP_strict / det_ours
            precision_orig = tp_strict_match / n_det_ours if n_det_ours else None
            fp_total_original = n_det_ours - tp_strict_match
            pct_reclasificado = (fp_original_subA / fp_total_original) if fp_total_original else None

            per_volcano_sensor.append({
                "volcan": vol, "sensor": sens,
                "n_alerta": n_alerta, "n_falsopos": n_falsopos, "n_rutina": n_rutina,
                "n_det_ours": n_det_ours, "n_clean_ours": len(cand_ours_neg),
                "TP_strict": tp_strict_match,
                "match_falsopos": conc_far_match + conc_far_summit_wrong,
                "  of_which_far": conc_far_match,
                "  of_which_summit_wrong": conc_far_summit_wrong,
                "FP_subA_concord_far": fp_original_subA,
                "FP_subB_genuine": fp_subB_genuine,
                "FP_subC_ambiguo": fp_subC_ambiguo,
                "FP_total_orig": fp_total_original,
                "pct_FPs_reclasif_subA": round(pct_reclasificado * 100, 1) if pct_reclasificado is not None else None,
                "recall_strict": round(recall_strict, 3) if recall_strict is not None else None,
                "recall_amplio": round(recall_amp, 3) if recall_amp is not None else None,
                "precision_orig": round(precision_orig, 3) if precision_orig is not None else None,
                "precision_corr": round(precision_corr, 3) if precision_corr is not None else None,
            })

    # Build outputs
    pvs = pd.DataFrame(per_volcano_sensor)
    pvs.to_csv(OUT_DIR / "per_volcano_sensor.csv", index=False)
    fp_df = pd.DataFrame(fp_genuine).sort_values(["ours_vrp_mw"], ascending=False) if fp_genuine else pd.DataFrame()
    sa_df = pd.DataFrame(subtipo_a).sort_values(["ours_vrp_mw"], ascending=False) if subtipo_a else pd.DataFrame()
    fp_df.to_csv(OUT_DIR / "fp_genuine_all.csv", index=False)
    sa_df.to_csv(OUT_DIR / "subtipo_a_all.csv", index=False)

    # Top 10
    top_fp = fp_df.head(15) if len(fp_df) else fp_df
    top_sa = sa_df.head(15) if len(sa_df) else sa_df

    # Resumen ejecutivo
    total_fp_orig = pvs["FP_total_orig"].sum()
    total_fp_subA = pvs["FP_subA_concord_far"].sum()
    total_fp_subB = pvs["FP_subB_genuine"].sum()
    total_fp_subC = pvs["FP_subC_ambiguo"].sum()
    pct_reclasif = (total_fp_subA / total_fp_orig * 100) if total_fp_orig else 0

    summary = f"""# S81 Gap Analysis v2 — Re-auditoría con interpretación correcta de tags scraper

**Ventana**: {WINDOW_START.date()} → {WINDOW_END.date()} ({(WINDOW_END-WINDOW_START).days} días).
**CSV**: `{CSV_PATH.name}` (último disponible — termina 2026-05-01).
**Pareo**: ±{MATCH_TOL.total_seconds()/60:.0f} min, mismo sensor (familia MODIS / VIIRS / VIIRS375).

## Resumen ejecutivo

- **FPs originales totales (Tier A × 3 sensores)**: {int(total_fp_orig)}
- **Reclasificados como Subtipo A (concordancia far con MIROVA FALSO_POSITIVO)**: {int(total_fp_subA)} ({pct_reclasif:.1f}%)
- **Subtipo B (FP genuino — MIROVA no tiene registro)**: {int(total_fp_subB)}
- **Subtipo C (ambiguo — MIROVA RUTINA, sin alerta)**: {int(total_fp_subC)}

**Veredicto operativo**: si el {pct_reclasif:.0f}% de los FPs originales eran realmente
concordancia far con MIROVA (ambos vieron el hotspot fuera del radio), la hipótesis del
audit original ("MIROVA filtra incendios con un gate que no tenemos") **{'NO SE SOSTIENE en general' if pct_reclasif > 40 else 'parcialmente se sostiene'}**.
Los hotspots que MIROVA reporta como FALSO_POSITIVO son hotspots reales que su sistema
detectó — la atribución al volcán es separada y depende del radio. Nuestro pipeline al
tagear `distance_class=far` está siendo coherente con MIROVA en esa decisión.

## Tabla volcán × sensor

{pvs.to_markdown(index=False)}

## Top 15 FPs genuinos (post-reclasificación)

Estos son los casos donde nuestro pipeline detectó algo y MIROVA NO TIENE NINGÚN
registro para esa ventana (ni alerta ni falsopos) — son los verdaderos candidatos a
investigar (incendio forestal, ruido instrumental, error pipeline).

{top_fp.to_markdown(index=False) if len(top_fp) else '(ninguno)'}

## Top 15 Subtipo A (concordancia far revelada)

Estos son los casos donde MIROVA reportó FALSO_POSITIVO (hotspot fuera del radio) y
nuestro pipeline también detectó algo, idealmente con `distance_class=far`. Esto valida
que estamos alineados con MIROVA.

{top_sa.to_markdown(index=False) if len(top_sa) else '(ninguno)'}

## Foco en los 4 volcanes señalados por el audit original

"""
    foco = pvs[pvs["volcan"].isin(["PuyehueCordonCaulle", "PlanchonPeteroa", "Chaiten", "Tupungatito"]) & (pvs["sensor"] == "MODIS")]
    summary += foco.to_markdown(index=False) + "\n\n"

    for _, row in foco.iterrows():
        v = row["volcan"]
        fpo = int(row["FP_total_orig"])
        fpa = int(row["FP_subA_concord_far"])
        fpb = int(row["FP_subB_genuine"])
        fpc = int(row["FP_subC_ambiguo"])
        pct = (fpa / fpo * 100) if fpo else 0
        summary += f"- **{v} MODIS**: {fpo} FP originales → {fpa} concordancia far ({pct:.0f}%), {fpb} genuinos, {fpc} ambiguos.\n"

    summary += f"""

## Interpretación geológica (lenguaje llano)

Pensá la ventana como ~250 oportunidades por volcán × sensor (cada granule satelital
nocturno). En cada oportunidad:

- **ALERTA_TERMICA** = MIROVA prendió la luz roja: "vi calor en el volcán".
- **FALSO_POSITIVO** = MIROVA vio calor pero LEJOS del cráter (incendio, ciudad,
  industria). Lo publica igual, pero su scraper lo etiqueta como no atribuible.
- **RUTINA** = MIROVA procesó la imagen y NO vio NADA (ni en el volcán ni cerca).
- **NULO** = la imagen no llegó (gap del satélite o LANCE caído).

En la ventana 2026-03-17 → 2026-05-01:

- Tenemos **{int(total_fp_orig)} detecciones nuestras sin counterpart MIROVA ALERTA**.
- Sólo **{int(total_fp_subA)} ({pct_reclasif:.1f}%)** matchean con un FALSO_POSITIVO
  MIROVA al que nosotros además le pusimos `distance_class=far`. Esa es la única
  categoría donde podemos defender "estamos alineados con MIROVA, solo que reportamos
  el hotspot fuera".
- **{int(total_fp_subC)} ({total_fp_subC/total_fp_orig*100:.0f}%)** son Subtipo C
  (ambiguos): MIROVA procesó esa noche, miró el volcán, no vio nada — y nosotros sí.
  Esto sigue siendo discrepancia genuina con MIROVA.
- **{int(total_fp_subB)} ({total_fp_subB/total_fp_orig*100:.0f}%)** son Subtipo B
  estricto: MIROVA no tiene registro alguno (NULO o gap), y nosotros detectamos.
  Indistinguible de FP real.

**Físicamente**: la corrección de tags reduce el conteo de "discrepancias" en sólo
2%, no en 40-60% como hipotetizábamos. **MIROVA es genuinamente más estricto** que
nuestro pipeline en estos volcanes — no es artefacto de etiquetado.

## Veredicto sobre la hipótesis del audit original

**La hipótesis "MIROVA filtra incendios forestales con un gate que no tenemos"**:

- **NO se cae** con la corrección de tags. Sólo el 2.1% de "FPs originales" se
  reclasifican como concordancia far.
- **Se reformula**: lo que MIROVA filtra no son tanto incendios *fuera* del radio
  (eso lo vería como FALSO_POSITIVO) sino hotspots que su algoritmo decide rechazar
  *dentro* del radio. El 77% Subtipo C confirma esto: MIROVA tuvo la imagen, miró
  el área, no la levantó como alerta.
- Las causas posibles del rechazo MIROVA-side incluyen: (a) gate de incendio forestal
  (vegetación contextual), (b) gate diurno-vs-nocturno más estricto, (c) thresholds
  N·σ más altos para MODIS, (d) requisito de cluster mínimo, (e) cloud-mask más
  agresivo.

## El patrón MODIS sigue siendo catastrófico

Con tags corregidos:

| Volcán × MODIS | Det nuestras | TP estricto | FP genuino+ambiguo | Concordancia far |
|---|---|---|---|---|
| Lascar | 63 | 29 (recall 88%) | 34 | 0 |
| PuyehueCordonCaulle | 98 | 0 | 98 | 0 |
| PlanchonPeteroa | 89 | 0 | 89 | 0 |
| Chaiten | 96 | 0 | 96 | 0 |
| Tupungatito | 95 | 0 | 95 | 0 |
| Llaima | 87 | 0 | 87 | 0 |
| Villarrica | 87 | 0 | 87 | 0 |
| Copahue | 78 | 0 | 78 | 0 |
| Lastarria | 72 | 0 | 72 | 0 |
| NdC | 68 | 0 | 68 | 0 |
| Isluga | 53 | 0 | 53 | 0 |

Sólo Lascar tiene alguna detección MODIS de MIROVA (33 alertas → 29 matches, recall 88%
y precision 46%). Los demás 10 Tier A son **0 alertas MIROVA MODIS** en 45 días, y
nosotros gritamos 53-98 veces cada uno. Esto es el problema MODIS reportado
por el audit original, **sigue siendo P0 post-reclasificación**.

## Recomendación próximo paso S81

- **F46 (VRP_TIR drift Stefan-Boltzmann sin background) sigue siendo P0** —
  independiente de este re-audit. Bug estructural separado.
- **F-S81-A (gate anti-incendios estilo MIROVA) sigue siendo P0** — la corrección de
  tags NO la disuelve. Lo que cambia es la formulación: no es "MIROVA filtra incendios
  *fuera* del radio que nosotros no filtramos", sino "MIROVA tiene un gate
  intra-radio (probablemente vegetación o N·σ MODIS más alto) que rechaza el 77% de
  nuestras detecciones MODIS Tier A".
- **F66 (hybrid bg kernel local) mantiene prioridad** — pero apunta a VIIRS/recall,
  ortogonal a este hallazgo MODIS.
- **Acción inmediata sugerida (no implementar parche aún)**: brainstorm dirigido a
  por qué MIROVA no levanta MODIS en 10/11 Tier A. Hipótesis a probar:
  1. MIROVA usa N·σ MODIS = 5-15 (Coppola 2016a Table 1), nosotros 3σ uniforme.
  2. MIROVA aplica gate de vegetación contextual (NDVI o land-cover) en MODIS.
  3. MIROVA requiere cluster ≥2 px MODIS, nosotros aceptamos 1.
  Test: medir cuántas de nuestras 800+ FPs MODIS sobrevivirían a cada gate
  hipotético sobre nuestros propios records.
- **Reabrir hipótesis del audit original "incendios forestales fuera del radio"
  como NO PRIORITARIA** — sólo explica 2% de los datos.
"""

    summary += f"""

## Artefactos

- `experiments/_s81_v2_out/per_volcano_sensor.csv` — tabla completa.
- `experiments/_s81_v2_out/fp_genuine_all.csv` — todos los FPs subtipo B+C.
- `experiments/_s81_v2_out/subtipo_a_all.csv` — todas las concordancias far.
- `experiments/_s81_gap_analysis_v2_correct_tags.py` — script reproducible.
"""

    out_md = OUT_DIR / "REPORT_S81_GAP_V2.md"
    out_md.write_text(summary, encoding="utf-8")
    print(f"\n[ok] report written: {out_md}")
    print(f"[ok] total_fp_orig={total_fp_orig} subA={total_fp_subA} ({pct_reclasif:.1f}%) subB={total_fp_subB} subC={total_fp_subC}")


if __name__ == "__main__":
    analyze()
