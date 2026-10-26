"""S163 D-39: verificacion despues del merge de Mirova-v1#26, sin clonar (lee los CSV por la API de GitHub).
Compara el consolidado y el OCR del tag defensivo contra main: 0 llaves perdidas y 0 repetidas en main, las 2.351 llaves
de la reposicion presentes en main, y 0 notas con mojibake en el OCR.
Las dos preguntas del instrumento: (1) si se perdieran filas, ¿falla? Si: control positivo con --antes 53b1e6d3c0^ y
--despues 53b1e6d3c0, debe dar 241 perdidas y ROJO. (2) si no leyera nada, ¿se veria distinto? Si: con 0 filas leidas sale ROJO.
Uso: python -I s20_verificar_post_merge.py --antes pre-pr26-referencia-estable --despues main
Sale 0 (VERDE) o 1 (ROJO)."""
import argparse, csv, io, re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
REPO = 'MendozaVolcanic/Mirova-v1'
CONS = 'monitoreo_satelital/registro_vrp_consolidado.csv'; OCR = 'monitoreo_satelital/registro_vrp_ocr.csv'
REPO_FILAS = 'monitoreo_satelital/filas_perdidas_por_mezcla_2026.csv'
MOJ = re.compile('Ã|â€|â‰|Â')
def bajar(ruta, ref):
    r = subprocess.run(['gh', 'api', f'repos/{REPO}/contents/{ruta}?ref={ref}', '-H', 'Accept: application/vnd.github.raw'],
                       capture_output=True, stdin=subprocess.DEVNULL)
    if r.returncode != 0:
        return None
    return r.stdout.decode('utf-8')
def llave(f):
    ts = (f.get('timestamp') or '').strip()
    try: ts = str(int(float(ts)))
    except ValueError: pass
    return (ts, (f.get('Volcan') or '').strip(), (f.get('Sensor') or '').strip())
def filas(t): return list(csv.DictReader(io.StringIO(t))) if t else []
ap = argparse.ArgumentParser(); ap.add_argument('--antes', required=True); ap.add_argument('--despues', default='main')
ap.add_argument('--reposicion', default=None, help='ref de donde leer el archivo de reposicion (por defecto, --despues)')
a = ap.parse_args(); rojo = []
a.reposicion = a.reposicion or a.despues
for nombre, ruta in (('consolidado', CONS), ('OCR', OCR)):
    fa, fd = filas(bajar(ruta, a.antes)), filas(bajar(ruta, a.despues))
    ka = {llave(f) for f in fa}; kd = [llave(f) for f in fd]
    perd = ka - set(kd); rep = len(kd) - len(set(kd))
    print(f'{nombre}: antes {len(fa)} filas, despues {len(fd)}; llaves perdidas {len(perd)}; repetidas despues {rep}; nuevas {len(set(kd) - ka)}')
    for k in sorted(perd)[:5]: print('   perdida:', k)
    if not fa or not fd: rojo.append(f'{nombre}: 0 filas leidas')
    if perd: rojo.append(f'{nombre}: {len(perd)} llaves perdidas')
    if rep: rojo.append(f'{nombre}: {rep} llaves repetidas')
    if nombre == 'consolidado':
        rp = filas(bajar(REPO_FILAS, a.reposicion))
        faltan = [llave(f) for f in rp if llave(f) not in set(kd)]
        print(f'   reposicion ({a.reposicion}): {len(rp)} filas, faltan en despues {len(faltan)}')
        if rp and faltan: rojo.append(f'{len(faltan)} filas de la reposicion faltan')
        if not rp: rojo.append('sin archivo de reposicion en ' + a.reposicion)
    else:
        moj = sum(bool(MOJ.search(f.get('Nota_Validacion') or '')) for f in fd)
        print(f'   notas con mojibake despues: {moj}')
print('ROJO: ' + '; '.join(rojo) if rojo else 'VERDE')
sys.exit(1 if rojo else 0)
