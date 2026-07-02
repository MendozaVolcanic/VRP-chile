"""
profile.py — active VRP-Chile detection profile loader.

Loads one YAML file from pipeline/profiles/ and exposes its values as
module-level constants that the processor modules import. The active
profile is selected via the VRP_PROFILE environment variable, which
run_pipeline.py sets from its --profile command-line flag BEFORE any
pipeline module is imported.

Default profile: mirova_equivalent (operational).

Usage from a processor module:
    from pipeline.profile import ANOMALY_THRESHOLD_K, N_SIGMA_MIR, ...

Usage from run_pipeline.py:
    os.environ["VRP_PROFILE"] = args.profile  # BEFORE importing pipeline
    from pipeline import process_viirs  # now loads with the selected profile
"""

import os
import sys
import yaml
from pathlib import Path


PROFILES_DIR = Path(__file__).parent / "profiles"
DEFAULT_PROFILE = "mirova_equivalent"
# S24: discovery dinámico — un profile válido es cualquier YAML en profiles/.
# Antes era hardcoded duplicado en run_pipeline.py argparse choices, drift
# generaba bug invisible (S24 A/B P3.1 falló 8/8 jobs por profile no en lista).
VALID_PROFILES = {p.stem for p in PROFILES_DIR.glob("*.yaml")}


def _load_profile() -> dict:
    name = os.environ.get("VRP_PROFILE", DEFAULT_PROFILE)
    if name not in VALID_PROFILES:
        raise ValueError(
            f"VRP_PROFILE={name!r} is not a known profile. "
            f"Valid: {sorted(VALID_PROFILES)}"
        )
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Profile YAML not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # F31 S75 — soporte `extends: <parent_profile>` para herencia simple.
    # Útil para perfiles experimentales que clonan operacional + cambian 1-2
    # flags (ej: experimental_lowT extends mirova_equivalent + activa
    # enable_vrptir_aveni). Merge deep: child overrides parent al mismo key.
    if isinstance(cfg, dict) and "extends" in cfg:
        parent_name = cfg.pop("extends")
        parent_path = PROFILES_DIR / f"{parent_name}.yaml"
        if not parent_path.exists():
            raise FileNotFoundError(
                f"Profile '{name}' extends '{parent_name}' but parent YAML not found: {parent_path}"
            )
        with open(parent_path, "r", encoding="utf-8") as fp:
            parent_cfg = yaml.safe_load(fp)
        def _deep_merge(base, override):
            if isinstance(base, dict) and isinstance(override, dict):
                merged = dict(base)
                for k, v in override.items():
                    merged[k] = _deep_merge(merged.get(k), v) if k in merged else v
                return merged
            return override
        cfg = _deep_merge(parent_cfg, cfg)

    cfg["_name"] = name
    return cfg


_cfg = _load_profile()

# --- Profile identity ---
PROFILE_NAME: str = _cfg["_name"]

# --- Detection thresholds ---
_t = _cfg["thresholds"]
ANOMALY_THRESHOLD_K: float = float(_t["anomaly_threshold_k"])
TIR_THRESHOLD_K: float = float(_t["tir_threshold_k"])
N_SIGMA_MIR: float = float(_t["n_sigma_mir"])
N_SIGMA_TIR: float = float(_t["n_sigma_tir"])
N_SIGMA: float = N_SIGMA_MIR  # alias for process_modis.py compatibility
VENT_THRESHOLD_K: float = float(_t["vent_threshold_k"])
N_SIGMA_VENT: float = float(_t["n_sigma_vent"])
NTI_K1_NIGHT: float = float(_t["nti_k1_night"])
NTI_BT_SANITY_K: float = float(_t["nti_bt_sanity_k"])
CLOUD_MASK_BT_K: float = float(_t.get("cloud_mask_bt_k", 260.0))
MAX_SIGMA_COMPONENT_K: float = float(_t.get("max_sigma_component_k", 7.0))
# S12 F1b: cap on sigma contribution for VENT-path threshold. Prevents
# orographically-noisy backgrounds (Tupungatito, Lastarria) from inflating
# the effective gate beyond real sub-pixel signal magnitude (1–3 K).
MAX_VENT_SIGMA_CONTRIB_K: float = float(_t.get("max_vent_sigma_contrib_k", 3.0))
# Session 12: configurable Path C sigma and MODIS vent threshold
NTI_REL_N_SIGMA: float = float(_t.get("nti_rel_n_sigma", 3.0))
NTI_REL_MIN_FLOOR: float = float(_t.get("nti_rel_min_floor", 0.005))
# S15 P3.2: dNTI contextual 8-vecinos (Coppola 2016a SP 426.5).
# Pixel hot si (NTI_pixel - median(NTI_8_vecinos)) > C1 AND bt > t_bg + sanity.
DNTI_CONTEXTUAL_C1: float = float(_t.get("dnti_contextual_c1", 0.003))
# S15 P3.1: dual-ROI thresholds (Coppola 2016a Table 2).
# summit (dist <= inner_radius_km): C1_SUMMIT sensible.
# scene  (dist >  inner_radius_km): C1_SCENE estricto (3.3x summit).
DNTI_CONTEXTUAL_C1_SUMMIT: float = float(_t.get("dnti_contextual_c1_summit", 0.003))
DNTI_CONTEXTUAL_C1_SCENE: float = float(_t.get("dnti_contextual_c1_scene", 0.010))
MODIS_VENT_THRESHOLD_K: float = float(_t.get("modis_vent_threshold_k", VENT_THRESHOLD_K))
MODIS_VENT_VRP_FLOOR_MW: float = float(_t.get("modis_vent_vrp_floor_mw", 0.0))
# S23 T18: P95_VENT_EXCLUSION_KM antes hardcoded en process_*.py.
# Margen alrededor del vent_radius_km para excluir el cráter del cómputo
# del percentil 95 local (sino contaminaría con detecciones reales).
# Defaults: MODIS 5km (pixels 1km), VIIRS 750m 4km (pixels 750m).
P95_VENT_EXCLUSION_MODIS_KM: float = float(_t.get("p95_vent_exclusion_modis_km", 5.0))
P95_VENT_EXCLUSION_VIIRS750_KM: float = float(_t.get("p95_vent_exclusion_viirs750_km", 4.0))
# S12 2026-04-15: piso VRP por sensor. Aplicado en store.py después de
# unificar vrp_mw = max(eruption, vent). Cualquier VRP por debajo del
# piso se lleva a 0 (no-detección). Piso calibrado al mínimo MIROVA
# observado por sensor (inclusive, operador >=). Default 0.0 = sin piso.
# S12 E4: mínimo de pixeles calientes en el vent radius para declarar
# detección vent-path. Default 1 = comportamiento actual.
MIN_VENT_PIXELS: int = int(_t.get("min_vent_pixels", 1))
MIN_VRP_MW_VIIRS375: float = float(_t.get("min_vrp_mw_viirs375", 0.0))
MIN_VRP_MW_VIIRS750: float = float(_t.get("min_vrp_mw_viirs750", 0.0))
MIN_VRP_MW_MODIS: float = float(_t.get("min_vrp_mw_modis", 0.0))

