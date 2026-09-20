# -*- coding: utf-8 -*-
"""LIBRO DE PRUEBAS: un registro único de lo que este proyecto probó.

POR QUÉ EXISTE
==============
La auditoría S146 midió el mismo problema tres veces, desde tres ángulos
distintos: `hipotesis.json` (frente H, 53 pruebas con su script, ventana y
veredicto), `inventario.json` (frente G, 57 mecanismos vivos de la cadena de
detección) y `grafo.json` (frente E, 63 cierres con sus dependencias). Cada uno
es correcto y ninguno solo alcanza para contestar la pregunta que el proyecto
necesita: "¿esto se probó? ¿con qué? ¿el instrumento sigue existiendo? ¿qué
mecanismo toca? ¿qué cierre se apoya en esto?".

Sin ese cruce, `docs/audit_s146/ESPACIO_Y_ARCHIVO_S146.md` §5 hizo la misma
observación que ya hizo el proyecto muchas veces (A89, A111, A145): "un registro
único de lo probado (pregunta, script, ventana, configuración, veredicto, si el
instrumento existe)". Este script ES ese registro. Se genera, no se edita a
mano: la sección final del `.md` explica cómo agregar una prueba nueva.

CÓMO ESTÁ HECHO
===============
Fusiona los tres JSON de la auditoría S146 sin reinterpretarlos: una fila por
prueba del frente H (que ya es la unidad natural "una prueba, un veredicto"),
con el ID que el frente H ya le dio (estable, no se reasigna acá). Comprueba
contra el sistema de archivos si el instrumento que la midió sigue existiendo
, directo, o dentro de los zips de `experiments/_archivo_ab_local/`, , y cruza
identificadores (D-números, A-números, B-números, flags ENABLE_/MAX_/N_SIGMA_,
rutas de script o de datos) con el inventario de mecanismos (frente G) y con
los cierres del grafo de dependencias (frente E). Un enlace sólo se establece
si hay un identificador o una ruta que aparece literalmente en los dos lados;
si no lo hay, el enlace queda vacío: no se infieren enlaces por parecido de
redacción.

Determinismo: mismas entradas, mismos bytes. Sin fecha de generación adentro,
claves ordenadas, JSON con `sort_keys=True`, y el `.md` con fin de línea LF.
"""
import json
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

F_HIPOTESIS = os.path.join(ROOT, "experiments", "_s146_auditoria", "frente_H", "hipotesis.json")
F_INVENTARIO = os.path.join(ROOT, "experiments", "_s146_auditoria", "frente_G", "inventario.json")
F_GRAFO = os.path.join(ROOT, "experiments", "_s146_auditoria", "frente_E", "grafo.json")
DIR_ZIPS = os.path.join(ROOT, "experiments", "_archivo_ab_local")

OUT_JSON = os.path.join(ROOT, "docs", "LIBRO_DE_PRUEBAS.json")
OUT_MD = os.path.join(ROOT, "docs", "LIBRO_DE_PRUEBAS.md")


def _leer_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ══ 1. Identificadores compartidos ══════════════════════════════════════════
# Sólo se usan para ENLAZAR (frente H <-> frente G <-> cierres del frente E).
# Deliberadamente estrictos: un identificador es un D-número, A-número,
# B-número, un flag en mayúsculas con guión bajo, o una ruta de archivo con
# directorio y extensión de código/datos. Nunca "parecido de texto".
_RE_DAB = re.compile(r"\b[DAB]\d{1,3}[A-Z]{0,3}\b")
_RE_FLAG = re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+){1,}\b")
_RE_PATH = re.compile(r"(?:[\w\-]+/)+[\w\-.]+\.(?:py|yml|yaml|json|md|csv|txt)")

