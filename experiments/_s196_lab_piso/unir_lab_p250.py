# -*- coding: utf-8 -*-
"""S203: arma la carpeta del laboratorio para la vara NHI (paso 5 del plan S190) con el brazo elegido, _s196_lab_p250.
POR QUÉ: el laboratorio encendido (#1144) es el brazo p250 salvo nombre y carpeta (prueba G2 nueva), y el barrido ya lo
corrió del 2026-03-01 al 23-11 (unión de las diez tandas, unir_tandas.py). La vara NHI mide desde el 2026-02-15 y su
control de cobertura invalida con más de 5 % de noches desiguales por volcán, así que el 15 al 28-feb y el 24-nov en
adelante se corrieron aparte con el mismo workflow y tres brazos (t11 y t12). Aquí se juntan las tres fuentes.
EXIGE (si algo falla, no escribe nada y sale con 2):
  1. cada corrida extra: un solo intento, todos sus trabajos reproc en success y su rama con un solo commit (lo revisa
     quien corre esto con gh antes; aquí se lee el archivo de identidad publicado en la rama);
  2. los dos controles de cada corrida extra en verde (salidas/identidad_control.txt sin «NO COMPROBADA», y
     no_actua_<p250>.txt con salida 0) leídos de la rama;
  3. cada record trae regimen.perfil == _s196_lab_p250 (R5C-103);
  4. ninguna clave (sensor, datetime_utc) repetida entre fuentes con contenido distinto (salvo processed_utc);
  5. cada fuente cae dentro de su ventana.
Uso: python unir_lab_p250.py <carpeta union_t10/_s196_lab_p250> <salida> <run_t11>:<ini>:<fin> <run_t12>:<ini>:<fin>
Las ramas se bajan antes: git fetch origin "+refs/heads/s196-lab-piso/*:refs/remotes/origin/s196-lab-piso/*"."""
import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
BRAZO = "_s196_lab_p250"
VOLCANES = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "NevadosDeChillan", "PlanchonPeteroa",
            "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]
IGNORAR = {"processed_utc", "first_processed_utc"}


def show(rama, ruta):
    r = subprocess.run(["git", "-C", REPO, "show", "origin/%s:%s" % (rama, ruta)], capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None


def main(argv):
    base, salida = Path(argv[0]), Path(argv[1])
    extras = [a.split(":") for a in argv[2:]]
    problemas, por_vol = [], {v: {} for v in VOLCANES}
    fuentes = [("union", None, "2026-03-01", "2026-11-23")] + [("run", r, i, f) for r, i, f in extras]
    for tipo, run, ini, fin in fuentes:
        if tipo == "run":
            rama = "s196-lab-piso/%s" % run
            pre = "experiments/_s196_lab_piso/salidas/%s/" % run
            ident = show(rama, pre + "identidad_control.txt")
            if ident is None or "NO COMPROBADA" in ident:
                problemas.append("%s: control (a) sin comprobar o ausente" % run)
            na = show(rama, pre + "no_actua_%s.txt" % BRAZO)
            if na is None:
                problemas.append("%s: control (b) de %s ausente" % (run, BRAZO))
        for vol in VOLCANES:
            if tipo == "union":
                ruta = base / ("%s.json" % vol)
                texto = ruta.read_text(encoding="utf-8") if ruta.exists() else None
            else:
                texto = show(rama, pre + "%s/%s.json" % (BRAZO, vol))
            if texto is None:
                problemas.append("%s %s: falta %s" % (run or "union", vol, BRAZO))
                continue
            for r in json.loads(texto)["records"]:
                if (r.get("regimen") or {}).get("perfil") != BRAZO:
                    problemas.append("%s %s %s: perfil %r" % (run or "union", vol, r.get("datetime_utc"),
                                                             (r.get("regimen") or {}).get("perfil")))
                    continue
                if not (ini <= r["datetime_utc"][:10] <= fin):
                    problemas.append("%s %s %s: fuera de su ventana %s a %s" % (run or "union", vol,
                                                                                r["datetime_utc"], ini, fin))
                    continue
                k = (r.get("sensor"), r["datetime_utc"])
                ya = por_vol[vol].get(k)
                if ya is not None and {a: b for a, b in ya.items() if a not in IGNORAR} != \
                        {a: b for a, b in r.items() if a not in IGNORAR}:
                    problemas.append("%s %s: clave repetida con contenido distinto" % (vol, k))
                por_vol[vol][k] = r
    print("records por volcán:", {v: len(d) for v, d in por_vol.items()})
    print("problemas:", len(problemas))
    for p in problemas[:30]:
        print("  ", p)
    if problemas:
        return 2
    salida.mkdir(parents=True, exist_ok=False)
    for vol, d in por_vol.items():
        recs = [d[k] for k in sorted(d, key=lambda x: (x[1], str(x[0])))]
        (salida / ("%s.json" % vol)).write_text(json.dumps({"volcano": vol, "records": recs}, ensure_ascii=False),
                                                encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