# --- Background annulus geometry (km) ---
_bg = _cfg["background"]
BG_INNER_KM: float = float(_bg["inner_km"])
BG_OUTER_KM: float = float(_bg["outer_km"])

# --- Detection paths ---
_p = _cfg["paths"]
ENABLE_ERUPTION_PATH: bool = bool(_p["enable_eruption_path"])
ENABLE_VENT_PATH: bool = bool(_p["enable_vent_path"])
# Session 10: sensor-specific vent_path gate for MODIS (RF1 fix).
# Defaults to ENABLE_VENT_PATH for backward compatibility.
ENABLE_VENT_PATH_MODIS: bool = bool(_p.get("enable_vent_path_modis", ENABLE_VENT_PATH))
# Session 11: NTI-relative detection path (Path C) for weak fumarolic signals.
# When True, pixels passing nti > nti_bg + max(0.005, 3*sigma_nti) AND
# bt > t_bg + NTI_BT_SANITY_K are included in hot_mask_2d.
ENABLE_NTI_RELATIVE_PATH: bool = bool(_p.get("enable_nti_relative_path", False))
# S15 P3.2: dNTI contextual 8-vecinos (Path D). On = agregar al OR de
# hot_mask el gate contextual vs vecinos inmediatos. Default false para
# compatibilidad con profiles previos.
ENABLE_DNTI_CONTEXTUAL_PATH: bool = bool(_p.get("enable_dnti_contextual_path", False))
# S15 P3.1: dual-ROI (summit vs scene C1 distintos). On = Path D usa
# C1_SUMMIT cerca del vent y C1_SCENE lejos. Off = usa C1 unico (P3.2 solo).
ENABLE_DNTI_DUAL_ROI: bool = bool(_p.get("enable_dnti_dual_roi", False))
# S83 F-S81-A Fase 2: gate Path D MODIS intra-radio. On = mascarea
# dnti_ctx_hot fuera del inner_radius_km per-volcán (KMZ MIROVA oficial).
# Motivación: 99.5% FPs MODIS Tier A audit S81/S82 son Path D puro lejos
# del cráter; MIROVA tagged RUTINA en 98% de los casos → gate intra-ROI
# no replicado. Ver docs/F_S81_A_FASE1_DIAGNOSIS.md +
# docs/F_S81_A_FASE1B_SANITY_P95.md. Default false hasta validación A/B.
ENABLE_PATH_D_INTRA_RADIO_GATE: bool = bool(_p.get("enable_path_d_intra_radio_gate", False))
# S85 Fase B' (F-S81-B'): gate intra-radio sobre pixels NUEVOS del
# second_pass_recapture (`pipeline/detection_context.py:second_pass_adjacent`).
# Motivación: audit B0 (docs/R3_RESIDUAL_BY_PATH.md) mostró que 87.7% de los
# 106 R3 violators del operacional post-S84 NO tienen ningún path 1er pase
# activo. Volcanes con más R3 (NdC/Llaima/Copahue/PP) son los que más
# recapturan (NdC=1247, PP=776). El second pass no tiene restricción
# espacial (paper Coppola 2016a §347-356 no la exige) — recaptura cualquier
# pixel de la escena. En cirrus uniforme/glaciar parcialmente cálido,
# rescata ruido distribuido lejos del cono → arma cluster fuera del
# inner_radius → R3 violator.
# Sanity: 1332 ALERTAs MIROVA Tier A (CSV+OCR) caen 100% intra-radio
# (docs/F_S81_B_SANITY_VIIRS.md). Pérdida de TPs esperada = 0.
# El gate solo toca pixels NUEVOS del 2nd pass (los del 1er pase, intactos).
# Diseño completo: docs/F_S81_B_PRIME_SECOND_PASS_GATE.md. Default false
# hasta validación A/B (S85).
ENABLE_SECOND_PASS_INTRA_RADIO_GATE: bool = bool(_p.get("enable_second_pass_intra_radio_gate", False))
# S25: Path Test 1 integrated-ROI (Coppola 2015 Eq.1). Suma exceso de radiancia
# MIR sobre toda la ROI vent (default 3 km radio); detecta señales sub-pixel
# espacialmente extendidas que paths per-pixel pierden. POC S25 6/6 refs
# Villarrica disparan vs 0/6 con paths actuales.
ENABLE_TEST1_PATH: bool = bool(_p.get("enable_test1_path", False))
TEST1_K_SIGMA: float = float(_t.get("test1_k_sigma", 3.0))
TEST1_MIR_RELATIVE: float = float(_t.get("test1_mir_relative", 0.02))
TEST1_ROI_KM: float = float(_t.get("test1_roi_km", 3.0))
TEST1_INNER_RING_KM: float = float(_t.get("test1_inner_ring_km", 1.0))
# S105 — Test1 con FONDO LOCAL sobre NTI (realineamiento MIROVA Coppola 2024 Eq.13).
# Reemplaza el fondo del anillo entero por la mediana del NTI en un anillo local por
# píxel (in..out km) → cancela la estructura topográfica residual uniformemente, sin
# per-vol. Solo aplica junto a enable_test1_nti_integral. Ver design doc 2026-06-10.
TEST1_LOCAL_BG_RING_IN_KM: float = float(_t.get("test1_local_bg_ring_in_km", 0.5))
TEST1_LOCAL_BG_RING_OUT_KM: float = float(_t.get("test1_local_bg_ring_out_km", 1.5))
TEST1_MIN_LOCAL_BG_PIXELS: int = int(_t.get("test1_min_local_bg_pixels", 8))
# S26 Dual-ROI N·σ en eruption-path BT (Coppola 2016a Tabla 1).
# Path BT (eruption) usa thresholds N·σ distintos summit vs scene.
# - summit (dist <= inner_radius_km): N·σ_summit = 5 (sensible).
# - scene  (dist >  inner_radius_km): N·σ_scene  = 10 (estricto).
# Análogo a P3.1 P3.2 que ya aplican dual-ROI en Path D dNTI.
# Default OFF mientras se valida con A/B.
ENABLE_DUAL_ROI_BT: bool = bool(_p.get("enable_dual_roi_bt", False))
N_SIGMA_MIR_SUMMIT: float = float(_t.get("n_sigma_mir_summit", 5.0))
N_SIGMA_MIR_SCENE: float = float(_t.get("n_sigma_mir_scene", 10.0))

