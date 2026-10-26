"""S163 D-39 (punto 3): mutaciones sobre el codigo del PR #26 (copia en mut/). Cada mutacion quita un arreglo;
se corre la prueba que deberia atraparla y se cuenta como ATRAPADA solo si falla por asercion (failure en el
JUnit), no por error de importacion o caida (leccion S152). Control: sin mutacion todas pasan."""
import subprocess, sys, os, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding='utf-8')
M = r'D:\vrp-trabajo\s163-d39\mut'
MUT = [
 ('control (sin mutacion)', None, None, None, 'tests/test_orden_determinista.py tests/test_guarda_llaves.py tests/test_reponer_filas.py tests/test_fallo_ruidoso.py tests/test_reparar_mojibake.py tests/test_bucle_push_main_yml.py'),
 ('R1 orden viejo (solo timestamp, empates sin desempate)', 'orden_registros.py', "return df.sort_values(COLUMNAS_ORDEN, ascending=[False, True, True], kind='mergesort')", "return df.sample(frac=1).sort_values('timestamp', ascending=False)", 'tests/test_orden_determinista.py'),
 ('R3 guarda no mira llaves perdidas', 'guarda_llaves.py', 'perdidas = set(_llaves(texto_anterior)) - set(nuevas)', 'perdidas = set()', 'tests/test_guarda_llaves.py'),
 ('R3 guarda no mira repetidas', 'guarda_llaves.py', '    if repetidas:\n', '    if False:\n', 'tests/test_guarda_llaves.py'),
 ('R3 guarda sale 0 aunque haya problemas', 'guarda_llaves.py', '        return 1\n    print(f\'Guarda de llaves OK', '        return 0\n    print(f\'Guarda de llaves OK', 'tests/test_guarda_llaves.py'),
 ('R4 reponer pisa filas existentes', 'reponer_filas.py', 'faltan = validas[[k not in existentes for k in zip(*(validas[c] for c in LLAVE))]]', 'faltan = validas', 'tests/test_reponer_filas.py'),
 ('R4 reponer sin filtro de nombres y tipos', 'reponer_filas.py', 'validas = df_perdidas[df_perdidas["Volcan"].isin(NOMBRES) & df_perdidas["Tipo_Registro"].isin(TIPOS)]', 'validas = df_perdidas', 'tests/test_reponer_filas.py'),
 ('H-P1 scraper sale 0 en falla', 'scraper.py', '        log_debug(f"ERROR: {e}", "ERROR")\n        return 1', '        log_debug(f"ERROR: {e}", "ERROR")\n        return 0', 'tests/test_fallo_ruidoso.py'),
 ('H-O8 mojibake: repara el texto entero, no por tramo', 'reparar_mojibake.py', '    return _TRAMO.sub(_reparar_tramo, texto)', '    try:\n        return texto.encode("cp1252").decode("utf-8")\n    except Exception:\n        return texto', 'tests/test_reparar_mojibake.py'),
 ('R2 main.yml sin reset a origin/main', '.github/workflows/main.yml', '            git reset --hard origin/main\n', '', 'tests/test_bucle_push_main_yml.py'),
 ('R2 main.yml vuelve el pull -X ours antes del push', '.github/workflows/main.yml', '            if git push origin main; then echo', '            git pull origin main --rebase --autostash -X ours || true\n            if git push origin main; then echo', 'tests/test_bucle_push_main_yml.py'),
 ('R3 main.yml sin guarda', '.github/workflows/main.yml', '            python guarda_llaves.py "$CSV" --ref origin/main\n', '', 'tests/test_bucle_push_main_yml.py'),
 ('R2 ocr_workflow vuelve -X ours', '.github/workflows/ocr_workflow.yml', 'if ! git pull origin main --rebase --autostash; then', 'if ! git pull origin main --rebase --autostash -X ours; then', 'tests/test_bucle_push_main_yml.py'),
]
env = dict(os.environ, PYTHONUTF8='1'); env.pop('MSYS_NO_PATHCONV', None)
for nom, archivo, viejo, nuevo, pruebas in MUT:
    orig = None
    if archivo:
        p = os.path.join(M, archivo); orig = open(p, encoding='utf-8', newline='').read()
        assert orig.count(viejo) == 1, (nom, orig.count(viejo))
        open(p, 'w', encoding='utf-8', newline='').write(orig.replace(viejo, nuevo))
    try:
        x = os.path.join(M, 'junit_mut.xml')
        subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', f'--junitxml={x}', *pruebas.split()], cwd=M, env=env, capture_output=True, text=True)
        t = ET.parse(x).getroot(); s = t if t.tag == 'testsuite' else t[0]
        f, e, n = int(s.get('failures')), int(s.get('errors')), int(s.get('tests'))
        fallidas = [c.get('name') for c in s.iter('testcase') if c.find('failure') is not None]
        veredicto = 'CONTROL OK' if (archivo is None and f + e == 0) else ('ATRAPADA' if f > 0 else ('CAE (error, no cuenta)' if e else 'NO ATRAPADA'))
        print(f'{veredicto:22s} | {nom} | {n} pruebas, {f} fallan por asercion, {e} errores | {fallidas[:3]}')
    finally:
        if orig is not None: open(p, 'w', encoding='utf-8', newline='').write(orig)
