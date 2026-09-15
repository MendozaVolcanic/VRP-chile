# -*- coding: utf-8 -*-
"""Descomposicion de la magnitud nuestra/MIROVA contra el OSF v2.5 (Fase 0, tarea 4, plan S139).

POR QUE. Nuestra magnitud V375 publicada queda en ~0,7 de la de MIROVA. Como usamos el mismo k y la
misma area que MIROVA (verificado S139 en experiments/_s139_audit/magnitud/01), la razon por pasada
se separa exactamente en dos factores fisicos:
  * F_n  = pixeles que integramos / pixeles que integra MIROVA (Npix). Es SELECCION: cuantos pixeles
    del cumulo del crater entran a la suma.
  * F_ex = exceso de radiancia por pixel nuestro / exceso por pixel de MIROVA. En 375 m se parte en
    nivel caliente (F_hot, nuestro L(bt) contra hot/Npix) y fondo (F_bg, lo que agrega usar NUESTRO
    fondo en vez del de MIROVA).
S139 midio R_gm 0,659 = F_n 0,553 x F_ex 1,192 sobre 1.499 pares V375, y R 0,995 cuando contamos el
mismo numero de pixeles: la formula esta bien, falta seleccion (y el fondo compensa en parte).

El OSF es un archivo SUPERVISADO A MANO (Coppola 2023 §2.5): sirve para definiciones por fila
(formula, Tot_Lmir_bk, Npix), nunca para conteos del NRT. Aca se usa asi: pasada contra pasada.

INSTRUMENTO. P1: si k o A estuvieran mal, F_ex saldria lejos de 1 aun con los mismos pixeles
(subconjunto igual_conteo); si la seleccion estuviera rota, F_n lo mostraria. P2: desplazar el
pareo 6 h debe dejar 0 pares (control negativo); la replica del nucleo F5' debe coincidir con el
valor que el pipeline persiste (0 discrepancias).

ORIGEN. Cuerpos copiados sin reescribir de experiments/_s139_audit/magnitud/02_descomposicion_pares.py
(planck, res, crater, nearest, core_pixels, build, gm, table) y el subconjunto de igual conteo de
04_fondo_y_test1.py. Solo se envolvio en funciones para que el modulo no corra al importarse y se
agrego la salida JSON. Los scripts de experiments/ no se tocan.
"""
from __future__ import annotations

import argparse
import bisect
import json
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

T_INICIO = time.time()
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
from pipeline.f5_core import F5_BT_EXT_K, F5_R_CORE_KM, _hav_km  # noqa: E402

OSF_DEFECTO = R / "data" / "mirova_reference" / "VRP_GLOBAL_ARCHIVE_2025.csv"
MAP = {'Láscar': 'Lascar', 'Lastarria': 'Lastarria', 'Isluga': 'Isluga', 'Llaima': 'Llaima', 'Villarrica': 'Villarrica',
       'Chaitén': 'Chaiten', 'Copahue': 'Copahue', 'Planchón-Peteroa': 'PlanchonPeteroa',
       'Puyehue-Cordón Caulle': 'PuyehueCordonCaulle', 'Chillán, Nevados de': 'NevadosDeChillan', 'Tupungatito': 'Tupungatito'}
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5, "Chaiten": 5,
         "Villarrica": 5, "Llaima": 5, "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
KA = {375: 18.0 * 140625, 750: 19.7 * 562500, 1000: 18.9 * 1e6}
LAM = {375: 3.74, 750: 4.05, 1000: 3.929}   # banda MIR que usa NUESTRO codigo (MODIS: B21, D21)
C1, C2 = 1.191042e8, 14388.0
T0, T1 = datetime(2025, 2, 15), datetime(2025, 12, 1)
NOMBRE_RES = {375: "VIIRS375", 750: "VIIRS750", 1000: "MODIS"}
ZBINS = [0, 15, 25, 35, 50, 90]

# cargados por cargar(); globales porque asi los usan los cuerpos copiados de 02
o = None
ours = {}


def planck(T, l): return C1 / (l ** 5 * (math.exp(C2 / (l * T)) - 1))


def res(s): return 1000 if s.startswith('MODIS') else (750 if s.endswith('_750') else 375)


def cargar(osf_path):
    global o, ours
    osf = pd.read_csv(osf_path)
    osf['t'] = pd.to_datetime(osf.timeUTC, format='%d/%m/%Y %H:%M', errors='coerce')
    o = osf[osf.Volc_Name.isin(MAP) & (osf.t >= T0) & (osf.t < T1) & (osf.Dayflag == 0)].copy()
    o['vol'] = o.Volc_Name.map(MAP); o['res'] = o.Resolution.astype(int)
    ours = {}
    for v in INNER:
        for r in json.load(open(R / f'data/mirova_equivalent/{v}.json', encoding='utf-8'))['records']:
            dt = datetime.strptime(r['datetime_utc'], '%Y-%m-%d %H:%M')
            if T0 - timedelta(hours=7) <= dt < T1 + timedelta(hours=7):
                ours.setdefault((v, res(r['sensor'])), []).append((dt, r))
    for k in ours: ours[k].sort(key=lambda x: x[0])