# S90 — parámetros DÍA MODIS (Coppola 2016a SP426.5 Tabla 1, verbatim; confirmado
# Coppola 2024 cap.11 Tabla 2). MIROVA procesa MODIS de día con umbrales más
# estrictos (no corrección solar): K1=-0.6, C1=0.02 (ambos ROIs), N·σ=15 (ambos).
# Solo se aplican cuando ENABLE_DAYTIME_MODIS=True y la escena es diurna; el
# default deja los valores listos pero el flag OFF los mantiene inertes.
NTI_K1_DAY: float = float(_t.get("nti_k1_day", -0.6))
N_SIGMA_MIR_DAY: float = float(_t.get("n_sigma_mir_day", 15.0))
DNTI_CONTEXTUAL_C1_DAY: float = float(_t.get("dnti_contextual_c1_day", 0.02))
# S90 — detección diurna MODIS (opt-in). OFF (default) = excluir diurno
# (comportamiento histórico "MIR solo nocturno"). ON = procesar MODIS diurno con
# params día + dejar pasar el gate de store.py. NO toca operacional hasta validar A/B.
ENABLE_DAYTIME_MODIS: bool = bool(_p.get("enable_daytime_modis", False))

# S32 P2 Driver B — Test 1 pixel-level filter (Coppola 2016a Tabla 1 aplicado
# a la mask Test 1 antes de sumar VRP). Cuando Test 1 integrated-ROI dispara,
# nuestra mask test1_hot incluye TODOS los pixels que contribuyeron al
# integrated trigger sin filtro N·σ pixel-level adicional. Resultado:
# clusters de 14-49 pixels suman VRP factor 8-30× MIROVA. Hipótesis (validada
# vía análisis agregación): MIROVA reporta sum solo de los pixels que
# además superan threshold dual-ROI 5σ summit / 10σ scene.
# Default OFF (backward compat). Activar en profile experimental para A/B.
ENABLE_TEST1_PIXEL_FILTER: bool = bool(_p.get("enable_test1_pixel_filter", False))

# S99 Candidato B — recorte de compacidad ESPACIAL del path Test 1.
# El Test 1 integrado-ROI (Coppola 2015) es un test de DETECCIÓN: su
# mask_contributing marca todo píxel del ROI sobre la mediana del fondo. Sobre el
# glaciar nevado de Tupungatito en invierno eso es el mosaico nieve/roca entero
# (anillo difuso 1-3 km) → VRP suma el halo → factor ~8-30× MIROVA (que reporta el
# foco compacto, ~0.2 MW estable). El discriminante correcto es ESPACIAL (foco vs
# halo), NO térmico (gate t_bg refutado A54/S86). spatial_core_filter conserva solo
# el foco compacto alrededor del pico de energía (TEST1_CORE_R_KM), conservando
# SIEMPRE el pico (guard anti-FN: un foco sub-píxel genuino como Villarrica lava lake
# nunca queda en VRP=0), + lava extendida real (bt ≥ TEST1_CORE_BT_EXT_K). Análogo en
# pipeline del Núcleo F5' display (S95). Default OFF (backward compat). Activar en
# perfil A/B para validación (A18) antes de adopción operacional (A45).
ENABLE_TEST1_SPATIAL_CORE: bool = bool(_p.get("enable_test1_spatial_core", False))
TEST1_CORE_R_KM: float = float(_t.get("test1_core_r_km", 0.75))
TEST1_CORE_BT_EXT_K: float = float(_t.get("test1_core_bt_ext_k", 295.0))

# S99 DF-1 — Candidato Eq.16 lava lake sub-píxel (Coppola 2024 §Lava lakes,
# Burgi-Coppola). Hallazgo dormido: compute_vrp_lava_lake_eq16 estaba construido +
# testeado (test_vrp_regimes_lava_lake.py) pero nunca conectado. Cuando la fuente es
# Test 1 y el volcán es lava lake magmático (gate per-vol `lava_lake_magmatic` en
# volcanoes.yaml, Villarrica), Wooster/suma está fuera de rango (señal sub-píxel con
# BT mezclado); Eq.15+16 despeja el área caliente asumiendo T_e y aplica
# Stefan-Boltzmann → magnitud estilo MIROVA. Default OFF; A/B S99 (la validación S54
# que el diseño 2026-05-17 dejó pendiente). T_e=1000K es el riesgo a calibrar.
ENABLE_TEST1_LAVA_LAKE_EQ16: bool = bool(_p.get("enable_test1_lava_lake_eq16", False))
TEST1_LAVA_LAKE_TE_K: float = float(_t.get("test1_lava_lake_te_k", 1000.0))
TEST1_LAVA_LAKE_EPS: float = float(_t.get("test1_lava_lake_eps", 0.95))

# S99 Candidato C — filtro CONTEXTUAL del path Test 1 (la vía más fiel a MIROVA).
# El Test 1 integrado marca por exceso vs la mediana del anillo regional (1-3 km), que
# sobre glaciar está sesgada fría → marca el halo nival entero. MIROVA marca por
# criterio contextual (Tests 2/3, SP426.5: anómalo = supera a sus 8 vecinos). Cuando
# ON: el VRP del Test 1 suma solo los píxeles que también están en dnti_ctx_hot
# (intersección) = comportamiento MIROVA. Es el mecanismo de flagging LITERAL (no un
# proxy espacial). Riesgo: cráter embebido en roca tibia puede caer → FN (medir en A/B
# con canario). Default OFF. Alternativas previas: fondo-local refutado S62/A19,
# per-pixel mata recall S99. Ver docs/S99_TEST1_AB_RESULTS.md.
ENABLE_TEST1_CONTEXTUAL_FILTER: bool = bool(_p.get("enable_test1_contextual_filter", False))

# S99 Candidato C+keep-peak (híbrido) — el filtro contextual da el mejor ratio pero
# borra el cráter embebido (31 FN Tupun, A/B S99). Con este flag, tras intersectar con
# dnti_ctx_hot se CONSERVA siempre el píxel pico (cráter = más caliente entre los Test1)
# → guard anti-FN. Combina flagging fiel MIROVA (corta halo) + recall garantizado.
# Requiere enable_test1_contextual_filter=True. Default OFF.
ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK: bool = bool(_p.get("enable_test1_contextual_keep_peak", False))

# S104 — co-validación NTI del Test1 integrado (realineamiento MIROVA). El Test1
# integra exceso de radiancia MIR ABSOLUTA → en volcanes nevados el terreno tibio
# de baja altitud (gradiente topográfico, NTI plano) supera la mediana del anillo,
# dispara el Test1 y arrastra el centroide ~9 km al N del cráter (Tupun/Villarrica/
# Llaima). Con este flag, solo los píxeles que también pasaron un path NTI relativo
# (Path C nti_rel ∪ Path D dNTI contextual) cuentan para disparar/integrar/posicionar
# (Coppola 2024 Eq.13). El valle tibio queda fuera; el lava lake real (que pasa dNTI)
# se conserva → recall protegido. Default OFF (A/B pendiente). Ver
# docs/AUDIT_S104_VIIRS_POSITION_OFFSET.md + docs/superpowers/specs/2026-06-09-*.
ENABLE_TEST1_NTI_COVALIDATION: bool = bool(_p.get("enable_test1_nti_covalidation", False))

