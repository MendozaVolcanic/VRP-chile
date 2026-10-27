# -*- coding: utf-8 -*-
"""S162 V750-B: nulo de la batería sellada `bateria_regla_v750b.py`, condición de sello de la coordinadora (2026-10-24).

POR QUÉ. Una batería en verde no prueba nada si con la regla rota también sale en verde (A110). Se rompe a mano UNA línea
del analizador por vez y se corre la batería entera: la mutación cuenta como ATRAPADA sólo si la batería sale 1 por
ASERCIÓN (línea «== BATERÍA: FALLAS») y ningún escenario del analizador mutado se cayó con una excepción; si alguno se
cayó, es CAÍDA (S156: una mutación que sólo hace caer el programa no se cuenta como atrapada). Controles: IDENTIDAD (la
copia sin mutar tiene que salir 0, «TODOS LOS ESCENARIOS COMO SE ESPERA») y CAIDA (una mutación que sólo lanza una
excepción tiene que salir CAÍDA, no ATRAPADA).

Las once mutaciones M1 a M11 son las de la tercera vuelta del verificador (`verificador_v3/mutar_v3.py`, no se
modifica), con el texto apuntado a las líneas de hoy cuando la línea cambió (M5, M7 y M9). M12 y M13 son mías: el
desempate a igual E (VB3-01) y el archivo de pasadas sin gránulo aceptado sin comprobar (VB3-02).
Uso: python mutar_bateria.py --arbol <árbol de origin/main con esta carpeta y evaluar_d25.py del tag> --dest <tmp>
Salida: 0 si los controles salen como deben y todas las mutaciones quedan ATRAPADAS; 1 si no.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

MUTACIONES = {
    "M1": ("no_peor: SIN SUSTRATO siempre es «no peor», sin mirar el neto (VB2-02)",
           'return reg in ("GANA", "EMPATE") or (reg == "SIN SUSTRATO" and neto <= 0)',
           'return reg in ("GANA", "EMPATE") or (reg == "SIN SUSTRATO")'),
    "M2": ("§6.2: se quita «no peor con la tabla sola»",
           'ver[(b, "TO", "decide")][1] == "GANA" and no_peor(b, "tabla")]',
           'ver[(b, "TO", "decide")][1] == "GANA"]'),
    "M3": ("§6.3: se quita «no peor en el canal que decide»",
           '(b == "B1" or (no_peor(b, "decide") and no_peor(b, "tabla")))]',
           '(b == "B1" or no_peor(b, "tabla"))]'),
    "M4": ("§6.3: se quita «no peor con la tabla sola» (VB2-01)",
           '(b == "B1" or (no_peor(b, "decide") and no_peor(b, "tabla")))]',
           '(b == "B1" or no_peor(b, "decide"))]'),
    "M5": ("las pasadas sin gránulo no se leen (VB2-07)",
           'sin_g = dsg.get("pasadas", []) if sg_ok else []',
           'sin_g = []'),
    "M6": ("la cobertura siempre pasa",
           'cob_pasa = cob_ok or bool(a.leer_con_faltantes)',
           'cob_pasa = True'),
    "M7": ("§6.2: entre los que ganan, el de MAYOR E",
           'elegido = min(ganan, key=lambda b: (ver[(b, "TO", "decide")][2], PREF.index(b)))',
           'elegido = max(ganan, key=lambda b: (ver[(b, "TO", "decide")][2], PREF.index(b)))'),
    "M8": ("control positivo sin exigir que B1 publique 3 o más (VB2-06)",
           'and len(pcc) >= 1 and len(pcc_b1) >= 3',
           'and len(pcc) >= 1'),
    "M9": ("una protegida SIN DATO ya no frena la lectura",
           'cob_ok = sg_ok and len(sin) + len(sin_g) <= MAX_SIN_DATO * den_cob and not prot_sin',
           'cob_ok = sg_ok and len(sin) + len(sin_g) <= MAX_SIN_DATO * den_cob'),
    "M10": ("K = producción deja de cerrar la compuerta",
            'gen_ok = bool(nidx) and c_nulo == 0 and k_ok',
            'gen_ok = bool(nidx) and c_nulo == 0'),
    "M11": ("la marca «SIN CENSO» no se escribe en la línea de la ROI",
            'pr(f"== §6 {aviso}ROI elegida: {elegido} ({motivo})")',
            'pr(f"== §6 ROI elegida: {elegido} ({motivo})")'),
    "M12": ("§6.2: a igual E se desempata por el orden de CANDIDATOS y no por el del §6.3 (VB3-01)",
            'elegido = min(ganan, key=lambda b: (ver[(b, "TO", "decide")][2], PREF.index(b)))',
            'elegido = min(ganan, key=lambda b: ver[(b, "TO", "decide")][2])'),
    "M13": ("el archivo de pasadas sin gránulo se acepta sin comprobar que sea de esta lista (VB3-02)",
            'sg_ok = isinstance(dsg, dict) and dsg.get("objetivos_sha256") == sha_obj',
            'sg_ok = isinstance(dsg, dict)'),
    "CAIDA": ("CONTROL: el analizador sólo se cae (excepción al cargar los objetivos)",
              'obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}',
              'raise RuntimeError("mutación de control: el programa se cae")'),
}


def correr(base, dest, nombre, viejo=None, nuevo=None):
    arbol = dest / f"arbol_{nombre}"
    if arbol.exists():
        shutil.rmtree(arbol)
    shutil.copytree(base, arbol)
    f = arbol / "experiments/_s162_v750b/analizar_v750b.py"
    if viejo is not None:
        src = f.read_text(encoding="utf-8")
        assert src.count(viejo) == 1, (nombre, "la línea a mutar aparece", src.count(viejo), "veces")
        f.write_text(src.replace(viejo, nuevo), encoding="utf-8")
    sal = dest / f"bat_{nombre}"
    if sal.exists():
        shutil.rmtree(sal)
    o = subprocess.run([sys.executable, str(arbol / "experiments/_s162_v750b/bateria_regla_v750b.py"), "--arbol",
                        str(arbol), "--dest", str(sal)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=3600, cwd=str(arbol / "experiments/_s162_v750b"))
    txt = o.stdout + o.stderr
    linea = next((l for l in txt.splitlines() if l.startswith("== BATERÍA")), "(sin línea de batería)")
    cayo = any("Traceback (most recent call last)" in p.read_text(encoding="utf-8", errors="replace")
               for p in sal.rglob("stdout.txt"))
    shutil.rmtree(arbol)
    if o.returncode == 0 and "TODOS LOS ESCENARIOS COMO SE ESPERA" in linea:
        estado = "PASA"
    elif cayo or "FALLAS" not in linea:
        estado = "CAÍDA"
    else:
        estado = "ATRAPADA"
    return estado, o.returncode, linea


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arbol", required=True, type=Path)
    ap.add_argument("--dest", required=True, type=Path)
    a = ap.parse_args()
    a.dest.mkdir(parents=True, exist_ok=True)
    L = []

    def pr(s):
        print(s, flush=True)
        L.append(s)

    ident = correr(a.arbol, a.dest, "IDENTIDAD")
    pr(f"IDENTIDAD | {ident[0]} (tiene que ser PASA) | rc {ident[1]} | {ident[2][:200]}")
    malos = 0 if ident[0] == "PASA" else 1
    for nom, (que, viejo, nuevo) in MUTACIONES.items():
        est, rc, linea = correr(a.arbol, a.dest, nom, viejo, nuevo)
        esperado = "CAÍDA" if nom == "CAIDA" else "ATRAPADA"
        malos += est != esperado
        pr(f"{nom} | {est} (tiene que ser {esperado}) | rc {rc} | {que} | {linea[:300]}")
    n_mut = len(MUTACIONES) - 1
    atr = sum(1 for l in L if l.split(" | ")[0] in MUTACIONES and l.split(" | ")[0] != "CAIDA"
              and l.split(" | ")[1].startswith("ATRAPADA"))
    pr(f"== RESUMEN: {atr} de {n_mut} mutaciones atrapadas por aserción; controles "
       f"{'como deben' if ident[0] == 'PASA' and 'CAIDA | CAÍDA' in ' '.join(L) else 'FALLAN'}; "
       f"{'SELLO POSIBLE' if malos == 0 else f'{malos} FUERA DE LO ESPERADO: NO SE SELLA'}")
    (a.dest / "mutar_bateria_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0 if malos == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
