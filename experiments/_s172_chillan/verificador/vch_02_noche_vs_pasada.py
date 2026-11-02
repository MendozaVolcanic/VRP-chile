# -*- coding: utf-8 -*-
"""vch_02 (verificador S172): descompone la brecha noche (auto-audit) vs pasada para Chillan, por otro camino.
Usa el CSV de pasadas del auditor (s02, reproducido por mi en salidas/r02_pasadas.csv) SOLO para la lista de pares;
el estadistico de noche se recalcula aqui: max(nuestro)/max(MIROVA) por noche UTC (como auto_audit nuestros_por_noche:
clave = fecha UTC del record), mediana de noches, y se compara con (a) latest.json de main, (b) mediana por pasada.
P1: si el calculo estuviera roto no reproduciria 0,56/0,662/0,683 de latest.json (se imprime lado a lado).
P2: control negativo: noches barajadas entre si (razones de noche emparejadas con otra noche) no cambian la mediana,
    asi que el control relevante es el control positivo: duplicar nuestro valor duplica la mediana.
"""
import csv, json, statistics, collections, sys
R = list(csv.DictReader(open('salidas/r02_pasadas.csv', encoding='utf-8')))
lat = json.load(open('copia/data/audit_continuous/latest.json'))['magnitud_publicada_by_vol_sensor']
ahora = {}
for b in ('MODIS', 'VIIRS375', 'VIIRS750'):
    pub = collections.defaultdict(list); mir_all = collections.defaultdict(list); pares = collections.defaultdict(list)
    for r in R:
        if r['b'] != b: continue
        d = r['dt'][:10]
        if r['pub'] == '1' and float(r['disp']) > 0: pub[d].append(float(r['disp']))
        if r['vrp_M'] not in ('', 'None') and float(r['vrp_M']) > 0: mir_all[d].append(float(r['vrp_M']))
        if r['pub'] == '1' and float(r['disp']) > 0 and r['vrp_M'] not in ('', 'None') and float(r['vrp_M']) > 0:
            pares[d].append((float(r['disp']), float(r['vrp_M'])))
    noches = [d for d in pub if d in mir_all]
    rn = [max(pub[d]) / max(mir_all[d]) for d in noches]
    rn_par = [max(a for a, _ in pares[d]) / max(m for _, m in pares[d]) for d in pares]
    rp = [a / m for v in pares.values() for a, m in v]
    multi = [d for d in pares if len(pares[d]) >= 2]
    rp_multi = [a / m for d in multi for a, m in pares[d]]
    rp_uni = [a / m for d in pares if len(pares[d]) == 1 for a, m in pares[d]]
    ahora[b] = dict(
        noche_max_pub_sobre_max_mirova_n=len(rn), noche_mediana=round(statistics.median(rn), 3),
        latest_json=lat['NevadosDeChillan|' + b], noche_solo_pares_mediana=round(statistics.median(rn_par), 3), n_noches_pares=len(rn_par),
        pasada_mediana=round(statistics.median(rp), 3), n_pasadas=len(rp),
        pasada_en_noches_con_1_par=(round(statistics.median(rp_uni), 3) if rp_uni else None, len(rp_uni)),
        pasada_en_noches_con_2mas_pares=(round(statistics.median(rp_multi), 3) if rp_multi else None, len(rp_multi)),
        control_positivo_doble=round(statistics.median([2 * x for x in rn]), 3))
print(json.dumps(ahora, indent=1, ensure_ascii=False))
json.dump(ahora, open('salidas/v02_noche_vs_pasada.json', 'w'), indent=1, ensure_ascii=False)