# S104 V2 — el Test1 integra exceso de NTI (MIR−TIR) en vez de MIR absoluto. Cancela
# el gradiente topográfico de los nevados (V1 per-píxel refutada por A/B porque apaga
# el Test1; V2 valida por ground truth de 2 probes). Captura lava débil (NTI elevado
# en cráter, sin firma per-píxel) y rechaza el valle tibio (NTI plano). El VRP usa
# L_bg_mir sobre los píxeles NTI-elegidos. Default OFF (A/B pendiente, k_sigma a
# calibrar por SNR bajo). Ver docs/superpowers/specs/2026-06-09-*.md §V2.
ENABLE_TEST1_NTI_INTEGRAL: bool = bool(_p.get("enable_test1_nti_integral", False))
# S105 — fondo LOCAL sobre NTI en el Test1 (realineamiento MIROVA uniforme, Coppola
# 2024 Eq.13). Solo surte efecto junto a enable_test1_nti_integral. Cancela el sesgo
# topográfico residual del centroide del Test1 sin per-vol. Default OFF (A/B pendiente).
# Ver docs/superpowers/specs/2026-06-10-test1-local-bg-nti-design.md.
ENABLE_TEST1_LOCAL_BG_NTI: bool = bool(_p.get("enable_test1_local_bg_nti", False))

# S106 — ancla espacial honesta (design 2026-06-11). Solo POSICIÓN del record
# (final_hotspot_*), nunca magnitud/detección. OFF = comportamiento legacy.
ENABLE_HONEST_ANCHOR: bool = bool(_p.get("enable_honest_anchor", False))
# Destino de los records Test1-dominantes: "vent" (cráter, semántica integral)
# o "nti_peak" (píxel de NTI máximo del ROI — conserva fuente real offset).
HONEST_ANCHOR_TEST1_MODE: str = str(_p.get("honest_anchor_test1_mode", "vent"))
# S106 Fase 2 — espejos del ancla por sensor, flags SEPARADOS del de VIIRS375.
# MODIS NO puede activarse hasta resolver el fix de magnitud del destape (131
# records path-D first-pass inflados, design 2026-06-11 §4/§7 pre-comprometido).
ENABLE_HONEST_ANCHOR_MODIS: bool = bool(_p.get("enable_honest_anchor_modis", False))
# S111 D11 — gate del ancla honesta MODIS por señal-summit propia (design
# 2026-06-16). El override del ancla MODIS solo se aplica si hay ≥1 píxel del
# FIRST-PASS Tests 2&3 dentro del inner_radius (excluye la recaptura second-pass
# que el gate S85 preserva, A55). Default True: cuando el maestro se prenda, el
# gate evita promover el artefacto topográfico de NdC (A69). El brazo A/B
# "ancla-sin-gate" lo pone False para reproducir el ancla S106 puro.
ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE: bool = bool(
    _p.get("enable_honest_anchor_modis_first_pass_gate", True))
ENABLE_HONEST_ANCHOR_VIIRS750: bool = bool(_p.get("enable_honest_anchor_viirs750", False))

# S33 Driver B Phase 2 — filtro dual-ROI 5σ summit / 10σ scene aplicado a
# la mask final combinada (post-OR de todos los paths) antes de calcular
# n_anomalous_pixels, cluster_hotspots y vrp_mw.
# Phase 1 (test1_pixel_filter) cubre solo path Test 1; Phase 2 cubre TODOS
# los paths incluyendo Path D dNTI contextual (Coppola 2016a SP 426.5)
# que aporta los pixels marginales en Chaiten 14.5x y PCC 11.9x post-Phase 1.
# Default OFF (backward-compat). Activar en profile A/B para validación.
ENABLE_FINAL_PIXEL_FILTER: bool = bool(_p.get("enable_final_pixel_filter", False))

# S35 H8 — Filtro distance pixel-por-pixel en store.append_record.
# Cuando True, filtra anomaly_pixels in/out según volcano.radius_km en lugar
# del filtro all-or-nothing (basado en pixel más caliente individual).
# Bug pre-S35: cuando coexistían cluster summit + pixel lejano (incendio),
# el lejano "robaba" la decisión y se descartaba TODO. Reach 13.7% records
# Tier A en 30d. Fix sin cambio metodológico — alinea con MIROVA per-pixel.
# Default OFF (CLAUDE.md regla: requiere A/B antes de adopción operacional).
ENABLE_PIXEL_LEVEL_DISTANCE_FILTER: bool = bool(_p.get("enable_pixel_level_distance_filter", False))

# S33 D4 fix — Tupungatito 51% FNs sub-pixel: cuando Test 1 dispara, usar
# L_bg del anillo background global (5-25km) en lugar de test1_L_bg_local
# (ring 1-3km del cráter). En volcanes con geotermal crónico (Tupungatito,
# Lastarria fumarolas, Llaima cráter, Copahue lago ácido), el ring 1-3km
# está contaminado por el calor crónico — ΔL pixel-individual clip a 0 →
# suma=0 aunque Test 1 integrated SÍ haya detectado señal.
# Fallback a L_bg global anillo 5-25km (lejos del cráter) recupera la
# señal que el integrated trigger ya detectó.
# Default OFF (backward-compat). Activar via profile A/B.
ENABLE_TEST1_LBG_GLOBAL: bool = bool(_p.get("enable_test1_lbg_global", False))

# S111 Parte A (design 2026-06-16-test1-lowmag) — el Test1 gana final_hotspot_source
# (y con él el recompute de magnitud) cuando detectó summit pero el cluster rival es
# trivialmente débil (vrp < eps). Destapa la magnitud Muy Bajo (FN reactivación NdC
# 0.06 MW) que un cluster de 1 píxel con radiancia nula tapaba. Default OFF.
# SCOPE: solo VIIRS (process_viirs usa el helper resolve_test1_source_priority).
# process_modis NO está cubierto (mantiene su cascada inline) — el caso NdC es VIIRS375.
# INTERACCIÓN (verificación adversarial S111): NdC/Lascar/Lastarria tienen
# lbg_global_compatible=true + enable_test1_lbg_global ON → con este flag ON, su recompute
# usa el fondo GLOBAL (no local), que SOBRE-estima (~0.26 vs MIROVA 0.06) y puede inflar
# noches RUTINA. La calibración (Parte B) debe medir RUTINA inflada estratificada por
# esos 3 volcanes (criterio A66) antes de adoptar.
ENABLE_TEST1_PRIORITY_WEAK_CLUSTER: bool = bool(
    _p.get("enable_test1_priority_weak_cluster", False))
TEST1_WEAK_CLUSTER_EPS_MW: float = float(
    _t.get("test1_weak_cluster_eps_mw", 0.01))

