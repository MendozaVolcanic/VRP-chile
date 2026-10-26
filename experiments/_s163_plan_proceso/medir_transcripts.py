"""S163: tokens y tiempo de los transcripts locales de Claude Code para VRP Chile.

POR QUE: el plan de proceso (docs/PLAN_PROCESO_VRP_CHILE_S163.md) necesita un rango de
costo apoyado en datos, no en recuerdos. Claude Code guarda un .jsonl por sesion en
~/.claude/projects/<carpeta>/ con el campo message.usage de cada respuesta del modelo.
Limite que se declara: Claude Code borra transcripts viejos (cleanupPeriodDays), asi
que esto cubre solo las sesiones que siguen en disco; el script imprime la ventana.

Uso: python -I medir_transcripts.py  (lee solo; no escribe nada fuera de stdout)
"""
import json, os, sys, io, glob, collections, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.expanduser("~/.claude/projects")
carpetas = [d for d in os.listdir(BASE) if "VRP-Chile" in d or d.startswith("D--vrp-trabajo")]
tot = collections.Counter(); por_modelo = collections.defaultdict(collections.Counter)
por_mes = collections.defaultdict(collections.Counter)
n_arch = 0; n_resp = 0; tmin = None; tmax = None; vistos = set()
sesiones = collections.Counter()
for c in carpetas:
    for f in glob.glob(os.path.join(BASE, c, "**", "*.jsonl"), recursive=True):
        n_arch += 1
        es_sub = "subagents" in f.replace("\\", "/")
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try: o = json.loads(line)
                except Exception: continue
                ts = o.get("timestamp")
                if ts:
                    t = ts[:19]
                    tmin = t if tmin is None or t < tmin else tmin
                    tmax = t if tmax is None or t > tmax else tmax
                m = o.get("message") or {}
                u = m.get("usage") if isinstance(m, dict) else None
                if not u: continue
                # una respuesta puede repetirse en varias lineas (bloques); contar por id
                rid = (m.get("id"), o.get("requestId"))
                if rid in vistos: continue
                vistos.add(rid); n_resp += 1
                mod = m.get("model", "?")
                mes = (ts or "?")[:7]
                for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
                    v = u.get(k) or 0
                    tot[k] += v; por_modelo[mod][k] += v; por_mes[mes][k] += v
                sesiones["subagente" if es_sub else "principal"] += 1
print(f"carpetas={len(carpetas)} archivos_jsonl={n_arch} respuestas_unicas={n_resp}")
print(f"ventana_de_timestamps: {tmin} a {tmax} (UTC)")
print("respuestas por tipo:", dict(sesiones))
def fmt(c): return " ".join(f"{k.replace('_input_tokens','').replace('_tokens','')}={c[k]/1e6:.1f}M" for k in ("input_tokens","cache_creation_input_tokens","cache_read_input_tokens","output_tokens"))
print("TOTAL:", fmt(tot))
for mod, c in sorted(por_modelo.items(), key=lambda x: -x[1]["output_tokens"]):
    print(f"  {mod}: {fmt(c)}")
for mes in sorted(por_mes): print(f"  {mes}: {fmt(por_mes[mes])}")