def crater(r, v):
    pc = r.get('primary_cluster') or {}
    vr = pc.get('vrp_mw') or 0; d = pc.get('centroid_dist_km')
    return vr > 0 and d is not None and d <= INNER[v] and vr <= 50000 and r.get('distance_class') in ('summit', None)


def nearest(v, rs, t, tol=10):
    L = ours.get((v, rs), []); ts = [x[0] for x in L]; i = bisect.bisect_left(ts, t); best = None
    for j in (i - 1, i):
        if 0 <= j < len(L) and abs((L[j][0] - t).total_seconds()) <= tol * 60:
            if best is None or abs((L[j][0] - t).total_seconds()) < abs((best[0] - t).total_seconds()): best = L[j]
    return best


def core_pixels(r, inner):
    """Replica del conjunto de pixeles que suma f5_core_vrp_mw (misma logica, devuelve la lista)."""
    px = r.get('anomaly_pixels') or []; pc = r.get('primary_cluster') or {}
    if not px or pc.get('centroid_lat') is None: return None
    cand = [p for p in px if p.get('lat') is not None and _hav_km(p['lat'], p['lon'], pc['centroid_lat'], pc['centroid_lon']) <= inner]
    if not cand: return None
    pk = max(range(len(cand)), key=lambda i: (cand[i].get('vrp_mw') or 0, -i))
    # max() devuelve el primero en empates si usamos -i; f5 usa '>' estricto => primero. ok
    return [p for i, p in enumerate(cand) if i == pk or _hav_km(p['lat'], p['lon'], cand[pk]['lat'], cand[pk]['lon']) <= F5_R_CORE_KM
            or (p.get('bt_k') or 0) >= F5_BT_EXT_K]


def build(shift_h=0):
    rows = []
    for _, x in o[(o['class'] == 1) & (o.VRP > 0)].iterrows():
        m = nearest(x.vol, x.res, x.t.to_pydatetime() + timedelta(hours=shift_h))
        if m is None or not crater(m[1], x.vol): continue
        r = m[1]; pc = r['primary_cluster']; ka = KA[x.res]; lam = LAM[x.res]; inner = INNER[x.vol]
        d = dict(vol=x.vol, res=x.res, satzen=abs(x.SatZen), Npix=x.Npix, osf_mw=x.VRP / 1e6,
                 hot1=x.Tot_Lmir_hot / x.Npix, bk1=x.Tot_Lmir_bk / x.Npix, ex1=(x.Tot_Lmir_hot - x.Tot_Lmir_bk) / x.Npix,
                 pc_mw=pc['vrp_mw'], pc_n=pc['n_pixels'], n_anom=r.get('n_anomalous_pixels'), sensor=r['sensor'],
                 t_bg=r.get('t_bg_k'), dt_min=(m[0] - x.t.to_pydatetime()).total_seconds() / 60,
                 test1=r.get('final_hotspot_source') == 'test1_roi', single=pc.get('single_pixel_mode'),
                 t_osf=x.t.to_pydatetime(), t_ours=m[0])  # S141: horas de la pasada, para el probe de la Fase 1
        d['Lbg_ring'] = planck(r['t_bg_k'], lam) if r.get('t_bg_k') else np.nan
        px = r.get('anomaly_pixels') or []
        inn = [p for p in px if (p.get('dist_km') is not None and p['dist_km'] <= inner)]
        d['scene_inner_mw'] = sum(p.get('vrp_mw') or 0 for p in inn); d['scene_inner_n'] = len(inn)
        d['scene_mw'] = r.get('vrp_mw'); d['n_px_saved'] = len(px)
        if x.res == 375:
            f5 = r.get('f5_core_vrp_mw'); cp = core_pixels(r, inner)
            d['f5_persist'] = f5
            if cp:
                d['core_mw'] = sum(p.get('vrp_mw') or 0 for p in cp); d['core_n'] = len(cp)
                pos = [p for p in cp if (p.get('vrp_mw') or 0) > 0 and p.get('bt_k')]
                if pos:
                    Lh = [planck(p['bt_k'], lam) for p in pos]
                    d['hot1_ours'] = float(np.mean([planck(p['bt_k'], lam) for p in cp if p.get('bt_k')]))
                    d['Lbg_imp'] = float(np.median([Lh[i] - p['vrp_mw'] * 1e6 / ka for i, p in enumerate(pos)]))
                    d['n_zero'] = len(cp) - len(pos)
            pub, npub = (f5, d.get('core_n')) if (f5 is not None and d.get('core_n')) else (pc['vrp_mw'], pc['n_pixels'])
        else:
            pub, npub = pc['vrp_mw'], pc['n_pixels']
        d['pub_mw'], d['pub_n'] = pub, npub
        rows.append(d)
    return pd.DataFrame(rows)


def gm(x): x = x[(x > 0) & np.isfinite(x)]; return float(np.exp(np.log(x).mean())) if len(x) else np.nan


