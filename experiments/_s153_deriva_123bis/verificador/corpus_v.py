# Reconteo independiente del corpus: snapshots por --first-parent, firma de 5 campos (la del investigador)
# y firma rica; ademas firma estructural del gate con anomaly_pixels (sp <= pixeles dentro del inner).
import json, subprocess, sys, io, collections, math, yaml, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
VOLS = ['Chaiten','Copahue','Isluga','Lascar','Lastarria','Llaima','NevadosDeChillan','PlanchonPeteroa','PuyehueCordonCaulle','Tupungatito','Villarrica']
Y = {v['name']: v for v in yaml.safe_load(open(REPO + '/volcanoes.yaml', encoding='utf-8'))['volcanoes']}
def sig5(r):
    return (r.get('n_anomalous_pixels'),r.get('diag_n_first_pass_pixels'),r.get('diag_n_second_pass_recapture'),r.get('product_version'),round(r.get('t_bg_k') or 0,3))
DET = ['n_anomalous_pixels','diag_n_first_pass_pixels','diag_n_second_pass_recapture','diag_n_dnti_ctx_path','n_hotspots_clustered','t_bg_k','t_max_k','diag_sigma_bg_k','granule','product_version']
def sigR(r):
    ap = r.get('anomaly_pixels') or []
    return tuple(r.get(k) for k in DET) + (hashlib.md5(json.dumps(ap, sort_keys=True).encode()).hexdigest(),)
def before(path, iso, fp):
    a = ['git','-C',REPO,'log','-1','--format=%H','--before='+iso] + (['--first-parent'] if fp else []) + ['HEAD','--',path]
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()
def load(c, path):
    b = subprocess.run(['git','-C',REPO,'show','%s:%s'%(c,path)], capture_output=True).stdout
    x = json.loads(b.decode('utf-8')); x = x['records'] if isinstance(x,dict) else x
    return {(r.get('datetime_utc'),r.get('sensor')): r for r in x}
def hav(a,b,c,d):
    R=6371.0; p1,p2=math.radians(a),math.radians(c); dp=p2-p1; dl=math.radians(d-b)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*R*math.asin(math.sqrt(h))
out = []; tot = collections.Counter()
for v in VOLS:
    p = 'data/mirova_equivalent/%s.json' % v
    cg_np, cf_np = before(p,'2026-05-28T04:44:00Z',False), before(p,'2026-07-01T20:46:00Z',False)
    cg, cf = before(p,'2026-05-28T04:44:00Z',True), before(p,'2026-07-01T20:46:00Z',True)
    G = load(cg,p); F = load(cf,p); H = load('HEAD',p)
    vy = Y[v]; vl, vo, inner = vy.get('vent_lat', vy.get('lat')), vy.get('vent_lon', vy.get('lon')), vy.get('inner_radius_km')
    for k, r in H.items():
        if not k[1].startswith('MODIS'): continue
        cls5 = ('ventana' if (k in F and sig5(F[k])==sig5(r) and not (k in G and sig5(G[k])==sig5(r))) else
                ('anterior' if (k in F and sig5(F[k])==sig5(r)) else 'posterior'))
        clsR = ('ventana' if (k in F and sigR(F[k])==sigR(r) and not (k in G and sigR(G[k])==sigR(r))) else
                ('anterior' if (k in F and sigR(F[k])==sigR(r)) else 'posterior'))
        n = r.get('n_anomalous_pixels') or 0; sp = r.get('diag_n_second_pass_recapture'); ap = r.get('anomaly_pixels') or []
        n_in = sum(1 for q in ap if hav(vl,vo,q['lat'],q['lon']) <= inner)
        out.append(dict(v=v, dt=k[0], s=k[1], cls5=cls5, clsR=clsR, n=n, sp=sp, fp=r.get('diag_n_first_pass_pixels'),
                        nap=len(ap), n_in=n_in, n_out=len(ap)-n_in, pv=r.get('product_version'), proc=r.get('processed_utc')))
        tot[(cls5, 'con_px' if n>0 else 'sin_px')] += 1
    print(v, 'G', cg_np[:9], cg[:9], 'F', cf_np[:9], cf[:9], flush=True)
print(dict(tot))
json.dump(out, open('corpus_v.json','w'))
