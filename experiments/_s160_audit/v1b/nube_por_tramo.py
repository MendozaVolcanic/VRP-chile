"""R10 (#535) en un A/B reprocesado: existe el cambio de regimen dentro de los datos de los brazos?
#535 (1888c1e3e) hizo que VIIRS 375 lea la mascara de nube del perfil; el corpus de produccion escrito
antes la tenia encendida. Un brazo reprocesado entero con codigo posterior no deberia tenerla en ningun tramo.
Control positivo: el JSON de produccion de NdC en 1888c1e3e^ (antes de #535) debe mostrar n_cloud_masked > 0.
Pregunta 2: si el campo no existiera, el conteo de records con campo presente daria 0 y se avisa."""
import json, glob, sys, collections
def contar(archivos, desde='2026-06-01', hasta='2026-08-31'):
    c = collections.Counter()
    for f in archivos:
        r = json.load(open(f, encoding='utf-8')); r = r.get('records', r) if isinstance(r, dict) else r
        for x in r:
            s = x.get('sensor', '')
            if not s.startswith('VIIRS') or s.endswith('750'): continue
            if not (desde <= x['datetime_utc'][:10] <= hasta): continue
            t = 'post535' if x['datetime_utc'] >= '2026-08-28T23:00' else 'pre535'
            c[(t, 'n')] += 1; c[(t, 'con_campo')] += 'n_cloud_masked' in x
            c[(t, 'nube>0')] += (x.get('n_cloud_masked') or 0) > 0
    return dict(c)
print('CONTROL POSITIVO produccion NdC antes de #535:', contar([sys.argv[1]], hasta='2026-08-27'))
print('S143 brazo control (9 volcanes):', contar(glob.glob(sys.argv[2] + '/s143ab-_s142_ab_control-*/*.json')))
print('S143 brazo lit_con_compuerta:', contar(glob.glob(sys.argv[2] + '/s143ab-_s142_ab_lit_con_compuerta-*/*.json')))
