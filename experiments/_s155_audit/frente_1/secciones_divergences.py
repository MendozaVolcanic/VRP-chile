"""Lista cada seccion '## ' de MIROVA_DIVERGENCES.md con: estado en el encabezado, si menciona
Test 1 integrado / conectiva min / banda 21, y si lleva marca S153 en sus primeras 15 lineas.
P1: si una seccion hablara de C0 sin marca, aparece con temas!=[] y s153_inicio=False.
P2: control positivo: D21, D26, D30 y H_S27_1 deben salir con s153_inicio=True (#850 los marco).
Denominador: todas las secciones '## ' del archivo en el worktree cb90031a."""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
path = sys.argv[1]
L = open(path, encoding="utf-8").read().split("\n")
idx = [i for i,l in enumerate(L) if l.startswith("## ")]
idx.append(len(L))
pat = {
 "test1": re.compile(r"test ?1 integrad|integrated-roi|test1 integrad|enable_test1_path|ENABLE_TEST1_PATH", re.I),
 "min": re.compile(r"min\(C1|conectiva `?min|rama OR|`min`", re.I),
 "b21": re.compile(r"banda 21|B21 primaria|band 21|enable_modis_b22_primary|ENABLE_MODIS_B22_PRIMARY", re.I),
}
n=0; nmark=0
for a,b in zip(idx, idx[1:]):
    sec = L[a:b]; head = L[a]
    body = "\n".join(sec)
    temas = [k for k,p in pat.items() if p.search(body)]
    s153_ini = any("S153" in l for l in sec[:15])
    s153_any = "S153" in body
    estado = re.findall(r"\*\*(ABIERTA|CERRADA|RESUELTA|ABIERTO|CERRADO|RESUELTO)[^*]*\*\*", head)
    n+=1
    if temas:
        nmark += s153_ini
        print(f"L{a+1}\t{'S153ini' if s153_ini else ('S153dentro' if s153_any else 'SIN_S153')}\t{','.join(temas)}\t{estado[:1]}\t{head[:110]}")
print(f"\nTOTAL secciones={n}; con temas K impresas arriba; con S153 al inicio={nmark}")
