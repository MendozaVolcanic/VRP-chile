from common import *
import gzip
idx=load_idx(); rf=ref()
CS=ROOT+"/experiments/_s144_keep_peak_direccion/control_s143/"
noches=[("Isluga","2026-06-16"),("Lastarria","2026-06-07"),("Lastarria","2026-06-14"),("Lastarria","2026-07-25"),("Lascar","2026-06-13")]
for v,n in noches:
    recs=[]
    for tr in ("t1","t2"):
        recs+=json.loads(gzip.decompress(open(CS+f"{tr}/{v}.json.gz","rb").read()))["records"]
    recs=[r for r in recs if r["datetime_utc"].startswith(n) and int(r["datetime_utc"][11:13])<12 and not r.get("sensor","").endswith("_750") and not r.get("sensor","").startswith("MODIS")]
    al=rf[(rf.Volcan==CSVN.get(v,v))&(rf.t.dt.strftime("%Y-%m-%d")==n)&rf.Tipo_Registro.str.startswith("ALERTA")&(rf.t.dt.hour<12)]
    print("==",v,n,"alertas:",al[["src","Fecha_Satelite_UTC","VRP_MW","Distancia_km"]].values.tolist())
    tv=idx[idx.volcano==v]
    for r in recs:
        pc=r.get("primary_cluster") or {}
        if pc.get("centroid_lat") is None or r.get("final_hotspot_lat") is None: continue
        P=(pc["centroid_lat"],pc["centroid_lon"]);F=(r["final_hotspot_lat"],r["final_hotspot_lon"])
        dPF=hav(*P,*F)
        t=pd.Timestamp(r["datetime_utc"],tz="UTC")
        c=tv[(tv.acquisition_utc-t).abs().dt.total_seconds()<=120]
        tif="-" if c.empty else f"TIF own={c.iloc[0].own} lat_h={c.iloc[0].lat_h:.1f}"
        pat=pc.get("n_pixels")==1 and dPF>0.5
        line=f"  rec {r['datetime_utc']} {r.get('sensor')} src={r.get('final_hotspot_source')} npx={pc.get('n_pixels')} dPv={hav(*P,*vent(v)):.2f} dFv={hav(*F,*vent(v)):.2f} dPF={dPF:.2f} dPmc={hav(*P,*mc(v)):.2f} pat={pat} {tif}"
        if pat:
            reach=[]
            for _,a in al.iterrows():
                ca=tv[(tv.acquisition_utc-a.t).abs().dt.total_seconds()<=120]
                if ca.empty: reach.append((a.src,str(a.t)[11:16],a.Distancia_km,"sinTIF")); continue
                R=raster(ca.iloc[0].path); Dist=a.Distancia_km
                dv=hav(R["lat"],R["lon"],*vent(v)); dm=hav(R["lat"],R["lon"],*mc(v))
                ring=((dv<=3.4)|(dm<=Dist+1))&(np.abs(dm-Dist)<=0.6)
                dP=hav(R["lat"],R["lon"],*P); dF=hav(R["lat"],R["lon"],*F)
                reach.append((a.src,str(a.t)[11:16],Dist,"Preach" if (ring&(dP<=0.75)&(dF>0.75)).any() else "noP","Freach" if (ring&(dF<=0.75)&(dP>1.5)).any() else "noF", "med%.3f"%R["med"],"own",bool(ca.iloc[0].own)))
            line+=f"\n     A1 {reach}"
        print(line)
