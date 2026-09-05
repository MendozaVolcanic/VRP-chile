# -*- coding: utf-8 -*-
"""VERIF/04 - el control de georreferencia de 03_ mide desde el CRATER, no desde el centro.
semi_km = nanmax(dist al VENT) = distancia del vent a la esquina mas lejana. Compararla con
25,5*raiz(2)=36,06 solo cuadra porque el vent esta cerca del centro. Mido el semiancho REAL
del raster (desde su propio centro) y la media-diagonal, que es lo que S131 midio (25,29-25,65)."""
import os, sys, io, math, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import numpy as np, rasterio, yaml
RAIZ="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
TIFD="C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s134-f2/experiments/_s134_audit/tif"
CAT={v["name"]:v for v in yaml.safe_load(open(os.path.join(RAIZ,"volcanoes.yaml"),encoding="utf-8"))["volcanoes"]}
def hav(a,b,c,d):
    R=6371.0088;p1,p2=math.radians(a),math.radians(c)
    x=(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2)
    return 2*R*math.asin(math.sqrt(x))
fs=sorted(f for f in os.listdir(TIFD) if f.endswith(".tif"))
print("archivos locales: %d" % len(fs))
print("%-46s %-9s %-9s %-9s %-9s" % ("archivo","ancho_km","alto_km","semi_km","semidiag_km"))
import collections
ac=[]; al=[]
for f in fs[:8]+fs[-4:]:
    with rasterio.open(os.path.join(TIFD,f)) as s:
        T=s.transform; h,w=s.height,s.width
        lon0=T.c; lat0=T.f
        lon1=T.c+w*T.a; lat1=T.f+h*T.e
        clat=(lat0+lat1)/2
        anc=hav(clat,lon0,clat,lon1); alt=hav(lat0,(lon0+lon1)/2,lat1,(lon0+lon1)/2)
    ac.append(anc); al.append(alt)
    print("%-46s %-9.2f %-9.2f %-9.2f %-9.2f" % (f[-30:],anc,alt,anc/2,math.hypot(anc/2,alt/2)))
print("\nmediana ancho=%.2f km  alto=%.2f km  -> semiancho=%.2f km  semidiagonal=%.2f km" % (
    np.median(ac),np.median(al),np.median(ac)/2,math.hypot(np.median(ac)/2,np.median(al)/2)))
print("half_km declarado por S131 = 25.5  -> semidiagonal teorica = %.2f km" % (25.5*math.sqrt(2)))
print("-> el 36,08 de 03_ es la distancia del VENT a la esquina, no la semidiagonal del raster.")
