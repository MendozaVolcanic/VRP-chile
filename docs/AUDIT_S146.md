# Auditoría S146: los cierres, no el código

> Ejecutada el 2026-09-20 según `docs/PLAN_AUDITORIA_S146.md`: cinco auditores Fable en paralelo
> (uno por frente, salidas disjuntas) y un verificador con contexto limpio en dos tramos (el
> primero se cortó por un fallo técnico tras 12 ítems; el segundo retomó desde el disco).
> **Read-only sobre `pipeline/`, `frontend/` y el perfil.** Los informes completos, con la salida
> cruda de cada medición, están en `docs/audit_s146/`; los scripts en
> `experiments/_s146_auditoria/`. Este documento es el índice y la síntesis: **todo número de acá
> está copiado de esos informes, que son la fuente** (S91). El plan que sigue a esta auditoría es
> `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md`.

## 1. Cobertura, primero

| frente | universo | cubierto | cómo | lo que NO se cubrió |
|---|---|---|---|---|
| **A**. Sin respaldo citable | 50 | 50 | 21 re-medidos con herramienta propia, 19 cotejados contra el documento, run o test citado más lejos en la sección, 10 resultaron no ser cierres | no re-ejecutó runs de GitHub Actions ni abrió PDF; no reconstruyó el corpus de cada sesión vieja |
| **B**. Con script | 38 | 25 | 11 scripts corridos (3 en copia), 9 sólo leídos (piden artefactos de CI), 5 sin script que correr | 13 declarados SIN DATO: A/B de S133, D12 de S122, A54, A66, A67, A103, A109/A110, paridad 78 de 78, D10 y 4 hipótesis antiguas |
| **C**. Con paper | 67 (25 del censo, 42 fuera) | 59 | todas contra la página renderizada a imagen, 18 documentos | 8: 4 no eran afirmaciones sobre paper, las baterías S141 de D17 y D18 (muestra de 4, bien), "Coppola 2016b enhanced" sin identificar, Tabla 3 del capítulo Springer |
| **D**. Con número | 74 de los 89 traen cifra | 27 | 24 re-medidos en 8 familias, 3 trazados a su fuente | 33 SIN DATO: 24 históricos sobre un corpus ya reprocesado, 9 con runs sin salida en disco |
| **E**. Cruzados | 89 | 89 | grafo de 63 nodos y 73 aristas (60 explícitas con `archivo:línea`, 13 inferidas y marcadas) | `META_RULES_S80.md` sólo por barrido; no abrió AUDIT_S114, S116, S118 ni S121; bloques de arranque fuera |
| **Verificador** | 17 afirmaciones fundidas | 17 | fuente primaria primero, camino propio, re-corrida de scripts, informe del auditor al final | los frentes A, C y E más allá de los 17 ítems; la cita textual del boletín del GVP (403) |

**El alcance real es mayor que el medido en S145.** El censo de S145 era un piso y además tenía
el control roto (V-14: un `any` sobre una lista vacía que no puede fallar). Con las mismas palabras
clave sin distinguir mayúsculas y con flexiones el universo sube de 89 a **173**; con otras
redacciones de cierre llega a 371 como techo blando. El subconjunto útil son **89 frases nuevas que
apagan trabajo, 55 sin respaldo cerca** (`experiments/_s146_auditoria/frente_A/06_censo_ampliado_prioritarios.md`).
Y el frente E encontró que **40 de los 63 nodos de su grafo no estaban en el censo**. Esta
auditoría cubre bien los 89 originales; los 89 nuevos quedan listados y sin verificar.

**El titular de S145 sobreestimaba por un lado y subestimaba por otro.** "50 de 89 son creencias"
no se sostiene: de los 50, 27 se verifican, 5 en parte, 1 queda sin evidencia, 7 se refutan y 10 no
eran cierres. El censo miraba una ventana de 5 líneas y el respaldo casi siempre está más lejos en
la misma sección. Lo que sí es grave es otra cosa, que ningún conteo capturaba, y es el hallazgo
central de abajo.

## 2. El hallazgo central: el proyecto sabe que el cierre cayó, y el texto caído sigue donde se lee

En las 7 refutadas del frente A, en el E-01 y en V-13 el patrón es el mismo: **otro documento, o
el mismo más abajo, ya registra que el cierre cayó, pero el encabezado, la nota que se lee primero
o `docs/MISSION.md` siguen diciendo lo viejo sin ninguna marca.** No es ignorancia, es propagación:
una rebaja se anota en la raíz y no baja a los hijos.

