"""Verificador v2: espaciado en tierra entre filas y columnas consecutivas de los pixeles exportados
(lat/lon que uso el pipeline). Pregunta 1: si la geolocalizacion estuviera rota (filas a 0,3 km en vez
de 1-2 km), esto lo veria? Si, mide la distancia entre centros de pixeles vecinos. Control positivo: C3
(nadir) debe dar ~1 km entre filas y columnas."""
import json, sys, math
def hav(a,b,c,d):
    R=6371.0; p1,p2=math.radians(a),math.radians(c); dp=p2-p1; dl=math.radians(d-b)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*R*math.asin(math.sqrt(h))
for line in open(sys.argv[1], encoding="utf-8"):
    fila=json.loads(line); P=fila.get("P") or {}
    px={(q["i"],q["j"]):q for q in P.get("pixeles",[])}
    if not px: continue
    filas=[]; cols=[]
    for (i,j),q in px.items():
        if (i+1,j) in px: filas.append(hav(q["lat"],q["lon"],px[(i+1,j)]["lat"],px[(i+1,j)]["lon"]))
        if (i,j+1) in px: cols.append(hav(q["lat"],q["lon"],px[(i,j+1)]["lat"],px[(i,j+1)]["lon"]))
    filas.sort(); cols.sort()
    med=lambda x: x[len(x)//2] if x else None
    print(f"{fila['tag']} j_crater={P.get('pixel_crater')} n_lineas={P.get('n_lineas')} area_factor={P.get('area_factor_crater')} "
          f"fila->fila km: n={len(filas)} min={filas[0] if filas else None:.2f} med={med(filas):.2f} max={filas[-1] if filas else None:.2f} | "
          f"col->col km: n={len(cols)} min={cols[0] if cols else 0:.2f} med={med(cols) or 0:.2f} max={cols[-1] if cols else 0:.2f}")
