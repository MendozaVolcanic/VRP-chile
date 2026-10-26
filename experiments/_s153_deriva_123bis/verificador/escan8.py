# Barrido lineal (no biseccion) de los 8 records sobre TODOS los commits no-NRT que tocaron el JSON
# desde 2026-04-01, mas un muestreo de commits NRT, comparando campos de deteccion completos.
import json, subprocess, sys, io, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
OCHO = [('Chaiten','2026-03-06 07:00','MODIS_AQUA'),('Chaiten','2026-04-28 07:55','MODIS_AQUA'),
        ('Copahue','2026-03-06 01:35','MODIS_TERRA'),('Isluga','2026-05-09 08:15','MODIS_AQUA'),
        ('Isluga','2026-05-18 07:25','MODIS_AQUA'),('Isluga','2026-05-19 08:05','MODIS_AQUA'),
        ('Llaima','2026-03-11 01:35','MODIS_TERRA'),('NevadosDeChillan','2026-03-19 01:50','MODIS_TERRA')]
DET = ['n_anomalous_pixels','diag_n_first_pass_pixels','diag_n_second_pass_recapture','diag_n_dnti_ctx_path',
       'n_hotspots_clustered','t_bg_k','t_max_k','diag_sigma_bg_k','granule','product_version']
def h(r):
    if r is None: return None
    ap = r.get('anomaly_pixels') or []
    return tuple(r.get(k) for k in DET) + (len(ap), hashlib.md5(json.dumps(ap, sort_keys=True).encode()).hexdigest()[:8])
vols = sorted({v for v,_,_ in OCHO})
for v in vols:
    path = 'data/mirova_equivalent/%s.json' % v
    log = subprocess.run(['git','-C',REPO,'log','--format=%H|%cI|%s','--since=2026-05-25','--',path],capture_output=True,text=True,encoding='utf-8').stdout.strip().split('\n')
    log = [l.split('|',2) for l in log][::-1]
    sel = [l for l in log if not l[2].startswith('NRT update')]
    nrt = [l for l in log if l[2].startswith('NRT update')]
    sel += nrt[::max(1,len(nrt)//12)]
    sel.sort(key=lambda l: l[1])
    keys = [(d,s) for vv,d,s in OCHO if vv==v]
    prev = {k: 'INI' for k in keys}
    print('==', v, len(log), 'commits; revisados', len(sel))
    for c, t, msg in sel:
        b = subprocess.run(['git','-C',REPO,'show','%s:%s'%(c,path)],capture_output=True).stdout
        try: x = json.loads(b.decode('utf-8'))
        except Exception: print('  no parse', c[:9]); continue
        x = x['records'] if isinstance(x,dict) else x
        idx = {(r.get('datetime_utc'),r.get('sensor')): r for r in x if (r.get('datetime_utc'),r.get('sensor')) in keys}
        for k in keys:
            s = h(idx.get(k))
            if s != prev[k]:
                print('  ', k, c[:9], t[:16], msg[:55], '->', s)
                prev[k] = s
