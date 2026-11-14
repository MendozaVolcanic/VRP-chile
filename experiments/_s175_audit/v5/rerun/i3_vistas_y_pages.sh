#!/usr/bin/env bash
# I3 extendido (mejora 6): firmas de mirovaEqVrp en las tres vistas, tabla INNER_RADIUS_KM de diario contra volcanoes.yaml,
# qué compara el guard de tres vistas, records que caen en las divergencias, y GitHub Pages contra la base 752d348bc.
R=/c/Users/nmend/vrp-temporales/s175_audit/f5/root
T=/c/Users/nmend/vrp-temporales/s175_audit/f5
for f in index diario mosaico; do echo "== $f"; grep -n "function mirovaEqVrp(" -A6 $R/frontend/$f.html | grep -v "^\S*-\s*//"; done
echo "== guard: funciones que compara"; grep -n "function\\s+\w*\|_cuerpo_\w*(" $R/tests/test_guard_predicado_tres_vistas_s147.py | head -5
echo "== records sin primary_cluster por vrp y distance_class, y PCC con cúmulo summit a 10-20 km"
PYTHONIOENCODING=utf-8 python -c "
import json,collections
V=['Lascar','Lastarria','Isluga','Tupungatito','PlanchonPeteroa','NevadosDeChillan','Llaima','Villarrica','Copahue','PuyehueCordonCaulle','Chaiten']
c=collections.Counter()
for v in V:
  for r in json.load(open(r'C:\Users\nmend\vrp-temporales\s175_audit\f5\root\data\mirova_equivalent\%s.json'%v,encoding='utf-8'))['records']:
    pc=r.get('primary_cluster')
    if not pc: c[('sin_pc','vrp>0' if (r.get('vrp_mw') or 0)>0 else 'vrp0',r.get('distance_class'))]+=1
    elif v=='PuyehueCordonCaulle' and pc.get('centroid_dist_km') is not None and 10<pc['centroid_dist_km']<=20 and (pc.get('vrp_mw') or 0)>0 and r.get('distance_class')=='summit': c[('PCC_pc_10_20km_summit',)]+=1
print(sorted(c.items(),key=str))
python_yaml_check=1
import yaml
Y={v['name']:v.get('inner_radius_km') for v in yaml.safe_load(open(r'C:\Users\nmend\vrp-temporales\s175_audit\f5\root\volcanoes.yaml',encoding='utf-8'))['volcanoes']}
D={'Lascar':5,'Lastarria':3,'Tupungatito':7,'Villarrica':5,'PuyehueCordonCaulle':20,'Copahue':4,'NevadosDeChillan':5,'Llaima':5,'Chaiten':5,'PlanchonPeteroa':3,'Isluga':5}
print('diario INNER_RADIUS_KM distinto de volcanoes.yaml:',{k:(D[k],Y[k]) for k in D if D[k]!=Y[k]})
"
echo "== GitHub Pages (bajado $(curl -sI https://github.com | grep -i '^date' | tr -d '\r')) contra la base, normalizado a LF"
mkdir -p $T/pages
for f in index.html diario.html mosaico.html cambio_detector.js; do curl -s -f -o $T/pages/$f "https://mendozavolcanic.github.io/VRP-chile/$f"; a=$(tr -d '\r' < $T/pages/$f | sha256sum | cut -c1-16); b=$(tr -d '\r' < $R/frontend/$f | sha256sum | cut -c1-16); echo "$f publicado=$a base=$b"; done
