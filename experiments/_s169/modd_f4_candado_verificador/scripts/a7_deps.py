# P1: si el arnes/bateria importaran un paquete que el workflow no instala, lo veria: lista de paquetes de terceros cargados tras importar todo lo que usa la `prueba` y el `probe`.
# P2: control positivo: debe listar numpy y scipy (los que el workflow instala). 
import sys, os
R='D:/vrp-trabajo/temporales/s169_ver_candado/arbol'; A=R+'/experiments/_s166_modd_f4'
os.environ.setdefault('VRP_PROFILE','mirova_equivalent')
sys.path[:0]=[R,R+'/scripts',A]
import probe_f4, evaluar_f4, identidad_f4, probar_probe_f4, probar_evaluar_f4, manifiesto_candado_f4, externos_f4, head_e, poblacion_f4  # poblacion_f4 solo informativo
import run_pipeline
from pipeline.fetch import auth, download_granules
top=sorted({m.split('.')[0] for m,v in sys.modules.items() if getattr(v,'__file__',None) and 'site-packages' in (v.__file__ or '').replace(chr(92),'/')})
print(top)
