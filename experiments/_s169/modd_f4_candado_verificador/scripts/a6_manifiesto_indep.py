# P1: si un archivo del arbol difiriera del manifiesto, lo vería (recalculo independiente, sin importar manifiesto_candado_f4).
# P2: control positivo: cambio un byte de una copia en memoria y compruebo que el hash cambia.
import json, hashlib, os
R='D:/vrp-trabajo/temporales/s169_ver_candado/arbol/'
m=json.load(open(R+'experiments/_s166_modd_f4/MANIFIESTO_CANDADO_F4.json',encoding='utf-8'))
mal=[]
for f,h in m['archivos'].items():
    b=open(R+f,'rb').read().replace(b'\r\n',b'\n')
    if hashlib.sha256(b).hexdigest()!=h: mal.append(f)
print('archivos', len(m['archivos']), 'distintos', mal, 'tag', m['tag'], 'commit_tag', m['commit_tag'])
b=open(R+'frontend/index.html','rb').read(); print('control positivo (1 byte cambiado cambia el hash):', hashlib.sha256(b).hexdigest()!=hashlib.sha256(b+b'x').hexdigest())
# archivos de la familia del candado en el arbol que NO estan en el manifiesto
d=R+'experiments/_s166_modd_f4/'
fuera=[f for f in sorted(os.listdir(d)) if 'experiments/_s166_modd_f4/'+f not in m['archivos']]
print('en _s166_modd_f4 y fuera del manifiesto:', fuera)
