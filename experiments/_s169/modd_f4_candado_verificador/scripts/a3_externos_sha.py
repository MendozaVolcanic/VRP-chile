# P1: si el hash de la poblacion no calzara con externos_referencia.json, este script lo veria? Si: llama a la funcion real referencia_y_reetiquetado.
# P2: control positivo: misma llamada con un externos_referencia.json cuyo poblacion_sha256 se reemplaza por el hash LF de la poblacion -> debe dar OK.
import sys, json, hashlib, importlib.util
A='D:/vrp-trabajo/temporales/s169_ver_candado/arbol/experiments/_s166_modd_f4/'
sys.path.insert(0, A)
spec=importlib.util.spec_from_file_location('externos_f4', A+'externos_f4.py'); X=importlib.util.module_from_spec(spec); spec.loader.exec_module(X)
pob=open(A+'poblacion_f4.json','rb').read()
ref=json.load(open(A+'externos_referencia.json',encoding='utf-8'))
lf=X.sha256_lf(pob)
cab=[{'sha256_poblacion': lf}]   # lo que escribiria un job en Linux: sha256 LF de la poblacion
for nombre, r in (('committed (CRLF sha en el json)', ref), ('control positivo (sha LF en el json)', dict(ref, poblacion_sha256=lf))):
    out=X.referencia_y_reetiquetado(r, cab, pob)
    print(nombre, '->', {k:(v['estado'], v.get('motivo')) for k,v in out.items()})
# variante Windows: la poblacion local con CRLF
pobw=pob.replace(b'\n', b'\r\n')
out=X.referencia_y_reetiquetado(ref, cab, pobw)
print('local CRLF (checkout Windows autocrlf) ->', {k:(v['estado'], v.get('motivo')) for k,v in out.items()})
