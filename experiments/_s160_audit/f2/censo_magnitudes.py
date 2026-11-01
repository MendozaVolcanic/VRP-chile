#!/usr/bin/env python
"""Censo de constantes numéricas (F2, auditoría S160).

Recorre el AST de pipeline/*.py y scripts/*.py de la instantánea de origin/main, los valores
efectivos del perfil (pipeline.profile con VRP_PROFILE=mirova_equivalent, nunca el YAML a mano)
y los umbrales numéricos de frontend/index.html, diario.html y mosaico.html. Escribe
censo_bruto.csv (una fila por constante encontrada, columnas automáticas) y, en --control,
verifica que el censo encuentre entero el control positivo del plan (§3 F2) y que un archivo
sin constantes dé 0 filas; además compara el conteo por archivo contra un grep independiente.

Las dos preguntas del instrumento:
1. Si el censo estuviera roto (no viera una clase de constante), ¿se vería? Sí para las clases
   del control positivo (asignación de módulo, valor del perfil, comparación, default de
   función, .get con respaldo, clave de YAML del volcán). No para clases que el control no
   cubre: literales dentro de f-strings, constantes en archivos .js aparte y números escritos
   como cadena. Eso queda declarado en el informe.
2. Si el instrumento estuviera muerto, el control positivo falla con código 2 y el control
   negativo (archivo sin constantes) sigue dando 0 por otra razón: por eso el negativo no vale
   solo, se lee junto con el positivo.

Uso:
  python censo_magnitudes.py --raiz D:/.../main --salida censo_bruto.csv
  python censo_magnitudes.py --raiz D:/.../main --control
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# ----------------------------------------------------------------------------- unidades
# Inferencia por nombre y por texto de la línea. Es heurística: la columna se llama
# unidad_inferida y la revisión a mano decide.
REGLAS_UNIDAD = [
    (r"(?i)(_k\b|_k_|kelvin|\bbt\b|t_bg|t_max|temp|_tbg|tbg|_bt\b|bt_|delta_t|dt_k|sat_k|_te_k|t_min|t_max)", "K"),
    (r"(?i)(_mw\b|_mw_|vrp|megawatt|\bmw\b)", "MW"),
    (r"(?i)(_km\b|_km_|\bkm\b|radius|radio|dist|inner|outer|ring)", "km"),
    (r"(?i)(_m\b|metros|meters|_m_)", "m"),
    (r"(?i)(zenith|zenit|cenit|\bdeg\b|grados|lat\b|lon\b|azimut|angle|theta)", "deg"),
    (r"(?i)(tol_s\b|_s\b|segundos|seconds|timeout|sleep|_sec\b|minutes|_min\b|hours)", "s"),
    (r"(?i)(dnti|deti|\bnti\b|nti_|_nti|eti_|_eti)", "NTI (adimensional)"),
    (r"(?i)(sigma|nsigma|n_sigma|_std|std_)", "sigma (multiplo)"),
    (r"(?i)(pixel|_px\b|px_|pixeles|n_pix|npix)", "px"),
    (r"(?i)(area|a_pix)", "km2 o m2"),
    (r"(?i)(coeff|wooster|k_tir)", "coef. Wooster (W m-2 sr-1 um-1 por MW)"),
    (r"(?i)(lambda|wavelength|_um\b|micron)", "um"),
    (r"(?i)(radiance|_l\b|l_bg|l_hot|l_mir|\bL_)", "W m-2 sr-1 um-1"),
    (r"(?i)(frac|ratio|razon|percent|pct|recall|precision|share)", "fraccion"),
    (r"(?i)(eps\b|epsilon|emis)", "emisividad o eps"),
    (r"(?i)(planck|c1\b|c2\b)", "cte Planck o C1/C2 Coppola"),
    (r"(?i)(dpi|width|height|figsize|fontsize|linewidth|alpha|marker|zorder)", "grafico"),
    (r"(?i)(\bn_\w+|count|num_|max_\w*(pixels|records|cluster)|min_\w*(pixels|records))", "conteo"),
]


def inferir_unidad(nombre: str, linea: str) -> str:
    texto = f"{nombre} {linea}"
    for patron, unidad in REGLAS_UNIDAD:
        if re.search(patron, texto):
            return unidad
    return "?"


def sensor_de(ruta: str, linea: str) -> str:
    r = ruta.lower()
    t = linea.lower()
    if "process_modis" in r or "modis" in t:
        return "MODIS"
    if "process_viirs_mod" in r or "viirs750" in t or "viirs_750" in t or "m13" in t or "m15" in t:
        return "VIIRS750"
    if "process_viirs" in r or "viirs375" in t or "i04" in t or "i05" in t:
        return "VIIRS375"
    if "viirs" in t:
        return "VIIRS"
    return "todos/no aplica"


# ----------------------------------------------------------------------------- AST
class Censo(ast.NodeVisitor):
    def __init__(self, ruta: Path, raiz: Path, lineas: list[str]):
        self.ruta = ruta
        self.rel = str(ruta.relative_to(raiz)).replace("\\", "/")
        self.lineas = lineas
        self.filas: list[dict] = []
        self.funcion = "<modulo>"
        self._en_subscript = 0

    # contexto de función
    def visit_FunctionDef(self, node):
        previa = self.funcion
        self.funcion = node.name
        # defaults
        args = node.args
        todos = list(args.args) + list(args.kwonlyargs) + list(args.posonlyargs)
        defaults = list(args.defaults) + list(args.kw_defaults)
        for d in defaults:
            if d is None:
                continue
            for c in self._constantes(d):
                self._fila(c, "default_arg", nombre=self._nombre_default(node, d))
        self.generic_visit(node)
        self.funcion = previa

    visit_AsyncFunctionDef = visit_FunctionDef

    def _nombre_default(self, fn, d):
        args = fn.args
        pos = list(args.posonlyargs) + list(args.args)
        for a, dv in zip(pos[len(pos) - len(args.defaults):], args.defaults):
            if dv is d:
                return a.arg
        for a, dv in zip(args.kwonlyargs, args.kw_defaults):
            if dv is d:
                return a.arg
        return "?"

    def _constantes(self, node):
        out = []
        for n in ast.walk(node):
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool):
                out.append(n)
        return out

    def _fila(self, c, contexto, nombre="", extra=""):
        lin = self.lineas[c.lineno - 1].strip() if c.lineno - 1 < len(self.lineas) else ""
        if lin.lstrip().startswith("#"):
            return
        # excluir enteros de indexacion, formateo y conteos triviales sin nombre
        self.filas.append({
            "archivo_linea": f"{self.rel}:{c.lineno}",
            "archivo": self.rel,
            "linea": c.lineno,
            "valor": repr(c.value),
            "contexto": contexto,
            "nombre": nombre,
            "funcion": self.funcion,
            "unidad_inferida": inferir_unidad(nombre, lin),
            "sensor": sensor_de(self.rel, lin),
            "texto": lin[:200].replace("—", ":").replace("–", "-"),  # sin guiones largos en los entregables
            "extra": extra,
        })

    def visit_Subscript(self, node):
        # indices y slices no son magnitudes
        self._en_subscript += 1
        self.visit(node.value)
        self._en_subscript -= 1

    def visit_Assign(self, node):
        if self._en_subscript:
            return
        nombres = [ast.unparse(t) for t in node.targets]
        nombre = ",".join(nombres)
        # asignacion de constante directa o expresion con constantes (evita strings/formatos)
        if isinstance(node.value, (ast.JoinedStr, ast.Str if hasattr(ast, "Str") else ast.JoinedStr)):
            return
        for c in self._constantes(node.value):
            if self._es_trivial(c, node.value):
                continue
            self._fila(c, "asignacion", nombre=nombre)
        self.generic_visit(node.value)

    def visit_AnnAssign(self, node):
        if node.value is None:
            return
        nombre = ast.unparse(node.target)
        for c in self._constantes(node.value):
            if self._es_trivial(c, node.value):
                continue
            self._fila(c, "asignacion", nombre=nombre)

    def visit_AugAssign(self, node):
        nombre = ast.unparse(node.target)
        for c in self._constantes(node.value):
            if self._es_trivial(c, node.value):
                continue
            self._fila(c, "asignacion_aug", nombre=nombre)

    def visit_Compare(self, node):
        if self._en_subscript:
            return
        lados = [node.left] + list(node.comparators)
        nombre = " ".join(ast.unparse(x) for x in lados if not isinstance(x, ast.Constant))[:80]
        for c in self._constantes(node):
            self._fila(c, "comparacion", nombre=nombre, extra=ast.unparse(node)[:120])
        # no descender: ya tomamos todas las constantes del compare

    def visit_Call(self, node):
        fn = ast.unparse(node.func)
        base = fn.split(".")[-1]
        if base in {"clip", "maximum", "minimum", "min", "max", "nanmax", "nanmin", "round", "where", "isclose", "allclose"}:
            for c in self._constantes(node):
                self._fila(c, f"recorte:{base}", nombre=fn, extra=ast.unparse(node)[:120])
            return
        if base == "get" and len(node.args) >= 2:
            clave = ast.unparse(node.args[0])
            for c in self._constantes(node.args[1]):
                self._fila(c, "get_respaldo", nombre=clave, extra=ast.unparse(node)[:120])
            for a in node.args[2:]:
                self.visit(a)
            return
        if base in {"range", "print", "format", "zfill", "sleep", "info", "debug", "warning", "error", "ljust", "rjust", "center", "savefig", "subplots", "figure", "set_size_inches", "exit"}:
            return
        for kw in node.keywords:
            for c in self._constantes(kw.value):
                if self._es_trivial(c, kw.value):
                    continue
                self._fila(c, "kwarg", nombre=f"{fn}({kw.arg}=)", extra=ast.unparse(node)[:120])
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, (int, float)) and not isinstance(a.value, bool):
                if a.value in (0, 1, -1, 2) and base not in {"haversine", "ring_mask", "mask", "cluster_hotspots"}:
                    continue
                self._fila(a, "arg_posicional", nombre=fn, extra=ast.unparse(node)[:120])
            else:
                self.visit(a)
        for kw in node.keywords:
            self.visit(kw.value)

    def visit_Return(self, node):
        if node.value is None:
            return
        for c in self._constantes(node.value):
            if self._es_trivial(c, node.value):
                continue
            self._fila(c, "return", nombre="return")
        self.generic_visit(node)

    def visit_Dict(self, node):
        for k, v in zip(node.keys, node.values):
            kn = ast.unparse(k) if k is not None else "?"
            for c in self._constantes(v):
                if self._es_trivial(c, v):
                    continue
                self._fila(c, "dict_valor", nombre=kn)
        # no descender dos veces

    def _es_trivial(self, c, expr):
        # 0, 1, -1 sueltos dentro de aritmetica de indices (i+1, n-1) se omiten; si la expresion
        # entera ES la constante (x = 0.0) se conserva, porque un piso en 0 es magnitud.
        if expr is c:
            return False
        if isinstance(expr, ast.UnaryOp) and expr.operand is c:
            return False
        return c.value in (0, 1, -1) and isinstance(expr, (ast.BinOp, ast.Call, ast.Tuple, ast.List))


def censar_python(ruta: Path, raiz: Path) -> list[dict]:
    src = ruta.read_text(encoding="utf-8", errors="replace")
    try:
        arbol = ast.parse(src)
    except SyntaxError as e:
        print(f"SINTAXIS {ruta}: {e}", file=sys.stderr)
        return []
    v = Censo(ruta, raiz, src.splitlines())
    v.visit(arbol)
    # dedupe (misma linea, mismo valor, mismo contexto)
    vistos = set()
    out = []
    for f in v.filas:
        k = (f["archivo_linea"], f["valor"], f["contexto"])
        if k in vistos:
            continue
        vistos.add(k)
        out.append(f)
    return out


# ----------------------------------------------------------------------------- perfil
def censar_perfil(raiz: Path) -> list[dict]:
    env = dict(os.environ, VRP_PROFILE="mirova_equivalent", PYTHONIOENCODING="utf-8")
    cod = (
        "import pipeline.profile as p, json\n"
        "out={}\n"
        "for k in sorted(dir(p)):\n"
        "    if k.startswith('_'): continue\n"
        "    v=getattr(p,k)\n"
        "    if isinstance(v,bool) or not isinstance(v,(int,float,list,tuple)): continue\n"
        "    out[k]=v\n"
        "print(json.dumps(out))\n"
    )
    r = subprocess.run([sys.executable, "-c", cod], cwd=str(raiz), env=env, capture_output=True, text=True)
    vals = json.loads(r.stdout.strip().splitlines()[-1])
    yaml = (raiz / "pipeline/profiles/mirova_equivalent.yaml").read_text(encoding="utf-8").splitlines()
    prof = (raiz / "pipeline/profile.py").read_text(encoding="utf-8").splitlines()
    filas = []
    for k, v in vals.items():
        # linea en profile.py donde se asigna
        ln = next((i + 1 for i, l in enumerate(prof) if re.match(rf"\s*{re.escape(k)}\s*(:\s*\w+)?\s*=", l)), None)
        # clave yaml candidata (minusculas)
        kl = k.lower()
        ly = next((i + 1 for i, l in enumerate(yaml) if re.match(rf"\s*{re.escape(kl)}\s*:", l)), None)
        filas.append({
            "archivo_linea": f"pipeline/profile.py:{ln}" if ln else "pipeline/profile.py:?",
            "archivo": "pipeline/profile.py",
            "linea": ln or 0,
            "valor": json.dumps(v),
            "contexto": "perfil_efectivo",
            "nombre": k,
            "funcion": "<perfil mirova_equivalent>",
            "unidad_inferida": inferir_unidad(k, k),
            "sensor": sensor_de("pipeline/profile.py", k),
            "texto": f"yaml: pipeline/profiles/mirova_equivalent.yaml:{ly}" if ly else "yaml: (sin clave directa; respaldo de profile.py)",
            "extra": "",
        })
    return filas


# ----------------------------------------------------------------------------- volcanes
def censar_volcanes(raiz: Path) -> list[dict]:
    ruta = raiz / "volcanoes.yaml"
    if not ruta.exists():
        return []
    filas = []
    vol = None
    for i, l in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
        m = re.match(r"\s*-\s*name:\s*(.+)", l) or re.match(r"\s*name:\s*(.+)", l)
        if m:
            vol = m.group(1).strip().strip('"').strip("'")
        m2 = re.match(r"\s*([a-z_]+):\s*(-?\d+(?:\.\d+)?)\s*(#.*)?$", l)
        if m2 and vol:
            k, v = m2.group(1), m2.group(2)
            filas.append({
                "archivo_linea": f"volcanoes.yaml:{i}", "archivo": "volcanoes.yaml", "linea": i,
                "valor": v, "contexto": "volcan_yaml", "nombre": f"{vol}.{k}", "funcion": "<volcanoes.yaml>",
                "unidad_inferida": inferir_unidad(k, l), "sensor": "todos/no aplica", "texto": l.strip()[:200].replace("—", ":").replace("–", "-"), "extra": "",
            })
    return filas


# ----------------------------------------------------------------------------- frontend
JS_PATRONES = [
    ("comparacion", re.compile(r"([A-Za-z_$][\w.$\[\]']*)\s*(<=|>=|<|>|===|!==|==|!=)\s*(-?\d+(?:\.\d+)?(?:e-?\d+)?)\b")),
    ("comparacion", re.compile(r"\b(-?\d+(?:\.\d+)?(?:e-?\d+)?)\s*(<=|>=|<|>)\s*([A-Za-z_$][\w.$\[\]']*)")),
    ("asignacion", re.compile(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(-?\d+(?:\.\d+)?(?:e-?\d+)?)\b")),
    ("recorte", re.compile(r"Math\.(max|min)\(([^)]*?-?\d+(?:\.\d+)?[^)]*)\)")),
    ("respaldo", re.compile(r"(\w+)\s*(?:\?\?|\|\|)\s*(-?\d+(?:\.\d+)?)\b")),
    ("ternario", re.compile(r"\?\s*(-?\d+(?:\.\d+)?)\s*:\s*(-?\d+(?:\.\d+)?)")),
]


def censar_html(ruta: Path, raiz: Path) -> list[dict]:
    rel = str(ruta.relative_to(raiz)).replace("\\", "/")
    filas = []
    en_script = False
    for i, l in enumerate(ruta.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if "<script" in l:
            en_script = True
        if "</script>" in l:
            en_script = False
            continue
        if not en_script:
            continue
        s = l.strip()
        if s.startswith("//") or s.startswith("*") or s.startswith("/*"):
            continue
        for ctx, pat in JS_PATRONES:
            for m in pat.finditer(l):
                g = m.groups()
                nums = [x for x in g if x is not None and re.fullmatch(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", x)]
                nombres = [x for x in g if x is not None and x not in nums and not re.fullmatch(r"<=|>=|<|>|===|!==|==|!=|max|min", x)]
                for v in nums:
                    if ctx == "comparacion" and v in ("0", "1", "-1") and not any(k in l for k in ("vrp", "mw", "km", "dist", "_k")):
                        continue
                    filas.append({
                        "archivo_linea": f"{rel}:{i}", "archivo": rel, "linea": i, "valor": v,
                        "contexto": f"js_{ctx}", "nombre": ",".join(nombres)[:80], "funcion": "<js>",
                        "unidad_inferida": inferir_unidad(",".join(nombres), l), "sensor": sensor_de(rel, l),
                        "texto": s[:200].replace("—", ":").replace("–", "-"), "extra": "",
                    })
    vistos, out = set(), []
    for f in filas:
        k = (f["archivo_linea"], f["valor"], f["contexto"])
        if k in vistos:
            continue
        vistos.add(k)
        out.append(f)
    return out


# ----------------------------------------------------------------------------- control
CONTROL_POSITIVO = [
    # (archivo que debe contener la fila, valor, patron de nombre o texto)
    ("pipeline/process_modis.py", "18.9", "WOOSTER_COEFF"),
    ("pipeline/process_viirs.py", "18.0", "WOOSTER_COEFF"),
    ("pipeline/process_viirs_mod.py", "19.7", "WOOSTER_COEFF"),
    ("pipeline/profile.py", "0.003", "DNTI_CONTEXTUAL_C1_SUMMIT"),
    ("pipeline/profile.py", "0.01", "DNTI_CONTEXTUAL_C1_SCENE"),
    ("pipeline/profile.py", "5.0", "N_SIGMA_MIR_SUMMIT"),
    ("pipeline/profile.py", "10.0", "N_SIGMA_MIR_SCENE"),
    ("pipeline/profile.py", "15.0", "N_SIGMA_MIR_DAY"),
    ("pipeline/profile.py", "5.0", "PATH_D_ONLY_CAP_MW"),
    ("scripts/clase_mirova.py", "1.0", "UMBRAL_PROTEGIDA_MW"),
    ("scripts/clase_mirova.py", "0.05", ""),
    ("scripts/banco_paridad.py", "120", "TOL_S"),
    ("volcanoes.yaml", "20", "PuyehueCordonCaulle.inner_radius_km"),
    ("volcanoes.yaml", "3", "Lastarria.inner_radius_km"),
]


def control(filas: list[dict], raiz: Path, carpeta: Path) -> int:
    fallas = 0
    print("== Control positivo (plan S160 §3 F2) ==")
    for arch, val, nombre in CONTROL_POSITIVO:
        hits = [f for f in filas if f["archivo"] == arch and _mismo_valor(f["valor"], val)
                and (nombre == "" or nombre in f["nombre"] or nombre in f["texto"])]
        est = "OK " if hits else "FALTA"
        if not hits:
            fallas += 1
        print(f"  {est} {arch} {nombre or '(sin nombre)'} = {val}  -> {hits[0]['archivo_linea'] if hits else '-'}")
    print("== Control negativo ==")
    neg = carpeta / "control_negativo_sin_constantes.py"
    neg.write_text('"""Archivo de control: no tiene constantes numericas."""\n'
                   "def f(a, b):\n    return a + b\n", encoding="utf-8")
    fn = censar_python(neg, carpeta)
    print(f"  archivo sin constantes -> {len(fn)} filas (esperado 0)")
    if fn:
        fallas += 1
    print("== Conteo por archivo: AST contra grep independiente (literales numericos fuera de comentarios) ==")
    por_arch: dict[str, int] = {}
    for f in filas:
        if f["contexto"].startswith("js_") or f["contexto"] in ("perfil_efectivo", "volcan_yaml"):
            continue
        por_arch[f["archivo"]] = por_arch.get(f["archivo"], 0) + 1
    pat = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?:[eE]-?\d+)?(?![\w.])")
    cmp_rows = []
    for arch, n in sorted(por_arch.items(), key=lambda kv: -kv[1])[:12]:
        src = (raiz / arch).read_text(encoding="utf-8", errors="replace").splitlines()
        g = 0
        for l in src:
            s = l.split("#", 1)[0]
            g += len(pat.findall(s))
        cmp_rows.append((arch, n, g))
        print(f"  {arch:45s} AST {n:5d}  grep {g:5d}  AST/grep {n / g if g else 0:.2f}")
    (carpeta / "control_conteo_grep.csv").write_text(
        "archivo,ast,grep\n" + "\n".join(f"{a},{n},{g}" for a, n, g in cmp_rows) + "\n", encoding="utf-8")
    print(f"== fallas: {fallas}")
    return 2 if fallas else 0


def _mismo_valor(a: str, b: str) -> bool:
    try:
        return abs(float(a) - float(b)) < 1e-12
    except ValueError:
        return a == b


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raiz", required=True)
    ap.add_argument("--salida", default=None)
    ap.add_argument("--control", action="store_true")
    a = ap.parse_args()
    raiz = Path(a.raiz)
    carpeta = Path(__file__).resolve().parent
    filas: list[dict] = []
    for sub in ("pipeline", "scripts"):
        for p in sorted((raiz / sub).glob("*.py")):
            filas += censar_python(p, raiz)
    filas += censar_perfil(raiz)
    filas += censar_volcanes(raiz)
    for h in ("index.html", "diario.html", "mosaico.html"):
        filas += censar_html(raiz / "frontend" / h, raiz)
    campos = ["archivo_linea", "valor", "contexto", "nombre", "funcion", "unidad_inferida", "sensor", "texto", "extra", "archivo", "linea"]
    salida = Path(a.salida) if a.salida else carpeta / "censo_bruto.csv"
    with open(salida, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    por_ctx: dict[str, int] = {}
    for f in filas:
        por_ctx[f["contexto"]] = por_ctx.get(f["contexto"], 0) + 1
    print(f"filas: {len(filas)} -> {salida}")
    for k, v in sorted(por_ctx.items(), key=lambda kv: -kv[1]):
        print(f"  {k:20s} {v}")
    if a.control:
        sys.exit(control(filas, raiz, carpeta))


if __name__ == "__main__":
    main()
