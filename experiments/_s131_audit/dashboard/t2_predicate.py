# -*- coding: utf-8 -*-
"""S131 T2 - El predicado de deteccion dentro y fuera del frontend.
READ-ONLY. Compara, sobre los 11 Tier A:
  P1  isValidDetection            frontend/index.html:1371 (== mosaico.html:373)
  P2  frontend DASHBOARD          isThermalArtifact ? 0 : mirovaEqVrpDisplay > 0
                                  (index.html:1201 / 1408-1409 / 1909)
  P3  auto_audit DASHBOARD        scripts/auto_audit_weekly.py:231-239
  P4  audit_metrics.mirova_eq_vrp pipeline/audit_metrics.py:75 > 0
"""
import io, json, os, sys, math, yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, ROOT)
from pipeline.audit_metrics import mirova_eq_vrp  # noqa: E402

TIER_A = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
          "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
          "Tupungatito", "Villarrica"]
INNER = {v['name']: v.get('inner_radius_km') for v in
         yaml.safe_load(open(os.path.join(ROOT, 'volcanoes.yaml'), encoding='utf-8'))['volcanoes']}
CAP = 50000.0


# ---- P1: frontend/index.html:1371 ----
def is_valid_detection(r):
    if (r.get('vrp_mw') or 0) > 0:
        return True
    return r.get('triggered_test1') is True


# ---- mirovaEqVrp (index.html:972) ----
def mirova_eq_vrp_front(r, inner_km, include_far=False):
    if not r:
        return 0.0
    pc = r.get('primary_cluster')
    if not pc:
        vfb = r.get('vrp_mw')
        if vfb is None:
            vfb = r.get('vrp_mir_mw')
        if vfb is None:
            vfb = 0.0
        return 0.0 if vfb > CAP else vfb
    dc = r.get('distance_class')
    if dc and dc != 'summit' and not include_far:
        return 0.0
    cd = pc.get('centroid_dist_km')
    if not include_far and cd is not None and cd > inner_km:
        return 0.0
    v = pc.get('vrp_mw') or 0.0
    return 0.0 if v > CAP else v


def is_cirrus(r, inner_km):
    if not r or r.get('_mirova_confirmed'):
        return False
    t = r.get('t_max_k')
    if t is None or t >= 273.15:
        return False
    return mirova_eq_vrp_front(r, inner_km) > 10


def is_diffuse(r, inner_km):
    if not r or r.get('_mirova_confirmed'):
        return False
    pc = r.get('primary_cluster')
    t = r.get('t_max_k')
    if not pc or t is None or t >= 278.15:
        return False
    npx = pc.get('n_pixels') or 0
    if npx < 100:
        return False
    eq = mirova_eq_vrp_front(r, inner_km)
    return eq >= 50 and (eq / npx) < 1.0


def is_thermal_artifact(r, inner_km):
    return is_cirrus(r, inner_km) or is_diffuse(r, inner_km)


# ---- P2: gate efectivo del dashboard (index.html:1201/1409/1909) ----
def p2_front_dash(r, inner_km):
    # F5' Core nunca borra una deteccion (guard S96, index.html:1089) =>
    # (core>0) <=> (base>0). El gate binario coincide con mirovaEqVrp.
    if is_thermal_artifact(r, inner_km):
        return False
    return mirova_eq_vrp_front(r, inner_km) > 0


# ---- P3: scripts/auto_audit_weekly.py:231-239 ----
def p3_audit_dash(r, inner_km):
    pc = r.get('primary_cluster') or {}
    vrp = pc.get('vrp_mw') or 0.0
    cdist = pc.get('centroid_dist_km')
    if not (0 < vrp <= CAP):
        return False
    if not (cdist is not None and cdist <= inner_km):
        return False
    dc = r.get('distance_class')
    return (not dc) or dc == 'summit'


print("=== T2 - predicados de deteccion, 11 Tier A ===")
print("P1 isValidDetection        frontend/index.html:1371, mosaico.html:373")
print("P2 dashboard efectivo      index.html:1201,1408-1409,1909 (artefacto + mirovaEqVrpDisplay>0)")
print("P3 auto_audit dashboard    scripts/auto_audit_weekly.py:231-239")
print("P4 audit_metrics           pipeline/audit_metrics.py:75 (mirova_eq_vrp>0)")
print()

tot = 0
cnt = {k: 0 for k in ('P1', 'P2', 'P3', 'P4')}
dis = {k: 0 for k in ('P1vP2', 'P2vP3', 'P2vP4', 'P3vP4')}
why = {'p2_si_p3_no_pc_null_cdist': 0, 'p2_si_p3_no_fallback_sin_pc': 0,
       'p3_si_p2_no_artefacto': 0, 'otros': 0}
