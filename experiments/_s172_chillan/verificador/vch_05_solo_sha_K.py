# vch_05: Spearman razon vs cenit usando solo records con codigo_sha 34cea39e (merge de K, #850). Salida: salidas/v05_solo_sha_K.txt
import csv, math
exec(open('vch_04_plataforma_regimen.py', encoding='utf-8').read().split("out = {}")[0])
for b in ('MODIS', 'VIIRS375', 'VIIRS750'):
    P = [r for r in R if r['b'] == b and r['pub'] == '1' and float(r['disp']) > 0 and r['vrp_M'] not in ('', 'None') and float(r['vrp_M']) > 0 and r['sha'].startswith('34cea39e')]
    z = [float(r['z']) for r in P]; rz = [float(r['disp']) / float(r['vrp_M']) for r in P]
    print(b, 'solo codigo_sha=34cea39e (merge K #850): n', len(P), 'spearman', sp(z, rz))
