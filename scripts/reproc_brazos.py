"""S157: corre los brazos de un A/B que comparten volcán y ventana en el mismo job.

POR QUÉ. En un A/B cada brazo corría en su propio job y volvía a buscar en CMR y a bajar los mismos gránulos: buscar
y bajar son 20 a 30 % de un job con CMR rápido y hasta 70 % con CMR lento
(experiments/_s157_busqueda_ventana/MEDICION.md). Lo único que cambia entre brazos es el perfil, o sea el
procesamiento.

CÓMO. Día por fuera, brazo por dentro. Cada brazo es un `run_pipeline.py --profile P --date D` aparte, porque el perfil
se lee al importar (pipeline/profile.py) y no se puede cambiar dentro de un proceso. Todos comparten:
  - VRP_VENTANA_BUSQUEDA y VRP_CACHE_BUSQUEDA_DIR: el primer proceso consulta CMR una vez por producto para toda la
    ventana y deja la respuesta en disco; los siguientes la leen (pipeline/fetch.py).
  - VRP_TMP_DIR y VRP_CONSERVAR_GRANULOS=1: el primer brazo baja los gránulos del día y los deja; los siguientes los
    encuentran (earthaccess no vuelve a bajar un archivo que ya existe). Al terminar los brazos de un día, este
    script borra ese día: un día ocupa ~1,3 GB y la ventana entera no cabe en el runner.
Los brazos escriben cada uno en su data_subdir y corren en serie, nunca a la vez (A47).

Salida: código 1 si algún brazo falló en algún día (sigue con el resto, para no perder los demás días); con
--estricto-cobertura, 3 si alguna búsqueda o descarga no se pudo hacer, o si un L1B quedó sin
geolocalización o un día era parcial (S159); 0 si no. Las búsquedas sin gránulos se informan y no cuentan.

Uso:
  python scripts/reproc_brazos.py --volcano Lascar --start 2026-09-01 --end 2026-09-20 \
      --perfiles _s146_ab_control,_s146_ab_sin_test1 --trabajo /tmp/brazos --logs logs \
      --overwrite --estricto-cobertura --cobertura-json logs/cobertura_Lascar.json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


# Presupuesto de un trozo (A15): paso de 170 min con margen 1,3 = 130 min. Costo por día de ventana: 0,6 min de
# búsqueda y descarga, compartidos por los brazos (MEDICION.md, CMR rápido; con la ventana, CMR lento ya casi no
# pesa), y 1,6 min de proceso por brazo (2,2 min por día y brazo de experiments/_s151_prereg_fk_11/duracion_runs.py
# menos lo compartido). El peor job de F/K tardó 1,42 veces la mediana.
_PRESUPUESTO_MIN = 170 / 1.3
_COMPARTIDO_MIN_DIA = 0.6
_PROCESO_MIN_DIA_BRAZO = 1.6
# Un proceso de run_pipeline por día y brazo: imports (~2,3 s medidos en local) y lectura y escritura del store.
_ARRANQUE_MIN_DIA_BRAZO = 0.1
_PEOR_SOBRE_MEDIANA = 1.42


def dias_por_trozo(n_brazos: int) -> int:
    """Días de ventana por job para que n_brazos quepan en el paso de 170 min."""
    costo = _PEOR_SOBRE_MEDIANA * (_COMPARTIDO_MIN_DIA
                                   + (_PROCESO_MIN_DIA_BRAZO + _ARRANQUE_MIN_DIA_BRAZO) * max(1, n_brazos))
    return max(1, int(_PRESUPUESTO_MIN // costo))


def fechas(ini: str, fin: str) -> list[str]:
    d, d_fin = datetime.strptime(ini, "%Y-%m-%d"), datetime.strptime(fin, "%Y-%m-%d")
    out = []
    while d <= d_fin:
        out.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    return out


def correr(volcan: str, ini: str, fin: str, perfiles: list[str], trabajo, overwrite: bool = True,
           estricto: bool = False, cobertura_json=None, logs=None, ejecutar=subprocess.run) -> int:
    trabajo = Path(trabajo)
    granulos = trabajo / "granulos"
    logs = Path(logs) if logs else trabajo / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({"VRP_VENTANA_BUSQUEDA": f"{ini}:{fin}",
                "VRP_CACHE_BUSQUEDA_DIR": str(trabajo / "busquedas"),
                "VRP_TMP_DIR": str(granulos),
                "VRP_CONSERVAR_GRANULOS": "1"})
    fallidos, fallas, incidencias = [], [], []
    for fecha in fechas(ini, fin):
        for perfil in perfiles:
            cob = trabajo / "cobertura" / f"{perfil}_{fecha}.json"
            cmd = [sys.executable, str(RAIZ / "scripts" / "run_pipeline.py"), "--profile", perfil,
                   "--volcano", volcan, "--date", fecha, "--cobertura-json", str(cob)]
            if overwrite:
                cmd.append("--overwrite")
            t0 = time.time()
            with open(logs / f"{perfil}_{volcan}.log", "a", encoding="utf-8") as fh:
                r = ejecutar(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT)
            print(f"[brazos] {volcan} {fecha} {perfil} rc={r.returncode} {time.time() - t0:.0f}s", flush=True)
            if r.returncode != 0:
                fallidos.append((fecha, perfil, r.returncode))
            if cob.exists():
                leido = json.loads(cob.read_text(encoding="utf-8"))
                for f in leido.get("fallas", []):
                    fallas.append(dict(f, perfil=perfil))
                # S159 (I1): incidencias que no son fallas (sin gránulos, L1B sin geolocalización, día parcial).
                for i in leido.get("incidencias", []):
                    incidencias.append(dict(i, perfil=perfil))
            elif r.returncode == 0:
                fallidos.append((fecha, perfil, "sin archivo de cobertura"))
        shutil.rmtree(granulos / volcan / fecha.replace("-", ""), ignore_errors=True)
        # Día a día y no al final: si el paso muere por timeout, lo ya visto queda escrito (verificador S157).
        if cobertura_json:
            Path(cobertura_json).parent.mkdir(parents=True, exist_ok=True)
            Path(cobertura_json).write_text(json.dumps({"fallas": fallas, "n": len(fallas), "incidencias": incidencias,
                                                        "hasta": fecha},
                                                       ensure_ascii=False, indent=1), encoding="utf-8")
    if fallidos:
        print(f"::error::reproc_brazos {volcan}: {len(fallidos)} corridas de brazo fallaron: {fallidos[:10]}",
              flush=True)
        return 1
    cuentan = [i for i in incidencias if i.get("cuenta_estricto")]
    if fallas or cuentan:
        print(f"::warning::reproc_brazos {volcan}: {len(fallas)} búsquedas o descargas fallidas y {len(cuentan)} "
              f"incidencias que cuentan (L1B sin geolocalización o día parcial) "
              f"(días: {sorted({f.get('fecha') for f in fallas + cuentan})[:12]})", flush=True)
        return 3 if estricto else 0
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--volcano", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--perfiles", required=True, help="perfiles separados por coma, en el orden en que corren")
    ap.add_argument("--trabajo", required=True, help="directorio de caché (búsquedas, gránulos, cobertura)")
    ap.add_argument("--logs", default=None, help="un log por brazo: <perfil>_<volcan>.log (se agrega al final)")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--estricto-cobertura", action="store_true")
    ap.add_argument("--cobertura-json", default=None)
    a = ap.parse_args(argv)
    perfiles = [p.strip() for p in a.perfiles.split(",") if p.strip()]
    if not perfiles:
        ap.error("--perfiles vacío")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return correr(a.volcano, a.start, a.end, perfiles, a.trabajo, overwrite=a.overwrite,
                  estricto=a.estricto_cobertura, cobertura_json=a.cobertura_json, logs=a.logs)


if __name__ == "__main__":
    sys.exit(main())
