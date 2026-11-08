import json,os,sys,math
sys.path.insert(0,r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f5b")
import numpy as np
from PIL import Image, ImageDraw
import yaml
import f5b_lib as L
F=r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f5b"
TMP=r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
OUT=r"C:\Users\nmend\vrp-temporales\s175_audit\v5b\crops"
V={v["name"]:v for v in yaml.safe_load(open(r"C:\Users\nmend\vrp-temporales\s175_audit\main\volcanoes.yaml",encoding="utf-8"))["volcanoes"]}
o=[x for x in json.load(open(F+r"\p8_clases.json",encoding="utf-8")) if x.get("vol")=="NevadosDeChillan"]
want=[("VIIRS375","2026-10-18 05:06"),("VIIRS750","2026-10-29 06:42"),("VIIRS750","2026-10-10 06:54"),("VIIRS750","2026-10-16 06:42"),("VIIRS375","2026-10-18 06:00")]
refs=json.load(open(F+r"\p6_tif_referencia_out.json",encoding="utf-8"))
print(V["NevadosDeChillan"].get("mirova_center_lat"),V["NevadosDeChillan"].get("mirova_center_lon"),V["NevadosDeChillan"].get("lat"),V["NevadosDeChillan"].get("lon"),V["NevadosDeChillan"].get("vent_lat"),V["NevadosDeChillan"].get("vent_lon"),V["NevadosDeChillan"].get("inner_radius_km"))
for b,dt_ in want:
    x=[r for r in o if r["b"]==b and r["dt"]==dt_]
    print(b,dt_,len(x))
    x=x[0]
    print({k:x.get(k) for k in ("sensor","vrp_mirova","protegida","dist_tabla_km","d_png_mirova_center_km","d_png_nuestro_km","png_rc","png_lat","png_lon","our_lat","our_lon","clase","panel","etiqueta_panel","png","lum_max","lum_p99_panel","prominencia","mancha_px","marco_verde","geometria")})
    fn=os.path.join(TMP,"png",x["png"].split("/")[-2]+"_"+os.path.basename(x["png"]))
    im=Image.open(fn).convert("RGB")
    if "full" not in globals(): 
        im.save(os.path.join(OUT,"lamina_ejemplo.png")); full=1
    k=x["panel"]; col,row=k%5,k//5
    box=(8+165*col-4,146+236*row,8+165*col+165,146+236*row+200)
    c=im.crop(box); c=c.resize((c.width*5,c.height*5),Image.NEAREST)
    d=ImageDraw.Draw(c)
    ref=refs[f"ChillanNevadosde|{b}"]["ref_sep"]
    g=L.grilla(os.path.join(TMP,"tif_ref","ChillanNevadosde_"+os.path.basename(ref["path"])))
    print("ref",ref["path"],g["n"],g["crs"],g["transform"])
    bb=L.bbox_marco(np.array(im),k); X0,Y0,W,Hh=L.geometria(bb); n=g["n"]
    def to_px(lat,lon):
        dd=(g["lats"]-lat)**2+((g["lons"]-lon)*math.cos(math.radians(lat)))**2
        r,c_=np.unravel_index(np.argmin(dd),dd.shape)
        return X0+(c_+.5)/n*W, Y0+(r+.5)/n*Hh, r, c_
    mc=(V["NevadosDeChillan"]["mirova_center_lat"],V["NevadosDeChillan"]["mirova_center_lon"])
    pts={"ours":(float(x["our_lat"]),float(x["our_lon"]),(0,255,255)),"png":(x["png_lat"],x["png_lon"],(255,0,0)),"mc":(mc[0],mc[1],(255,255,0))}
    for nm,(la,lo,col_c) in pts.items():
        px,py,r,c_=to_px(la,lo)
        print(" ",nm,la,lo,"rc",r,c_)
        xx=(px-box[0])*5; yy=(py-box[1])*5
        d.ellipse((xx-9,yy-9,xx+9,yy+9),outline=col_c,width=2)
    c.save(os.path.join(OUT,f"{b}_{dt_.replace(' ','_').replace(':','')}.png"))
