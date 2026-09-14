# Línea base congelada del plan de paridad (S139, generada en S140)

**Qué es.** La medición de partida contra la que se juzga cada cambio de la Fase 1 en adelante
(`docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md` §2 y §3.3). Dos archivos:

| archivo | qué mide | script |
|---|---|---|
| `banco.json` | por sensor y por volcán, en pasada y noche de volcán: recall en positivos, publicación en negativos limpios, `far_ref` y controles | `scripts/banco_paridad.py` |
| `magnitud.json` | razón nuestra/MIROVA contra el OSF v2.5 separada en conteo de píxeles (F_n) y exceso por píxel (F_ex = F_hot × F_bg) | `scripts/descomponer_magnitud_osf.py` |

**No se regenera.** Es una foto. Si se corre de nuevo, va a otra carpeta con su propia fecha; esta
queda para comparar.

## Procedencia

| qué | valor |
|---|---|
| fecha del servidor al generar | 2026-09-14 15:19 UTC (`gh api repos/MendozaVolcanic/VRP-chile -i`, cabecera `Date`) |
| `main` de VRP-chile (código y records) | `04c25f3445ec8d5777bd81a00cab87d570c72bfd` |
| `frontend/index.html` (predicado del dashboard) | blob `24fba8a157136bf76509ed647c7d086d3f9f45aa` |
| consolidado de Mirova-v1 (remoto) | commit `500cf71502721dc2219bc9aeb9eef87293b03243` |
| OCR de Mirova-v1 (remoto) | commit `49ba42714c139c3bda007972811c59e5d6b7eb5e` |
| respaldo del consolidado del 2026-04-08 | blob `3bb77309a1f5c9ec061f908436cb2bdd2d3ea303` |
| OSF v2.5 | `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (fuera de git, 98 MB) |
| ventana del banco | 2026-03-01 a 2026-09-14 |
| ventana de la magnitud | 2025-02-15 a 2025-12-01 (la del OSF) |

## Comandos exactos

```bash
python scripts/banco_paridad.py --out data/audit_continuous/linea_base_s139/banco.json
```

```bash
python scripts/descomponer_magnitud_osf.py --out data/audit_continuous/linea_base_s139/magnitud.json
```

Con `PYTHONIOENCODING=utf-8`, sobre `main` en el sha de arriba. El banco baja los CSV del remoto de
Mirova-v1 en el momento de correr, así que repetirlo después da otra referencia: los shas de arriba
son los que valen para esta foto.

## Números de partida (copiados de los JSON, no transcritos a mano de otra fuente)

Publicación en negativos limpios, por pasada: **VIIRS375 63,7 %** (n 3.026), VIIRS750 22,2 %
(n 4.941), MODIS 11,3 % (n 4.392). Recall por noche de volcán, cualquier sensor: 99,6 % (n 798).

Magnitud V375 contra OSF: n 1.499, R_gm 0,659 = F_n 0,553 × F_ex 1,192; a igual conteo de píxeles
(n 342) R 0,995.

Controles: identidad del predicado OK, AUC barajado 0,488 a 0,508, oráculo 1,0; 0 pares con el
reloj desplazado 6 h, réplica del núcleo F5' sin discrepancias en 1.499.

Estos números reproducen los de S139 (`docs/audit_s139/VERIFICADOR.md`,
`docs/audit_s139/MAGNITUD_DESCOMPOSICION_OSF.md`) con otro código y otra referencia.
