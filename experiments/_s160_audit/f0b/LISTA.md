# Lista de F0b: hallazgos de S158 sin verificar, encontrados por agentes Fable (los verifica Opus)

Fuente: `docs/AUDIT_S158.md` l. 76; R2-17 de `docs/AUDIT_S158_R2.md` l. 169 (qué modelo lo encontró: SOSPECHA,
asignado a Opus sin saberlo, plan §10 punto 12). Gravedad de S158: 1 o 2. NO abras los `INFORME.md` de S158 antes de
escribir y sellar tu `caminos.md`; después, si un título es ambiguo, puedes leer sólo la sección dada, y lo declaras.

| ID | título | scripts | sección (sólo después de sellar caminos.md) |
|---|---|---|---|
| F4-H2 | K1 casi no decide en Chile: la cota inferible desde la referencia es K1 ≥ -0,87 y no separa -0,8 de -0,7 | `experiments/_s158_audit/f4/` | f4/INFORME.md l. 100 a 121 |
| F4-H3 | El mínimo de cumbre 0,003 es inerte en los tres sensores; lo que decide en la cumbre es 5σ y la caja | ídem | l. 122 a 133 |
| F4-H5 | El OSF v2.5 no puede dar umbrales de detección para ningún sensor: sus pisos son los filtros de Coppola 2026 | ídem | l. 151 a 164 |
| F4-H7 | K1 diurno: el código usa -0,5; la rama diurna (apagada) trae -0,6 de la Tabla 1 de MODIS; el informe S158 no lo registra | ídem | l. 184 a 196 |
| F4-H8 | Coppola 2025 cap. 11 Tabla 2 no es evidencia para VIIRS: sólo trae el NTI de MODIS, atribuido a Wright 2002 | ídem | l. 197 en adelante |
| R2-17 | Las tres vistas del tablero coinciden hoy en efecto (0 diferencias sobre 74.811 records), con divergencias latentes en el texto | `experiments/_s158_audit_r2/m2/05_tres_vistas.js` y `.txt` | `docs/AUDIT_S158_R2.md` l. 169 |

Las páginas de papers de F4 (`experiments/_s158_audit/f4/paginas/`) son renders que no van al repo público: léelas
ahí, no las copies a tu carpeta.
