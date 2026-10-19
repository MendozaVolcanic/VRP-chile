"""inner_radius_km de volcanoes.yaml contra el valor escrito a mano en las vistas (index VOLCANOES_ALL, diario
INNER_RADIUS_KM, mosaico TIER_A; los tres iguales, leidos en esta sesion)."""
import yaml, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
d = yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))
vs = d["volcanoes"] if isinstance(d, dict) and "volcanoes" in d else d
F = {'Lascar':5,'Lastarria':3,'Tupungatito':7,'Villarrica':5,'PuyehueCordonCaulle':20,'Copahue':4,'NevadosDeChillan':5,'Llaima':5,'Chaiten':5,'PlanchonPeteroa':3,'Isluga':5}
it = vs.items() if isinstance(vs, dict) else [(v.get('name'), v) for v in vs]
for n, v in it:
    if n in F: print(n, v.get('inner_radius_km'), 'frontend', F[n], 'OK' if v.get('inner_radius_km') == F[n] else 'DIFIERE')