# Rutas y flags demasiado genéricos (citados en decenas de documentos por ser
# los documentos rectores, no porque compartan una prueba concreta). Enlazar
# por ellos sería la misma trampa que A55/A92: "coincide por texto, no por
# identidad". Se excluyen de la fase de ENLACE; para la existencia de archivo
# (columna del instrumento) sí se comprueban igual, sin esta lista.
_RUTAS_GENERICAS = {
    "CLAUDE.md", "docs/MIROVA_DIVERGENCES.md", "docs/MISSION.md",
    "docs/META_RULES_S80.md", "docs/HYPOTHESIS_LOG.md", "docs/AUDIT_S146.md",
    "docs/INDEX.md", "docs/LIBRO_DE_CUENTAS.json", "scripts/libro_de_cuentas.py",
}


def _ids(*textos):
    """Identificadores compartibles presentes en el texto (unión de patrones).

    Las rutas se extraen primero y se enmascaran del texto antes de buscar
    D/A/B-números y flags: si no, el nombre de un documento citado (ej.
    "docs/HYPOTHESIS_LOG.md") se cuela como si fuera un flag ("HYPOTHESIS_LOG")
    y enlaza por igual cualquier par de filas que sólo comparten haber citado
    ese documento: la trampa que el enunciado pide evitar (identificador real,
    no parecido de texto).
    """
    out = set()
    for t in textos:
        if not t:
            continue
        if isinstance(t, list):
            t = " ".join(str(x) for x in t)
        rutas = set(_RE_PATH.findall(t))
        out |= {p for p in rutas if p not in _RUTAS_GENERICAS}
        sin_rutas = _RE_PATH.sub(" ", t)
        out |= set(_RE_DAB.findall(sin_rutas))
        out |= set(_RE_FLAG.findall(sin_rutas))
    return out


# ══ 2. Existencia de archivos citados como instrumento ══════════════════════
_RE_PATH_LIBRE = re.compile(r"[\w\-./]+\.(?:py|yml|yaml|json|md|csv|txt)")
# Directorios citados sin archivo puntual (ej. "experiments/_s107_modis_localmag/
# (existe)"): sólo se reconocen si empiezan por un directorio raíz conocido del
# repo, para no capturar fragmentos de prosa con barra ("y/o").
_RE_DIR_LIBRE = re.compile(
    r"\b(?:experiments|scripts|docs|pipeline|data|tests|scratchpad|frontend|"
    r"\.github)(?:/[\w\-.]+)*/")


def _indice_zips():
    """basename -> [(zip relativo, miembro), ...] para los 205 zips de S146."""
    idx = {}
    if not os.path.isdir(DIR_ZIPS):
        return idx
    for nombre in sorted(os.listdir(DIR_ZIPS)):
        if not nombre.endswith(".zip"):
            continue
        ruta_zip = os.path.join(DIR_ZIPS, nombre)
        rel_zip = os.path.relpath(ruta_zip, ROOT).replace(os.sep, "/")
        try:
            with zipfile.ZipFile(ruta_zip) as z:
                for miembro in z.namelist():
                    base = os.path.basename(miembro.rstrip("/"))
                    if not base:
                        continue
                    idx.setdefault(base, []).append((rel_zip, miembro))
        except zipfile.BadZipFile:
            continue
    return idx


_ZIP_INDEX = _indice_zips()


def _indice_arbol():
    """basename -> [ruta relativa, ...] de TODO el árbol del repo (una sola pasada).

    Los textos de `instrumento` suelen citar rutas parciales (una lista separada
    por comas que omite el directorio compartido, ej. "_archive/x.yml" cuando el
    archivo real vive en ".github/workflows/_archive/x.yml"). Este índice permite
    resolver esas rutas parciales por coincidencia de sufijo, sin adivinar por
    parecido de texto: si el sufijo no calza, no hay resolución.
    """
    idx = {}
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "node_modules", "__pycache__", ".venv")]
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), ROOT).replace(os.sep, "/")
            idx.setdefault(f, []).append(rel)
    return idx


_ARBOL_INDEX = _indice_arbol()