per_vol = {}
dates = []
for vol in TIER_A:
    recs = json.load(open(os.path.join(ROOT, 'data/mirova_equivalent', vol + '.json'),
                          encoding='utf-8'))['records']
    ik = INNER[vol]
    c = dict(n=len(recs), P1=0, P2=0, P3=0, P4=0, P1vP2=0, P2vP3=0, P2vP4=0, P3vP4=0)
    for r in recs:
        tot += 1
        if r.get('datetime_utc'):
            dates.append(r['datetime_utc'])
        a = is_valid_detection(r)
        b = p2_front_dash(r, ik)
        cc = p3_audit_dash(r, ik)
        d = mirova_eq_vrp(r, vol) > 0
        for k, v in (('P1', a), ('P2', b), ('P3', cc), ('P4', d)):
            if v:
                cnt[k] += 1
                c[k] += 1
        for k, v in (('P1vP2', a != b), ('P2vP3', b != cc),
                     ('P2vP4', b != d), ('P3vP4', cc != d)):
            if v:
                dis[k] += 1
                c[k] += 1
        if b != cc:
            pc = r.get('primary_cluster')
            if b and not cc:
                if not pc:
                    why['p2_si_p3_no_fallback_sin_pc'] += 1
                elif pc.get('centroid_dist_km') is None:
                    why['p2_si_p3_no_pc_null_cdist'] += 1
                else:
                    why['otros'] += 1
            elif cc and not b:
                if is_thermal_artifact(r, ik):
                    why['p3_si_p2_no_artefacto'] += 1
                else:
                    why['otros'] += 1
    per_vol[vol] = c

print("denominador = %d records; ventana %s .. %s UTC" % (tot, min(dates), max(dates)))
print("positivos:  P1=%d (%.2f%%)  P2=%d (%.2f%%)  P3=%d (%.2f%%)  P4=%d (%.2f%%)"
      % (cnt['P1'], 100.0 * cnt['P1'] / tot, cnt['P2'], 100.0 * cnt['P2'] / tot,
         cnt['P3'], 100.0 * cnt['P3'] / tot, cnt['P4'], 100.0 * cnt['P4'] / tot))
print("desacuerdos:")
for k in ('P1vP2', 'P2vP3', 'P2vP4', 'P3vP4'):
    print("  %-6s %7d  (%.2f%% del corpus)" % (k, dis[k], 100.0 * dis[k] / tot))
print("desglose P2 vs P3:")
for k, v in why.items():
    print("  %-32s %d" % (k, v))
print("\npor volcan (n | P1 P2 P3 P4 | P1vP2 P2vP3 P2vP4 P3vP4):")
for v, c in per_vol.items():
    print("  %-22s n=%6d | %6d %5d %5d %5d | %6d %6d %6d %6d"
          % (v, c['n'], c['P1'], c['P2'], c['P3'], c['P4'],
             c['P1vP2'], c['P2vP3'], c['P2vP4'], c['P3vP4']))

# ---- desglose direccional + artefacto termico ----
art = art_pos = p1_no_p2 = p2_no_p1 = p1_only_t1 = 0
for vol in TIER_A:
    recs = json.load(open(os.path.join(ROOT, 'data/mirova_equivalent', vol + '.json'),
                          encoding='utf-8'))['records']
    ik = INNER[vol]
    for r in recs:
        a = is_valid_detection(r)
        b = p2_front_dash(r, ik)
        if is_thermal_artifact(r, ik):
            art += 1
            if mirova_eq_vrp_front(r, ik) > 0:
                art_pos += 1
        if a and not b:
            p1_no_p2 += 1
        if b and not a:
            p2_no_p1 += 1
        if a and not ((r.get('vrp_mw') or 0) > 0):
            p1_only_t1 += 1
print("\n=== T2-B  desglose ===")
print("  isThermalArtifact=True: %d (con mirovaEqVrp>0: %d) / %d" % (art, art_pos, tot))
print("  P1 y no P2: %d   |   P2 y no P1: %d" % (p1_no_p2, p2_no_p1))
print("  P1 true SOLO por triggered_test1 (vrp_mw==0): %d" % p1_only_t1)

# ---- por que isThermalArtifact = 0 ----
n_tmax_null = n_tmax_lt273 = n_tmax_lt278 = n_cirrus_cand = n_diff_cand = 0
casos_p2_no_p1 = []
for vol in TIER_A:
    recs = json.load(open(os.path.join(ROOT, 'data/mirova_equivalent', vol + '.json'),
                          encoding='utf-8'))['records']
    ik = INNER[vol]
    for r in recs:
        t = r.get('t_max_k')
        if t is None:
            n_tmax_null += 1
        else:
            if t < 273.15:
                n_tmax_lt273 += 1
                if mirova_eq_vrp_front(r, ik) > 0:
                    n_cirrus_cand += 1
            if t < 278.15:
                n_tmax_lt278 += 1
                pc = r.get('primary_cluster') or {}
                if (pc.get('n_pixels') or 0) >= 100:
                    n_diff_cand += 1
        if p2_front_dash(r, ik) and not is_valid_detection(r):
            pc = r.get('primary_cluster') or {}
            casos_p2_no_p1.append((vol, r.get('datetime_utc'), r.get('sensor'),
                                   r.get('vrp_mw'), pc.get('vrp_mw'),
                                   pc.get('centroid_dist_km'), r.get('distance_class'),
                                   r.get('discarded_reason')))
print("\n=== T2-C  por que el filtro de artefacto termico no dispara ===")
print("  t_max_k null: %d | t_max_k<273.15: %d (de ellos con eqVrp>0: %d)"
      % (n_tmax_null, n_tmax_lt273, n_cirrus_cand))
print("  t_max_k<278.15: %d (de ellos con pc.n_pixels>=100: %d)" % (n_tmax_lt278, n_diff_cand))
print("\n=== T2-D  los %d records P2-si / P1-no (asimetria A46) ===" % len(casos_p2_no_p1))
for c in casos_p2_no_p1:
    print("  %-20s %s %-18s vrp_mw=%s pc.vrp=%s pc.dist=%s dclass=%s disc=%s" % c)
