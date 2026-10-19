"""Extrae de la seccion 9 de experiments/_s153_fk_v2/v1.log y v2.log el recall de alertas por sensor
de C0 y K, para comparar con lo que declaran la ficha SDA y el modal del tablero.
P1: si los logs no tuvieran la seccion 9 o el regex no calzara, la tabla sale vacia y el script
    termina con codigo 2 (no reporta cero).
P2: control positivo: debe reproducir los numeros que la ficha SI cita (VIIRS375 K 239/260 y 400/426,
    negativos 21/832 y 37/1010). Si no los reproduce, el parser esta roto.
Denominadores: los de cada log (V1 2026-08-29..2026-10-08, V2 2026-03-01..2026-06-12; 11 volcanes)."""
import re, sys
pat = re.compile(r"^\s+(MODIS|VIIRS375|VIIRS750)\s+(C0|K)\s+recall\s+(\d+) de\s+(\d+) \| protegidas A\s+(\d+) de\s+(\d+) \| negativos limpios publicados\s+(\d+) de\s+(\d+)")
tot = 0
for v in ("v1", "v2"):
    rows = {}
    for line in open(f"experiments/_s153_fk_v2/{v}.log", encoding="utf-8"):
        m = pat.match(line)
        if m:
            s, b, *n = m.groups(); rows[(s, b)] = list(map(int, n))
    tot += len(rows)
    print(f"== {v}")
    for s in ("MODIS", "VIIRS375", "VIIRS750"):
        c, k = rows.get((s, "C0")), rows.get((s, "K"))
        if not c or not k:
            print(s, "SIN DATO"); continue
        print(f"{s:9s} recall C0 {c[0]}/{c[1]} ({100*c[0]/c[1]:.1f} %)  K {k[0]}/{k[1]} ({100*k[0]/k[1]:.1f} %)"
              f"  alertas que K deja de publicar netas = {c[0]-k[0]}  | protegidas K {k[2]}/{k[3]}"
              f"  | negativos K {k[4]}/{k[5]}")
lascar = sum(1 for l in open("experiments/_s153_fk_v2/v2.log", encoding="utf-8") if "recuperada (C0 no la publica): Lascar|MODIS" in l)
print("V2: protegidas MODIS de Lascar que C0 no publica y K si (lineas 'recuperada'):", lascar)
sys.exit(0 if tot >= 12 else 2)
