"""Tarea 1.19 (ii): fuente sintetica subpixel pasada por la huella VIIRS 375 segun el angulo y por NUESTRO detector.

Fisica fijada antes de correr (PREREGISTRO.md): fuente a 800 K con area a = VRP / (18,0 (L4(800) - L4(263))),
VRP_verdadero 1,0 y 3,0 MW; fondo I04 263 K, I05 261 K, ruido gaussiano 0,5 K; toda la energia de la fuente en
UN pixel nativo (sin PSF). Huella: modelo esferico R = 6371 km, h = 833 km (ATBD Imagery p. 21) con agregacion
3/2/1 en 31,589 / 44,680 grados de barrido (ATBD geolocalizacion p. 14 y 27). NO es VNP03: es un modelo declarado,
contrastado contra las cotas del ATBD (factor de borde) en la salida.

Corre `calculate_vrp` + `store.append_record` de PRODUCCION (perfil mirova_equivalent) con la lectura del L1B
reemplazada (patron de experiments/_s151_saturacion_chillan/probe_saturacion.py:105, importado, no copiado).
Volcan: Lascar (sin kernel local, inner 5 km, radio 25 km). Hora 06:00 UTC (noche).
"""
import sys, io, os, json, math, pathlib, tempfile, warnings
import numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
REPO = pathlib.Path(r'C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile')
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / 'scripts'))
sys.path.insert(0, str(REPO / 'experiments' / '_s151_saturacion_chillan'))
os.environ['VRP_PROFILE'] = 'mirova_equivalent'
import h5py
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import probe_saturacion as P
import run_pipeline as rp
from pipeline.geo_utils import get_detection_anchor

R, H = 6371.0, 833.0
C1, C2 = 1.191042e8, 14388.0
L = lambda T, lam: C1 / (lam ** 5 * (np.exp(C2 / (lam * T)) - 1))
BT = lambda Lv, lam: C2 / (lam * np.log(C1 / (lam ** 5 * Lv) + 1))
A_NADIR = 140625.0
TB4, TB5, SIG, THOT = 263.0, 261.0, 0.5, 800.0


from huella import huella  # modelo compartido con 03


def granulo(z_deg, vrp_mw, semilla, vlat, vlon, tmp):
    dxs, dyt = huella(z_deg)
    A = dxs * dyt
    nx, ny = int(math.ceil(80e3 / dxs)) | 1, int(math.ceil(80e3 / dyt)) | 1
    i0, j0 = ny // 2, nx // 2
    ii, jj = np.mgrid[0:ny, 0:nx]
    lat = (vlat - (ii - i0) * dyt / 111320.0).astype(np.float32)
    lon = (vlon + (jj - j0) * dxs / (111320.0 * math.cos(math.radians(vlat)))).astype(np.float32)
    rng = np.random.default_rng(semilla)
    t4 = TB4 + rng.normal(0, SIG, (ny, nx))
    t5 = TB5 + rng.normal(0, SIG, (ny, nx))
    a_hot = vrp_mw * 1e6 / (18.0 * (L(THOT, 3.74) - L(TB4, 3.74)))
    p = a_hot / A
    l4 = (1 - p) * L(t4[i0, j0], 3.74) + p * L(THOT, 3.74)
    l5 = (1 - p) * L(t5[i0, j0], 11.45) + p * L(THOT, 11.45)
    t4[i0, j0], t5[i0, j0] = BT(l4, 3.74), BT(l5, 11.45)
    geo = pathlib.Path(tmp) / f'VNP03IMG.A2026280.0600.002.2026280120000.nc'
    with h5py.File(geo, 'w') as f:
        g = f.create_group('geolocation_data')
        g['latitude'], g['longitude'] = lat, lon
        g['sensor_zenith'] = np.full((ny, nx), z_deg, np.float32)
    l1b = pathlib.Path(tmp) / 'VNP02IMG.A2026280.0600.002.2026280120000.nc'
    l1b.touch()
    return l1b, geo, {'I04': t4.astype(np.float32), 'I05': t5.astype(np.float32)}, A, float(t4[i0, j0])


def main():
    volc = rp.load_volcanoes('Lascar')[0]
    vlat, vlon = get_detection_anchor(volc)
    # contraste del modelo contra el ATBD: factores en el borde (56,063 de barrido = 69,74 de cenit)
    zb = math.degrees(math.asin((R + H) / R * math.sin(math.radians(56.063))))
    s_b, t_b = huella(zb)
    print(f'borde cenit {zb:.2f}: along-scan x{s_b/375:.2f} (ATBD M: 776->1600 = x2.06), along-track x{t_b/375:.2f} (742->1600 = x2.16), area x{s_b*t_b/A_NADIR:.2f}')
    angs = sorted(set([2, 6, 10, 14, 18, 22, 26, 30, 33, 35, 35.9, 36.8, 38, 41, 44, 47, 50, 52.2, 53.1, 55, 58, 61, 64, 67]))
    out = []
    for vrp in (1.0, 3.0):
        for z in angs:
            for sem in range(4):
                with tempfile.TemporaryDirectory() as tmp:
                    l1b, geo, datos, A, t4c = granulo(z, vrp, 1000 * sem + int(10 * z), vlat, vlon, tmp)
                    rec = P.correr_brazo('V375', l1b, geo, volc, datos)
                r = P.resumir(rec) or {}
                pred = vrp * A_NADIR / A
                out.append(dict(vrp_true=vrp, cenit=z, semilla=sem, area_rel=A / A_NADIR, t4_centro=round(t4c, 2),
                                pred_nuestro=pred, pc_vrp=r.get('pc_vrp'), f5=r.get('f5_core_vrp_mw'),
                                pc_n=r.get('pc_n'), dc=r.get('dc'), vrp_mw=r.get('vrp_mw')))
            sel = [o for o in out if o['vrp_true'] == vrp and o['cenit'] == z]
            f5 = [o['f5'] if o['f5'] is not None else o['pc_vrp'] for o in sel]
            f5 = [x for x in f5 if x is not None]
            print(f"VRP {vrp} cenit {z:5.1f} area x{sel[0]['area_rel']:.2f} T4c {sel[0]['t4_centro']:.1f} pred {sel[0]['pred_nuestro']:.3f} "
                  f"pc {[o['pc_vrp'] for o in sel]} f5 {[o['f5'] for o in sel]} n {[o['pc_n'] for o in sel]} dc {[o['dc'] for o in sel]}", flush=True)
    pathlib.Path(__file__).with_name('02_salida.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
