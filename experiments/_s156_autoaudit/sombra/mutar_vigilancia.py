"""Mutaciones de scripts/vigilancia_sombra.py: cada una debe hacer FALLAR una prueba (no caer el script).
Uso: python mutar_vigilancia.py <raiz_worktree>. Restaura el archivo original al terminar."""
import subprocess
import sys
from pathlib import Path

raiz = Path(sys.argv[1])
p = raiz / "scripts" / "vigilancia_sombra.py"
orig = p.read_text(encoding="utf-8")

MUT = {
    "tolerancia_3600": ("TOL_S = cm.VENTANA_S", "TOL_S = 3600"),
    "publica_all": ("return None if not cands else any(r[\"pub\"] for r in cands)",
                    "return None if not cands else all(r[\"pub\"] for r in cands)"),
    "negativos_cualquier_lab": ('if r["b"] == "VIIRS375" and r["lab"] == "neg_limpio"', 'if r["b"] == "VIIRS375"'),
    "negativos_cualquier_sensor": ('if r["b"] == "VIIRS375" and r["lab"] == "neg_limpio"', 'if r["lab"] == "neg_limpio"'),
    "negativos_sin_corte": ("and corte_dt is not None and r[\"dt\"] >= corte_dt]", "]"),
    "cotas_en_todos_los_sensores": ('cotas = COTAS_AB[tipo].get(sensor)', 'cotas = COTAS_AB[tipo].get("VIIRS375")'),
    "ventana_ignorada": ('if f.get("tipo") in cm.TIPOS_ALERTA and win[0] <= f["fecha_utc"][:10] <= win[1]:',
                         'if f.get("tipo") in cm.TIPOS_ALERTA:'),
    "diurnas_incluidas": ("        if diurna(b, vol, dt):\n            continue\n", ""),
    "cumplida_solo_por_dias": ('"cumplida": vistas >= PROTEGIDAS_OBJETIVO or bool(vence and hoy >= vence)',
                               '"cumplida": bool(vence and hoy >= vence)'),
    "muy_bajo_incluye_protegidas": ('if p["protegida"] or p["prod_pub"] is None', 'if p["prod_pub"] is None'),
    "sin_corte_prospectivo": ('pros = [p for p in pasadas if p["fecha_utc"][:16] >= corte]', "pros = list(pasadas)"),
    "corte_estricto": ('pros = [p for p in pasadas if p["fecha_utc"][:16] >= corte]',
                       'pros = [p for p in pasadas if p["fecha_utc"][:16] > corte]'),
    "reversion_sin_protegida": ('reversion = [p for p in calla if p["protegida"]]', "reversion = list(calla)"),
    "calla_sin_sombra": ('return [p for p in pasadas if p["sombra_pub"] is True and p["prod_pub"] is False]',
                         'return [p for p in pasadas if p["prod_pub"] is False]'),
    "sin_d9": ('for f in cm.aplicar_regla_minimas(filas, "SN").filas:', "for f in filas:"),
    "sin_aviso_perfiles": ("avisos = avisos_sombra(ultima, hoy) + avisos_perfiles(prod, sombra)",
                           "avisos = avisos_sombra(ultima, hoy)"),
    "ciega_no_degrada": ('veredicto = "VIGILANCIA_CIEGA"\n    out.update', 'pass\n    out.update'),
    "sombra_detenida_tarde": ("MAX_DIAS_SOMBRA_SIN_DATOS = 3", "MAX_DIAS_SOMBRA_SIN_DATOS = 30"),
    "persistencia_dos": ("def _corridas(fechas, largo=3):", "def _corridas(fechas, largo=2):"),
    "sospecha_apagada": ("sospechosa = (bool(protegidas)", "sospechosa = (False and bool(protegidas)"),
    "duracion_cuenta_retro": ('vistas = sum(1 for p in pros if', 'vistas = sum(1 for p in pasadas if'),
}
tests = ["tests/test_vigilancia_sombra_s156.py"]
try:
    for nombre, (a, b) in MUT.items():
        if orig.count(a) != 1:
            print(f"{nombre:30s} NO APLICA (cuenta {orig.count(a)})")
            continue
        p.write_text(orig.replace(a, b), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-m", "pytest", *tests, "-q", "--no-header", "-p", "no:cacheprovider"],
                           cwd=raiz, capture_output=True, text=True)
        ult = (r.stdout.strip().splitlines() or [""])[-1]
        estado = ("ATRAPADA" if r.returncode == 1 and "failed" in ult and "error" not in ult
                  else f"NO ATRAPADA rc={r.returncode}")
        print(f"{nombre:30s} {estado}  | {ult}")
finally:
    p.write_text(orig, encoding="utf-8", newline="\n")