# S112 Parte B Q3 (design 2026-06-16-test1-lowmag) — fondo de ANILLO INTERMEDIO para el
# recompute de magnitud del Test1. PRECEDENCIA sobre el global per-vol (S33 D4). En un
# cráter con calor crónico (NdC Nicanor, domo + lava reciente) el local 1-3 km está
# contaminado (→ exceso 0, FN) y el global 5-25 km es nieve fría de altura (→ exceso
# inflado ~4.4× MIROVA). El anillo intermedio [r_in, r_out] km queda fuera del halo
# crónico pero sobre terreno de altitud similar → fondo "Goldilocks". Default OFF
# (operacional inerte); se prueba en el A/B de calibración Muy Bajo (S112) contra las 6
# ALERTAS VIIRS375 NdC. NaN-safe: si el anillo no tiene min_pixels válidos cae al global/
# local (select_test1_effective_lbg). Helpers puros en pipeline/test1_integrated.py.
ENABLE_TEST1_INTERMEDIATE_BG: bool = bool(
    _p.get("enable_test1_intermediate_bg", False))
# (r_in_km, r_out_km) del anillo intermedio. 2-4 km y 3-5 km son los candidatos del A/B.
# Validación defensiva (S112 review LOW): un perfil mal escrito debe fallar con mensaje
# claro al cargar, no con un IndexError opaco dentro del loop de granules.
_ring_int = list(_t.get("test1_intermediate_bg_ring_km", [2.0, 4.0]))
if len(_ring_int) != 2 or not (float(_ring_int[0]) < float(_ring_int[1])):
    raise ValueError(
        "test1_intermediate_bg_ring_km debe ser [r_in, r_out] con r_in<r_out; "
        f"got {_ring_int}")
TEST1_INTERMEDIATE_BG_RING_KM: tuple[float, float] = (
    float(_ring_int[0]), float(_ring_int[1]))
TEST1_INTERMEDIATE_BG_MIN_PIXELS: int = int(
    _t.get("test1_intermediate_bg_min_pixels", 20))

# S27 MIROVA literal: flag para deshabilitar exclude_zones (parche nuestro).
# MIROVA NO usa máscaras geográficas (verificado vs Coppola 2016a, Coppola 2020,
# Laiolo 2026). Default true (operacional mantiene comportamiento actual);
# false en _mirova_literal para test A/B.
ENABLE_EXCLUDE_ZONES: bool = bool(_p.get("enable_exclude_zones", True))

# S37 H_D8_5 — algoritmo MIROVA literal (Coppola 2016a SP 426.5).
# Tres flags coordinados que activan el clon literal:
#   1. enable_eti_quadratic_scene: regresión cuadrática scene-wide
#      (NTI_bk = a·NTI²_app + b·NTI_app + c, eqs 4-5 paper) +
#      first pass Tests 2 ∧ 3 sobre dNTI/dETI contextuales.
#   2. enable_second_pass_adjacent: tras first pass, re-correr el cómputo
#      excluyendo active pixels (líneas 347-356 paper). Recapture pixels
#      marginales que el first pass perdió por contaminación de vecinos.
#   3. enable_sum_vrp_reporting: store.py reporta vrp_mw_sum_active y
#      hotspot_dist_km_furthest (cluster-agnostic). MIROVA no selecciona
#      cluster — suma TODOS los active pixels (eq 8). Resuelve D8.
# Default OFF en mirova_equivalent. Activar solo en _h_d8_5_full.yaml para A/B.
ENABLE_ETI_QUADRATIC_SCENE: bool = bool(_p.get("enable_eti_quadratic_scene", False))
ENABLE_SECOND_PASS_ADJACENT: bool = bool(_p.get("enable_second_pass_adjacent", False))
ENABLE_SUM_VRP_REPORTING: bool = bool(_p.get("enable_sum_vrp_reporting", False))

# C2 multiplicadores σ contextual para Tests 2 (dNTI) y 3 (dETI), por ROI.
# Coppola 2016a Tabla 1 noche: 5σ summit (ROI1) / 10σ scene (ROI2).
# Tests 2 y 3 usan los mismos valores pero los expongo separados para
# afinamientos futuros (paper deja libertad ROI-specific).
C2_DNTI_SUMMIT_NIGHT: float = float(_t.get("c2_dnti_summit_night", 5.0))
C2_DNTI_SCENE_NIGHT: float = float(_t.get("c2_dnti_scene_night", 10.0))
C2_DETI_SUMMIT_NIGHT: float = float(_t.get("c2_deti_summit_night", 5.0))
C2_DETI_SCENE_NIGHT: float = float(_t.get("c2_deti_scene_night", 10.0))

# S38 D8 fix verdadero — cluster selection vent-anchored.
# A/B H_D8_5 (S37) refutó "MIROVA suma todo" empíricamente: el path ETI
# cuadrático del paper produce subset redundante con paths existentes,
# NO mejora recall. Re-análisis caso canónico Puyehue lacolito + Lascar
# Salar: el problema no es detección (clusters relevantes sí se detectan)
# sino selection — nuestro pipeline elige el cluster con vrp_mw máximo,
# que típicamente es el más grande, NO el más relevante volcanológicamente.
# Fix S38: cuando ON, cluster_hotspots() ordena por vent-anchored
# (clusters dentro de inner_radius_km ganan sobre lejanos, entre cada
# grupo el más cercano gana). Combinado con enable_pixel_level_distance_filter
# (H8 fix existente OFF default) para filtrar pixels lejanos individuales.
# Default OFF en mirova_equivalent. Activar solo en _d8_vent_anchored.yaml.
ENABLE_VENT_ANCHORED_CLUSTERING: bool = bool(_p.get("enable_vent_anchored_clustering", False))

# S58 H_S57_LOCAL_KERNEL — flag para activar background local kernel 3x3.
#
# Coppola 2024 chapter L1129 literal: "T_bk is retrieved from the pixels
# adjacent to the hot one". MIROVA usa kernel local 3x3 alrededor de cada
# hot pixel, NO median del ring 5-25km como nuestro pipeline actual.
#
# Hipotesis S56-S57: median(ring 5-25km) sesgado hacia caliente en Villarrica
# por incluir lake/valley adyacentes (1.5-3K mas caliente que summit nevado).
# Result: pixels summit reales con vrp_individual=0 por clip ΔL.
#
# Cuando flag ON: per_pixel_vrp_mw usa L_bg_local computed con kernel 3x3
# alrededor de cada hot pixel (excluye otros hot + NaNs).
# Default OFF: comportamiento legacy (L_bg = bt_to_spectral_radiance(t_bg_i04)).
#
# Implementacion en pipeline/vrp_regimes.py:compute_local_background (S57).
# Tests sinteticos en tests/test_local_kernel_background.py (8 PASS).
ENABLE_LOCAL_KERNEL_BG: bool = bool(_p.get("enable_local_kernel_bg", False))