def _existe_directo(rel):
    return os.path.exists(os.path.join(ROOT, rel))


_MANIFIESTO_ZIP = os.path.join(ROOT, "experiments", "_s146_espacio", "manifiesto_zip.json")


def _dir_archivado_en_zip(rel_dir):
    """¿El directorio (sin barra final) es el `origen` de algún zip del manifiesto?"""
    if not os.path.exists(_MANIFIESTO_ZIP):
        return []
    entradas = _leer_json(_MANIFIESTO_ZIP)
    rel_dir = rel_dir.rstrip("/")
    return sorted({e["zip"] for e in entradas if e["origen"] == rel_dir})


def _buscar_en_zips(rel):
    base = os.path.basename(rel)
    return _ZIP_INDEX.get(base, [])


def _buscar_en_arbol(rel):
    """Candidatos cuyo basename coincide; se prefieren los que además terminan
    con la ruta parcial citada (sufijo exacto), porque eso descarta homónimos
    en otro directorio."""
    base = os.path.basename(rel)
    candidatos = _ARBOL_INDEX.get(base, [])
    si_sufijo = [c for c in candidatos if c == rel or c.endswith("/" + rel)]
    return si_sufijo or candidatos


def _estado_instrumento(campo_instrumento):
    """Para cada ruta citada en el campo `instrumento`: existe / en zip / no existe.

    Devuelve (estado_resumen, detalle[]): estado_resumen es el peor caso entre
    todas las rutas citadas ("EXISTE" si todas existen directo o se resuelven por
    sufijo en el árbol, "EN_ZIP" si al menos una sólo está archivada,
    "NO_ENCONTRADO" si al menos una no se pudo localizar en ningún lado,
    "SIN_RUTA" si el campo no cita ninguna ruta con extensión reconocible).
    """
    campo = campo_instrumento or ""
    archivos = set(_RE_PATH_LIBRE.findall(campo))
    dirs = set(_RE_DIR_LIBRE.findall(campo)) - {a for a in archivos if a.endswith("/")}
    # Un directorio que además calzó como prefijo de un archivo ya listado no se
    # repite (ej. "experiments/x/y.py" no vuelve a aparecer como "experiments/x/").
    dirs = {d for d in dirs if not any(a.startswith(d) for a in archivos)}
    rutas = sorted(archivos) + sorted(dirs)
    if not rutas:
        return "SIN_RUTA", []
    detalle = []
    peor = "EXISTE"
    orden = {"EXISTE": 0, "EN_ZIP": 1, "NO_ENCONTRADO": 2}
    for r in rutas:
        es_dir = r in dirs
        if es_dir:
            if os.path.isdir(os.path.join(ROOT, r.rstrip("/"))):
                detalle.append({"ruta": r, "estado": "EXISTE", "resuelto_en": r})
                continue
            en_zip = _dir_archivado_en_zip(r)
            if en_zip:
                detalle.append({"ruta": r, "estado": "EN_ZIP", "zip": en_zip})
            else:
                detalle.append({"ruta": r, "estado": "NO_ENCONTRADO"})
            if orden[detalle[-1]["estado"]] > orden[peor]:
                peor = detalle[-1]["estado"]
            continue
        if _existe_directo(r):
            detalle.append({"ruta": r, "estado": "EXISTE", "resuelto_en": r})
            continue
        en_arbol = _buscar_en_arbol(r)
        if en_arbol:
            detalle.append({"ruta": r, "estado": "EXISTE",
                             "resuelto_en": en_arbol[0],
                             "ambiguo": len(en_arbol) > 1})
            continue
        en_zip = _buscar_en_zips(r)
        if en_zip:
            detalle.append({"ruta": r, "estado": "EN_ZIP",
                             "zip": sorted({z for z, _m in en_zip})})
        else:
            detalle.append({"ruta": r, "estado": "NO_ENCONTRADO"})
        if orden[detalle[-1]["estado"]] > orden[peor]:
            peor = detalle[-1]["estado"]
    return peor, detalle


