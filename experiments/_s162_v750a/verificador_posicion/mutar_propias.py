# -*- coding: utf-8 -*-
"""Mutaciones PROPIAS del verificador (una línea cada una) sobre evaluar_v750a.py, contra MIS escenarios W1 a W6.

Preguntas del instrumento: (1) si el analizador estuviera roto en esa línea, ¿lo vería? ATRAPADA = el escenario nombrado
FALLA por ASERCIÓN (falta/sobra una línea), no por caída. (2) si el instrumento estuviera muerto: IDENTIDAD (copia sin
mutar, sólo con RAIZ corregida) tiene que PASAR en todos, y CAIDA (excepción al cargar) tiene que dar CAÍDA, no FALLA.
La copia vive en esta carpeta; RAIZ se corrige de parents[1] a parents[2] (única diferencia con el original).
Uso: python mutar_propias.py --dest <dir> --evaluador <evaluar_d25.py del tag>
"""
import argparse
import subprocess
import sys
from pathlib import Path

AQ = Path(__file__).resolve().parent
ORIG = AQ.parent / "evaluar_v750a.py"
RAIZ_VIEJO, RAIZ_NUEVO = "RAIZ = AQUI.parents[1]", "RAIZ = AQUI.parents[2]"

MUT = {
    "MV1": ("W1", '"summit" if d <= inner[obj[i]["volcan"]] else "far"', '"summit" if d < inner[obj[i]["volcan"]] else "far"'),
    "MV2": ("W4", 'startswith("FALSO_POSITIVO") and f.get("source") == "CONS"',
            'startswith("FALSO_POSITIVO") and True'),
    "MV3": ("W3", "for v in VENTANAS for canal in CANALES) for b in POS}", 'for v in VENTANAS for canal in ("tabla",)) for b in POS}'),
    "MV4": ("W4", '(reg == "SIN SUSTRATO" and neto <= 0)', '(reg == "SIN SUSTRATO" and neto < 0)'),
    "MV5": ("W5", 'return min(cands, key=lambda b: (sum(e_tot[b]), b != "Ppico"))',
            'return min(cands, key=lambda b: (e_tot[b][0], b != "Ppico"))'),
    "MV6": ("W2", "c = err(b) - err(ref)", "c = err(ref) - err(b)"),
    "MV7": ("W1", "d = float(np.hypot(f - ancla[0], c - ancla[1]) * 0.75)", "d = float(np.hypot(f - ancla[0], c - ancla[1]) * 1.0)"),
    "MV8": ("W6", 'and (f.get("source") == "CONS" or o["hora_utc"] >= AB.FRONTERA_OCR)', "and True"),
    "MV9": ("W4", 'canal = "tabla" if o["hora_utc"] < AB.FRONTERA_OCR else "todo"\n    if canal == "tabla":',
            'canal = "tabla"\n    if canal == "tabla":'),
    "MV10": ("W4", 'p2t = {b: p2(b, "P", "TODO", "tabla", lejana=True) for b in POS[1:]}',
             'p2t = {b: p2(b, "P", "TODO", "decide", lejana=True) for b in POS[1:]}'),
    "MV11": ("W2", "return sum(1 for i in oks if etiqueta_lejana(obj[i], canal) and en_ventana(obj[i], v) and pub(i, b))",
             "return sum(1 for i in oks if etiqueta_lejana(obj[i], canal) and en_ventana(obj[i], v) and not pub(i, b))"),
    "CAIDA": ("W1", 'obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}',
              'raise RuntimeError("mutación de control: el programa se cae")'),
}


def correr(nombre, esc, viejo, nuevo, dest, evaluador):
    src = ORIG.read_text(encoding="utf-8")
    assert src.count(RAIZ_VIEJO) == 1
    src = src.replace(RAIZ_VIEJO, RAIZ_NUEVO)
    if viejo is not None:
        n = src.count(viejo)
        if n != 1:
            return nombre, f"TEXTO NO ENCONTRADO EXACTAMENTE UNA VEZ ({n})", ""
        src = src.replace(viejo, nuevo)
    copia = AQ / f"_mut_{nombre}.py"
    copia.write_text(src, encoding="utf-8")
    try:
        sal = dest / nombre
        o = subprocess.run([sys.executable, str(AQ / "mis_escenarios.py"), "--dest", str(sal), "--analizador", str(copia),
                            "--evaluador", str(evaluador), "--solo", esc], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=3600)
        return nombre, (o.stdout.strip().splitlines() or ["(sin salida) " + o.stderr[-300:]])[-1], ""
    finally:
        copia.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--evaluador", required=True)
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    sel = [x for x in a.solo.split(",") if x] or list(MUT)
    a.dest.mkdir(parents=True, exist_ok=True)
    print("IDENTIDAD (todos los escenarios, copia sin mutar):", flush=True)
    r = subprocess.run([sys.executable, str(AQ / "mis_escenarios.py"), "--dest", str(a.dest / "ident"),
                        "--evaluador", str(a.evaluador)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout, flush=True)
    for k in sel:
        esc, v, n = MUT[k]
        nom, ult, _ = correr(k, esc, v, n, a.dest, a.evaluador)
        est = ult.split("|")[1].strip() if "|" in ult else ult
        veredicto = {"FALLA": "ATRAPADA por aserción", "CAÍDA": "CAÍDA (excepción)", "OK": "ESCAPA (el escenario pasó)"}.get(est, est)
        print(f"{k} | {esc} | {veredicto} | {ult[:260]}", flush=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
