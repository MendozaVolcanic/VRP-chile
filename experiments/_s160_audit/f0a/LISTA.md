# Lista de F0a: hallazgos de S158 sin verificar, encontrados por agentes Opus (los verifica Fable)

Fuente de la lista: `docs/AUDIT_S158.md` l. 76 y `docs/PLAN_AUDITORIA_S158.md` l. 201 a 203 (qué modelo corrió cada
frente). Gravedad de S158: 1 o 2 en todos. Para cada uno: título textual del informe de S158 y carpeta con los scripts
de ese frente (puedes correrlos; NO abras su `INFORME.md` antes de escribir y sellar tu `caminos.md`; después, si un
título es ambiguo, puedes leer sólo la sección de ese hallazgo, en las líneas dadas, y lo declaras).

| ID | título | scripts | sección del informe (sólo después de sellar caminos.md) |
|---|---|---|---|
| F1-H4 | Fuera de la cumbre el mínimo de MIROVA en NTI es 0,02 (0,0225 en nuestras unidades) y decide en 3 de cada 4 pasadas; el nuestro (0,01) decide en 6 % | `experiments/_s158_audit/f1/` | f1/INFORME.md l. 120 a 141 |
| F1-H6 | Lo publicado es un cúmulo con modo de un píxel; MIROVA suma todos los alertados de la escena | ídem | l. 166 a 179 |
| F1-H8 | Diferencias de entrada sin sustrato medible desde los records | ídem | l. 192 a 209 |
| F1-H9 | Un record sin detección vale 0,0 MW; MIROVA lo declara NaN y advierte que no es emisión cero | ídem | l. 210 en adelante |
| F6-3 | Los umbrales de detección de VIIRS 750 no tienen contraste con ningún resultado publicado | `experiments/_s158_audit/f6/` | f6/INFORME.md l. 92 a 108 |
| F6-4 | El código no recorta ΔL, pero MIROVA nunca publica una alerta con VRP nulo o negativo | ídem | l. 109 a 120 |
| F6-5 | La función de VRP probablemente falla, en vez de devolver NaN, cuando la detección rechazó la escena | ídem | l. 121 a 131 |
| F6-6 | El README describe otro empaquetado que el depositado | ídem | l. 132 a 140 |
| F6-7 | Algunos comentarios afirman efectos que el código no tiene | ídem | l. 141 a 150 |
| F6-8 | La dilatación del fondo también agranda los huecos que ya trae M13, y los TIF de MIROVA traen huecos | ídem | l. 151 en adelante |

«El código» en F6 es el código MATLAB de MIROVA publicado en OSF (zm62w); lo que haya de él en el disco lo ubicas
tú (memoria del proyecto: `reference_codigo_mirova_osf.md`).
