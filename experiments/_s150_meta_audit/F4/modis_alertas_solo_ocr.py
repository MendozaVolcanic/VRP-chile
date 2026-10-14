"""F4 (meta-auditoria S150): cuantas alertas MODIS de MIROVA existen SOLO en el canal OCR.

Afirmacion bajo prueba: CLAUDE.md A119 dice "0 alertas MODIS dependen del OCR, medido S149";
AUDIT_S149.md l. 50 dice que los auditores la corrigieron ("hay 2 de Lascar en marzo").

Preguntas del instrumento:
1. Si el OCR aportara alertas MODIS que la tabla no trae, esta medicion lo veria: cruza cada
   alerta MODIS del OCR contra alertas de la tabla del mismo volcan y sensor a +-30 min.
2. Si el instrumento estuviera muerto (nombres sin normalizar, fechas mal parseadas) daria 100 %
   "solo OCR" tambien en VIIRS 375; el control positivo es VIIRS375, donde A119 espera 20-39 %
   de solo-OCR, no 0 ni 100 %.
Denominador: alertas ALERTA_TERMICA_OCR del snapshot local (ventana impresa abajo).
Solo lectura. Nocturno = hora UTC entre 00 y 12 (noche en Chile continental).
"""
import io, sys, unicodedata
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
o = pd.read_csv(BASE + "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv")
c = pd.read_csv(BASE + "latest_consolidado.csv")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum())


ALIAS = {"puyehuecordoncaulle": "pcc", "puyehuecordoncaull": "pcc", "planchonpeteroa": "pp"}
for df in (o, c):
    df["v"] = df.Volcan.map(norm).map(lambda x: ALIAS.get(x, x))
    df["t"] = pd.to_datetime(df.Fecha_Satelite_UTC, errors="coerce")
    df["s"] = df.Sensor.replace({"VIIRS": "VIIRS750"})

print("ventana tabla", c.t.min(), c.t.max(), "| ventana OCR", o.t.min(), o.t.max())
tab = c[c.Tipo_Registro == "ALERTA_TERMICA"]
for sensor in ("MODIS", "VIIRS375"):
    oa = o[(o.Tipo_Registro == "ALERTA_TERMICA_OCR") & (o.s == sensor) & (o.t.dt.hour < 12)]
    solo = []
    for _, r in oa.iterrows():
        m = tab[(tab.v == r.v) & (tab.s == sensor) & ((tab.t - r.t).abs() <= pd.Timedelta("30min"))]
        if m.empty:
            solo.append(r)
    solo = pd.DataFrame(solo)
    print(f"\n{sensor}: alertas OCR nocturnas = {len(oa)}; sin alerta de tabla a +-30 min = {len(solo)}"
          f" ({100*len(solo)/max(len(oa),1):.1f} %)")
    if len(solo) and sensor == "MODIS":
        print(solo[["Fecha_Satelite_UTC", "Volcan", "VRP_MW", "Distancia_km", "Version_OCR"]].to_string(index=False))
    if len(solo):
        print("por mes:", solo.t.dt.strftime("%Y-%m").value_counts().sort_index().to_dict())
