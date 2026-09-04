# -*- coding: utf-8 -*-
"""
Mide cuantas de las corridas PROGRAMADAS que deberian haber ocurrido, ocurrieron.

FICHA SDA - no participa de la deteccion ni de la clasificacion. Es instrumentacion
operacional: mide la puntualidad del cron, no el contenido de los datos.

POR QUE EXISTE (S133). El 2026-08-27 GitHub dejo de entregar aproximadamente la mitad de
los eventos `schedule` de este repo. La caida fue UNIFORME sobre los cuatro workflows con
cron (NRT 98%->40%, retry 96%->45%, pages 96%->40%, sync 84%->22%) y nuestra configuracion
no habia cambiado: los mismos crones antes y despues. Es decir, es de GitHub y no nuestro.

Nadie se entero durante ocho dias, y no porque fallara un monitor sino porque NINGUNO mide
esto. `nrt-monitor` avisa si fallan 3 corridas seguidas, y no fallo ninguna: las 200
ultimas terminaron en success. `nrt-healthcheck` avisa si el dato pasa de 48 h de viejo, y
nunca paso de 7. Las dos metricas estaban en verde sobre un mecanismo degradado a la mitad,
que es exactamente la forma de la regla A87. Lo que faltaba medir era la AUSENCIA de
corridas, y una corrida que no ocurre no deja rastro que un monitor de fallas pueda ver.

QUE NO ES ESTO. No es un detector de perdida de datos. Se verifico que la degradacion de
2026-08-27 NO perdio un solo record (116 records/dia antes contra 121 despues, 11/11
volcanes cubiertos todos los dias): cada corrida del NRT procesa el dia completo, asi que
una franja saltada la cubre la siguiente. El efecto es de LATENCIA -el dato llega con ~7 h
en vez de ~3-4 h-, no de completitud. Por eso este script REPORTA siempre y ALERTA solo en
el caso accionable, que es cero corridas en la ventana: una alerta que no se puede accionar
es ruido, y el ruido tapa la alerta que si importa (la leccion de la issue #567).
"""
import argparse
import datetime as dt
import io
import json
import sys

# Corridas por dia que declara el cron de cada workflow. Si se cambia un cron, se cambia
# aca: el numero esperado es parte del contrato, no se deduce.
ESPERADO_POR_DIA = {
    "NRT VRP Pipeline (both profiles)": 12,      # cron "0 */2 * * *"
    "NRT Retry (NASA recovery)": 12,             # cron "30 1-23/2 * * *"
    "Deploy GitHub Pages": 12,                   # cron "50 */2 * * *"
    ".github/workflows/sync-mirova-csv.yml": 24,  # cron "12 * * * *"
}

# El unico workflow cuya ausencia total es accionable por si sola.
CRITICO = "NRT VRP Pipeline (both profiles)"


def _a_utc(texto):
    t = dt.datetime.fromisoformat(str(texto).replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def medir(corridas, ahora, ventana_h=24, esperado_por_dia=None):
    """Cuenta corridas por schedule dentro de la ventana y las compara con lo declarado.

    `corridas` son dicts con al menos createdAt, name y event, tal como los devuelve
    `gh run list --json createdAt,name,event`. Se ignora todo lo que no sea `schedule`:
    un dispatch manual no dice nada sobre la puntualidad del cron.
    """
    esperado_por_dia = esperado_por_dia or ESPERADO_POR_DIA
    desde = ahora - dt.timedelta(hours=ventana_h)
    vistas = {n: 0 for n in esperado_por_dia}
    for r in corridas:
        if r.get("event") != "schedule":
            continue
        nombre = r.get("name")
        if nombre not in vistas:
            continue
        try:
            t = _a_utc(r.get("createdAt"))
        except (TypeError, ValueError):
            continue
        if desde <= t <= ahora:
            vistas[nombre] += 1

    filas = []
    for nombre, por_dia in esperado_por_dia.items():
        esperado = por_dia * ventana_h / 24.0
        obtenido = vistas[nombre]
        # Un esperado de 0 no define un porcentaje; se informa None en vez de inventarlo.
        entrega = round(100.0 * obtenido / esperado, 1) if esperado > 0 else None
        filas.append({"workflow": nombre, "esperado": round(esperado, 1),
                      "obtenido": obtenido, "entrega_pct": entrega})

    criticas = vistas.get(CRITICO, 0)
    return {
        "ventana_h": ventana_h,
        "hasta_utc": ahora.isoformat(),
        "filas": filas,
        "entrega_global_pct": round(
            100.0 * sum(f["obtenido"] for f in filas)
            / max(1e-9, sum(f["esperado"] for f in filas)), 1),
        "corridas_del_critico": criticas,
        "alerta": criticas == 0,
        "motivo_alerta": (
            "cero corridas programadas de %s en %d h" % (CRITICO, ventana_h)
            if criticas == 0 else None),
    }


def a_markdown(res):
    L = ["### Cadencia del cron (ultimas %d h)" % res["ventana_h"], "",
         "| workflow | esperadas | ocurrieron | entrega |", "|---|---:|---:|---:|"]
    for f in res["filas"]:
        pct = "—" if f["entrega_pct"] is None else "%.0f %%" % f["entrega_pct"]
        L.append("| %s | %.1f | %d | %s |"
                 % (f["workflow"], f["esperado"], f["obtenido"], pct))
    L += ["", "Entrega global: **%.0f %%**." % res["entrega_global_pct"]]
    if res["alerta"]:
        L += ["", "> ⚠️ %s" % res["motivo_alerta"]]
    else:
        L += ["",
              "Una entrega baja **no implica perdida de datos**: cada corrida del NRT "
              "procesa el dia completo, asi que una franja saltada la cubre la siguiente. "
              "Degrada la latencia, no la completitud. La alerta salta solo con cero "
              "corridas del NRT en la ventana."]
    return "\n".join(L)


def main():
    # El reenvoltorio de stdout va aca y no en el import: hacerlo a nivel de modulo
    # rompe la captura de pytest, que reemplaza sys.stdout por un objeto propio.
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ventana-h", type=int, default=24)
    ap.add_argument("--entrada", default="-",
                    help="JSON de `gh run list --json createdAt,name,event`; - es stdin")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--ahora", default=None, help="ISO UTC; solo para pruebas")
    a = ap.parse_args()

    texto = sys.stdin.read() if a.entrada == "-" else io.open(
        a.entrada, encoding="utf-8").read()
    corridas = json.loads(texto) if texto.strip() else []
    ahora = _a_utc(a.ahora) if a.ahora else dt.datetime.now(dt.timezone.utc)

    res = medir(corridas, ahora, a.ventana_h)
    print(a_markdown(res))
    if a.json_out:
        with io.open(a.json_out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)
    # Se sale con 0 siempre: quien decide si abrir un issue es el workflow, leyendo el
    # JSON. Un exit code distinto pondria el job en rojo por algo que no es una falla.
    return 0


if __name__ == "__main__":
    sys.exit(main())
