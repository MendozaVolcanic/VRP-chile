"""Frente G: fecha cada atributo de pipeline.profile con git (solo lectura):
 - primer commit que introduce el NOMBRE en pipeline/profile.py (git log -S --reverse)
 - ultimo commit que toca la linea de su clave en mirova_equivalent.yaml (git log -G)
 - si la clave esta ESCRITA en el YAML operacional o el valor viene del default de profile.py"""
import json, os, re, subprocess
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.abspath(os.path.join(here, "..", "..", ".."))
attrs = json.load(open(os.path.join(here, "perfil_efectivo.json"), encoding="utf-8"))
yml = open(os.path.join(root, "pipeline/profiles/mirova_equivalent.yaml"), encoding="utf-8").read()
prof = open(os.path.join(root, "pipeline/profile.py"), encoding="utf-8").read()
def git(*a):
    return subprocess.run(["git", "-C", root, *a], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
out = {}
for a in attrs:
    if a in ("DEFAULT_PROFILE","PROFILES_DIR","VALID_PROFILES","PROFILE_NAME","DATA_SUBDIR"): continue
    # clave yaml: buscarla como la lee profile.py
    m = re.search(r"^" + re.escape(a) + r"\s*(?::[^=\n]+)?=\s*(.+)$", prof, flags=re.M)
    linea_def = m.group(1)[:160] if m else None
    keys = re.findall(r"""["']([a-z0-9_]+)["']""", linea_def or "")
    key = next((k for k in keys if re.search(r"^\s*" + re.escape(k) + r"\s*:", yml, flags=re.M)), None)
    primero = git("log", "--reverse", "--format=%as %h %s", "-S", a, "--", "pipeline/profile.py").splitlines()
    ultimo = git("log", "-1", "--format=%as %h %s", "-G", r"^\s*" + key + r"\s*:", "--", "pipeline/profiles/mirova_equivalent.yaml") if key else ""
    out[a] = {"definicion_profile_py": linea_def, "claves_candidatas": keys, "clave_escrita_en_yaml_operacional": key,
              "primer_commit_profile_py": primero[0][:140] if primero else None,
              "ultimo_commit_linea_yaml": ultimo[:140] or None}
    print(a, "|", key, "|", (primero[0][:90] if primero else None), "|", ultimo[:90])
json.dump(out, open(os.path.join(here, "fechas_mecanismos.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