# ══ 3. Sesión (para ordenar) ═════════════════════════════════════════════
_RE_SESION = re.compile(r"S(\d+)")


def _sesion_orden(campo_sesion):
    nums = [int(n) for n in _RE_SESION.findall(campo_sesion or "")]
    return min(nums) if nums else 10**6


# ══ 4. Construcción del libro ════════════════════════════════════════════
def construir():
    hipotesis = _leer_json(F_HIPOTESIS)
    inventario = _leer_json(F_INVENTARIO)
    grafo = _leer_json(F_GRAFO)

    filas_g = inventario["filas"]
    nodos_e = grafo["nodos"]
    cierres_e = [n for n in nodos_e if n.get("tipo") == "cierre"]

    ids_g = {fila["id"]: _ids(fila.get("mecanismo"), fila.get("donde"),
                               fila.get("valor_efectivo"),
                               fila.get("justificacion_de_entrada"),
                               fila.get("evidencia_estado"),
                               fila.get("referencia_origen"))
             for fila in filas_g}
    ids_e = {nodo["id"]: _ids(nodo.get("etiqueta"), nodo.get("donde"),
                               nodo.get("estado_declarado"),
                               nodo.get("caido_segun_el_proyecto"))
             for nodo in cierres_e}

    filas = []
    for h in hipotesis:
        ids_h = _ids(h.get("que"), h.get("instrumento"), h.get("config_divergente"),
                      h.get("por_que"), h.get("fuente"), h.get("cobertura"),
                      h.get("veredicto_original"), h.get("veredicto_H"))
        mecanismos = sorted(gid for gid, s in ids_g.items() if ids_h & s)
        cierres = sorted(cid for cid, s in ids_e.items() if ids_h & s)
        estado_instr, detalle_instr = _estado_instrumento(h.get("instrumento"))

        filas.append({
            "id": h["id"],
            "que_se_probo": h.get("que"),
            "sesion": h.get("sesion_fecha"),
            "sesion_orden": _sesion_orden(h.get("sesion_fecha")),
            "instrumento_declarado": h.get("instrumento"),
            "instrumento_estado": estado_instr,
            "instrumento_detalle": detalle_instr,
            "ventana_datos": h.get("ventana_datos"),
            "configuracion": h.get("config_divergente"),
            "cobertura": h.get("cobertura"),
            "criterio_preregistrado": h.get("criterio_preregistrado"),
            "veredicto_original": h.get("veredicto_original"),
            "veredicto_frente_h": h.get("veredicto_H"),
            "por_que": h.get("por_que"),
            "profundidad": h.get("profundidad"),
            "fuente": h.get("fuente"),
            "mecanismos_g": mecanismos,
            "cierres_e": cierres,
        })

    filas.sort(key=lambda r: (r["sesion_orden"], r["id"]))

    resumen_veredicto = {}
    for f in filas:
        v = f["veredicto_frente_h"] or "SIN_VEREDICTO"
        resumen_veredicto[v] = resumen_veredicto.get(v, 0) + 1

    resumen_instrumento = {}
    for f in filas:
        e = f["instrumento_estado"]
        resumen_instrumento[e] = resumen_instrumento.get(e, 0) + 1

    n_con_mecanismo = sum(1 for f in filas if f["mecanismos_g"])
    n_con_cierre = sum(1 for f in filas if f["cierres_e"])

    libro = {
        "fuentes": {
            "hipotesis": os.path.relpath(F_HIPOTESIS, ROOT).replace(os.sep, "/"),
            "inventario": os.path.relpath(F_INVENTARIO, ROOT).replace(os.sep, "/"),
            "grafo": os.path.relpath(F_GRAFO, ROOT).replace(os.sep, "/"),
        },
        "pruebas": filas,
        "resumen": {
            "total_pruebas": len(filas),
            "por_veredicto": resumen_veredicto,
            "por_estado_instrumento": resumen_instrumento,
            "con_mecanismo_g_enlazado": n_con_mecanismo,
            "sin_mecanismo_g_enlazado": len(filas) - n_con_mecanismo,
            "con_cierre_e_enlazado": n_con_cierre,
            "sin_cierre_e_enlazado": len(filas) - n_con_cierre,
        },
    }
    return libro


