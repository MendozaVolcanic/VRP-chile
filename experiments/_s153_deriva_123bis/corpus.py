# Clasifica TODOS los records del corpus (11 Tier A) segun en que regimen del gate intra-radio se escribieron,
# comparando el record en tres fotos del JSON: antes del gate (#224, 2026-05-26), antes del flip (#474, 2026-07-01) y HEAD.
import json,subprocess,sys,io,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
REPO="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
VOLS=sys.argv[1:] or ['Chaiten','Copahue','Isluga','Lascar','Lastarria','Llaima','NevadosDeChillan','PlanchonPeteroa','PuyehueCordonCaulle','Tupungatito','Villarrica']
def sig(r):
    return (r.get('n_anomalous_pixels'),r.get('diag_n_first_pass_pixels'),r.get('diag_n_second_pass_recapture'),r.get('product_version'),round(r.get('t_bg_k') or 0,3))
def commit_before(path,iso):
    return subprocess.run(['git','-C',REPO,'log','-1','--format=%H','--before='+iso,'HEAD','--',path],capture_output=True,text=True).stdout.strip()
def load(c,path):
    b=subprocess.run(['git','-C',REPO,'show','%s:%s'%(c,path)],capture_output=True).stdout
    x=json.loads(b.decode('utf-8')); x=x['records'] if isinstance(x,dict) else x
    return {(r.get('datetime_utc'),r.get('sensor')):r for r in x}
tot=collections.Counter(); res={}
for v in VOLS:
    p='data/mirova_equivalent/%s.json'%v
    cg=commit_before(p,'2026-05-28T04:44:00Z'); cf=commit_before(p,'2026-07-01T20:46:00Z')
    G={k:sig(r) for k,r in load(cg,p).items()} if cg else {}
    F_full=load(cf,p); F={k:sig(r) for k,r in F_full.items()}; del F_full
    H=load('HEAD',p)
    c=collections.Counter()
    for k,r in H.items():
        s=sig(r); fam=('MODIS' if k[1].startswith('MODIS') else ('V750' if k[1].endswith('_750') else 'V375'))
        if k in F and F[k]==s:
            if k in G and G[k]==s: cls='anterior_al_gate'
            else: cls='ventana_gate'
        else: cls='posterior_al_flip'
        # dentro de ventana_gate: tiene pixeles? (un record sin pixeles no puede perder recaptura)
        extra='con_px' if (r.get('n_anomalous_pixels') or 0)>0 else 'sin_px'
        c[(fam,cls,extra)]+=1
    res[v]={'|'.join(k):n for k,n in c.items()}
    tot.update(c)
    print(v,cg[:9],cf[:9],{('|'.join(k)):n for k,n in sorted(c.items())},flush=True)
print('TOTAL')
for k in sorted(tot): print(k,tot[k])
json.dump({'por_volcan':res,'total':{'|'.join(k):n for k,n in tot.items()}},open('corpus.json','w'),indent=1)
