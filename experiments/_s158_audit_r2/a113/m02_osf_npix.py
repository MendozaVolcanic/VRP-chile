# M02: Npix del OSF v2.5 de MIROVA, ¿pixeles o regiones?
# Fisica: si Npix contara regiones contiguas de 5-50 pixeles, el fondo integrado por "unidad"
#   (Tot_Lmir_bk/Npix) seria 5-50 veces la radiancia de fondo de UN pixel; si cuenta pixeles,
#   queda cerca de Planck(T_superficie) a la longitud de onda MIR.
# Pregunta 1: si Npix fueran regiones, la razon bk/Npix creceria con el tamano de la region y
#   saldria muy por encima de Planck(330 K); el percentil 99 lo veria.
# Pregunta 2: control positivo = VRP recomputado desde Tot_Lmir_hot-Tot_Lmir_bk con k y area
#   nominales; si las columnas estuvieran mal leidas, ese control falla.
# Denominador: todas las filas 2025 del OSF con Npix>0, por Resolution. Ventana: archivo 2025 entero.
import pandas as pd, numpy as np
p = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
d = pd.read_csv(p)
print("filas:", len(d), "Resolution:", d.Resolution.value_counts().to_dict())
d["t"] = pd.to_datetime(d.timeUTC, format="%m/%d/%Y %H:%M", errors="coerce")
print("ventana:", d.t.min(), "->", d.t.max())
h=6.6256e-34; c=2.9979e8; k=1.38e-23
def planck(T, lam_um):
    lam=lam_um*1e-6
    return 2*h*c**2/(lam**5*(np.exp(h*c/(k*lam*T))-1))*1e-6
for res, lam, kk, A in [(750,4.05,1.97e7,0.5625),(375,3.74,None,None),(1000,3.96,None,None)]:
    s = d[(d.Resolution==res)&(d.Npix>0)].copy()
    if len(s)==0: print(res,"sin filas"); continue
    r = s.Tot_Lmir_bk/s.Npix
    print(f"\nRes {res}: n={len(s)}  Npix mediana={s.Npix.median()}  max={s.Npix.max()}")
    print("  bk/Npix percentiles 1,50,99:", np.percentile(r,[1,50,99]).round(4))
    for T in (250,280,300,330): print(f"  Planck({T}K,{lam}um)={planck(T,lam):.4f}")
    # por tamaño
    for lo,hi in [(1,1),(2,4),(5,20),(21,10000)]:
        q = s[(s.Npix>=lo)&(s.Npix<=hi)]
        if len(q): print(f"  Npix {lo}-{hi}: n={len(q)} mediana bk/Npix={np.median(q.Tot_Lmir_bk/q.Npix):.4f}")
    if kk:
        vr = (s.Tot_Lmir_hot - s.Tot_Lmir_bk)*kk*A
        rel = (vr/s.VRP).replace([np.inf,-np.inf],np.nan).dropna()
        print("  control: VRP recomputado/VRP OSF percentiles 1,50,99:", np.percentile(rel,[1,50,99]).round(4))