# ══ 5. Render Markdown ═══════════════════════════════════════════════════
def _md_escape(s):
    if s is None:
        return ""
    return str(s).replace("|", "\\|").replace("\n", " ")


def _acorta(s, n=220):
    s = _md_escape(s)
    return s if len(s) <= n else s[: n - 1] + "…"


def render_md(libro):
    L = []
    L.append("# Libro de pruebas: VRP Chile")
    L.append("")
    L.append("Registro único de lo que este proyecto probó: una fila por prueba del "
              "catálogo de hipótesis S146 (frente H), con el instrumento que la midió, "
              "si ese instrumento sigue existiendo hoy, y sus enlaces (cuando hay un "
              "identificador compartido, nunca por parecido de redacción) con los "
              "mecanismos vivos de la cadena de detección (frente G) y con los cierres "
              "del grafo de dependencias (frente E). Generado por "
              "`scripts/libro_de_pruebas.py` a partir de:")
    L.append("")
    for k, v in sorted(libro["fuentes"].items()):
        L.append("- `%s`" % v)
    L.append("")
    L.append("**No editar a mano**: ver la última sección, \"Cómo agregar una prueba\".")
    L.append("")

    r = libro["resumen"]
    L.append("## Resumen")
    L.append("")
    L.append("- Total de pruebas: **%d**" % r["total_pruebas"])
    L.append("- Con al menos un mecanismo del inventario G enlazado: **%d** "
              "(sin enlace: %d)" % (r["con_mecanismo_g_enlazado"], r["sin_mecanismo_g_enlazado"]))
    L.append("- Con al menos un cierre del grafo E enlazado: **%d** "
              "(sin enlace: %d)" % (r["con_cierre_e_enlazado"], r["sin_cierre_e_enlazado"]))
    L.append("")
    L.append("**Por veredicto del frente H:**")
    L.append("")
    L.append("| veredicto | pruebas |")
    L.append("|---|---|")
    for k in sorted(r["por_veredicto"]):
        L.append("| %s | %d |" % (k, r["por_veredicto"][k]))
    L.append("")
    L.append("**Por estado del instrumento** (¿el script/workflow citado existe hoy?):")
    L.append("")
    L.append("| estado | pruebas |")
    L.append("|---|---|")
    for k in sorted(r["por_estado_instrumento"]):
        L.append("| %s | %d |" % (k, r["por_estado_instrumento"][k]))
    L.append("")

    L.append("## Tabla, ordenada por sesión")
    L.append("")
    L.append("| id | sesión | qué se probó | instrumento (estado) | ventana de datos | "
              "configuración | veredicto (frente H) | veredicto original | mecanismos G | cierres E |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for f in libro["pruebas"]:
        instr = "%s: **%s**" % (_acorta(f["instrumento_declarado"], 140), f["instrumento_estado"])
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            f["id"],
            _md_escape(f["sesion"]),
            _acorta(f["que_se_probo"], 180),
            instr,
            _acorta(f["ventana_datos"], 60),
            _acorta(f["configuracion"], 60),
            _md_escape(f["veredicto_frente_h"]),
            _acorta(f["veredicto_original"], 60),
            ", ".join(f["mecanismos_g"]) or ", ",
            ", ".join(f["cierres_e"]) or ", ",
        ))
    L.append("")

    L.append("## Detalle del instrumento por prueba")
    L.append("")
    L.append("Para cada ruta citada en el campo `instrumento` de la prueba: si existe "
              "directamente en el árbol, si sólo se encontró comprimida en "
              "`experiments/_archivo_ab_local/*.zip` (y en qué zip), o si no se encontró "
              "en ningún lado.")
    L.append("")
    for f in libro["pruebas"]:
        if not f["instrumento_detalle"]:
            continue
        L.append("- **%s**:" % f["id"])
        for d in f["instrumento_detalle"]:
            if d["estado"] == "EXISTE":
                extra = "" if d["resuelto_en"] == d["ruta"] else " (resuelto en `%s`)" % d["resuelto_en"]
                if d.get("ambiguo"):
                    extra += ": **ambiguo, hay más de un archivo con ese nombre**"
                L.append("  - `%s`: EXISTE%s" % (d["ruta"], extra))
            elif d["estado"] == "EN_ZIP":
                L.append("  - `%s`: sólo en zip: %s" % (d["ruta"], ", ".join("`%s`" % z for z in d["zip"])))
            else:
                L.append("  - `%s`: NO_ENCONTRADO" % d["ruta"])
    L.append("")

    L.append("## Cómo agregar una prueba")
    L.append("")
    L.append("Este documento y su JSON gemelo (`docs/LIBRO_DE_PRUEBAS.json`) se generan "
              "corriendo `python scripts/libro_de_pruebas.py`: no se editan a mano, "
              "porque el guard `tests/test_guard_libro_de_pruebas_s146.py` falla si el "
              "JSON commiteado no coincide byte a byte con lo que el generador produce "
              "hoy.")
    L.append("")
    L.append("Para agregar una prueba nueva:")
    L.append("")
    L.append("1. Agregar un objeto al final de "
              "`experiments/_s146_auditoria/frente_H/hipotesis.json` (es una lista). "
              "Campos **obligatorios**: `id` (nuevo y único, ej. `H-54`), `que` (qué se "
              "probó, en lenguaje llano), `sesion_fecha`, `instrumento` (script o "
              "workflow que lo midió, con ruta: es lo que este libro comprueba contra "
              "el disco), `ventana_datos`, `veredicto_H`. Los demás campos "
              "(`config_divergente`, `veredicto_original`, `por_que`, `fuente`, "
              "`cobertura`, `profundidad`, `criterio_preregistrado`, "
              "`codigo_respecto_535`, `trabajo_que_apaga`) son opcionales para este "
              "libro, pero el frente H los usa: no borrarlos si ya existen en un "
              "objeto vecino.")
    L.append("2. Si la prueba toca un mecanismo del inventario (frente G) o sostiene o "
              "refuta un cierre del grafo de dependencias (frente E), citar el mismo "
              "identificador (D-número, A-número, flag `ENABLE_...`, o ruta de archivo) "
              "que ya usan `inventario.json` o `grafo.json`: el enlace lo arma este "
              "script solo, por coincidencia literal de identificador. Un enlace vacío "
              "después de agregar la prueba significa que no hay un identificador común "
              "todavía, no que el generador falló.")
    L.append("3. Volver a correr `python scripts/libro_de_pruebas.py` y commitear los dos "
              "archivos generados junto con el cambio al JSON de origen.")
    L.append("")
    return "\n".join(L) + "\n"


def main():
    libro = construir()
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(libro, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")
    md = render_md(libro)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print("pruebas: %d" % libro["resumen"]["total_pruebas"])
    print("por veredicto:", libro["resumen"]["por_veredicto"])
    print("por estado instrumento:", libro["resumen"]["por_estado_instrumento"])
    print("con mecanismo G:", libro["resumen"]["con_mecanismo_g_enlazado"],
          "/ sin:", libro["resumen"]["sin_mecanismo_g_enlazado"])
    print("con cierre E:", libro["resumen"]["con_cierre_e_enlazado"],
          "/ sin:", libro["resumen"]["sin_cierre_e_enlazado"])
    print("escrito:", os.path.relpath(OUT_JSON, ROOT))
    print("escrito:", os.path.relpath(OUT_MD, ROOT))


if __name__ == "__main__":
    main()
