# Que cambiaria si se corrige la geolocalizacion MODIS: tamano del corrimiento por volcan y satelite en
# produccion, etiquetas summit/far que cambiarian, y las dos perdidas del veto de la caja. Solo lectura.
#
# POR QUE: el corrimiento es geometrico (depende solo del frame del barrido, no del volcan), asi que se puede
# calcular para cada record de produccion con su cenit y su lado. Lo que NO se puede calcular aca es que
# detecta el pipeline con la posicion corregida: los umbrales de cumbre se aplican dentro de un circulo
# medido con la geolocalizacion, y moverla cambia que pixeles pasan. Eso lo tiene que medir el A/B.
#
# Correccion aproximada usada aca: mover la posicion reportada el corrimiento predicho, alejandola del sensor
# (solo la componente a lo largo del barrido; la de a lo largo de la traza depende de la linea del granulo,
# que el record no guarda).
import datetime as dt
import json
import math
import statistics as st
import sys

import yaml

import comun
import medir_corrimiento

sys.stdout.reconfigure(encoding="utf-8")
ALERTAS = medir_corrimiento.alertas_mirova()


def inner_radios():
    d = yaml.safe_load(open(comun.RAIZ / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]
    if isinstance(d, list):
        d = {x["name"]: x for x in d}
    return {k: float(d[k]["inner_radius_km"]) for k in comun.TIER_A}


def corregir(lat, lon, la, lo, pred, az):
    dn, de = comun.ne_km(la, lo, lat, lon)
    a = math.radians(az)
    return dn - pred * math.cos(a), de - pred * math.sin(a), dn, de


def main():
    vents = comun.vents()
    inner = inner_radios()
    out = open(comun.SALIDAS / "consecuencias.txt", "w", encoding="utf-8")

    def p(s=""):
        print(s)
        out.write(s + "\n")

    p("1. Corrimiento predicho a lo largo del barrido (km, hacia el sensor) en los records MODIS nocturnos de produccion")
    p("%-20s %-6s %5s %7s %7s %7s %7s" % ("volcan", "sat", "n", "mediana", "p90", "max", ">=2km"))
    cambios = {}
    for vol in comun.TIER_A:
        la, lo = vents[vol]
        recs = [r for r in comun.cargar_records(vol) if r["sensor"].startswith("MODIS")
                and r.get("sensor_zenith_deg") is not None and (r.get("solar_zenith_deg") or 0) > 90]
        for sat in ("AQUA", "TERRA"):
            xs = []
            for r in recs:
                if comun.satelite(r["sensor"]) != sat:
                    continue
                t = dt.datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
                ld = comun.lado(sat, t, lo, r["sensor_azimuth_deg"])
                xs.append(comun.pred_interp_km(r["sensor_zenith_deg"], ld == "der"))
            xs.sort()
            p("%-20s %-6s %5d %+7.2f %+7.2f %+7.2f %6.0f%%" % (vol, sat, len(xs), st.median(xs), xs[int(0.9 * len(xs))], xs[-1],
                                                           100.0 * sum(x >= 2 for x in xs) / len(xs)))
        # Etiquetas: final_hotspot (la del record) y centroide del cumulo primario (la que lee el tablero, A10).
        c = {"final": [0, 0, 0], "cumulo": [0, 0, 0], "final_al": [0, 0, 0], "cumulo_al": [0, 0, 0]}
        for r in recs:
            sat = comun.satelite(r["sensor"])
            t = dt.datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
            con_alerta = medir_corrimiento.es_alerta(ALERTAS, vol, "MODIS", t)
            az = r["sensor_azimuth_deg"]
            pred = comun.pred_interp_km(r["sensor_zenith_deg"], comun.lado(sat, t, lo, az) == "der")
            for k, (lat, lon) in (("final", (r.get("final_hotspot_lat"), r.get("final_hotspot_lon"))),
                                  ("cumulo", ((r.get("primary_cluster") or {}).get("centroid_lat"),
                                              (r.get("primary_cluster") or {}).get("centroid_lon")))):
                if lat is None or lon is None:
                    continue
                cn, ce, dn, de = corregir(lat, lon, la, lo, pred, az)
                antes = math.hypot(dn, de) <= inner[vol]
                despues = math.hypot(cn, ce) <= inner[vol]
                for kk in ((k, k + "_al") if con_alerta else (k,)):
                    c[kk][0] += 1
                    if antes and not despues:
                        c[kk][1] += 1
                    elif despues and not antes:
                        c[kk][2] += 1
        cambios[vol] = c
    p()
    p("2. Etiqueta summit/far (distancia al crater contra inner_radius_km) antes y despues de mover la posicion")
    p("   reportada el corrimiento predicho, records MODIS nocturnos. ESTO NO PREDICE LAS ETIQUETAS DEL PIPELINE")
    p("   CORREGIDO: en produccion casi todos los pixeles anomalos cercanos son un disco de ruido que el umbral de")
    p("   cumbre marca DENTRO del circulo medido con la geolocalizacion (densidad 4 a 7 veces mayor adentro que afuera,")
    p("   ver README); con la geolocalizacion corregida ese disco se volveria a centrar en el crater. Lo que cuenta es")
    p("   cuantas etiquetas quedan a menos de un corrimiento del borde, o sea cuantas dependen de la geolocalizacion.")
    p("   Las columnas 'con alerta' se limitan a pasadas con ALERTA_TERMICA MODIS de MIROVA (+-6 min).")
    p("%-20s %5s | %-24s | %-24s | %-22s | %-22s" % ("volcan", "inner", "final n / s->f / f->s", "cumulo n / s->f / f->s",
                                                     "final con alerta", "cumulo con alerta"))
    tot = {k: [0, 0, 0] for k in ("final", "cumulo", "final_al", "cumulo_al")}
    for vol, c in cambios.items():
        p("%-20s %5.0f | %6d %7d %8d | %6d %7d %8d | %5d %6d %7d | %5d %6d %7d" % (
            vol, inner[vol], *c["final"], *c["cumulo"], *c["final_al"], *c["cumulo_al"]))
        for k in tot:
            for i in range(3):
                tot[k][i] += c[k][i]
    p("%-20s %5s | %6d %7d %8d | %6d %7d %8d | %5d %6d %7d | %5d %6d %7d" % (
        "TOTAL", "", *tot["final"], *tot["cumulo"], *tot["final_al"], *tot["cumulo_al"]))

    p()
    p("3. Las dos pasadas que la caja de 5 x 5 km apaga en el brazo K (Lascar, PR #825), con la posicion corregida")
    la, lo = vents["Lascar"]
    for fecha, lat, lon, z, az, sat in (("2026-03-27 07:10", -23.36081, -67.70013, 39.85, 101.3, "AQUA"),
                                        ("2026-03-14 07:05", -23.36182, -67.69750, 44.59, 101.1, "AQUA")):
        t = dt.datetime.strptime(fecha, "%Y-%m-%d %H:%M")
        ld = comun.lado(sat, t, lo, az)
        pred = comun.pred_interp_km(z, ld == "der")
        cn, ce, dn, de = corregir(lat, lon, la, lo, pred, az)
        p("   %s %s lado %s cenit %.1f: reportado dN %+.2f dE %+.2f (|max| %.2f km); corrimiento predicho %.2f km;"
          " corregido dN %+.2f dE %+.2f (|max| %.2f km; la caja es 2,5)" % (
              fecha, sat, ld, z, dn, de, max(abs(dn), abs(de)), pred, cn, ce, max(abs(cn), abs(ce))))
    out.close()


if __name__ == "__main__":
    main()
