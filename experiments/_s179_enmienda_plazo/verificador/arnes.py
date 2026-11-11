"""Verificador: arnes sobre disparadores() del vigilante real (archivo del worktree, identico a origin/main por hash).
Nada se escribe en el worktree: la variante con tope se arma en memoria."""
import io, sys, types
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path.cwd(); sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
RUTA = RAIZ / "scripts" / "vigilancia_guardia_modis.py"
src = RUTA.read_text(encoding="utf-8")

def cargar(fuente, nombre):
    m = types.ModuleType(nombre); m.__file__ = str(RUTA)
    exec(compile(fuente, str(RUTA), "exec"), m.__dict__)
    return m

real = cargar(src, "vg_real")
VIEJO = "    orden = {vs._clave(p): i + 1 for i, p in enumerate(vistas)}\n"
assert src.count(VIEJO) == 1
NUEVO = ("    _c = {}\n    _v = []\n    for p in vistas:\n        if _c.get(p['volcano'], 0) >= 10:\n            continue\n"
         "        _c[p['volcano']] = _c.get(p['volcano'], 0) + 1\n        _v.append(p)\n    vistas = _v\n" + VIEJO)
tope_ingenuo = cargar(src.replace(VIEJO, NUEVO), "vg_tope")   # tope en vistas, dentro_de_plazo SIN cambiar

ENC = "2026-11-02 20:11:43"
def pasada(vol, i, calla=False):
    t = datetime(2026, 11, 3, 5, 0) + timedelta(hours=12 * i)
    return {"volcano": vol, "sensor": "MODIS", "fecha_utc": t.strftime("%Y-%m-%d %H:%M"),
            "instante_utc": t.strftime("%Y-%m-%d %H:%M:%S"), "vrp_mirova_mw": 10.0, "protegida": True, "minima": False,
            "prod_pub": (False if calla else True), "guardia_pub": True, "prod_via": True}

def correr(m, pasadas, hoy="2026-12-01"):
    d = m.disparadores(pasadas, [], [], hoy, ENC, juzgadas={}, ahora=f"{hoy} 12:00:00")
    return d["veredicto"], d["duracion"]["protegidas_vistas_en_guardia"], d["duracion"]["cumplida"], len(d["reversion"]), len(d["fuera_de_plazo"])

print("columnas: veredicto, vistas, cumplida, n_reversion, n_fuera_de_plazo")
# T1/T2: 13 de Chillan, la 12.a es callada por la via
P = [pasada("NevadosDeChillan", i, calla=(i == 11)) for i in range(13)]
print("T1 real, 13 Chillan, la 12.a callada      :", correr(real, P))
print("T2 tope ingenuo, mismo insumo             :", correr(tope_ingenuo, P))
# T3: la prueba que propone el borrador: 13 de un volcan y 3 de otro
P = [pasada("NevadosDeChillan", i) for i in range(13)] + [pasada("Lascar", 20 + i) for i in range(3)]
print("T3 real (sin tope), 13 + 3                :", correr(real, P))
print("T3 tope ingenuo, 13 + 3                   :", correr(tope_ingenuo, P))
# T3b: insumo con el que la mutacion si cierra: 26 + 3
P = [pasada("NevadosDeChillan", i) for i in range(26)] + [pasada("Lascar", 40 + i) for i in range(3)]
print("T3b real (sin tope), 26 + 3               :", correr(real, P))
print("T3b tope ingenuo, 26 + 3                  :", correr(tope_ingenuo, P))
# T4: hoy, la 29.a contada esta dentro del plazo y la 30.a fuera
P = [pasada("NevadosDeChillan", i, calla=(i == 28)) for i in range(30)]
print("T4 real, 30 Chillan, la 29.a callada      :", correr(real, P))
P = [pasada("NevadosDeChillan", i, calla=(i == 29)) for i in range(30)]
print("T4 real, 30 Chillan, la 30.a callada      :", correr(real, P))
# T5: la guardia tiene record pero NO publica: cuenta para el plazo igual
P = [dict(pasada("NevadosDeChillan", i), guardia_pub=False) for i in range(5)]
print("T5 real, 5 con record de guardia sin publicar:", correr(real, P))
P = [dict(pasada("NevadosDeChillan", i), prod_via=False) for i in range(5)]
print("T6 real, 5 con prod_via False (caida a K) :", correr(real, P))
P = [dict(pasada("NevadosDeChillan", i), prod_via=None, prod_pub=None) for i in range(5)]
print("T7 real, 5 sin record de produccion       :", correr(real, P))
