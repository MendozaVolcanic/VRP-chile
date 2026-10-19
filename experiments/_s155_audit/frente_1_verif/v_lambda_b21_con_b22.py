"""V1-02: con ENABLE_MODIS_B22_PRIMARY=True el BT/radiancia MIR sale de la banda 22, pero la magnitud
(process_modis.py:1036,1040) y el NTI_app de los Tests 2-3 (l.773, l.857) siguen usando BAND21_LAMBDA.
Mide cuanto cambia (a) el Delta L de Wooster y (b) el residuo de NTI_app(l21) vs NTI_app(l22) tras un
ajuste cuadratico (que es lo que hace el ETI).
Pregunta 1: si las dos longitudes fueran iguales, todo daria 0 (control: l21 contra l21 -> 0 exacto).
Pregunta 2: el instrumento es la funcion de Planck del propio pipeline (radiancia_planck / constantes)."""
import numpy as np, sys
sys.path.insert(0,'.')
from pipeline.process_modis import BAND21_LAMBDA as L21, BAND22_LAMBDA as L22, BAND31_LAMBDA as L31
from pipeline.process_modis import C1, C2
def P(T,l): return C1/(l**5*(np.exp(C2/(l*T))-1))
for tag,la,lb in [('control l21-l21',L21,L21),('l21 vs l22',L21,L22)]:
    print('==',tag)
    for tbg,thot in [(250,255),(260,270),(270,290),(270,320),(280,400)]:
        dla=P(thot,la)-P(tbg,la); dlb=P(thot,lb)-P(tbg,lb)
        print(f'  Tbg={tbg} Thot={thot}: dL({la})={dla:.5f} dL({lb})={dlb:.5f} ratio={dla/dlb:.4f}')
    # NTI_app: radiancia MIR sintetica a BT31 frente a radiancia TIR
    T=np.linspace(220,300,400)
    nti_a=(P(T,la)-P(T,L31))/(P(T,la)+P(T,L31)); nti_b=(P(T,lb)-P(T,L31))/(P(T,lb)+P(T,L31))
    c=np.polyfit(nti_a,nti_b,2); res=nti_b-np.polyval(c,nti_a)
    print(f'  NTI_app(l_b) ajustado cuadratico sobre NTI_app(l_a): residuo max abs={np.abs(res).max():.2e} (C1 summit=0.003)')
