# Verificador con contexto limpio, segunda vuelta, del pre-registro V750-B v2 (S162)

**Hora del servidor** (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera Date): al empezar Sat, 24 Oct 2026 17:03:17 GMT; al terminar Sat, 24 Oct 2026 17:25:56 GMT.
**Commit verificado**: `607062ba7e1d93553eb5b64d1d228d4919b06afa` (rama `claude/s162-viirs750-f63ef4`). Durante mi sesión el HEAD avanzó a `a6b007e85` por commits de otra sesión; `git diff --stat 607062ba7 HEAD -- experiments/_s162_v750b/` salió vacío y los sha256 de `PREREGISTRO_V750B.md` y `analizar_v750b.py` siguen siendo los de abajo. `origin/main` = `fdbb0bbf0eaa32d2212b9383f6bdbbdd4003b736`; tag `s161-d25-lectura` = `a7418e01d`.
**Modelo y esfuerzo que declaro**: Claude Sonnet 5.5 (`claude-sonnet-5-5`), esfuerzo bajo. Soy otro modelo que el autor de la v2 y que el primer verificador (Fable 5.1).
**Carpeta propia** (scripts y salidas): `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-f63ef4\experiments\_s162_v750b\verificador_v2\`. No toqué nada fuera de ella (el worktree solo muestra `?? experiments/_s162_v750b/verificador_v2/`).
**Árbol temporal para correr** (origin/main por rutas + `_s162_v750b` + `evaluar_d25.py` del tag): `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs750-f63ef4\b455f415-8036-418a-afd4-61523e9603ae\scratchpad\v2\arbol\`. Grillas de N leídas en su lugar en `D:\vrp-trabajo\temporales\s159_n\`; censo S159 leído en `D:\vrp-trabajo\temporales\s159_oraculo\censo_39713438252`. Discos al terminar: C: 42 GB libres, D: 9,7 GB libres (no bajaron de 3 GB).

**Qué NO miré** (declarado, no escondido):
- No despaché ni miré ningún run de GitHub Actions; no corrí el brazo K ni N0/N1 sobre un gránulo real (sin red de LAADS en esta sesión). Lo que sé de ellos es por lectura y por pasadas sintéticas.
- **No calculé P1, P2 ni la ROI elegida sobre datos reales.** El pre-registro prohíbe mirar el resultado antes del sello y yo no quise filtrárselo a quien decide: el analizador completo lo corrí solo sobre poblaciones sintéticas, y sobre las 510 grillas de N solo con `--solo-controles`.
- No re-verifiqué la regla GEO de la grilla (esquina `X0 - 25.000 m`) contra un TIF, ni la cita de los papers del `.m`.
- Corrí el generador `objetivos_v750b.py` contra los datos de hoy (lo que la v1 no pudo), pero no es la lista que se despachará: esa se regenera el día del despacho.

## 0. sha256 de lo verificado (tomados a las 17:03 GMT, antes de leer nada)

| archivo (en `experiments/_s162_v750b/`) | sha256 |
|---|---|
| PREREGISTRO_V750B.md | 817d51cf76c294424c088ebc598089251425ea61c7ea5f44155fa253547f4512 |
| analizar_v750b.py | aa9b675417dbdb0257f40b1d3e6c4dc7dad3e9019037d2a9dd0c78c0a6ec2025 |
| probe_v750b.py | bcb8c419598e83e817c1b0943957f11a4c89ea234a47a079f7a32cd6fbf9addc |
| objetivos_v750b.py | 63199b7142a53245dfc9f3bd35c0d97188d256216299f77467132f538dcd1a4f |
| probe-s162-v750b.yml | 84817b0c121d3c7f24bd073717e90786e9248bffbed120cbecc0f975d89502c4 |
| ensayo_analizador.py | a50fcaed3268e20ce532c27e50a88e5b37a4af564ac03cc4bb64043bb3324ada |
| mutaciones_regla_s6_v2.py | 38fdccdca407f196958f29b0a97fc092fdb062b51c24c54adb915762c5b64b17 |
| prueba_local_510.py | 07f8c4f6fa87f189600f7e57b64cc8e4395e456cbc809a3fe94d2648d882cdc7 |
| `evaluar_d25.py` del tag `s161-d25-lectura` (extraído con `git show`) | 2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747 (coincide con el que fija el pre-registro) |

Mis scripts (en `verificador_v2/`): `potencia_control_censo.py` 863444a9a3738cbd0c5e9dba58e66e82fcd6aa0f2fbdcc8f53ea31ba139bd97e, `geometria_ancla.py` 69d23386c7f5d1bd46a417d631bd331a8b8c92ae3dd71e32a8ed16f27cfefa8c, `mutar_analizador.py` 6951a075ed377d6f4409be367f2187f9d240c462d4037ff0044db24cb8a2add4, `escenarios_v2.py` a0908eef2c6b201fafe9128d375add5ace3912abf4bb5068e6c33197edc9ff93, `escenarios_sobrevivientes.py` 351d611f31deb6f57a4d74affed88301d925da9fd2465fbfbe275db35d4db367; sus salidas están al lado con sufijo `_salida.txt`.

## 1. Caminos por los que la v2 podría estar mal (fijados antes de correr nada)

Honestidad sobre el orden: esta lista la fijé después de leer el pre-registro v2 y el informe del primer verificador, y antes de ejecutar cualquier cosa. No es a priori puro.

- K1. Que una corrección esté en el texto pero no en el código (VB-03, VB-06, VB-11, VB-14).
- K2. Que la regla §6 nueva siga pudiendo elegir un brazo por una razón ajena: canal que no es el escrito, brazo peor que B1 que pasa por «sin sustrato», B1 mismo inelegible.
- K3. Que la compuerta se abra por un camino sin sentido: bandera de pruebas, control positivo que no distingue un oráculo muerto, control negativo que no puede fallar.
- K4. Que la batería adaptada por el mismo autor no pueda fallar donde importa (A110): mutaciones que sobreviven.
- K5. Que las correcciones abran caminos nuevos: pasadas fuera del denominador sin nombre, pasadas sin gránulo, exclusión de pasadas por K distinta.
- K6. Que el generador de objetivos (nunca ejecutado antes de la v2) falle o produzca otra cosa que lo prometido.
- K7. Que la geometría del ancla (`pos_crater`) esté corrida media celda o en otro marco.
- K8. Que el brazo nativo (N0, N1) o su lectura por cenit tenga un defecto que la batería nunca ejecuta (sección que no corre en ninguna prueba).
- K9. Que el run quede desalineado con el código que escribió los records de producción (premisa de «K = producción»).
- K10. Que un desplazamiento de ids entre resultados y objetivos pase sin que nadie lo vea.

## 2. Veredicto por VB (v1 a v2)

| VB | veredicto | evidencia de mi sesión |
|---|---|---|
| VB-01 regla elige un brazo que PIERDE | **CORREGIDO** (queda el hueco VB2-01 en el canal) | `analizar_v750b.py:399-404` exige `b == "B1"` o P2 en EMPATE o SIN SUSTRATO. Batería v2 E1 reproducida: ROI = B1 con B0, B2 y B4 en PIERDE (`verificador_v2/` corrida de `mutaciones_regla_s6_v2.py`, 48 líneas, idéntica a la del autor salvo codificación). Mi S3: B2 y B4 en BLOQUEA, ROI = B1; con la mutación «6.3 admite BLOQUEA» el ROI pasa a B4 (la mutación cae). |
| VB-02 K en None tumba el analizador | **CORREGIDO** | `slim` acepta None (l. 133-139). E7 reproducida: rc 0. Mi V9: record None donde producción publicó una protegida, compuerta CERRADA, rc 3, «K sin record 1». |
| VB-03 OCR vetaba elegibilidad en T | **CORREGIDO** | canal `decide` (l. 301-316). E2 reproducida: CONS 0,6 MW y OCR 1,3 MW en T, B2 no la publica, B2 sigue elegible. Mi S5: la misma configuración fechada 2026-06-13 00:10 (en O) saca a B2 de los elegibles, como corresponde. En los datos de hoy la diferencia es nula en T: 42 protegidas por tabla y 42 por tabla más OCR (conteo propio sobre mi `objetivos_v750b.json`). |
| VB-04 error de K o grilla incompleta salían como «no observada» | **CORREGIDO** | `probe_v750b.py:185-191` pone `estado` `grilla_incompleta` o `error_K`; `main` cuenta como faltante todo estado distinto de `ok` y `volcan_fuera_del_granulo` (l. 277-278) y sale 2 (l. 287). E3 reproducida: las dos protegidas en «protegidas SIN DATO», SIN DATO 2, rc 3. Leído; no ejecuté el probe con red. |
| VB-05 `sorted` con granule None | **CORREGIDO EN PARTE** | El probe ya agrupa con `o.get("granule") or "~sin_granulo|..."` (l. 261-262) y `procesar_granulo` devuelve `sin_granulo` (l. 128-129). Pero `objetivos_v750b.py:102-104` las saca de la lista y solo las imprime: ver VB2-07. Hoy son 0 (mi corrida del generador). |
| VB-06 controles sin frenar | **CORREGIDO EN PARTE** | Positivo y negativo entran a `todo_ok` (l. 361-368); el censo es obligatorio: mi V4 (sin `--censo-art` y sin bandera) da CERRADA, rc 3. Pero el positivo no distingue un oráculo muerto, el negativo no puede fallar y la bandera de pruebas abre la compuerta: VB2-03 y VB2-06. |
| VB-07 distancia desde el centro | **CORREGIDO** | `record_cumulo(..., ancla)` con `pos_crater` (l. 116-130, 214-215). Mi `geometria_ancla.py`: `pos_crater` y `celda_crater` de los 11 volcanes coinciden con un recálculo independiente (11 de 11) y el control positivo (fila invertida) da distinto en 11 de 11. En el `objetivos_v750b.json` que generé hoy: 0 de 5.770 sin `pos_crater`. Mutación «ancla = centro» cae con mi S8 (cúmulo a 4,0 km del cráter y 9,06 km del centro en Tupungatito, inner 7 km); la batería del autor NO la veía. |
| VB-08 canal que decide no escrito | **CORREGIDO** en §6.1 y §6.2; **CORREGIDO EN PARTE** en §6.3 | El texto §4 y §6.1 y §6.2 coincide con el código (l. 390-394). El §6.3 no dice con qué canal se mide EMPATE o SIN SUSTRATO: VB2-01. |
| VB-09 lectura del comentario del `.m` | **CORREGIDO** | B5 = corona 21 × 21 sensible menos 7 × 7 central conservador (`probe_v750b.py:62-67`); el `.m` l. 105-123 (leído en `origin/main:experiments/_s159/o1/o2_paquete/MIROVA_VIIRS750_hotspot_detection.m`) describe BOX 1 central conservador y BOX 2 extendido sensible. El tamaño 7 y 21 lo toma de la matriz de ejemplo (supuesto, no del comentario). `prueba_sin_red_v750b` lo asevera. |
| VB-10 caja nativa en píxeles | **CORREGIDO** en el código (queda SIN DATO real y VB2-14) | `cajas_km` (l. 70-83): semilados 2,625 y 7,875 km desde el centro del TIF; la prueba sin red (`probe_v750b.py:221-228`) exige igualdad con la caja de la grilla sobre malla regular de 750 m y pasa (`--sin-red` corrido, 15 s). La predicción de Tupungatito fue retirada (§8). La sección nativa del analizador nunca corría en la batería: la ejecuté (V12, 3 pasadas S_C sintéticas) y cuenta bien, sin caerse. |
| VB-11 12-oct | **CORREGIDO** | `objetivos_v750b.py:34` incluye `2026-10-12`. Mi corrida del generador: ninguna pasada del 12, 13 ni 17 a 20 de octubre entre las 5.770. |
| VB-12 K = producción binario | **CORREGIDO EN PARTE** | Ahora hay tolerancia de 1 % y las distintas salen de todos los brazos (l. 272-273; mi V8 la ejercita: 1 de 116, compuerta ABIERTA). Se mantiene que una sola protegida distinta cierra la lectura (mi V7 y V9: CERRADA, rc 3). Lista truncada a 20: VB2-13. Premisa de datos verificada en Lascar: ver §5. |
| VB-13 citas y número sin script | **CORREGIDO EN PARTE** | El pre-registro ya cita `origin/s159-pruebas:...` (l. 29) y `01_poblacion.py`. Queda el comentario `probe_v750b.py:61` («medido: 0 de 510 grillas», «primera versión») sin script en el repo (el del primer verificador, `verificador/ancla_centro_vs_crater_510.py`, lo reproduce) y el párrafo escrito a mano al final de `prueba_local_510_salida.txt`. Las 4 primeras líneas de esa salida las reproduje idénticas con el script (`prueba_local_510.py`, 1 min 39 s). |
| VB-14 artefacto vacío | **CORREGIDO EN PARTE** | `probe-s162-v750b.yml:67-68` trae `if-no-files-found: error` y `retention-days: 30`, pero la carpeta `out/` nunca queda vacía porque `tee out/probe_N.log` (l. 61) crea el log: VB2-11. |
| VB-15 placebo | **CORREGIDO** | `PREREGISTRO_V750B.md` §5, última viñeta, lo declara de M (D-44) y de V750-A. |
| VB-16 cobertura en el cráter | **CORREGIDO** | `cobertura()` mide el 7 × 7 alrededor de `celda_crater` (`probe_v750b.py:115-123`); `partida` lo usa (l. 148-159). Mi V10 lo ejerce: la pasada sale como `sin_crater`. Falta el nombre: VB2-07. |

## 3. Hallazgos propios (VB2), lo peor primero

### VB2-01. El desempate §6.3 puede elegir un brazo que PIERDE con la tabla sola
- ARCHIVO:LINEA: `experiments/_s162_v750b/analizar_v750b.py:399-404` (el filtro de candidatos mira solo `ver[(b, "TO", "decide")]`), contra `:393-394` (para ganar sí exige la tabla sola). `PREREGISTRO_V750B.md` §6.3 dice «nunca uno que PIERDE o BLOQUEA» sin decir con qué canal.
- QUÉ PASA: la tabla de MIROVA y la tabla más OCR pueden dar signos distintos. En el canal que decide (T con tabla, O con tabla más OCR) un brazo puede salir EMPATE porque en O recupera alertas que solo trae el OCR, mientras que con la tabla sola pierde con p = 1/64. El §6.2 se cuida de eso para ganar; el §6.3 no se cuida para ser elegido por fidelidad.
- CÓMO SE VE EN EL DASHBOARD: el paquete V750-A heredaría una ROI que, medida contra la parte de la referencia más creíble (A119), publica más negativos de los que compensa.
- CÓMO REPRODUCIRLO: `python experiments/_s162_v750b/verificador_v2/escenarios_v2.py --arbol <arbol> --dest <tmp>`, bloque `== V1`: B2 en `EMPATE(neto 0, bl 12)` con el canal que decide, `PIERDE(neto 6, bl 6)` con la tabla; ROI = B2. Control positivo: `escenarios_sobrevivientes.py`, S2 (el mismo desajuste hecho ganador): la mutación «sin filtro de tabla en 6.2» cae.
- CONFIANZA: CONFIRMADO (corrido, sintético; la frecuencia en datos reales es SIN DATO).
- GRAVEDAD: 3. Arreglo de una línea: exigir también `ver[(b,"TO","tabla")][1] not in ("PIERDE","BLOQUEA")` en `cand`, y escribirlo en §6.3.

### VB2-02. «SIN SUSTRATO» deja pasar por fidelidad a un brazo estrictamente peor que B1
- ARCHIVO:LINEA: `analizar_v750b.py:399-404` (`("EMPATE", "SIN SUSTRATO")`); regla D-45 en `experiments/_s157_prereg_d25/evaluar_d25.py` del tag (`regla_signos_p2`: con 4 bloques o menos devuelve SIN SUSTRATO sin mirar el signo del neto).
- QUÉ PASA: con 4 bloques o menos la prueba de signos no puede rechazar nada (el p mínimo es 1/16), de modo que un brazo que publica 4 negativos de más en 4 noches distintas (neto +4, peor en todos los bloques) queda «SIN SUSTRATO» y, por la preferencia de fidelidad, desplaza a B1.
- CÓMO SE VE EN EL DASHBOARD: más puntos de cumbre en noches sin actividad que con B1, sellado como «a igual desempeño manda la fidelidad».
- CÓMO REPRODUCIRLO: `escenarios_v2.py`, bloque `== V3`: B0, B2 y B4 con `SIN SUSTRATO(neto 4, bl 4)`, ROI = B4.
- CONFIANZA: CONFIRMADO (corrido, sintético). Qué tan probable es en el run real: SIN DATO (con la ventana real hay decenas de bloques, así que lo normal es que el caso no se dé).
- GRAVEDAD: 3. Decisión de diseño para Nicolás: admitir SIN SUSTRATO solo si el neto es 0 o negativo, o declarar por escrito que la fidelidad gana aun siendo peor.

### VB2-03. La bandera `--censo-omitido-solo-pruebas` abre la compuerta y el veredicto sale con rc 0 y sin aviso en la línea que importa
- ARCHIVO:LINEA: `analizar_v750b.py:177-179` y `:290-293`; la línea `== §6 ROI elegida` (l. 405) no cambia.
- QUÉ PASA: la bandera pone `censo_ok = True`. El único aviso («PRUEBA SINTÉTICA: ESTE VEREDICTO NO VALE PARA EL RUN») sale una vez, a mitad de la salida; la línea de la ROI, el `salida.txt` y el código de salida (0) son los de un veredicto válido. Un pegado de la última línea a un informe no lleva la advertencia.
- CÓMO SE VE EN EL DASHBOARD: invisible; se vería como una ROI elegida sin control contra el censo.
- CÓMO REPRODUCIRLO: `escenarios_v2.py`, `== V5`: rc 0, compuerta ABIERTA, «ROI elegida: B4». Sin la bandera y sin censo (V4): CERRADA, rc 3, que es lo correcto.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. Arreglo: que la bandera fuerce rc 4 y reescriba la línea de la ROI con «SIN CENSO, NO VALE».

### VB2-04. No hay camino sancionado para «leer igual» con SIN DATO o con el censo caído
- ARCHIVO:LINEA: `analizar_v750b.py:209-211` (`cob_ok`), `:367-371` (compuerta; `return salir(0 if a.solo_controles else 3)`); `PREREGISTRO_V750B.md` §4: «si siguen faltando, se declaran y la coordinadora decide con Nicolás si se lee igual».
- QUÉ PASA: el texto promete una decisión humana, pero el código no tiene interruptor: leer igual exige editar `analizar_v750b.py` después del sello, o sea cambiar el instrumento con los datos a la vista (la bifurcación que un pre-registro quiere impedir). Lo mismo si el control contra el censo falla por una razón explicable.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: lectura de las líneas citadas; mi V4 y V7 muestran las compuertas cerradas sin salida.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 2. Arreglo: dejar escrita ahora una bandera `--leer-con-sin-dato` que imprima los SIN DATO en cada línea de veredicto, o declarar que el único camino es relanzar.

### VB2-05. La batería v2 del autor deja vivas 14 de 22 mutaciones del analizador (A110), y su sobrevivencia importa
- ARCHIVO:LINEA / SCRIPT:SALIDA: `verificador_v2/mutar_analizador.py` → `mutar_analizador_salida.txt`; escenarios que las matan: `escenarios_sobrevivientes.py` → `escenarios_sobrevivientes_salida.txt`.
- QUÉ PASA: mutación por mutación sobre `analizar_v750b.py` corriendo `mutaciones_regla_s6_v2.py` entera (control: línea base contra sí misma IGUAL; control positivo: la mutación que rompe la sintaxis CAE). Resultado: caen 9 (incluida la de sintaxis), sobreviven 14. Sobreviven: «quita P1 en O con tabla sola» (M1), «quita el filtro de tabla en 6.2» (M2), «6.3 admite BLOQUEA» (M3), «frontera OCR al 07-01» (M5), «ancla del record = centro» (M8), «cobertura ignora protegidas SIN DATO» (M9), «compuerta ignora K = producción» (M10), «compuerta ignora el control negativo» (M12), «tope de SIN DATO 50 %» (M13), «bloque = solo la noche» (M16), «K distinta no sale de los brazos» (M18), «desempate de 6.2 por MAYOR E» (M19), «elegible exige P1 solo en T» (M20), «6.2 con canal todo» (M21). La razón de varias es de diseño de la batería: E5 dice probar el desempate por menor E pero solo gana un brazo (B2 queda EMPATE); E3 mezcla protegida SIN DATO y más de 2 % en el mismo caso; todo ocurre en Lascar, así que el bloque (noche, volcán) nunca se distingue de la noche; nunca hay una K distinta; las fechas nunca tocan la frontera.
  Mis 11 escenarios dirigidos matan 10 de 11 (M2, M3, M5, M8, M9, M10, M13, M16, M18, M19 caen). Sobrevive M21 (no construí el caso). **M1 es un mutante equivalente**: toda protegida de la tabla en O es también protegida en el canal que decide en O (la etiqueta `tabla` es subconjunto de `decide`, l. 301-316), así que «P1 = 0 en O con la tabla sola» (§6.1, segunda condición) nunca puede vetar nada que la primera no vete. M12 sobrevive por el motivo de VB2-06.
- CÓMO SE VE EN EL DASHBOARD: invisible; el riesgo es que una edición futura del analizador rompa esas decisiones y la batería siga en verde.
- CONFIANZA: CONFIRMADO (corrido).
- GRAVEDAD: 2. Mi `escenarios_sobrevivientes.py` se puede sumar a la batería sellada.

### VB2-06. Los controles positivo y negativo de la ROI no distinguen un oráculo muerto ni pueden fallar
- ARCHIVO:LINEA: `analizar_v750b.py:361` (`neg_ctrl = p2("B1","TO","decide")`: B1 contra B1, la contribución `err(b) - err(ref)` es 0 por construcción) y `:362-366` (`pcc` cuenta protegidas de Cordón Caulle que B0 no publica, sin pedir que B1 sí).
- QUÉ PASA: (a) el negativo solo falla si el cálculo de `c` estuviera roto de forma grosera; un negativo con filo sería B4 contra B1 restringido a Cordón Caulle y Tupungatito, donde B4 = B1 por construcción (tiene que dar 0 bloques); la mutación «compuerta ignora el control negativo» sobrevive. (b) con el oráculo muerto (ningún brazo publica nada, producción sí) el positivo lee 1 y la compuerta se abre; hoy solo el control contra el censo lo cubriría, y el censo se puede omitir con la bandera de VB2-03.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `escenarios_v2.py`, `== V6`: «control positivo ... 1», compuerta ABIERTA, elegibles [].
- CONFIANZA: CONFIRMADO (corrido, sintético).
- GRAVEDAD: 2. Arreglo: exigir que B1 publique al menos 3 de esas protegidas, y reemplazar el negativo por B4 contra B1 en los dos volcanes sensibles.

### VB2-07. Las pasadas sin gránulo y las protegidas «no observadas» no se nombran en el analizador
- ARCHIVO:LINEA: `objetivos_v750b.py:102-104` (las saca de la lista y las imprime en stdout del generador); `analizar_v750b.py:201` (`no_obs` solo cuenta por categoría).
- QUÉ PASA: el pre-registro dice que se listan como SIN DATO y que «una protegida SIN DATO» frena la lectura, pero una protegida sin gránulo nunca llega al analizador, así que no puede frenar nada; y una protegida cuyo 7 × 7 del cráter tiene celdas sin dato sale del denominador de todos los brazos con un conteo, sin nombre (V10: `no observadas: {'sin_crater': 1}`, «protegidas SIN DATO: ninguna»).
- CÓMO SE VE EN EL DASHBOARD: «0 protegidas perdidas» con una protegida menos de la que hay. Hoy es latente: mi corrida del generador dio «pasadas sin gránulo: 0 []».
- CONFIANZA: CONFIRMADO (leído y V10).
- GRAVEDAD: 2. Arreglo: que el generador escriba las sin gránulo a un archivo con su sha256 y el analizador las lea; y que imprima por nombre las protegidas en `sin_crater` y `fuera`.

### VB2-08. Multiplicidad sin corregir en la elección de ROI
- ARCHIVO:LINEA: `analizar_v750b.py:393-396` y `PREREGISTRO_V750B.md` §6.2.
- QUÉ PASA: se contrastan hasta cinco brazos (B0, B2, B3, B4, B5) contra B1, cada uno con una prueba de una cola al 5 %, y gana cualquiera que la pase. Si fueran independientes, la probabilidad de que alguno pase por azar sería 1 - 0,95^5 = 22,6 % (aritmética propia; los brazos están muy correlacionados, así que el valor real es menor y no lo medí).
- CÓMO SE VE EN EL DASHBOARD: una ROI elegida por ganar «con p ≤ 5 %» que no tiene ese p.
- CONFIANZA: SOSPECHA (el valor real no está medido).
- GRAVEDAD: 2. El requisito de P1 = 0 y de no perder con la tabla sola ya acota el daño; declararlo por escrito o exigir p ≤ 1 % para elegir por GANA.

### VB2-09. El control contra el censo compara cuenta y VRP, no la posición de los píxeles
- ARCHIVO:LINEA: `analizar_v750b.py:284-289` (`igual = npix == npix and abs(vrp - vrp) < 1e-6`); `PREREGISTRO_V750B.md` §7 dice «mismos píxeles y VRP».
- QUÉ PASA: mi `potencia_control_censo.py`: sobre 504 pasadas comunes (ensayo de las grillas de N contra el censo), 163 tienen píxeles en B0 y 208 en B1 del censo (el control no es trivial). Mutar el VRP de una pasada en 1e-4 → B0_DISTINTO 1, FALLA; agregar un píxel donde el censo no tiene → B1_DISTINTO 1, FALLA; **cambiar solo la posición de los píxeles manteniendo cuenta y VRP → pasa** (`B0_igual 503`, compuerta ABIERTA). Un desplazamiento de la grilla casi seguro cambiaría el VRP, así que el riesgo real es chico.
- CONFIANZA: CONFIRMADO (corrido).
- GRAVEDAD: 1. Arreglo: comparar la lista `pixeles`.

### VB2-10. La segunda condición de §6.1 es redundante
- ARCHIVO:LINEA: `analizar_v750b.py:390`; `PREREGISTRO_V750B.md` §6.1 («y P1 = 0 en O con la tabla sola»).
- QUÉ PASA: ver VB2-05, M1: es un mutante equivalente. No daña, pero el texto sugiere dos vetos independientes cuando hay uno solo.
- CONFIANZA: CONFIRMADO (por lectura de l. 301-316 y por la mutación M1 que sobrevive también a mis escenarios).
- GRAVEDAD: 1.

### VB2-11. `if-no-files-found: error` no puede disparar, porque el log siempre existe
- ARCHIVO:LINEA: `probe-s162-v750b.yml:61` (`| tee out/probe_${{ matrix.chunk }}.log`) y `:67-72` (`out/*.log` está entre las rutas).
- QUÉ PASA: un trozo que muera antes de escribir `resultados_NN.json` sube un artefacto «no vacío» con solo el log. No es un fallo silencioso: el analizador ve `sin_resultado` para todas sus pasadas y la cobertura (más de 2 %) cierra la compuerta. Pero la corrección de VB-14 no hace lo que dice.
- CONFIANZA: CONFIRMADO (leído).
- GRAVEDAD: 1.

### VB2-12. El control «N0 y N1 actúan» del §7 no existe en el código
- ARCHIVO:LINEA: `PREREGISTRO_V750B.md:147`; `grep -n "actúan\|distintos de B0" analizar_v750b.py` da 0. Además la cabecera del §7 dice «todos dentro de la compuerta», y esta fila dice «no cierra la compuerta».
- QUÉ PASA: la lectura nativa imprime cuántas pasadas S_C tienen algún píxel en N0 y N1 al lado del de B0 y B1, pero no compara máscaras, que es lo que el control promete.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1 (es diagnóstico de V750-C).

### VB2-13. La lista de pasadas con K distinta se trunca a 20
- ARCHIVO:LINEA: `analizar_v750b.py:271` (`k_dist[:20]`).
- QUÉ PASA: el §7 dice que las distintas «se listan». Con el tope de 1 % de ~6.000 pasadas pueden salir de todos los brazos hasta unas 60 sin que quede la lista completa en la salida.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

### VB2-14. El centro de la grilla para N0 y N1 no es la celda (33, 33)
- ARCHIVO:LINEA: `probe_v750b.py:70-83` (caja en km desde el centro del TIF) y `:40` (`C = N // 2`).
- QUÉ PASA: `geometria_ancla_salida.txt` mide que el centro del TIF cae en índices de celda (32,75; 33,25), no en (33; 33), en los 11 volcanes. Las cajas de la grilla se centran en la celda (33, 33) y las nativas en el centro del TIF: difieren en un cuarto de celda (unos 0,19 km) por eje. Solo afecta a la comparación N contra B (diagnóstico) y al ancla «centro» informativa de `analizar_v750b.py:52`.
- CONFIANZA: CONFIRMADO (medido). GRAVEDAD: 1.

### VB2-15. Cifras de tamaño del §9
- El §9 (y el §2) dicen unas 6.900 pasadas; mi corrida del generador con los datos de hoy (`generador_objetivos_salida.txt`) da 5.770 pasadas en 1.301 gránulos (789 de Suomi NPP, 2.609 NOAA-20, 2.372 NOAA-21), sin pasadas sin gránulo, con 573 en octubre; al 2-nov serán unas 6.000. El tiempo (2 h) y los 170 MB siguen siendo SOSPECHA. No cambia ninguna decisión. GRAVEDAD: 1.

## 4. SIN DATO (lo que no pude medir)

- Brazo K y brazos B0 a B5, N0 y N1 sobre gránulos reales en el runner de GitHub Actions (sin red de LAADS).
- Que las pasadas de T y O escritas en `data/mirova_equivalent` por códigos posteriores a la adopción de K (15 `codigo_sha` distintos posteriores a la adopción, del 18 al 24 de octubre en Lascar V750) den lo mismo que el K del tag de despacho: hoy es 1 % o ninguna protegida; no lo medí en el run.
- Frecuencia en datos reales de VB2-01 y VB2-02.
- Que el despacho encuentre todos los gránulos en LAADS (A108).
- Que `EARTHDATA_TOKEN` siga vigente el día del despacho: el registro dice que vence el 2026-12-07 (`REGISTRO_CREDENCIALES.md`, fila 1); no lo probé.

## 5. VERIFICADO LIMPIO (no hay que volver a mirarlo, con el comando)

1. **El generador de objetivos corre de punta a punta** (nunca ejecutado antes de la v2): `python experiments/_s162_v750b/objetivos_v750b.py --data <11 JSON de origin/main> --ref-dest <carpeta> --hasta 2026-11-02` en el árbol temporal, 13 s: 5.770 objetivos, ids densos 0 a 5.769, 0 duplicados (volcán, hora), sin 12, 13 ni 17 a 20 de octubre, 0 sin `pos_crater`, S_C = 614, «alertas V750 de MIROVA sin record nuestro: 0». Conteos propios sobre ese JSON: T con 117 alertas que deciden (42 protegidas), O con 136 (36 por tabla más OCR, 31 solo por tabla), 1.822 y 3.681 negativos limpios. Necesité agregar al árbol `data/mirova_reference/union_historica`, el respaldo 20260408 y `experiments/_s158_d17_diseno/grilla_tif_salida.txt`: el despacho debe hacerse desde un checkout completo.
2. **Geometría del ancla y de la celda**: `python experiments/_s162_v750b/verificador_v2/geometria_ancla.py --arbol <arbol> --ens <ens>`: 11 de 11 iguales a un recálculo independiente; control positivo 11 de 11.
3. **Los controles generales dan verde sobre datos conocidos y con el censo**: `ensayo_analizador.py` (506 objetivos, 504 resultados) y `analizar_v750b.py --solo-controles --censo-art ... --censo-objetivos ...`: cobertura SUFICIENTE (2 SIN DATO), nulo del contador 1.718 perturbaciones con 0 sin cambiar, K = producción 0 de 503, censo B0 igual 503 y B1 igual 503, control positivo 7 protegidas de Cordón Caulle. Idéntico a `ensayo_analizador_salida.txt` salvo el párrafo escrito a mano (`ensayo_controles_con_censo_salida.txt`).
4. **El control contra el censo tiene filo**: ver VB2-09 (163 y 208 pasadas con píxeles; VRP y cuenta mutados caen).
5. **Un desplazamiento de ids entre resultados y objetivos no pasa**: `id_desplazado_salida.txt`: K = producción distintas 366 de 503 (con protegidas), censo FALLA, compuerta CERRADA.
6. **La sección nativa corre**: `escenarios_v2.py` bloque V12 (N0 en el píxel de K 3 de 3, N1 0, por tramo de cenit 40-50), sin caerse.
7. **La prueba de signos es la de D-45 sin copiar a mano**: `cargar_signos` extrae con `ast` y comprueba el sha256 `2e5576...` y las constantes 162, 20, 20; la dirección GANA (neto negativo) coincide con `regla_signos_p2`; bloques (noche UTC, volcán) con las de suma 0 (mutación «c = 0 también cuenta» cae; «bloque = solo la noche» cae con mi S16).
8. **Desempate §6.2 por menor E**: mi S19 (B2 y B3 ganan, B3 con menor E) da B3; la mutación «mayor E» cae.
9. **Compuertas que sí cierran**: más de 2 % SIN DATO sin protegidas (S13), una protegida SIN DATO (S9), K distinta en más de 1 % (S10), una protegida con K distinta (V7, V9), sin censo ni bandera (V4), control positivo en 0 (E4): todas CERRADA con rc 3.
10. **Premisa de «K = producción» en datos de producción** (Lascar V750, 2026-04-01 a 2026-10-24, `git show origin/main:data/mirova_equivalent/Lascar.json`): 618 records de la ventana escritos por el histórico (`codigo_sha` 3695f67, perfil `_s154_reproc_k_historico`, hasta 2026-09-17; 2.136 en todo el archivo desde 2025-02), 110 por `34cea39e` (el commit de adopción de K, #850) del 2026-09-18 al 10-18, y el resto por 15 códigos posteriores; `product_version` `standard` en todos. Las otras 10 volcanes no las miré.
11. **Prueba sin red del probe** (`python experiments/_s162_v750b/probe_v750b.py --sin-red`): `PRUEBA SINTETICA OK`, `prueba_sin_red_v750b: ok` (15 s). `prueba_local_510.py` reproduce las 4 líneas de su salida (celdas, 510 de 510, máscaras).
12. **Workflow**: `"on":` entre comillas (A43), `permissions: contents: read`, paso «Token presente» que falla si el token viene vacío, sin usuario ni clave, `set -o pipefail` antes del `tee`, el probe sale 2 si falta una pasada (`probe_v750b.py:287`), sin `git push`.
13. **Texto sin guiones largos** en los 11 archivos de `_s162_v750b` (conteo 0 en cada uno).
14. **Citas de la v2**: `origin/s159-pruebas` en lugar de rutas inexistentes; B5 contra el comentario del `.m` (l. 105-123); distancias vent-centro de 7,6, 4,9 y 2,0 km recalculadas (`geometria_ancla_salida.txt`).

## 6. Qué cambiaría antes del sello

Obligatorio (texto y una línea de código cada uno): VB2-01 (tabla sola también en §6.3), VB2-02 (decisión de Nicolás sobre «SIN SUSTRATO» con neto adverso), VB2-03 (la bandera de pruebas no puede producir una línea de veredicto limpia), VB2-04 (declarar el camino para leer con SIN DATO).
Antes del despacho, no del sello: VB2-05 (sumar mis escenarios a la batería), VB2-06, VB2-07 (archivo de sin gránulo), VB2-09, VB2-11, VB2-12, VB2-13.

**Conforme con cambios (VB2-01, VB2-02, VB2-03 y VB2-04 antes del sello; el resto antes del despacho).**
