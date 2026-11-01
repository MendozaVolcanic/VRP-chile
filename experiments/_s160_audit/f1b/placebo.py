"""Genera brazos placebo a partir de un brazo de control (fila R6 y R2 del plan S160 §3 F1).

Pregunta 1 del instrumento: si el evaluador aprobara cualquier cosa, lo veria? Si: un brazo que es el control con la
magnitud multiplicada por 1,10 o por 1,2, o con la magnitud desplazada entre pasadas (sin informacion), no puede ser
"mejor" que el control por ninguna razon fisica; si el evaluador lo aprueba, el evaluador no distingue.
Pregunta 2: si el generador estuviera muerto, se veria? Si: escribe cuantos valores toco y falla si toco cero
(salvo en modo id, que debe tocar cero y lo declara).

Modos:
  id          copia identica (control de que el harness reproduce el veredicto del control contra si mismo)
  x1.10       todos los campos de magnitud (*vrp*_mw) del record y de primary_cluster por 1,10
  x1.2        idem por 1,2
  desplazada  pc.vrp_mw, vrp_mw, f5_core_vrp_mw rotados una posicion entre records del mismo volcan y sensor,
              ordenados por datetime_utc (cada pasada recibe la magnitud de otra pasada)
  sin_dia:YYYY-MM-DD   borra los records de ese dia UTC (fila R2: cobertura)

Uso: python placebo.py <dir_control> <dir_salida> <modo>
"""
import json, os, re, sys, io, glob, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PAT = re.compile(r"vrp.*_mw$")
CAMPOS_DESPL = ("vrp_mw", "f5_core_vrp_mw")


def escalar(obj, f, n):
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, (int, float)) and not isinstance(v, bool) and PAT.search(k) and v:
                obj[k] = v * f; n[0] += 1
            elif isinstance(v, (dict, list)):
                escalar(v, f, n)
    elif isinstance(obj, list):
        for v in obj:
            escalar(v, f, n)


def main():
    src, dst, modo = sys.argv[1:4]
    os.makedirs(dst, exist_ok=True)
    tocados = 0; borrados = 0; total = 0
    for p in sorted(glob.glob(os.path.join(src, "*.json"))):
        d = json.load(open(p, encoding="utf-8"))
        recs = d.get("records") if isinstance(d, dict) else None
        if recs is None:
            shutil.copy(p, os.path.join(dst, os.path.basename(p))); continue
        total += len(recs)
        if modo.startswith("x"):
            f = float(modo[1:]); n = [0]
            for r in recs:
                escalar(r, f, n)
            tocados += n[0]
        elif modo == "desplazada":
            grupos = {}
            for r in recs:
                grupos.setdefault(r.get("sensor"), []).append(r)
            for g in grupos.values():
                g.sort(key=lambda r: r.get("datetime_utc", ""))
                if len(g) < 2:
                    continue
                vals = [(r.get("vrp_mw"), (r.get("primary_cluster") or {}).get("vrp_mw"), r.get("f5_core_vrp_mw")) for r in g]
                vals = vals[-1:] + vals[:-1]
                for r, (a, b, c) in zip(g, vals):
                    r["vrp_mw"] = a
                    if r.get("primary_cluster") is not None and b is not None:
                        r["primary_cluster"]["vrp_mw"] = b
                    if "f5_core_vrp_mw" in r:
                        r["f5_core_vrp_mw"] = c
                    tocados += 1
        elif modo.startswith("sin_dia:"):
            dia = modo.split(":", 1)[1]
            antes = len(recs)
            recs = [r for r in recs if not r.get("datetime_utc", "").startswith(dia)]
            borrados += antes - len(recs)
            d["records"] = recs
        elif modo == "id":
            pass
        else:
            raise SystemExit("modo desconocido " + modo)
        json.dump(d, open(os.path.join(dst, os.path.basename(p)), "w", encoding="utf-8"))
    print("placebo %s: %s -> %s | records %d | valores tocados %d | records borrados %d" % (modo, src, dst, total, tocados, borrados))
    if modo not in ("id",) and tocados == 0 and borrados == 0:
        raise SystemExit("el generador no toco nada: SIN DATO, no OK")


if __name__ == "__main__":
    main()
