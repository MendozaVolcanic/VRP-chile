# M07: port minimo (escrito desde cero) de MIROVA_VIIRS750_hotspot_detection.m sobre la matriz de ejemplo,
# para medir (a) cuantas alertas da cada pase y en que clase de BOX, (b) que con el primer pase contextual vacio el
# segundo devuelve lo mismo (condicion (a) del paper nula en efecto), (c) VRP con y sin recorte de deltaL.
# Pregunta 1: si el segundo pase dependiera de algo mas que de las alertas del primero, el control (b) lo veria
#   (se compara la salida del pase 2 con alertas previas vacias contra la del pase 1, elemento a elemento).
# Pregunta 2: control positivo = el ejemplo de MIROVA debe dar alertas (> 0) dentro de la caja BOX==2; si el port
#   estuviera muerto daria 0 en todo y se veria.
# Limite: colfilt de MATLAB rellena con ceros; aca relleno con NaN. Solo afecta a pixeles vecinos del marco, que el
#   codigo ya excluye (BOX del marco = NaN). No reproduce el redondeo de MATLAB.
import numpy as np, scipy.io as sio
from scipy.ndimage import binary_dilation
p = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2\experiments\_s158_d17_diseno\osf_codigo_mirova\Example\VIIRS750_example.mat"
S = sio.loadmat(p)
M13 = S["ZI_M13"].astype(float); M15 = S["ZI_M15"].astype(float); BOX = S["BOX"].astype(float)
BOX[:, [0, -1]] = np.nan; BOX[[0, -1], :] = np.nan
h=6.6256e-34; c=2.9979e8; k=1.38e-23
def r2t(L, lam):
    lm=lam*1e-6; return (h*c/k)/lm/np.log(2*h*c**2/(lm**5*(L*1e6))+1)
def t2r(T, lam):
    lm=lam*1e-6; return (2*3.14*h*c**2/(lm**5*(np.exp(h*c/k/(lm*T))-1))*1e-6)/3.14
def mean3(A):
    P = np.pad(A, 1, constant_values=np.nan)
    st = np.stack([P[i:i+A.shape[0], j:j+A.shape[1]] for i in range(3) for j in range(3)])
    with np.errstate(all="ignore"): return np.nanmean(st, axis=0)
excl = np.isnan(BOX)
m0 = np.where(BOX==0,1.0,np.nan); m1 = np.where(BOX==1,1.0,np.nan); m2 = np.where(BOX==2,1.0,np.nan)
BT15 = r2t(M15, 10.763); cold = BT15 <= 200; BT15[cold]=np.nan; M15[cold]=np.nan
with np.errstate(all="ignore"): NTI = (M13-M15)/(M13+M15)
NTIR = NTI.copy(); NTIR[excl]=np.nan
K1=-0.7; s1,s2=10,5; n1,n2=0.02,0.003; e1,e2=0.01,0.003
absal = np.flatnonzero((NTIR > K1).ravel())
def pase(prev):
    pop = NTIR.copy().ravel(); pop[absal]=np.nan; pop[prev]=np.nan; pop=pop.reshape(NTIR.shape)
    lb = mean3(pop); lb[excl]=np.nan
    dn = pop - lb; dn[dn < -0.1] = np.nan
    mu, sd = np.nanmean(dn), np.nanstd(dn, ddof=1)
    tn1, tn2 = max(mu+s1*sd, n1), max(mu+s2*sd, n2)
    exp13 = t2r(BT15, 4.05)
    with np.errstate(all="ignore"): ntiapp = (exp13-M15)/(exp13+M15)
    na = ntiapp.ravel().copy(); na[absal]=np.nan; na[prev]=np.nan; na=na.reshape(NTIR.shape); na[excl]=np.nan
    v = np.isfinite(na) & np.isfinite(pop)
    cf = np.polyfit(na[v], pop[v], 2); ref = np.polyval(cf, na)
    eti = pop - ref; de = eti - mean3(eti); de[excl]=np.nan
    mue, sde = np.nanmean(de), np.nanstd(de, ddof=1)
    te1, te2 = max(mue+s1*sde, e1), max(mue+s2*sde, e2)
    with np.errstate(invalid="ignore"):
        a0 = np.flatnonzero(((dn*m0>tn1)&(de*m0>te1)).ravel(order="F"))
        a1 = np.flatnonzero(((dn*m1>tn1)&(de*m1>te1)).ravel(order="F"))
        a2 = np.flatnonzero(((dn*m2>tn2)&(de*m2>te2)).ravel(order="F"))
    # devolver en indices C para reusar
    toC = lambda idx: np.ravel_multi_index(np.unravel_index(idx, NTIR.shape, order="F"), NTIR.shape)
    return toC(a0), toC(a1), toC(a2), (tn1,tn2,te1,te2)
p1 = pase(np.array([],dtype=int)); c1 = np.concatenate(p1[:3])
p2 = pase(c1)
print("alertas absolutas (NTI>-0,7):", len(absal))
print("pase 1 por clase BOX0/ROI1(BOX==1)/ROI2(BOX==2):", [len(x) for x in p1[:3]], "umbrales", np.round(p1[3],5))
print("pase 2 por clase:", [len(x) for x in p2[:3]], "umbrales", np.round(p2[3],5))
alert = np.concatenate([c1, absal, *p2[:3]])
print("alert total:", len(alert), "unicos:", len(np.unique(alert)))
# (b) control: segundo pase con prev vacio == primer pase
p2v = pase(np.array([],dtype=int))
print("(b) pase con prev vacio == pase 1:", all(np.array_equal(a,b) for a,b in zip(p1[:3],p2v[:3])))
# (c) VRP como el .m (sin recorte) y con recorte por pixel
npix=len(alert); ks = 3 if npix<=4 else (5 if npix<=30 else 7)
mask = np.zeros(M13.size,bool); mask[alert]=True; mask=mask.reshape(M13.shape)
ex = binary_dilation(mask, structure=np.ones((ks,ks),bool))
from scipy.interpolate import griddata
yy,xx = np.mgrid[0:M13.shape[0],0:M13.shape[1]]
ok = ~ex & np.isfinite(M13)
bk = griddata((yy[ok],xx[ok]), M13[ok], (yy,xx), method="linear")
dL = M13.ravel()[alert] - bk.ravel()[alert]
print("deltaL por pixel:", np.round(dL,4), " suma:", round(float(np.nansum(dL)),5), " suma con recorte >=0:", round(float(np.nansum(np.maximum(dL,0))),5))
print("VRP MW sin recorte:", round(float(np.nansum(dL))*1.97e7*0.5625/1e6,4))
print("(nota: griddata lineal no es fillmissing2; el fondo es aproximado)")
