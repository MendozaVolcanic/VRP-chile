"""Cuantas noches confirmadas y perdidas del A/B S143 caen en tramos con hitos de la referencia
(OCR sin geometria/distancia fiable antes de 2026-06-14) o despues de #535 (2026-08-29 en adelante).
Pregunta 1: si los hitos decidieran el veredicto, se veria (perdidas concentradas antes de 06-14). Pregunta 2:
si el script estuviera muerto daria 0 confirmadas; exige total > 0."""
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
f = d['noches_confirmadas']['fechas']
tot = sum(len(v) for v in f.values()); assert tot > 0
print('confirmadas', tot, '| antes de 2026-06-14:', sum(x < '2026-06-14' for v in f.values() for x in v),
      '| desde 2026-08-29:', sum(x >= '2026-08-29' for v in f.values() for x in v))
for b, v in d['brazos'].items():
    p = v['criterio1']['perdidas']
    print(b, 'perdidas', len(p), '| antes 06-14:', sum(x['fecha'] < '2026-06-14' for x in p),
          '| desde 08-29:', sum(x['fecha'] >= '2026-08-29' for x in p), '| cumple_1_2_3', v['cumple_1_2_3'])
print('control neg_limpio tasa publica', d['control']['neg_limpio_tasa_publica'], 'n', d['control']['neg_limpio_n'])
