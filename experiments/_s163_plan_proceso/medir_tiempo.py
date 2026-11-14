"""S163: horas de trabajo activo y mensajes escritos por Nicolas, desde los transcripts locales.

POR QUE: el plan necesita tiempo invertido con rango. Una hora activa = intervalos entre eventos
consecutivos de la MISMA sesion principal menores que un umbral (15 min piso, 30 min techo); las
sesiones en paralelo se cuentan como horas-sesion y aparte como horas de reloj (union de intervalos).
Mensajes de Nicolas = lineas type=user cuyo contenido es texto (no tool_result, no meta, no hooks).
Limite: solo la ventana que sigue en disco (impresa por medir_transcripts.py).
"""
import json, os, glob, io, sys, datetime as dt, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = os.path.expanduser("~/.claude/projects")
def ts(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
ses = []; msgs = 0; msgs_mes = collections.Counter()
for c in os.listdir(BASE):
    if not ("VRP-Chile" in c or c.startswith("D--vrp-trabajo")): continue
    for f in glob.glob(os.path.join(BASE, c, "*.jsonl")):  # solo principales, no subagentes
        t = []
        for line in open(f, encoding="utf-8", errors="replace"):
            try: o = json.loads(line)
            except Exception: continue
            if o.get("timestamp"): t.append(ts(o["timestamp"]))
            if o.get("type") == "user" and not o.get("isMeta") and not o.get("isSidechain"):
                m = o.get("message", {}); cont = m.get("content")
                txt = cont if isinstance(cont, str) else ("".join(b.get("text", "") for b in cont if isinstance(b, dict) and b.get("type") == "text") if isinstance(cont, list) else "")
                if txt.strip() and not txt.lstrip().startswith(("<command", "<local-command", "<system-reminder", "<task-notification", "<side-sessions-event", "<ci-monitor-event", "Caveat:")):
                    msgs += 1; msgs_mes[o["timestamp"][:7]] += 1
        if t: ses.append(sorted(t))
for umbral in (15, 30):
    lim = dt.timedelta(minutes=umbral); hs = 0.0; ivs = []
    for t in ses:
        for a, b in zip(t, t[1:]):
            if b - a < lim: hs += (b - a).total_seconds(); ivs.append((a, b))
    ivs.sort(); reloj = 0.0; cur = None
    for a, b in ivs:
        if cur and a <= cur[1]: cur = (cur[0], max(cur[1], b))
        else:
            if cur: reloj += (cur[1] - cur[0]).total_seconds()
            cur = (a, b)
    if cur: reloj += (cur[1] - cur[0]).total_seconds()
    print(f"umbral {umbral} min: horas-sesion={hs/3600:,.0f}  horas de reloj (union)={reloj/3600:,.0f}")
dias = sorted({x.date() for t in ses for x in t})
print(f"sesiones principales en disco={len(ses)} dias con actividad={len(dias)} ({dias[0]} a {dias[-1]})")
print(f"mensajes escritos por Nicolas (texto, sin eventos automaticos)={msgs}")
print("por mes:", dict(sorted(msgs_mes.items())))