def table(g):
    return pd.Series({'n': len(g), 'R_med': g.R.median(), 'R_gm': gm(g.R), 'Fn_gm': gm(g.F_n), 'Fex_gm': gm(g.F_ex),
                      'Fn_med': g.F_n.median(), 'Fex_med': g.F_ex.median(), 'Npix_med': g.Npix.median(), 'pub_n_med': g.pub_n.median(),
                      'pc_n_med': g.pc_n.median(), 'R_pc_med': g.R_pc.median()})


# ---------------------------------------------------------------- salida JSON
def _limpio(v):
    if isinstance(v, (float, np.floating)):
        return None if not np.isfinite(v) else round(float(v), 4)
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def _fila(g, con_fondo):
    t = {k: _limpio(v) for k, v in table(g).items()}
    t['n'] = int(len(g))
    if con_fondo:
        v = g[g.Lbg_imp.notna()] if 'Lbg_imp' in g else g.iloc[0:0]
        t['Fhot_gm'] = _limpio(gm(v.F_hot)) if len(v) else None
        t['Fbg_gm'] = _limpio(gm(v.F_bg)) if len(v) else None
    return t


def subconjunto_04(d):
    """Filtro literal de 04_fondo_y_test1.py: V375 con fondo implicito, R>0 y F_hot>0."""
    s = d[(d.res == 375) & d.Lbg_imp.notna() & (d.R > 0)].copy()
    s['F_hot'] = (s.hot1_ours - s.bk1) / s.ex1; s['F_bg'] = s.F_ex / s.F_hot
    return s[s.F_hot > 0]


def _t04(g):
    # 04 usa gm sin filtro de finitud: x[(x > 0)]
    g4 = lambda x: float(np.exp(np.log(x[(x > 0)]).mean())) if (x > 0).any() else None
    return {'n': int(len(g)), 'R': _limpio(g4(g.R)), 'Fn': _limpio(g4(g.F_n)),
            'Fhot': _limpio(g4(g.F_hot)), 'Fbg': _limpio(g4(g.F_bg))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--osf", default=str(OSF_DEFECTO))
    ap.add_argument("--out", default=str(R / "experiments" / "_s140" / "magnitud_osf_out.json"))
    a = ap.parse_args(argv)

    cargar(a.osf)
    d = build(0)
    neg = build(6)
    d['R_pc'] = d.pc_mw / d.osf_mw; d['R'] = d.pub_mw / d.osf_mw
    d['F_n'] = d.pub_n / d.Npix
    d['ex_ours'] = d.pub_mw * 1e6 / (d.res.map(KA) * d.pub_n)
    d['F_ex'] = d.ex_ours / d.ex1
    d['zbin'] = pd.cut(d.satzen, ZBINS)
    # F_hot / F_bg como en 02 l. 133-134 (sobre las filas con fondo implicito)
    if 'Lbg_imp' in d:
        d['F_hot'] = (d.hot1_ours - d.bk1) / d.ex1
        d['F_bg'] = d.F_ex / d.F_hot

    s375 = d[(d.res == 375) & d.core_mw.notna() & d.f5_persist.notna()] if 'core_mw' in d else d.iloc[0:0]
    salida = {
        "meta": {"osf": str(a.osf), "ventana_osf": [T0.strftime("%Y-%m-%d"), T1.strftime("%Y-%m-%d")],
                 "tolerancia_pareo_min": 10, "n_pares": int(len(d)),
                 "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "definiciones": {"R": "pub_mw / VRP OSF (V375 publica el nucleo F5' persistido, fallback pc)",
                                  "F_n": "pub_n / Npix", "F_ex": "exceso por pixel nuestro / (hot-bk)/Npix",
                                  "F_hot": "(L(bt) nuestro - bk/Npix) / ((hot-bk)/Npix)", "F_bg": "F_ex / F_hot",
                                  "gm": "media geometrica sobre valores > 0 y finitos"}},
        "controles": {"pares_desplazados_6h": int(len(neg)),
                      "replica_f5_discrepa": int(((s375.core_mw - s375.f5_persist).abs() > 1e-3).sum()),
                      "replica_f5_n": int(len(s375))},
    }
    for rr, nombre in NOMBRE_RES.items():
        g = d[d.res == rr]
        con_fondo = rr == 375
        bloque = {"total": _fila(g, con_fondo) if len(g) else None,
                  "por_volcan": {v: _fila(gv, con_fondo) for v, gv in g.groupby('vol')},
                  "por_cenit": {str(z): _fila(gz, con_fondo) for z, gz in g.groupby('zbin', observed=True)}}
        if con_fondo:
            s = subconjunto_04(d)
            bloque["igual_conteo"] = _t04(s[s.pub_n == s.Npix])
            bloque["conteo_distinto"] = _t04(s[s.pub_n != s.Npix])
        salida[nombre] = bloque
    salida["meta"]["segundos"] = round(time.time() - T_INICIO, 1)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")

    print("controles:", salida["controles"])
    for nombre in NOMBRE_RES.values():
        print(nombre, "total:", salida[nombre]["total"])
    print("VIIRS375 igual conteo:", salida["VIIRS375"]["igual_conteo"], "| conteo distinto:", salida["VIIRS375"]["conteo_distinto"])
    print(f"listo en {salida['meta']['segundos']} s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