# S107 §2 / D12 destape — fondo LOCAL de magnitud: corona del cluster CONTIGUO
# (Coppola 2016a Eq.6 "around the active cluster"). Recomputa pc.vrp_mw del
# cluster primario con la media BT del anillo que rodea TODO el cluster (NO el
# kernel per-pixel compute_local_background, que re-infla los INTERIORES de un
# blob compacto — gap A48). Cura los ~134 inflados warm-scene sin tocar detección.
# Default OFF (flag-OFF + A/B antes de adoptar, A45). Gatea el destape del ancla
# MODIS. Helpers pipeline/vrp_regimes.py:cluster_corona_background +
# cluster_vrp_mw_with_bg. Tests tests/test_cluster_corona_magnitude.py. Design
# docs/superpowers/specs/2026-06-13-magnitud-modis-fondo-local-design.md.
ENABLE_LOCAL_CLUSTER_MAGNITUDE: bool = bool(_p.get("enable_local_cluster_magnitude", False))
LOCAL_CLUSTER_MAG_MODE: str = str(_p.get("local_cluster_mag_mode", "footprint"))  # "footprint" (V-B) | "ring" (V-A)
LOCAL_CLUSTER_MAG_RING_PX: int = int(_p.get("local_cluster_mag_ring_px", 1))
LOCAL_CLUSTER_MAG_MIN_CORONA: int = int(_p.get("local_cluster_mag_min_corona", 4))

# S109 §1 — magnitud NÚCLEO FOCAL/CONTEXTUAL del cluster MODIS. Restringe la suma
# de pc.vrp_mw a los píxeles contextualmente anómalos (dnti_ctx ∪ {pico}) del cluster
# YA seleccionado — el campo difuso topográfico (tibio uniforme, no anómalo vs sus 8
# vecinos = A69/D11) se cae; el foco discreto (cráter activo / lava / incendio) se
# conserva. Generaliza ctxpeak (VIIRS S100) a la magnitud del cluster eruption+test1.
# NO es fondo-local (no toca L_bg ni la radiancia per-pixel — solo SELECCIONA píxeles;
# guard A48). Cura los ~121 inflados MODIS donde MIROVA no publica MODIS (campo difuso,
# Coppola 2023 "insensitive to diffuse heat") y gatea el flip del ancla MODIS. Default
# OFF (flag-OFF + A/B antes de adoptar, A45). Helper vrp_regimes.cluster_focal_vrp_mw.
# Tests tests/test_focal_cluster_magnitude.py. Design
# docs/superpowers/specs/2026-06-14-magnitud-modis-nucleo-focal-design.md.
ENABLE_FOCAL_CLUSTER_MAGNITUDE: bool = bool(_p.get("enable_focal_cluster_magnitude", False))
FOCAL_CLUSTER_KEEP_PEAK: bool = bool(_p.get("focal_cluster_keep_peak", True))
# S112 — magnitud núcleo-focal portada a VIIRS750 (M13), frente A69/D11. process_viirs_mod.py
# era el ÚNICO path Test1 sin la cura (MODIS la tiene S109, VIIRS375 el contextual filter);
# su VRP al cráter está inflado 10-25× sobre MIROVA en los nevados por integrar el gradiente
# topográfico MIR sobre píxeles grandes (562.500 m²), EXCEPTO Lascar (foco real). Flag SEPARADO
# del global (que ya está ON para MODIS, #423) para mantener el port INERTE hasta su propio A/B
# con Lascar de canario (A45). Usa el mismo helper cluster_focal_vrp_mw + FOCAL_CLUSTER_KEEP_PEAK.
ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750: bool = bool(
    _p.get("enable_focal_cluster_magnitude_viirs750", False))

# S40 cleanup paths viejos — flag para desactivar bt_path_hot path.
# Análisis empírico S39 (records operacional 30d): bt_path_hot solo
# contribuye EXCLUSIVAMENTE en 0-6 records de 1846 TPs totales en 11 vol
# Tier A. Test 1 integrated-ROI (test1_hot) + dNTI contextual (dnti_ctx_hot)
# cubren prácticamente todas las detecciones. bt_path puede ser redundante.
# Default true para backward-compat. A/B desactivar en _no_bt_path.yaml
# y comparar recall delta. Si baja < 1pp → safe retirar del clon literal.
ENABLE_BT_PATH_HOT: bool = bool(_p.get("enable_bt_path_hot", True))

# S46 Drift #1a — Coppola 2016a SP426.5:298-300 dice que Test 1 K1 pixels
# se "discard (unsuitable) for further steps". Nuestro código actual los
# mete al hot_mask reportable vía nti_path_hot — drift respecto al paper.
# Cuando ON: nti_path_hot NO contribuye al hot_mask. Su cálculo se mantiene
# para diagnóstico. Default OFF (backward-compat).
ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK: bool = bool(_p.get("enable_test1_k1_retire_from_hot_mask", False))

# F2.8 S73 — Defensa secundaria BT-level post Planck-inversion.
# Coppola 2025 Cap.11 Table 1: MODIS B21 fire channel saturation ≈ 500 K (low-gain).
# Cualquier BT > 500K en B21 indica L1B sentinel-extrapolation o anomalía física
# fuera del rango Wooster (que requiere 600-1500 K para error ±30%). Default ON
# como defense in depth complementaria al fix L1B (calibrate() filter dn > 32767).
# Ver docs/F28_SATURATION_INVESTIGATION.md sec 5.3.
# S120 (cacería): estos dos viven TOP-LEVEL en los yaml (mirova_equivalent.yaml
# y derivados) pero se leían solo de _p (sección paths:) → el yaml se ignoraba y
# regían los defaults (hoy coinciden true/500.0 — bomba latente si se editaba el
# yaml). Se leen de ambos niveles, top-level gana.
ENABLE_BT_SAT_SECONDARY_GUARD: bool = bool(_cfg.get("enable_bt_sat_secondary_guard", _p.get("enable_bt_sat_secondary_guard", True)))
BT_SAT_MIR_K_MODIS: float = float(_cfg.get("bt_sat_mir_k_modis", _p.get("bt_sat_mir_k_modis", 500.0)))

# F31 S75 — VRPTIR Aveni 2025 GRL doi:10.1029/2024GL113324 opt-in feature flag.
# Permite usar el método VRPTIR (TIR single-band 10.5-12 μm) para retrieval de
# RP de features moderate-to-low-temperature (300-600 K): crater lakes,
# fumarole fields, hydrothermal systems. Complementario a Wooster MIR
# (válido 600-1500 K). Coeficientes verificados verbatim contra PDF S74 (A35
# confidence:HIGH, PR #150). Ver docs/F31_AVENI_GRL_2025_EXTRACT.md.
#
# Default: OFF. Habilitar solo en perfil experimental_lowT.yaml para piloto
# en volcanes candidatos (Lastarria, Copahue, Planchón-Peteroa, Villarrica
# lava lake). EXCLUIR PCC (A20 no-focal — invalida single-pixel TIRVolcH).
#
# Pre-requisito operacional: TIRVolcH detector (Aveni 2024 RSE) — Plan F31
# Task A1 (subagente paralelo S75). Sin TIRVolcH activo, flag no tiene efecto
# operacional — la función vrptir.vrp_tir es standalone llamable directo
# en experimentos pero NO se integra a process_viirs por defecto.
#
# NOTA: flags top-level del yaml usan _cfg.get() (no _p.get()). _p=_cfg["paths"]
# solo lee sub-section. Refactor profile loader S75+ recomendado para
# normalizar a una sola fuente top-level. Mismo bug latente en
# enable_bt_sat_secondary_guard pero su default True coincide con yaml.
ENABLE_VRPTIR_AVENI: bool = bool(_cfg.get("enable_vrptir_aveni", False))
VRPTIR_T_MIN_K: float = float(_cfg.get("vrptir_t_min_k", 300.0))    # rango validez inferior
VRPTIR_T_MAX_K: float = float(_cfg.get("vrptir_t_max_k", 600.0))    # rango validez superior
VRPTIR_K_TIR_I5: float = float(_cfg.get("vrptir_k_tir_i5", 60.17))  # μm·sr VIIRS I5 11.45 μm

