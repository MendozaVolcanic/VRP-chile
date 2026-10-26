"""S163 D-39: corre en una copia (sim/A o sim/B) un ciclo de scraper.py con la red simulada
(latest.php = la descarga del 2026-10-22; imagenes = 404) y la hora fija, como lo haria main.yml.
Uso: python s08_correr_ciclo.py <dir_brazo>   (cwd = el brazo; el brazo decide su propio codigo)."""
import os, sys, runpy, types
brazo = sys.argv[1]; os.chdir(brazo); sys.path.insert(0, brazo)
import requests
HTML = open(r'D:\vrp-trabajo\s163-d39\scripts\latest_20261022.html', encoding='utf-8', errors='replace').read()
class Resp:
    def __init__(s, code, text='', content=b''): s.status_code, s.text, s.content = code, text, content
def get(self, url, *a, **k):
    return Resp(200, HTML, HTML.encode()) if 'latest.php' in url else Resp(404)
requests.Session.get = get
import horas_utc
fijo = horas_utc.ahora_cl_y_utc(__import__('datetime').datetime(2026, 10, 26, 12, 0, 0, tzinfo=__import__('pytz').utc))
horas_utc.ahora_cl_y_utc = lambda *_a, **_k: fijo
sys.argv = ['scraper.py']
try:
    runpy.run_path('scraper.py', run_name='__main__')
    print('scraper: salida 0 (sin sys.exit)')
except SystemExit as e:
    print('scraper: SystemExit', e.code)
