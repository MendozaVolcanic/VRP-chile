# -*- coding: utf-8 -*-
"""Evaluación de W2 a W6 con los días con hueco de NASA excluidos (adenda 1 del §11 del pre-registro).

POR QUÉ. El evaluador sellado (`evaluar_diurno_k.py`, sha en `objetivos_sha256.txt`) no se toca, y su `main()` no
recibe una lista de días excluidos. La adenda 1 manda excluir de los dos brazos los días que entrega
`dias_excluidos_nasa.py` (CMR sin gránulos de una plataforma y el control sin ningún record de esa plataforma). Este
script hace eso y nada más: carga lo mismo que el `main()` sellado, saca de la referencia y de los records de los dos
brazos los días de la lista, y llama a la misma `evaluar_completo` del evaluador sellado. Sacar las filas y los records
de esos días equivale a `evaluar(..., excluir_dias=lista)`: lo comprobó el verificador de la adenda sobre W1
(`verificador_adenda1/va_glue.py`) y lo fija `test_evaluar_con_exclusion.py`. Además informa, por día excluido, cuántas
pasadas de MIROVA de cada clase salen de la cuenta (verificador de la adenda, V4).

Uso:
  python -I experiments/_s163_diurno_k/evaluar_con_exclusion.py --raiz <W2> ... --raiz <W6> --ref <referencia
      congelada> --sha-codigo <40 caracteres> --opcion-e e-ii --excluidos <json de dias_excluidos_nasa.py>
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for _p in (str(ROOT), str(ROOT / "scripts"), str(AQUI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import evaluar_diurno_k as ev  # noqa: E402


def quitar_dias(filas, recs_por_lado, dias):
    """Filas de la referencia y records de cada lado sin los días de la lista (día UTC)."""
    dias = set(dias)
    f = [x for x in filas if str(x["fecha_utc"])[:10] not in dias]
    r = {lado: [x for x in rs if x["dt"].strftime("%Y-%m-%d") not in dias] for lado, rs in recs_por_lado.items()}
    return f, r


def lo_que_sale(filas, dias, ventanas):
    """Por día excluido: cuántas pasadas de MIROVA de cada clase (por sensor y periodo) salen de la cuenta."""
    pas = ev.pasadas_de(filas, "union", ventanas)
    out = {d: collections.Counter() for d in dias}
    for p in pas:
        d = p.instante.strftime("%Y-%m-%d")
        if d in out:
            clase = "protegida" if (p.estado == "alerta" and p.vrp_mw is not None and p.vrp_mw >= 1.0) else p.estado
            out[d]["%s %s %s" % (p.sensor_bucket, "día" if ev.es_dia_vol(p.volcano, p.instante) else "noche", clase)] += 1
    return {d: dict(c) for d, c in out.items()}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Evaluación del A/B diurno sobre K con los días con hueco de NASA excluidos")
    ap.add_argument("--raiz", action="append", required=True)
    ap.add_argument("--brazos", default="_s154_ab_diurno_k_control,_s154_ab_diurno_k_on")
    ap.add_argument("--ref", required=True)
    ap.add_argument("--sustrato", default=str(AQUI / "sustrato_k.json"))
    ap.add_argument("--sha-codigo", required=True)
    ap.add_argument("--opcion-e", required=True, choices=ev.OPCIONES_E)
    ap.add_argument("--excluidos", required=True, help="json de dias_excluidos_nasa.py (clave excluir_dias)")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args(argv)
    import banco_paridad as bp
    import sustrato_k as sk
    control, brazo = a.brazos.split(",")
    sus = json.loads(Path(a.sustrato).read_text(encoding="utf-8"))
    ref = Path(a.ref)
    distintos = [n for n in sk.ARCHIVOS_REF if ev.sha256(ref / n) != sus["sha256"][n]]
    if distintos:
        print("REFERENCIA DISTINTA DE LA DEL PRE-REGISTRO (sha256): %s. No se decide." % distintos)
        return 3
    exc = json.loads(Path(a.excluidos).read_text(encoding="utf-8"))
    dias = list(exc["excluir_dias"])
    filas = sk.cargar_ref(ref)
    p_sup = ev.p_sup_de_vara(sus["vara_cobertura_nocturna_produccion"])
    ventanas = [(w[0], w[1], w[2]) for w in sk.VENTANAS if w[0] in sk.DECIDEN]
    inner = bp.inner_desde_html()
    recs = {control: ev.cargar_brazo(a.raiz, control, ventanas, inner),
            brazo: ev.cargar_brazo(a.raiz, brazo, ventanas, inner)}
    logs = ev.problemas_de_logs(a.raiz, (control, brazo), control)
    print("DÍAS EXCLUIDOS POR HUECO DE NASA (adenda 1, regla a y b'): %s" % dias)
    print("  consulta CMR del %s; evidencia: %s" % (exc.get("consulta_cmr_utc"), exc.get("evidencia")))
    print("  pasadas de MIROVA que salen, por día: %s" % lo_que_sale(filas, dias, ventanas))
    print("  informativo, regla (b) original: %s" % (exc.get("informativo_regla_b") or {}).get("excluir_dias"))
    filas_x, recs_x = quitar_dias(filas, recs, dias)
    r = ev.evaluar_completo(filas_x, recs_x, control, brazo, a.opcion_e, p_sup, a.sha_codigo, ventanas, logs,
                            ev._filas_1_13())
    print("reflejo probable (1.13): %d pasadas" % len(r["reflejo"]))
    ev.imprimir(r["principal"], r["variantes"], r["final"], r["motivo"], a.opcion_e)
    print("INFORMATIVO (no decide): %s" % r["info"])
    r["principal"].pop("T", None)
    if a.salida:
        Path(a.salida).write_text(json.dumps({"excluir_dias": dias, "principal": r["principal"],
                                              "variantes": r["variantes"], "final": r["final"], "motivo": r["motivo"],
                                              "info": r["info"]}, ensure_ascii=False, indent=1, default=str),
                                  encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