# S72 F2.3 — Coppola 2016a SP 426.5 §267-273 dice que pixels "unsuitable"
# (edge de matriz + dNTI<-0.1 + dETI<-0.1) NO entran al pool μ/σ de la rama
# estadística de Tests 2/3 ni al hot mask path D contextual. Previo a S72 F1.2
# (PR #115) los floors estaban hardcoded -0.1 dentro de build_unsuitable_mask
# y se aplicaban siempre que first_pass_tests_2_and_3 corría. Ese fix entró
# en mirova_equivalent operacional sin gating explícito.
#
# Cuando ON (default True post-F1.2.a): floors dNTI/dETI = -0.1 y, en los
# procesadores, apply_unsuitable_filters=True en contextual_dnti_hot_mask /
# dual_roi_contextual_dnti_hot_mask. Cuando OFF: floors = -inf (no filtran)
# y path D contextual no aplica filtros — comportamiento pre-F1.2.a.
#
# Independiente de ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK (§298-300 K1 retire)
# para permitir A/B aislados S72 F2.3.
ENABLE_UNSUITABLE_FILTERS_267_273: bool = bool(
    _p.get("enable_unsuitable_filters_267_273", True)
)

# S46 Drift #1b — Coppola 2016a SP426.5:352-356 dice "step 2 is performed a
# second time, being particularly careful to eliminate all of the 'active'
# pixels already detected". Nuestro bg_vals NO excluye pixels Test 1 K1 active,
# contaminando t_bg/std_bg si hay anomalías cerca/dentro del ring.
# Cuando ON: compute_bg_stats excluye pixels NTI > NTI_K1 antes de computar
# t_bg/std_bg. Default OFF (backward-compat).
ENABLE_TEST1_K1_BG_EXCLUDE: bool = bool(_p.get("enable_test1_k1_bg_exclude", False))

# S46 Drift #7 — Coppola 2016a SP426.5 línea 201-202 + Eq.7 dicen:
# "resampled within a 50x50 km grid... spatial resolution of the resampled
# MODIS pixels is 1 km" y "A_PIX is the pixel size (1 km^2 for the resampled
# MODIS pixels)". MIROVA usa A_pix nadir-fijo en los 3 sensores (CLAUDE.md
# regla científica). Flags opt-in por sensor para preservar calibración
# empírica S14 (MODIS sec^3, VIIRS factor lineal 1-2x) como default.
# Cuando ON: A_pix uniforme (1 km^2 MODIS, 0.140625 km^2 VIIRS I, 0.5625 km^2
# VIIRS M) — clon literal MIROVA.
ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS: bool = bool(
    _p.get("enable_nadir_fixed_pixel_area_modis", False)
)
ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS: bool = bool(
    _p.get("enable_nadir_fixed_pixel_area_viirs", False)
)

# S46 Drift #2+#3 — Coppola 2016a SP426.5 líneas 316-325 dicen literalmente:
#   Test 2: dNTI > C1   OR   dNTI > μ_dNTI + C2·σ_dNTI
#   Test 3: dETI > C1   OR   dETI > μ_dETI + C2·σ_dETI
#   pixel active ⇔ Test 2 ∧ Test 3
# Implementación actual contextual_dnti_hot_mask sólo computa `dnti > c1` (drift):
# falta Test 3 (dETI), falta rama OR estadística, falta dual-ROI Tabla 2.
# Cuando ON: paths legacy (bt_path, nti_path, dnti_ctx, test1) se calculan para
# diag pero NO contribuyen al hot_mask — éste se obtiene de first_pass_tests_2_and_3.
ENABLE_FIRST_PASS_TESTS_2_AND_3: bool = bool(
    _p.get("enable_first_pass_tests_2_and_3", False)
)
# ENABLE_DUAL_ROI_FIRST_PASS activa Tabla 2 noche: C1=0.003/C2=5 summit,
# C1=0.010/C2=10 scene. Off → set uniforme summit. Solo aplica si
# ENABLE_FIRST_PASS_TESTS_2_AND_3 está ON.
ENABLE_DUAL_ROI_FIRST_PASS: bool = bool(
    _p.get("enable_dual_roi_first_pass", False)
)

# S46 Task 6 Variante 13 EXPERIMENTAL — Di Bella 2024 n=12 noche VIIRS.
# NO clon literal MIROVA. Di Bella es INGV Catania (regla S26, NO MIROVA).
# Permite reemplazar Coppola C2=5/10 (Tabla 1 noche) con n=12 (Di Bella 2024
# RSDF Z-score) en first_pass_tests_2_and_3 dentro de los procesadores VIIRS
# (I-band 375m y M-band 750m). MODIS NO recibe override (drift solo VIIRS).
# Comparación empírica vs Coppola C2=5/10 en A/B aislado objetivo (2).
# Default None: preserva legacy (sin override). Cuando float, overrides
# summit y scene C2 (dNTI y dETI) simultáneamente.
VIIRS_C2_OVERRIDE_NIGHT = _p.get("viirs_c2_override_night", None)
if VIIRS_C2_OVERRIDE_NIGHT is not None:
    VIIRS_C2_OVERRIDE_NIGHT = float(VIIRS_C2_OVERRIDE_NIGHT)

# S46 Ronda 2 — overrides param C1/C2 summit para exploración A/B
# (Coppola 2016a Tabla 1 default: C1_summit=0.003, C2_summit=5).
# Aplican a first_pass_tests_2_and_3 + second_pass_adjacent (los 3 sensores).
# Defaults None preservan paper-Tabla 1 literal.
C1_SUMMIT_OVERRIDE = _p.get("c1_summit_override", None)
if C1_SUMMIT_OVERRIDE is not None:
    C1_SUMMIT_OVERRIDE = float(C1_SUMMIT_OVERRIDE)
C2_SUMMIT_OVERRIDE = _p.get("c2_summit_override", None)
if C2_SUMMIT_OVERRIDE is not None:
    C2_SUMMIT_OVERRIDE = float(C2_SUMMIT_OVERRIDE)