| dónde se lee lo viejo | qué dice | dónde el proyecto ya sabe que cayó |
|---|---|---|
| `docs/MISSION.md:99-110` (la puerta de 3 preguntas) | D4, D5, D8, D9 "resueltas"; D11 "irreducible, todos los ejes agotados"; GAP #A "no reabrir" | `CLAUDE.md`: A82 rebajada S124 y S138, GAP #A reabierto S128; catálogo: D5 abierta con signo opuesto, D25 reabre D8, D12 corrigió el "límite físico" de D4 |
| A83, A84, D13, NEW-8/S116, A85, D18 y una frase de D19 | citan "irreducible, agotado" de A82/D11 | la rebaja se aplicó sólo a A82 |
| `docs/MIROVA_DIVERGENCES.md:455` | "flag OFF permanentemente, el código ya es fiel" | líneas 1319-1335 del mismo archivo: GAP #A reabierto S128 (tres frentes llegaron a esta línea) |
| encabezado de D8 "RESUELTO" | fondo de anillo resuelto | D25, mismo archivo: la mediana de anillo sigue vigente en 6 de 11 volcanes en MODIS y en los 11 en banda M |
| encabezado de D26 | "efecto nulo bajo `min`" | S145: el sigma gobierna en 58,7 % de V375 y 75,0 % de V750 |
| título y "NO REABRIR" de D16 | "la grilla UTM no explica el sub-reporte" | nota S130 de D17: el mecanismo geométrico sí quedó probado y el brazo fiel nunca se corrió |
| D-PCC, `docs/MIROVA_DIVERGENCES.md:1135` | "adoptado inner = 7 en `volcanoes.yaml`" | `volcanoes.yaml` tiene 20: se revirtió el mismo día (PR #85) y el catálogo no lo anotó |
| NEW-8 en catálogo (435, 478) y `MISSION.md:112` | filtros de no aptos como gap abierto, con A/B pendiente | `ENABLE_UNSUITABLE_FILTERS_267_273 = True` desde S72, consumido por los tres procesadores en las dos ramas (V-05) |

Dos ciclos (A82 con D11 por cita mutua; D9 con NEW-8, cada uno cerrado apuntando al otro) y 13
contradicciones entre documentos completan el cuadro (`docs/audit_s146/FRENTE_E_GRAFO_DE_CIERRES.md`).
**La raíz con más arrastre es el criterio 9 de 9 de la batería del Apéndice A, con hasta 14 cierres
colgando**; por eso la corrección de la vara de A2 (§4) pesa más de lo previsto.

## 3. Veredictos del verificador (lo que sobrevivió al intento de romperlo)

Ninguno de los 17 salió REFUTADO. 13 llevan matiz, y en dos (V-01 y V-10) el matiz corrige al
auditor, no al cierre. Ordenados por cuánto trabajo apagaba el cierre:

| ID | cierre que cae o se matiza | veredicto | grav. | lo esencial |
|---|---|---|---|---|
| **V-06** | Test 1 integrado en el ROI "ES Coppola 2015, Bull. Volcanol. 77:55, §2.2 Eq. 1" | CONFIRMADO, más fuerte | **5** | El artículo 55 del vol. 77 es de Heap et al., mecánica de rocas en andesita (DOI 10.1007/s00445-015-0938-7). Crossref y OpenAlex: 0 artículos de Coppola en esa revista en 2015 (con control de consulta). En `sp426.5.pdf` p. 6 el Test 1 es por píxel contra K1, sin suma sobre el ROI. El Test 1 integrado es un **detector propio**, en producción, que cerró D4, pasó la pregunta 1 de MISSION con esa cita y la lleva en la cabecera FICHA publicable |
| **V-01** | D9 "207 de 214 = 96,7 % confirmados, 0 fuga, sin acciones abiertas" | CON MATIZ | 4 | Los denominadores de S113 se reproducen exactos sobre el commit de junio (199 `far`, 214 `summit`). El numerador no: con "MIROVA publicó alerta" el máximo es 80 de 214 (37,4 %). El rango 201 a 211 sólo aparece si "confirmado" cuenta cualquier fila, incluidas las RUTINA ("MIROVA miró", no "MIROVA vio"). El "0 fuga" es circular; el tope de 5 MW sí funciona. La población no es "altitud del norte": el volcán con más records es PCC y 3 de 4 son VIIRS 750 |
| **V-02** | A82, D11, D12: "en MODIS el pipeline encuentra el cráter el 90 %" | CONFIRMADO | 4 | Tasa base: con negativos limpios hay cúmulo con magnitud dentro del inner en 89,1 % de las pasadas (93,7 % cuando MIROVA alertó). Menos de 5 puntos de contraste, y 144 de 158 positivas son Láscar. El número mide presencia de cúmulo, no detección. En VIIRS sí hay contraste (84,5 contra 62,1; 47,5 contra 22,8), así que el instrumento funciona |
| **V-04** | D16 "la grilla no explica el sub-reporte, NO REABRIR" | CON MATIZ | 4 | Sólo VIIRS 375, 61 días, n = 1 y 2 en dos volcanes, con el remuestreo F70 que D17 declara mal centrado y sin bow tie. Lo refutado fue "el regrid F70 arregla la magnitud", no "la grilla de MIROVA explica el sub-reporte" |
| **V-08** | N·σ = 5 / 10 del test de temperatura de brillo "Coppola 2016a Tabla 1" | CONFIRMADO | 4 | En la Tabla 1, C2 multiplica la desviación de dNTI y dETI. El paper no tiene ningún test de temperatura de brillo. Es un préstamo de números a otra variable, dentro de la frase "la detección MODIS es FIEL", y es justo la clase de path que A69 identifica como vulnerable al gradiente topográfico. Cuánto decide hoy ese camino: SIN MEDIR |
| **V-03** | A83 "agotado", AUC 0,859 | CON MATIZ | 3 | El 0,859 vive en un JSON sin script. Etiqueta: "MIROVA publicó"; todo lo demás se llamó artefacto. Hoy 0,762 global, y es **paradoja de Simpson**: "es VIIRS 375" solo da 0,706 y dentro de volcán y sensor cae a 0,554. La conclusión práctica de A83 (no hay escalar por record) sale reforzada bajo esa etiqueta, pero A83 nunca midió real contra artefacto y no puede apagar esa búsqueda |
| **V-09** | D12 "76 noches de FN recuperadas (reales)" | CON MATIZ | 3 | El script de S121 no carga ninguna referencia: "curada" era "cúmulo dentro del inner". El CSV del scraper tiene 0 filas en esa ventana, pero el OSF v2.5 sí cubre Láscar ahí (55 noches) y corrobora cerca de la mitad. El 76 exacto es NO VERIFICABLE (artefactos perdidos) |
| **V-10** | cierre S126 de D13, "1,5 % corroborado" | CON MATIZ | 3 | Se reproduce exacto (41 de 2.704, 95,2 % MODIS) y parea por mismo sensor. Por noche real la diferencia entre lo apagado y lo publicado es 36,1 contra 38,8 %. De 92 noches sólo apagadas, 1 tiene alerta: **"D13 no es palanca" se sostiene, por otra vía** |
| **V-12** | A99 "a igual conteo la razón es 0,995; no buscar en k, área, banda ni Planck" | CON MATIZ | 3 | El 0,995 compensa dos factores opuestos (cerca de 1,14 y 0,873) y además compensa entre volcanes (0,66 en Copahue a 1,39 en Villarrica). Sólo 156 de 342 pares quedan entre 0,8 y 1,25 |
| **V-13** | `MISSION.md` sin rebajas; D-PCC inner = 7 | CON MATIZ | 3 | ver §2 |
| V-05 | NEW-8 abierta | CONFIRMADO | 2 | No apaga trabajo, lo inventa: alguien podría correr un A/B contra un control que ya tiene el filtro |
| V-07 | "Caso Gaua, p. 17" | CON MATIZ | 2 | "Gaua" no está en SP426.5 (es del paper de Vanuatu, JVGR 322). El "menos de 5 MW" sí está en p. 17, pero para falsas detecciones **diurnas**. La cita mala está también en `pipeline/profiles/mirova_equivalent.yaml:482` y seis perfiles más |
| V-11 | D20, banda 31 "despreciable" | CON MATIZ | 2 | Se midió contra el margen a K1 y no contra C1 = 0,003. La banda 32 amplifica más el terreno (6 a 9 %) que la lava (1 a 3 %). El "74 % de C1" del auditor exagera |
| V-14 | control del censo S145 | CON MATIZ | 2 | No puede fallar. Los 89 y 50 quedan sin control, no refutados |
| V-15 | hueco del corpus | CON MATIZ | 2 | 2025-11-16 a 2026-01-28 en 9 volcanes; en PCC son 111 días (desde 2025-10-10); sólo Villarrica es continuo. Los primeros 19 días de referencia sólo se parean en Villarrica. `CLAUDE.md` dice "serie continua desde 2025-02" |
| V-16 | caso A2 con la vara corregida | CON MATIZ | 2 | ver §4 |
| V-17 | `pc.classification` | CON MATIZ | 2 | ver §5 |

**Hallazgos de los auditores que NO pasaron por el verificador** (quedan como del auditor, con su
confianza): B-03 (A85, "0 robos en 214 noches" incluye noches donde el robo es imposible; sólo
leído), B-08 y B-09 (A83 y A84 con JSON sin script o con probe que ya no existe; A84 se reproduce
igual según el frente A), B-11 (el "no adoptar" de S143 depende de un criterio que su verificador
declaró incapaz de decidir), A-13 (D16, D18 y las compuertas S84/S85 medidas enteras antes de #535:
SIN DATO en el régimen actual, no refutación), C-02 (el tope de 5 MW "no es parche" no lo sostiene
el paper), C-04 a C-06 (A76 mezcla dos papers; el cierre de D3 se apoya en la Ec. 16 del capítulo,
que es del modelo de dos componentes), D-06 (el libro de cuentas mide 2026 entero y cruza #535),
D-07 (las 45 noches de FN de S136 caen todas en enero de 2026, en el hueco del corpus; la conclusión
de A94 sí se reproduce).

## 4. Trabajo nuevo 1: el caso A2 con la vara corregida (decisión 3 de Nicolás)

Criterio escrito y sellado antes de evaluar (`docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md`,
sha256 `758b3ea1c54e2bc9c7d8384ce2f279f723098b4a3f095fa431d573421cdc6b27`, verificado): un caso
positivo se evalúa fuera de la cumbre sólo si una fuente institucional publica una boca activa a
más de 5 km de la coordenada del catálogo **y** la máscara de la figura del autor está a más de
5 km del centro, del mismo lado. La caja de 5 km se traslada, no se agranda. Aplicada a ciegas sólo
cambia A2.

Resultado (`docs/audit_s146/A2_RESULTADO_VARA_CORREGIDA.md`): el mejor brazo (banda 22, sin
compuerta de temperatura, fondo local, conectiva `max`) pasa de 8 a **9 de 9**; producción baja de
6 a **5 de 9** (su "conforme" viejo eran 0,12 a 0,52 MW junto a una cumbre que ese día estaba bajo
hielo). Tres brazos quedan INDECIDIBLES por no guardar posición.

Lo que el verificador agrega (V-16): lo que sostiene el acierto **es la figura del paper**, no el
pre-registro. En la pasada de la figura (04:40) hay 58,3 MW a 0,97 km del punto del GVP y a 0,54 km
de la máscara del autor medida por script; boletín y figura quedan a 0,87 km entre sí. El acierto
aguanta desde 1 km de radio. **Los controles no aportan nada**: C1 es una identidad y los nulos N1
y N2 están vacíos por construcción (la batería guarda un cúmulo por pasada). El orden del
pre-registro no es demostrable (todo estaba sin commitear) y el agente no era ciego. La cita textual
del GVP quedó NO VERIFICABLE (403).

**Qué desbloquea y qué no.** Levanta el bloqueo de criterio que pesaba sobre D21, D22 y D11. No
autoriza adoptar nada: 9 de 9 en nueve escenas MODIS es fidelidad al Apéndice A y no dice nada de
la sobre-publicación, que es donde está la brecha hoy.

## 5. Trabajo nuevo 2: `pc.classification` como post-proceso (decisión 4 de Nicolás)

Implementado fuera del pipeline: `scripts/clasificacion_referencia.py`,
`scripts/clasificar_referencia.py`, `tests/test_clasificacion_referencia_s146.py`, salida en
`data/clasificacion_referencia/` (nunca en `data/mirova_equivalent/`). Cinco valores, ninguno dice
"artefacto": `mirova_confirmed`, `mirova_same_night`, `mirova_silent`, `mirova_saw_outside`,
`no_reference`. Con la copia de referencia de S145 reproduce exacto el diseño aprobado
(157 / 257 / 433 / 15 / 188). Informe: `docs/audit_s146/CLASSIFICATION_IMPLEMENTADA.md`.
**El operador todavía no lo ve**: faltan el workflow y el display, que son decisión aparte.

El verificador (V-17) lo confirmó determinista y sin escritura en los records, y encontró tres
defectos que **se corrigieron en esta misma sesión** (13 tests pasan; el test nuevo de precedencia
falla con el mutante M1, comprobado):

1. `--stats` escribía sin guarda: ahora pasa por `negar_si_dentro_de_records`.
2. El test de la guarda apuntaba a la carpeta real de records (un mutante del verificador escribió
   ahí 11 JSON; los borró y verificó por md5): ahora usa un directorio temporal.
3. Ningún test vigilaba la precedencia (el mutante M1 pasaba 12 de 12 y cambiaría 14 pasadas
   reales): test agregado.

Quedan **abiertos**, y van al plan: 33 de 368 `no_reference` sí tienen fila RUTINA de MIROVA (la
etiqueta les miente); 268 de 1.100 `mirova_silent` son posteriores al corte del OCR y por tanto
provisorios, porque `sync-mirova-csv.yml` no trae `registro_vrp_ocr.csv` (sólo lo trae el audit
semanal) y en la quincena previa 17 de 57 alertas del OCR no tenían equivalente en el consolidado.

## 6. Verificado limpio (lo que NO hay que volver a mirar)

Con una medición propia que podía refutarlos y no lo hizo:

- **Frente A**: D15 (la grilla del TIF coincide al sexto decimal), D20 en su cálculo de Planck, D24
  (margen a saturación), A84 (reproduce aunque su probe se perdió), D10 (411 pares, cero recall
  perdido), NOAA-21 en `fetch.py`, el ancla de Tupungatito con su test de regresión, el scraper de
  TIF vivo, `exclude_zones` apagado, pisos VRP en cero.
- **Frente B**: A12, D5, A94 con A81, A98, A10, A90, S98, el guard del GAP #A, H12, D18.
- **Frente C**: la Tabla 1 completa, los Tests 2 y 3, las ecuaciones 6 y 8, el remuestreo y la
  grilla, la banda 32, las descripciones de D20 a D29, las citas de D21 (p. 3) y D22 (p. 7). Los
  coeficientes 18,9 / 19,7 / 18,0 tienen hoy respaldo publicado en Coppola 2026, Tabla 1. Ningún
  cierre usa a INGV Catania o CNR Potenza como autoridad MIROVA.
- **Frente D**: el control con D13 coincide exacto con S145; la conclusión de A94 se reproduce; 8
  de 19 filas nombran lo que cuentan.
- **Verificador**: los denominadores de S113; "D13 no es palanca"; la conclusión práctica de A83
  bajo su etiqueta; la geometría de A2 por dos herramientas.

## 7. Correcciones redactadas y NO aplicadas

Aplicarlas es decisión del dueño. Están redactadas en los informes de cada frente (el D trae siete,
el E trae la cadena completa por cierre) y agrupadas por familia en
`docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md` §Fase 0.

## 8. Lo que esta auditoría enseña sobre el método

- **Un censo por palabras clave con ventana de 5 líneas mide la redacción, no el respaldo.** Sobreestimó
  las "creencias" (50 contra 8 reales) y subestimó el universo (89 contra 173 o más).
- **Una rebaja que no baja a los hijos es un cierre vivo.** El defecto dominante no fue la falta de
  evidencia sino la falta de propagación.
- **La etiqueta "MIROVA publicó" no es "real".** A83, el 207 de 214 de D9 y las 76 noches de D12
  caen por el mismo lado: se llamó "confirmado" o "artefacto" a algo que la referencia no dice.
- **Una tasa sin tasa base no es una tasa** (V-02). Es A110 aplicado a un porcentaje.
- **Un agregado que mezcla volcanes o sensores puede ser paradoja de Simpson** (V-03, V-12): refuerza
  la regla S126 de estratificar por volcán.
- **El verificador fue un segundo buscador, no un trámite** (Simpson en A83, el OSF en D12, el
  artículo real detrás del 77:55, la figura como ancla de A2), y un mutante suyo ensució el
  directorio de records: los tests de guardas no deben apuntar al árbol real.
