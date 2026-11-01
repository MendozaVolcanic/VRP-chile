# M1 T19. Cuanto depende el VRP del oraculo (y su 'acuerdo de 0,09 %' con el OSF) del desempate de la triangulacion
# de griddata en una grilla regular (fillmissing2 'linear' de MATLAB no se puede ejecutar aqui). Se corre el oraculo
# sobre Etna con (a) la convencion del port (columna, fila), (b) (fila, columna), (c) 30 perturbaciones de 1e-9 en las
# coordenadas que rompen los empates al azar. Pregunta 1: si el 0,09 % fuera independiente del desempate, (b) y (c)
# darian lo mismo que (a). Pregunta 2: control = (a) debe reproducir 9,880,936 W (el valor del README).
# Se trabaja en una COPIA del modulo dentro de esta carpeta (no se toca experiments/_s158_oraculo_mirova).
import sys,os,shutil,importlib.util,numpy as np,scipy.io as sio
from scipy.interpolate import griddata
src='experiments/_s158_oraculo_mirova/mirova_v750.py'
os.makedirs('experiments/_s158_audit_r2/m1/_copia',exist_ok=True)
shutil.copy(src,'experiments/_s158_audit_r2/m1/_copia/mirova_v750_copia.py')
spec=importlib.util.spec_from_file_location('mv','experiments/_s158_audit_r2/m1/_copia/mirova_v750_copia.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
S=sio.loadmat('experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat')
sg=m.sunglint_angle(S['sat_zen'].item(),S['sun_zen'].item(),S['sat_azi'].item(),S['sun_azi'].item())
a=m.hotspot_detection(S['ZI_M13'],S['ZI_M15'],S['BOX'],0,sg)
OSF=9889528.362
def run(fill):
    m._fillmissing2_linear=fill
    v,n,*_=m.vrp(S['ZI_M13'],a); return v*1e6,n
def mk(order,jit=0.0,seed=0):
    rng=np.random.default_rng(seed)
    def f(A):
        ok=np.isfinite(A)
        if ok.all(): return A.copy()
        fi,co=np.indices(A.shape); out=A.copy()
        P=np.column_stack([co[ok],fi[ok]]) if order=='cf' else np.column_stack([fi[ok],co[ok]])
        Q=np.column_stack([co[~ok],fi[~ok]]) if order=='cf' else np.column_stack([fi[~ok],co[~ok]])
        if jit: P=P+rng.normal(0,jit,P.shape)
        out[~ok]=griddata(P,A[ok],Q,method='linear'); return out
    return f
a_,n_=run(mk('cf')); print('(a) columna,fila (port): VRP %.1f W  (%+.3f %% vs OSF)  npix %d'%(a_,100*(a_/OSF-1),n_))
b_,_=run(mk('fc')); print('(b) fila,columna        : VRP %.1f W  (%+.3f %% vs OSF)'%(b_,100*(b_/OSF-1)))
vs=np.array([run(mk('cf',1e-9,s))[0] for s in range(30)])
print('(c) 30 desempates al azar: min %+.3f %%  mediana %+.3f %%  max %+.3f %% vs OSF; amplitud (max-min) %.3f %%'%(100*(vs.min()/OSF-1),100*(np.median(vs)/OSF-1),100*(vs.max()/OSF-1),100*(vs.max()-vs.min())/OSF))
print('referencia: mutacion "sin dilatacion" del README = +0.76 %; brazo D25 = +2.65 % (README)')