# S71 D9 fix — 3 alternativas A/B para mitigar FPs path D contextual en cirrus
# (fondo frío t_bg < ~265K). Ver experiments/127_path_d_tbg_calibration/ y
# docs/MIROVA_DIVERGENCES.md D9. Las 3 son ortogonales — cualquier combinación
# válida; defaults OFF preservan operacional.
#
# Opción A: gate atmosférico. Si t_bg < min_k, omitir el firing contextual
# (first_pass Tests 2&3 + path D legacy dnti_ctx). Default None = OFF.
PATH_D_ATM_GATE_TBG_MIN_K = _p.get("path_d_atm_gate_tbg_min_k", None)
if PATH_D_ATM_GATE_TBG_MIN_K is not None:
    PATH_D_ATM_GATE_TBG_MIN_K = float(PATH_D_ATM_GATE_TBG_MIN_K)

# Opción B: co-validación. Cuando ON, el firing contextual (first_pass o path
# D legacy) solo cuenta si BT path O NTI path también dispararon en la escena.
# Si solo first_pass/dnti_ctx fired aislado → descartar contribución contextual.
PATH_D_REQUIRES_COVALIDATION: bool = bool(
    _p.get("path_d_requires_covalidation", False)
)

# Opción C: cap magnitud. Cuando el firing es solo contextual (BT/NTI = 0) AND
# t_bg < cap_tbg_max_k, capear pc.vrp_mw a cap_mw. Ambos defaults None = OFF.
PATH_D_ONLY_CAP_MW = _p.get("path_d_only_cap_mw", None)
if PATH_D_ONLY_CAP_MW is not None:
    PATH_D_ONLY_CAP_MW = float(PATH_D_ONLY_CAP_MW)
PATH_D_ONLY_CAP_TBG_MAX_K = _p.get("path_d_only_cap_tbg_max_k", None)
if PATH_D_ONLY_CAP_TBG_MAX_K is not None:
    PATH_D_ONLY_CAP_TBG_MAX_K = float(PATH_D_ONLY_CAP_TBG_MAX_K)

# S46 Task 5 Drift #4 — Coppola 2016a SP426.5:347-356 dice literalmente:
#   "active pixels may strongly modify the average values of their surroundings,
#    with a consequent decrease in the dNTI and dETI values of adjacent pixels.
#    To avoid this problem, step 2 (spatial analysis) is performed a second time,
#    being particularly careful to eliminate all of the 'active' pixels already
#    detected"
# La flag ENABLE_SECOND_PASS_ADJACENT (definida arriba en bloque H_D8_5 S37)
# controla activación. ENABLE_DUAL_ROI_SECOND_PASS activa Tabla 2 noche thresholds
# summit/scene en el second-pass. Off → set uniforme summit. Solo aplica si
# ENABLE_SECOND_PASS_ADJACENT está ON.
ENABLE_DUAL_ROI_SECOND_PASS: bool = bool(
    _p.get("enable_dual_roi_second_pass", False)
)

# --- F52-B S77 (A45) — Single-pixel mode régimen sub-MW (drift T1.5 S72 fix).
# Cuando un cluster cae en régimen sub-MW (vrp_mw_sum < threshold Y n_pixels
# <= max_pixels), reportar `pc.vrp_mw = max(per_pixel_vrp)` (single pixel
# hottest) en vez de la suma. Alinea con MIROVA NRT single-pixel reporting en
# sub-MW (0.21-0.45 MW canónicos). Volcanes corregidos:
#   - Tupungatito (ratio 30.15× pre-fix), Chaitén (2.53×), PP (2.10×),
#     PCC (0.48× sub-estimación, patrón opuesto misma causa raíz).
# Default ON. Ver pipeline/single_pixel_mode.py + tests/test_single_pixel_mode_f52b.py.
# Tag defensivo: pre-s77-f52b-single-pixel-sub-mw. Refs PRs #191 + #192, A45.
ENABLE_SINGLE_PIXEL_SUB_MW_MODE: bool = bool(
    _cfg.get("enable_single_pixel_sub_mw_mode", False)
)
SUB_MW_REGIME_THRESHOLD_MW: float = float(
    _cfg.get("sub_mw_regime_threshold_mw", 5.0)
)
SINGLE_PIXEL_MAX_CLUSTER_PIXELS: int = int(
    _cfg.get("single_pixel_max_cluster_pixels", 3)
)

# --- F46 S77 (A45) — gate consistencia MIR/NTI + threshold subido sobre vrp_tir_mw.
# Helper `pipeline.process_viirs._compute_vrp_tir_with_gate` (Opción A+B
# combinada). Default ON post-fix. Cuando OFF, comportamiento legacy
# `max(0.5, 4σ)` sin gate. Ver docs/F46_VRP_TIR_BUG_S76.md §5.3 y
# tests/test_vrp_tir_consistency_gate_f46.py.
ENABLE_VRP_TIR_CONSISTENCY_GATE: bool = bool(
    _cfg.get("enable_vrp_tir_consistency_gate", True)
)
VRP_TIR_FLOOR_K: float = float(_cfg.get("vrp_tir_floor_k", 3.0))
VRP_TIR_N_SIGMA: float = float(_cfg.get("vrp_tir_n_sigma", 6.0))

# --- F46 provisional gate S81 (A45) — vrp_tir_mw silenciado hasta fix completo.
# Default True (legacy behavior); profiles operacionales setean False para
# evitar exposición de outliers Stefan-Boltzmann sobre máscara contaminada
# (726 records >1000× vs vrp_mir_mw detectados en auditoría S81 frente #3).
# Cuando False, _compute_vrp_tir_with_gate retorna 0.0 incondicionalmente.
# Ver docs/F46_VRP_TIR_GATE_S81.md (mitigación) y docs/F46_VRP_TIR_BUG_S76.md
# (plan completo Coppola 2024 Eq.16 background subtraction).
ENABLE_VRP_TIR_OUTPUT: bool = bool(_cfg.get("enable_vrp_tir_output", True))

# --- Sensor activation ---
_s = _cfg["sensors"]
SENSOR_MODIS: bool = bool(_s.get("modis", True))
SENSOR_VIIRS_375: bool = bool(_s.get("viirs_375", True))
SENSOR_VIIRS_750: bool = bool(_s.get("viirs_750", True))

# --- Data output subdirectory under data/ ---
DATA_SUBDIR: str = str(_cfg["output"]["data_subdir"])


def describe() -> str:
    return (
        f"[VRP profile={PROFILE_NAME}] "
        f"anomaly_K={ANOMALY_THRESHOLD_K} "
        f"nsigma_mir={N_SIGMA_MIR} "
        f"vent_K={VENT_THRESHOLD_K} "
        f"nti_k1={NTI_K1_NIGHT} "
        f"nti_rel={'on' if ENABLE_NTI_RELATIVE_PATH else 'off'} "
        f"vent_path={'on' if ENABLE_VENT_PATH else 'off'} "
        f"sensors=MODIS:{SENSOR_MODIS} V375:{SENSOR_VIIRS_375} V750:{SENSOR_VIIRS_750} "
        f"data_subdir={DATA_SUBDIR}"
    )


# Print the active profile once at import time so every run_pipeline.py run
# has an unambiguous header in its stdout log.
print(describe(), file=sys.stderr)
