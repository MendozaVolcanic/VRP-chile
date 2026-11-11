# Auditoría S179, frente A (MODIS): la adopción de S172 y lo que vino después

ESTADO: COMPLETO.

## 1. Encabezado

- **Hora del servidor** (GitHub, cabecera `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`): miércoles 11 de noviembre de 2026, 00:53:58 GMT. Los insumos de GitHub que me dejaron son del 2026-11-10 20:37:28 GMT.
- **Commit sobre el que medí**: código y datos de `main` en `438a60a1e`. Documentos del loop en `0472cd95e`. La regla sellada, en el tag `s173-regla-modd-sellada` (`33dac1eca`). La lectura de la retrospectiva, en la rama `claude/s178-retro-lectura` (`ff8a39972`). El A/B de MOD-D, en la rama `claude/s170-modd-f4-procedencia` (`25e3cc3ba`). La auditoría S175, en la rama `claude/relaxed-almeida-d17378` (`37670d910`).
- **Modelo y esfuerzo**: Fable 5.2 (`claude-fable-5-2`). En mi contexto leo `reasoning_effort 30`. Qué nivel de pedido es eso no lo puedo medir desde aquí: se mide en el transcripto.
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\a\`. Temporal: `D:\vrp-trabajo\temporales\s179-audit\a\` (205 MB; ahí está `base\`, la copia del código y los datos de `438a60a1e` con que corrí los instrumentos del repo; los scripts de la CARPETA la necesitan, no la borres).
- **Cómo medí**. Saqué de `438a60a1e`, con `git archive`, las carpetas `scripts`, `pipeline` y `frontend`, los datos de producción, de la guardia, de la sombra y la referencia de MIROVA. Comparé los 323 archivos de código con sus blobs del commit (0 distintos). Los sha256 de la referencia son los declarados en mi encargo (`40b1b928...7fdf6` y `7e54155a...1e75`). Todos los números de este informe salen de scripts que están en la CARPETA, con su salida al lado.
- **Cómo armé el inventario de decisiones**: `python 01_inventario_entradas.py` (salida `01_inventario_entradas.txt`): 153 entradas de la bitácora §6 de S171 a S178, 90 con palabras del eje MODIS. Leí enteras las 90 y los bloques de arranque S172 a S179 en sus partes de MODIS. Incluí S171 porque la decisión de adelantar MODIS es del 2026-10-31.
- **Uso de la API de GitHub**: 7 llamadas (lista de corridas del NRT, 4 corridas, 1 log, la hora). Ninguna llamada a NASA. Ningún commit, push, merge ni workflow.

### Qué NO miré (mi silencio aquí no quiere decir «todo bien»)

- `docs/PLAN_AUDITORIA_S179.md`, `experiments/_s179_*` fuera de mi carpeta y `D:\vrp-trabajo\temporales\s179-audit\papelera_ola1_cortada\` (el trabajo de la ola anterior). No los abrí.
- No volví a correr el lector de la retrospectiva ni el del A/B de MOD-D. Leí sus salidas y comprobé que son coherentes con sus reglas selladas.
- No abrí el tablero en un navegador ni el sitio publicado. No verifiqué #944 (regla de cirrus) ni #984 (los avisos fuera).
- No corrí la suite de pruebas.
- No miré las guardias de VIIRS, ni la sombra de los 34, ni el día (MODIS diurno).
- No pude abrir ningún gránulo: sin NASA no se puede decir por qué la vía descartó una pasada concreta.
- De las 8 corridas rojas del NRT desde el encendido abrí 4, y leí el log de 1.

### Una premisa que choca con la bitácora

Mi encargo dice que el tablero lo mira un operador del OVDAS. La bitácora del 2026-11-03 10:23 UTC registra a Nicolás: «nadie consume el producto, solo usan el scraper hasta que podamos demostrar que tenemos los mismos datos y podamos extender a los otros volcanes» (`tasks/LOOP_OBJETIVOS.md` l. 1360 a 1361, TEXTO). Puse la gravedad pensando en el uso que el sistema va a tener. Hoy, según esa frase, ninguna alerta de este informe llegó a un operador.

## 2. En una pantalla

1. **La adopción en MODIS de la vía «código MIROVA» (el detector nuevo, que corre el código que MIROVA publicó) se sostiene con los datos de hoy, pero la prueba de que no pierde alertas viene casi toda de Chillán y Láscar.** Desde el encendido (2026-11-02 20:11:43 UTC) MIROVA publicó 11 alertas MODIS nocturnas de 1 MW o más (protegidas), las 11 en Nevados de Chillán. La vía publicó las 11. El detector anterior (K), que corre aparte como guardia, publicó 8. Hay 212 records de la vía y ninguna caída a K.
2. **La reversión pre-autorizada se acaba hacia el 20 de noviembre, no en el día 109 que estima la regla.** El plazo cuenta 29 alertas protegidas y ya van 11, todas de Chillán. Después de eso, una alerta que la vía calle ya no autoriza a revertir sin Nicolás.
3. **La guardia no ve una pérdida de la vía cuando K tampoco publica** (3 de las 11 alertas desde el encendido están en ese caso) **ni cuando la vía no deja record y K no publica**. En esos casos el único aviso es el audit semanal, hasta 7 días después.
4. **Revertir ya no es un `git revert` limpio**: choca en 6 archivos sobre `main` y en 11 después de encender VIIRS. El flag sí se apaga limpio. Y el plan de reemplazo de la historia (#981) dejaría la vigilancia de la guardia en «ciega» todos los días.
5. **La retrospectiva dio lo que su pre-registro predijo para MODIS** (fila 4, DECIDE NICOLÁS; sin poder sin las 4 pasadas ya miradas). Esa decisión no está en la lista de preguntas del bloque S179.

## 3. Inventario de decisiones del eje MODIS y veredicto

Decisión de Nicolás quiere decir aquí una frase suya en la bitácora con su hora. Las líneas son de `D:\vrp-trabajo\temporales\s179-audit\loop\tasks\LOOP_OBJETIVOS.md` (`0472cd95e`).

| # | Fecha UTC, sesión, línea | Decisión | Veredicto | Evidencia de esta sesión |
|---|---|---|---|---|
| 1 | 2026-10-31 18:54, S171, l. 1811 | «cuando recomiendes»: encender MODIS en la parada de la sombra | Reemplazada por la 2 el mismo día | Leído |
| 2 | 2026-10-31 21:55, S171, l. 1695 | «hagamos todo lo recomiendas...»: adelantar MODIS sin la sombra de 28 noches, con K de guardia y regla de reversión | **SOSTENIDA CON RESERVAS** | La evidencia de ese día era el A/B de MOD-D, dentro de la ventana con que se armó la vía (`13_ab_modd_discordantes.txt`), y 0 noches de sombra (`12_sombra_primer_record.txt`). Lo posterior la apoya (hallazgo 407, sección 6). Reservas: 401, 402, 407. La frase no es un «sí» llano; la bitácora misma dice que no es el sí de A45, y el sí llegó el 2026-11-02 |
| 3 | 2026-11-01 23:37, S172, l. 1656 | «Sí, prepáralo»: dos PR (A inerte, B sólo el flag) y mini auditoría | **SOSTENIDA** | La mini auditoría encontró antes del merge el bloqueante de `pyproj`. Hoy `nrt.yml` l. 143 instala `pyproj`. El código de la vía no cambió desde el merge (sección 6) |
| 4 | 2026-11-02 15:42, S173, l. 1474 | D1: investigar con más de 2 alertas Muy Bajo perdidas en 120 días | **SOSTENIDA CON RESERVAS** | Conteo del A/B reproducido: 2 de 43 (`13_...txt`, `16_poblacion_ab_por_volcan.txt`). Desde el encendido no hubo ninguna alerta Muy Bajo (n = 0): la cota todavía no se probó |
| 5 | ídem | D2: investigar con más de 3 sobre-publicaciones en 120 días | **SOSTENIDA CON RESERVAS** | Conteo reproducido: 3 de 5.321. Desde el encendido: 1 de 152 en 8 noches (hallazgo 411) |
| 6 | ídem | D3: esperar 24 h antes de leer como silencio una protegida sin record | **SOSTENIDA CON RESERVAS** | Funciona (mutación M4). Sólo dispara si K publica (hallazgo 402, M10) |
| 7 | ídem | D4: sin disparador de rachas | **SOSTENIDA** | Nada medido en contra |
| 8 | ídem | D5: A y B separados; la reversión revierte sólo B | **SOSTENIDA CON RESERVAS** | El merge tiene dos padres y el flag se revierte limpio. El resto del revert ya choca (hallazgo 403) |
| 9 | ídem | D6: revertir sin la imagen de MIROVA si la alerta viene de la tabla | **SOSTENIDA**, sin probar | Las 11 protegidas desde el encendido están en la tabla. Si la captura de imágenes sirve hoy: SIN DATO |
| 10 | ídem | D7: el día después de una reversión, apartar los records de la vía | **DEBILITADA** en su premisa, ya marcada | La premisa «el NRT re-escribe 8 fechas» es falsa. La marca A113 del 2026-11-07 está en la regla de `main` (único cambio contra el sello, comprobado con `diff`) |
| 11 | 2026-11-02 17:12, S173, l. 1408 | «Sí, sellar y encender»: sello de la regla, A45 y merge de #934 por merge commit | **SOSTENIDA** | `499935c37` tiene dos padres (`438a010ab` y `33dac1eca`). El tag apunta a `33dac1eca`. Flags leídos de `pipeline.profile`: producción `True`, guardia `False`, laboratorio `False`. Encendido medido en los datos: 2026-11-02 20:11:43 |
| 12 | Regla §4.6 (sellada el 2026-11-02) | El plazo: 29 protegidas con record de la guardia o 120 días | **DEBILITADA** | Hallazgo 401 |
| 13 | 2026-11-03 09:39, S173, l. 1381 | «Sí, los cuatro»: la guardia K reemplaza la sombra de 28 noches de MODIS | **SOSTENIDA CON RESERVAS** | La guardia corre y cubre 213 de 213 pasadas hasta el 2026-11-09 (`05_...txt`). Reservas: 401, 402 |
| 14 | 2026-11-03 10:23, S173, l. 1359 | «nadie consume el producto»: el aviso a consumidores se da por cumplido | **SOSTENIDA** como dicho del dueño | No lo puedo comprobar. Ver «Una premisa que choca» en la sección 1 |
| 15 | 2026-11-03 02:26, S173, l. 1399 a 1406 | #937 (ablación de MODIS en Actions): «merge pendiente de frase» | **SIN RESPALDO en la bitácora** | Está en `main` (`f4ec1061d`, autor NMendoza, 2026-11-03 06:15 UTC). Ninguna entrada registra el merge ni la frase (hallazgo 414) |
| 16 | 2026-11-05, S173, l. 1226 | «Sí, merge #944»: la regla de cirrus del tablero exenta los records de la vía | No evaluada | Es del tablero. No lo abrí |
| 17 | 2026-11-05 20:23, S174, l. 1175 | «Sí, a todo», decisión 3: una pasada en que la vía no corre se trata como K, con aviso | **SOSTENIDA** y aplicada (#959) | Mutaciones M6 y M12. Desde el encendido: 0 caídas a K |
| 18 | 2026-11-08 15:24, S175, l. 847 | «Sí, merge de los tres»: #959, #957 y #956 | **SOSTENIDA** | Cierran en `main` los pendientes 151, 152, 153, 154, 251, 252, 253 y V1-01, V1-02 de la auditoría S175 (sección 7) |
| 19 | 2026-11-10 00:34, S177, l. 695 a 699 y l. 704 a 707 | #971: un volcán sin archivo de guardia ya no vacía la guardia de los demás | **SOSTENIDA**, sólo leída | `scripts/vigilancia_guardia_modis.py` l. 456 a 468. No la probé con mutación |
| 20 | 2026-11-10 08:51, S178, l. 629 | Lectura de la retrospectiva: MODIS fila 4, DECIDE NICOLÁS | **SOSTENIDA CON RESERVAS** | El veredicto sigue la tabla sellada y coincide con lo que el pre-registro predijo. Reservas: 406 y 407 |
| 21 | 2026-11-10 10:20 y 17:05, S178, l. 592 y 575 | «quita los 3»: salen los avisos de texto del tablero, entre ellos el de la vía de MODIS | No evaluada | Es del tablero |
| 22 | 2026-11-10, S178, l. 603 | Plan de reemplazo de la historia (#981), parte MODIS | Plan abierto | Hallazgo 405 y sección 9 |

Fuera de mi eje, con una línea cada una, en SEGUIMIENTOS: las decisiones de VIIRS 375 y 750, la sombra de los 34, el token y `fetch.py`, la prueba ciega de Codex, el visualizador.

## 4. Hallazgos

Ordenados por gravedad. La columna «eje» del CSV dice de qué tipo es cada uno.

### 401

- **TÍTULO**: El plazo de la reversión pre-autorizada de MODIS se agota hacia el 20 de noviembre y sólo con alertas de Chillán.
- **SCRIPT:SALIDA**: `03_proyeccion_plazo.py` : `03_proyeccion_plazo.txt`; `02_vigilancia_en_la_base.py` : `02_vigilancia_en_la_base.txt`. Código: `scripts/vigilancia_guardia_modis.py` l. 226 a 237 y l. 520 a 521 (`438a60a1e`).
- **QUÉ PASA**: Chillán está en erupción y MIROVA le publica entre 1 y 3 alertas MODIS fuertes por noche. La regla deja revertir sin preguntar sólo durante las primeras 29 alertas protegidas con record de la guardia. En 7 noches ya van 11, las 11 de Chillán (6,4 a 25,8 MW). Al ritmo medido, la número 29 llega entre el 17 y el 20 de noviembre (día 15 a 18), no «cerca del día 109». Desde ahí el script pasa a `plazo_cumplido` y una alerta callada sale como `CANDIDATA_FUERA_DE_PLAZO`: decide Nicolás. El script no abre ningún issue cuando el plazo se cumple.
- Además, la potencia que la regla le atribuye al plazo (l. 308, TEXTO: «con 29, una pérdida de una de cada diez se ve con 95 %») vale para alertas como las de Chillán. El caso que la regla declara como el peor, la señal débil o de borde, no tuvo ni un caso: 0 alertas Muy Bajo y 0 alertas en los otros 10 volcanes.
- Cita: `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` l. 313 (`438a60a1e`), TEXTO: «a ese ritmo las 29 llegan cerca del día 109».
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\a\02_vigilancia_en_la_base.py"` y después `python ...\03_proyeccion_plazo.py`. Volcán: Nevados de Chillán. Pasadas: 2026-11-04 08:45 a 2026-11-09 08:40 UTC.
- **CONFIANZA**: CONFIRMADO el conteo (11 de 29, las 11 de Chillán). La fecha es una proyección lineal mía: SOSPECHA.
- **GRAVEDAD 1-5**: 3. Desde fines de noviembre la red de seguridad del encendido deja de actuar sola, antes de haber visto el caso para el que se diseñó.

### 402

- **TÍTULO**: La vigilancia de la guardia da VERDE cuando la vía pierde una alerta protegida que K tampoco publica, o que la guardia no miró.
- **SCRIPT:SALIDA**: `04_mutaciones_vigilancia.py` : `04_mutaciones_vigilancia.txt` (casos M1, M2, M3, M7, M8, M10); `09_audit_semanal_con_mutaciones.py` : `09_audit_semanal_con_mutaciones.txt` (A1, A10). Código: `scripts/vigilancia_guardia_modis.py` l. 239 a 249 y l. 317 a 319.
- **QUÉ PASA**: El detector K ve menos que MIROVA cuando el satélite mira de lado: de las 11 alertas de Chillán desde el encendido, K publicó 8 y calló 3 (9,2, 6,4 y 7,2 MW). La regla sólo dispara si K publica y la vía calla. Si la vía callara una de esas 3, la vigilancia diría VERDE, sin aviso ni issue (M1, M7). Lo mismo si la vía no deja record de la pasada y K no publica (M10: es la pasada real de Chillán del 2026-11-09 02:35 UTC, cenit 64,5°, a medio grado de las que la vía descarta), y si la guardia no tiene record de esa noche (M2, M3, M8), hasta que pasan más de 3 días.
- El JSON guarda la lista `protegidas_sin_publicar_produccion` (l. 538), pero ni la salida ni el issue la muestran.
- El respaldo es el audit semanal. Lo probé con las mismas alteraciones: si la vía calla da flag (A1); si falta el record da sólo aviso de cobertura, veredicto DEGRADADO (A10). Corre los lunes y el cron llegó 10 horas tarde las dos últimas veces (19:15 y 19:35 UTC).
- **CÓMO SE VE EN EL DASHBOARD**: el operador vería una noche de Chillán sin punto MODIS en esa pasada, o sin la pasada. Nada le dice que MIROVA sí alertó.
- **CÓMO REPRODUCIRLO**: `python ...\04_mutaciones_vigilancia.py` y `python ...\09_audit_semanal_con_mutaciones.py`. Volcán: Nevados de Chillán. Pasadas: 2026-11-07 07:25 UTC (M1, A1) y 2026-11-09 02:35 UTC (M10, A10).
- **CONFIANZA**: CONFIRMADO (alteraciones en memoria sobre los datos reales; el control positivo C1 dispara REVERSION_CANDIDATA).
- **GRAVEDAD 1-5**: 3. Es el hueco de diseño de la regla, no un error del script. Lo nuevo es su tamaño: 3 de 11 (27 %) en la primera semana. La mini auditoría S172 ya conocía la parte de la guardia sin record (MA172-203).

### 403

- **TÍTULO**: La reversión por `git revert` del PR B ya choca: 6 archivos hoy y 11 después de encender VIIRS.
- **SCRIPT:SALIDA**: `10_revert_simulado.sh` : `10_revert_simulado.txt`.
- **QUÉ PASA**: Si la vía callara una alerta y hubiera que volver a K el mismo día, la sesión tendría que resolver conflictos a mano. Simulé `git revert -m 1 499935c37` sin tocar el checkout. Sobre `438a60a1e` choca en `CLAUDE.md`, la ficha, `docs/MIROVA_DIVERGENCES.md`, `docs/MISSION.md`, la regla misma y `tests/test_guard_modis_codigo_mirova_encendido_s172.py`. Sobre la rama de #974 y sobre la de #983 choca en 11: se suman 5 archivos de pruebas. En los tres casos el flag del perfil y `nrt.yml` se revierten limpios.
- La regla lo previó (§4.3, l. 236, TEXTO: «a mano, sin esperar a nadie»). Lo que no hay es un ensayo desde el 2026-11-02, y cada merge de VIIRS lo agranda. La ficha pública (`docs/FICHA_SDA_VRP_CHILE.md` l. 53, TEXTO) dice: «se revierte el cambio el mismo día».
- **CÓMO SE VE EN EL DASHBOARD**: invisible mientras no haga falta. Si hace falta, cada hora de demora es una hora más de MODIS con la vía en el tablero.
- **CÓMO REPRODUCIRLO**: `bash ...\10_revert_simulado.sh`. No depende de volcán ni de pasada.
- **CONFIANZA**: CONFIRMADO (control: el revert sobre el propio merge sale limpio, salida 0).
- **GRAVEDAD 1-5**: 3.

### 404

- **TÍTULO**: Las dos pasadas MODIS que la vía descartó por borde sí están en la tabla de MIROVA, y el log no dice por qué se descartaron.
- **SCRIPT:SALIDA**: `07_descarte_de_borde.py` : `07_descarte_de_borde.txt`; `08_alertas_modis_por_cenit.py` : `08_alertas_modis_por_cenit.txt`. Código: `pipeline/mirova_v750_codigo.py` l. 802 a 808; `scripts/run_pipeline.py` l. 414 a 427.
- **QUÉ PASA**: Cuando el volcán queda en el borde de la franja que barre el satélite, la vía no deja record si ve menos de 100 píxeles a 45 km o si el píxel más cercano al centro está a más de 5 km. Pasó 2 veces en 9 noches: Villarrica 2026-11-04 07:10 (Aqua, cenit 65,0°) y Chaitén 2026-11-09 00:55 (Terra, cenit 65,3°). MIROVA lista las dos como RUTINA con 0 MW: MIROVA sí miró. La vía sí publicó una protegida de Chillán a cenit 64,5° (2026-11-09 02:35, 7,2 MW).
- Puede ser que el cráter quedara fuera del gránulo y el descarte sea correcto, o que la regla de cobertura sea más estricta que la de MIROVA. No lo sé: el log (`scripts/run_pipeline.py` l. 424 a 425, TEXTO) dice «descarte de borde de la vía, 171-01, o volcán fuera del gránulo», sin distinguir.
- Tamaño: de 135 pasadas MODIS con alerta de MIROVA entre febrero y noviembre de 2026, 1 tiene cenit de 64,5° o más y 5 tienen 60° o más.
- **CÓMO SE VE EN EL DASHBOARD**: esa pasada no aparece. MIROVA la muestra con 0.
- **CÓMO REPRODUCIRLO**: `python ...\07_descarte_de_borde.py` y `python ...\08_alertas_modis_por_cenit.py`.
- **CONFIANZA**: CONFIRMADO que MIROVA lista las dos pasadas y que la vía no dejó record. SOSPECHA sobre la causa.
- **GRAVEDAD 1-5**: 2. Hasta hoy no se perdió ninguna alerta por esto.

### 405

- **TÍTULO**: El reemplazo de la historia (#981) dejaría la vigilancia de la guardia en «ciega» todos los días, y el plan no lo dice.
- **SCRIPT:SALIDA**: `04_mutaciones_vigilancia.py` : `04_mutaciones_vigilancia.txt` (caso M14). Código: `scripts/vigilancia_guardia_modis.py` l. 296 a 313 y l. 374 a 379.
- **QUÉ PASA**: La vigilancia comprueba que, antes del encendido, guardia y producción publicaban lo mismo, porque las dos eran K (hoy 167 pares, 0 distintos). Para eso busca records de producción sin la marca de la vía en los 14 días previos al encendido. Si la historia se reescribe con la vía, no queda ninguno: 0 pares. El script lo lee como «no medí», agrega un aviso y cambia VERDE por VIGILANCIA_CIEGA. El workflow abre o comenta el issue «vigilancia ciega» cada día. Una alarma permanente tapa una ceguera real.
- Busqué «nulo» y «vigilancia_guardia» en `docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md` de la rama `claude/s178-plan-reemplazo` (`62ccb8830`): no trata este efecto. Las guardias de VIIRS usan las mismas funciones.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Se vería como un issue diario.
- **CÓMO REPRODUCIRLO**: `python ...\04_mutaciones_vigilancia.py`, caso M14.
- **CONFIANZA**: CONFIRMADO para el mecanismo (alteración en memoria). Que el plan no lo trate: CONFIRMADO por búsqueda de texto, no por lectura completa del plan.
- **GRAVEDAD 1-5**: 2.

### 406

- **TÍTULO**: El «DECIDE NICOLÁS» de MODIS en la retrospectiva no está en la lista de decisiones que el bloque S179 le pide a Nicolás.
- **ARCHIVO:LÍNEA**: `D:\vrp-trabajo\temporales\s179-audit\loop\tasks\BLOQUE_ARRANQUE_S179.md` l. 19 (estado) y l. 34 a 45 (sección b, 8 preguntas, ninguna de MODIS); `experiments/_s178_lectura/lectura.json` de `ff8a39972`.
- **QUÉ PASA**: La lectura dio para MODIS: regla PROPONER ADOPCIÓN, ninguna protegida perdida, y sin las 4 pasadas que ya se habían mirado por nombre baja a SIN PODER. Por la tabla sellada eso es fila 4. El pre-registro dice qué hacer mientras tanto (se lee como SIN PODER y «no posterga nada»), pero la decisión es de Nicolás y pesa en con qué detector publicarían MODIS los 34 volcanes. Si nadie se la pregunta, queda como si estuviera resuelta.
- Cita: `experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md` del tag `s173-prereg-retro-sellado`, §8.2, l. 510, TEXTO: «decides con la lista; mientras tanto, como SIN PODER».
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git show origin/claude/s178-retro-lectura:experiments/_s178_lectura/lectura.json` (claves `sensores.MODIS.fila`, `motivos`, `regla_sin_pasadas_b`) y leer la sección b del bloque.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 407

- **TÍTULO**: Lo que se sabe de si la vía de MODIS pierde alertas viene de Chillán y de Láscar; en 7 de los 11 volcanes no hay ni una alerta MODIS con qué probarlo.
- **SCRIPT:SALIDA**: `16_poblacion_ab_por_volcan.txt`, `13_ab_modd_discordantes.txt`, `02_vigilancia_en_la_base.txt`, y `lectura.json` de `ff8a39972`.
- **QUÉ PASA**: MIROVA casi no alerta en MODIS fuera de los volcanes con actividad fuerte. A/B de MOD-D (marzo a octubre de 2026): 56 protegidas, 40 de Láscar, 15 de Chillán y 1 de Villarrica. Retrospectiva de febrero de 2026: 9 de 9 de Láscar. OSF de 2025: 155 de Láscar y 6 de Planchón-Peteroa. Desde el encendido: 11 de 11 de Chillán. En Chaitén, Copahue, Isluga, Lastarria, Llaima, Cordón Caulle y Tupungatito no hay ninguna alerta MODIS en ninguna de esas ventanas. Ahí sólo está medido que la vía calla donde MIROVA calla (0 publicaciones en 561 negativos limpios de febrero; K, 5).
- No es un defecto de la vía. Es el alcance de la evidencia, y la bitácora y la ficha lo dicen sin esa lista.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python ...\13_ab_modd_discordantes.py`; `16_poblacion_ab_por_volcan.txt` muestra el conteo por volcán.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 408

- **TÍTULO**: La ficha pública dice que, si falta la geolocalización de una pasada MODIS, se procesa con el método anterior; el NRT la salta sin dejar record.
- **ARCHIVO:LÍNEA**: `docs/FICHA_SDA_VRP_CHILE.md` l. 25 (`438a60a1e`, v1.22) contra `scripts/run_pipeline.py` l. 248 a 250 y `pipeline/process_modis.py` l. 644 a 645.
- **QUÉ PASA**: Si NASA entrega la imagen (MOD021KM) y no su archivo de posiciones (MOD03), `run_pipeline.py` anota la falta y sigue con el gránulo siguiente: nunca llama al procesador. La rama `sin_mxd03` del procesador, que escribiría K con aviso, no se alcanza desde el NRT. La pasada queda sin record hasta que llegue el MOD03 en una corrida posterior. La auditoría S175 ya había visto que esa rama es inalcanzable (V1-03); la frase de la ficha sigue igual.
- Cita: `docs/FICHA_SDA_VRP_CHILE.md` l. 25, TEXTO: «Si en una pasada eso no se puede hacer (el volcán sin grilla de MIROVA o el producto de geolocalización ausente o de otra forma), esa pasada se procesa con el método anterior y el registro lo dice.»
- **CÓMO SE VE EN EL DASHBOARD**: la pasada no aparece hasta que llega la geolocalización.
- **CÓMO REPRODUCIRLO**: leer `D:\vrp-trabajo\temporales\s179-audit\main\scripts\run_pipeline.py` l. 236 a 285. No lo ejecuté.
- **CONFIANZA**: CONFIRMADO por lectura. Cuántas veces pasa: SIN DATO.
- **GRAVEDAD 1-5**: 2. Es la ficha de transparencia (Resolución CPLT N°372).

### 409

- **TÍTULO**: 59 de 105 perfiles corren hoy la vía en MODIS sin decirlo, entre ellos 9 con «K» en el nombre y el del A/B diurno pendiente.
- **SCRIPT:SALIDA**: `11_censo_perfiles_via_modis.py` : `11_censo_perfiles_via_modis.txt`.
- **QUÉ PASA**: Los perfiles de experimentos heredan de producción. Desde el encendido, quien vuelva a correr uno de ellos corre MODIS con la vía aunque el nombre diga K: `_s154_reproc_k_historico`, `_s154_ab_diurno_k_control`, `_s154_ab_diurno_k_on`, `_s150_k_etiqueta`, `_s150_k_etiqueta_sin_tope` y los cuatro `_s157_ab_d25_k_*`. `reproc-s151-ab-diurno.yml` nombra `_s151_ab_diurno_control`, que también la hereda. La mini auditoría S172 lo dejó escrito (MA172-104, MA172-303) y sigue igual. Con #974 y #983 heredarán también las vías de VIIRS.
- Dos lugares donde importa: el «día después» de una reversión, que pide reponer records «con K» sin nombrar el perfil (el único K seguro de MODIS es `guardia_k_modis`), y una nueva corrida del A/B diurno (#813).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python ...\11_censo_perfiles_via_modis.py`.
- **CONFIANZA**: CONFIRMADO (control: producción `True`, `guardia_k_modis` `False`).
- **GRAVEDAD 1-5**: 2.

### 410

- **TÍTULO**: El único control de que MODIS sigue vivo volcán por volcán está dentro de la vigilancia de la guardia.
- **ARCHIVO:LÍNEA**: `scripts/vigilancia_guardia_modis.py` l. 354 a 355 (lo ve; mutación M11); `scripts/auto_audit_weekly.py` l. 346 a 361 (cobertura con cualquier record de cualquier volcán y sensor); `scripts/vigilar_plataformas.py` l. 8 a 11 (suma los 11 volcanes).
- **QUÉ PASA**: Si la vía dejara de escribir MODIS en un solo volcán, por ejemplo porque descarta todas sus pasadas, y VIIRS siguiera vivo ahí, el audit semanal y el vigilante de plataformas no lo verían. La vigilancia de la guardia sí, a los 4 días (M11). Si la vía cae a K en un volcán, también (M12). Si un día se apaga la guardia, ese control se va con ella. El bloque S178 lo tenía como SOSPECHA (`tasks/BLOQUE_ARRANQUE_S178.md` l. 68, TEXTO: «Auto-audit verde con sólo Láscar MODIS vivo 60 días»).
- **CÓMO SE VE EN EL DASHBOARD**: un volcán sin puntos MODIS, igual que un volcán tranquilo.
- **CÓMO REPRODUCIRLO**: `python ...\04_mutaciones_vigilancia.py`, casos M11 y M12; leer las líneas citadas.
- **CONFIANZA**: CONFIRMADO para la guardia (mutación). El audit y el vigilante de plataformas los leí, no los probé con datos alterados.
- **GRAVEDAD 1-5**: 2.

### 411

- **TÍTULO**: La vía publicó 1 vez donde MIROVA dio 0 en 8 noches; a ese ritmo la cota de 3 se cruza en un mes.
- **SCRIPT:SALIDA**: `02_vigilancia_en_la_base.txt` (sobre-publicación 1 de 152).
- **QUÉ PASA**: Láscar tiene una anomalía débil permanente en el cráter. El 2026-11-08 08:00 UTC (Aqua, cenit 10,9°) la vía marcó 1 píxel a 0,26 km del cráter, 0,246 MW, pasando el umbral por 1 % (`diag_codigo_mirova.celda_decisiva.margen` 1,0107). MIROVA lista esa pasada con 0. K no publicó. En el A/B fueron 3 de 5.321 en 240 días. Con esa tasa, ver 1 o más en 152 tiene probabilidad de 8 %.
- **CÓMO SE VE EN EL DASHBOARD**: un punto MODIS de 0,25 MW en Láscar esa noche; MIROVA no tiene alerta.
- **CÓMO REPRODUCIRLO**: `python ...\02_vigilancia_en_la_base.py`; el record está en `data/mirova_equivalent/Lascar.json` de `438a60a1e`, `MODIS_AQUA`, `2026-11-08 08:00`.
- **CONFIANZA**: CONFIRMADO el caso. Que sea una tendencia: SOSPECHA (un solo caso).
- **GRAVEDAD 1-5**: 1.

### 412

- **TÍTULO**: La regla sellada no registra los cambios que S175 le hizo a su instrumento.
- **ARCHIVO:LÍNEA**: `experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md` (`438a60a1e`): el único cambio contra el tag `s173-regla-modd-sellada` es la marca del hallazgo 154 (l. 8). `scripts/vigilancia_guardia_modis.py` l. 47 a 60 describe los cambios de #959.
- **QUÉ PASA**: Desde #959 la reversión exige que el record de producción sea de la vía, el plazo y las cotas cuentan sólo pasadas de la vía, y una caída a K es aviso. Son mejoras aprobadas por Nicolás. La regla, que manda anotar toda corrección como marca A113, no las nombra. Quien lea sólo la regla no sabe que el instrumento ya no hace exactamente lo sellado.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git diff s173-regla-modd-sellada 438a60a1e -- experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

### 413

- **TÍTULO**: `docs/MISSION.md` y la ficha citan como tag defensivo del encendido uno que está 58 commits antes del `main` previo al merge.
- **ARCHIVO:LÍNEA**: `docs/MISSION.md` l. 26 y `docs/FICHA_SDA_VRP_CHILE.md` (1 mención), en `438a60a1e`.
- **QUÉ PASA**: Citan `pre-s171-adopcion-modd` (`d3cd0b2ae`). El `main` justo antes del merge de #934 es `438a010ab`, que lleva el tag `pre-s173-adopcion-modd` (bitácora l. 1413). Entre los dos están el PR A (#933), #932 y #935. La regla manda revertir con `git revert`, no volver al tag, así que el daño es de documento.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git rev-parse pre-s171-adopcion-modd^{commit} pre-s173-adopcion-modd^{commit} 499935c37^1` y `git log --oneline pre-s171-adopcion-modd..499935c37^1 | wc -l`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

### 414

- **TÍTULO**: #937 (ablación de MODIS en Actions) está en `main` sin que la bitácora registre el merge ni la frase.
- **ARCHIVO:LÍNEA**: bitácora l. 1399 a 1406 («merge pendiente de frase»); commit `f4ec1061d` (autor NMendoza, 2026-11-03 06:15 UTC).
- **QUÉ PASA**: Lo mergeó la cuenta de Nicolás desde GitHub. El PR sólo agrega un workflow y un experimento, no toca producción. Falta la entrada.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git log -1 --format='%h %ci %an %s' f4ec1061d` y `grep -n "#937" tasks/LOOP_OBJETIVOS.md`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

### 415

- **TÍTULO**: 16 archivos de `main` citan `docs/AUDIT_S175.md`, que no existe en `main`.
- **ARCHIVO:LÍNEA**: entre otros `scripts/vigilancia_guardia_modis.py` l. 47, `scripts/auto_audit_weekly.py`, `scripts/run_pipeline.py` l. 415, la regla (l. 8), `docs/MISSION.md` l. 7, la ficha.
- **QUÉ PASA**: El documento vive sólo en el PR #955, que sigue en borrador. Las citas no resuelven.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git ls-tree --name-only 438a60a1e docs/ | grep -c AUDIT_S175` (da 0) y `grep -rl AUDIT_S175` sobre `scripts`, `pipeline`, `docs`, `tests` y `CLAUDE.md` de la copia de `main`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1. Se cierra con el merge de #955.

### 416

- **TÍTULO**: Queda un record MODIS de K, en producto NRT, dentro del tramo de la vía: Planchón-Peteroa 2026-11-02 01:15 UTC.
- **SCRIPT:SALIDA**: `05_cobertura_guardia_y_censo_via.py` : `05_cobertura_guardia_y_censo_via.txt`.
- **QUÉ PASA**: De las 23 pasadas de las 01:15 a 07:30 UTC del 2 de noviembre, 22 se reemplazaron por su producto estándar con la vía. Esta no, y ya salió de la ventana de 8 días del NRT: no se va a actualizar sola. El audit la cuenta como «K en noche VIA_MODIS: 1». La auditoría S175 la anotó (VX-04) y sigue igual.
- **CÓMO SE VE EN EL DASHBOARD**: un punto MODIS calculado con K en una noche de la vía. Sin alerta de MIROVA en esa pasada.
- **CÓMO REPRODUCIRLO**: `python ...\05_cobertura_guardia_y_censo_via.py`.
- **CONFIANZA**: CONFIRMADO. Por qué no llegó su producto estándar: SIN DATO.
- **GRAVEDAD 1-5**: 1.

## 5. PROPUESTAS PARA LOS PLANES

No implementé ninguna. Cada una va atada a un hallazgo o a una medición.

1. **Antes del 17 de noviembre, decidir qué pasa cuando MODIS llegue a 29** (401). Opciones para Nicolás, por marca A113 con su frase: mantener la pre-autorización hasta los 120 días aunque se cumplan las 29; contar como máximo un número fijo de protegidas por volcán; o aceptar que desde ahí decide él. Y que la vigilancia abra un issue el día que el plazo se cumpla.
2. **Antes de encender VIIRS, mirar lo mismo en su regla** (medición `15_ritmo_protegidas_por_sensor.txt`). La vigilancia de VIIRS usa las mismas funciones y el mismo objetivo de 29. Del 3 al 9 de noviembre MIROVA publicó 19 protegidas nocturnas en VIIRS 375 y 18 en VIIRS 750, 17 y 15 de Chillán: las 29 se juntan en unas 11 noches. Es del frente B; va también en SEGUIMIENTOS.
3. **Que la vigilancia informe toda protegida que producción no publica o no tiene, publique o no la guardia** (402). Como INVESTIGAR, no como reversión: no cambia el disparador sellado. Hoy esa lista ya está en el JSON (`protegidas_sin_publicar_produccion`); falta mostrarla y sumar las que no tienen record.
4. **Ensayar la reversión y dejar escrito el camino corto** (403). Antes de mergear #974: correr `10_revert_simulado.sh` sobre la rama que va a entrar, y anotar en la regla, por marca A113, que el camino rápido es un commit que deja `enable_modis_codigo_mirova: false` más la comprobación de `pipeline.profile`, con la lista de pruebas que quedarán rojas. Repetir después de cada merge que toque los archivos de B.
5. **Saber por qué la vía descarta una pasada** (404). Que el log diga cuál de los dos cortes actuó y a qué distancia quedó el píxel más cercano (toca `pipeline/`, A45). Mientras tanto, medir en Actions con el MOD03 las dos pasadas del hallazgo. Y agregar a la vigilancia el conteo de pasadas que MIROVA lista y producción no tiene.
6. **Corregir #981 antes de aplicarlo** (405, 416, 404). (a) Decir qué pasa con el nulo de las guardias: guardar su resultado al encender, o dejar que el aviso no cuente cuando la historia ya es de la vía. (b) Decir qué se hace con el record K de Planchón-Peteroa del 2026-11-02 01:15. (c) Antes de apartar las 217 pasadas MODIS de K sin par en la vía, cruzarlas con la tabla de MIROVA. Mi medición por cenit dice que antes del encendido ninguna pasada MODIS de cenit 64,5° o más tuvo alerta en 2026 (`08_alertas_modis_por_cenit.txt`), pero el cruce correcto es con esa lista de 217, que no abrí.
7. **Poner el «DECIDE NICOLÁS» de MODIS en la cola de decisiones** (406), con su alcance: en alertas la retrospectiva habla sólo de Láscar; en silencio, de los 11.
8. **Escribir el alcance por volcán junto a cada afirmación de paridad de MODIS** (407): ficha, `docs/MISSION.md` y la Compuerta B de los 34. Y al decir «3 noches verdes» de una guardia, decir cuántas alertas y de qué volcanes hubo en esas noches.
9. **Corregir la frase de la ficha** (408) en la próxima versión: sin geolocalización la pasada queda sin registro hasta que el producto llegue.
10. **Nombrar el perfil K en el «día después»** (409): `guardia_k_modis`. Y antes de volver a correr un A/B con perfiles heredados, declarar en cada uno el valor de los tres flags de vía.
11. **Antes de apagar cualquier guardia, pasar el control de frescura por volcán y sensor al healthcheck del NRT** (410).

## 6. VERIFICADO LIMPIO

Cada línea dice contra qué vara se verificó y con qué comando.

- **El código de la vía de MODIS que corre es el aprobado.** Vara: el merge de #934. `git diff --stat 499935c37 438a60a1e -- pipeline/ scripts/run_pipeline.py`: cambian `fetch.py` (#966, token), `grillas_mirova.yaml` (sólo `roi_v750` de dos volcanes), tres perfiles nuevos y dos avisos de log. `mirova_v750_codigo.py`, `process_modis.py` y `mirova_equivalent.yaml` no cambian.
- **Los flags efectivos son los aprobados.** Vara: `pipeline.profile` (A89), no el YAML. Producción `True`; `guardia_k_modis`, `experimental`, `experimental_ndc_focus` y `guardia_k_viirs` `False`; las sombras `True`. Las vías de VIIRS de producción, `False`. (`11_censo_perfiles_via_modis.py`.)
- **El merge y el sello son los que dice la bitácora.** `git log -1 --format='%H %P' 499935c37`: dos padres. Tag `s173-regla-modd-sellada` en `33dac1eca`. La regla de `main` difiere del sello sólo en la marca del 154.
- **La vía escribe y no cae a K.** Vara: los records de `438a60a1e`. 212 records MODIS con `via_codigo_mirova: true` desde el 2026-11-02, en los 11 volcanes; 0 con marca de caída; 0 records sin la vía escritos después del encendido; 0 records de la vía anteriores al 2026-11-02. (`05_...py`.)
- **La guardia corre y es K.** 213 de 213 pasadas MODIS de producción del 2 al 9 de noviembre tienen record de la guardia; 0 records de la guardia con marca de la vía. La falla del 2026-11-08 quedó reparada por la corrida siguiente. Nulo: 167 pares, 0 distintos. (`05_...py`, `02_...py`.)
- **La vigilancia reproduce lo que publicó.** Vara: `data/audit_continuous/guardia_modis_latest.json` del commit. Mi corrida da VERDE, 11 de 29, nulo 167 y 0, sobre-publicación 1 de 152, borde 2. Difiere en `n_pasadas_alerta` (25 contra 26): la referencia del repo cambió entre las 04:19 y las 17:00 UTC; no lo perseguí.
- **La vigilancia sí ve lo que promete en estos casos** (`04_...py`): protegida que K publica y la vía calla (C1, REVERSION_CANDIDATA); sin record de producción y K publica (M4, INVESTIGAR); fuera de plazo (M5); caída a K que calla (M6, INVESTIGAR, no reversión); guardia muerta más de 3 días (M9); MODIS muerto en un volcán (M11); la vía caída a K en un volcán (M12); referencia de MIROVA sin MODIS (M13).
- **El audit semanal separa la vía y avisa lo que no juzga.** Vara: `data/audit_continuous/latest.json` del 2026-11-09 19:50 UTC en el commit. `VIA_MODIS` desde el 2026-11-02; recall 100 % en 7 noches y 13 pasadas, «sin juzgar» hasta 15 noches, con aviso; magnitud de Chillán 1,035 con la vía contra 0,485 con K; publicaciones en negativos limpios 1 de 171 (0,6 %) contra 15 de 1.112 (1,3 %) con K. Con una protegida callada da flag (`09_...py`, A1). El audit del 2026-11-02 corrió a las 19:15 UTC, antes del primer record de la vía (20:11): juzgó K, como dice la bitácora.
- **Ninguna alerta MODIS de MIROVA sin record nuestro.** Vara: tabla y OCR del repo, pareo a ±120 s. Febrero: 0 de 14. Del 2026-02-01 al 2026-10-16: 0 de 106. Desde el encendido: 0 de 13. (`06_...py`.)
- **El A/B que sostuvo la adopción dice lo que la bitácora dice.** `resultado_f4.json` tiene el sha256 que cita la regla (`312e2050c680...4129d`) y `poblacion_f4.json` también (`e8315ba4ff93...3be8`). PROPONER ADOPCIÓN, 14 de 14 controles en OK, P1 sin pérdida, P2 GANA (neto -44, B 53), M MEJORA (n 83). Discordantes: 2 Muy Bajo y 3 negativos limpios en contra de la vía, sobre 43 y 5.321. (`13_...py`, `16_...txt`.)
- **La lectura de la retrospectiva es coherente con su regla en MODIS.** `lectura.json`: 601 pasadas, 593 evaluables, 9 protegidas y 5 Muy Bajo, todas de Láscar; la vía 9 de 9 y 5 de 5, K 8 de 9 y 3 de 5; negativos limpios publicados: la vía 0 de 561, K 5; los controles en OK; sin las pasadas ya miradas, fila 5; con la tabla sellada, fila 4. Contra el OSF de 2025: 160 de 161 publicadas y 1 sin record. Es lo que el §0 y el §7 del pre-registro predijeron. No la volví a correr.
- **El paso que deja rojo el NRT si la vía lanza una excepción existe y no ha disparado en lo que miré.** `nrt.yml` l. 382 a 384. En 4 de las 8 corridas rojas desde el encendido el paso que falla es el del pipeline, no ese; en el log que leí: «gránulos MODIS con ERROR processing: 0». (`14_...py`.)
- **Pendientes de la auditoría S175 de mi eje que ya están cerrados en `main`**: sección 7.

## 7. Pendientes de `docs/AUDIT_S175.md` (§6, §8 y §11.6) que caen en mi eje

| id | qué | estado en `438a60a1e` |
|---|---|---|
| 151, V1-01 | la vigilancia no miraba si el record de producción era de la vía | CERRADO (#959). Probado: M6 |
| 152 | vigilante ciego por volcán | CERRADO (#959). Probado: M11, M12 |
| 153 | el descarte de borde sin rastro | CERRADO EN PARTE: el log lo avisa y el JSON lo nombra pasada por pasada. Sigue sin decir la causa (404) |
| 154, V1-02 | la regla y la ficha suponían que el NRT re-escribe 8 días | CERRADO (#956): marca en la regla, ficha v1.19 |
| 253, decisión 4 | caídas a K como K con aviso | CERRADO (#959) |
| 251, 252, decisión 2 | `SINTOMAS.md` describía MODIS como K | CERRADO (#956): marcas en l. 13, 130 y 199 |
| 161, V33A-01, decisión 19 | el mapa con «Todos los pixels» | En `main` (#965, `7e0cc55da`). No lo probé |
| V1-04 | un volcán sin archivo de guardia cegaba a los once | CERRADO (#971). Sólo leído |
| V1-03 | la caída `sin_mxd03` es inalcanzable desde el NRT | ABIERTO, y la ficha dice lo contrario (408) |
| VX-04 | record de Planchón-Peteroa en K | ABIERTO (416) |
| VX-05 | ningún record MODIS guarda qué geolocalización usó | No lo miré. Los records de la vía traen `diag_codigo_mirova`, sin un campo de geolocalización a la vista |
| 115 | bandas de recall calibradas sobre el detector viejo | ABIERTO: `RECALL_MIN` de MODIS sigue en 95,0 (`scripts/auto_audit_weekly.py` l. 121). Con la vía en 100 % no molesta hoy |
| 156, 157 | el audit no da flag de recall hasta 15 noches | Por diseño, con aviso. La vía llevaba 7 noches el 2026-11-09; al ritmo de Chillán llega a 15 hacia el 2026-11-17 |
| 158 | el encendido cuelga del primer record | Sin cambio. Ojo con #981: los records reemplazados traerán `processed_utc` posterior, así que el encendido no se mueve |
| 109 | 49 pasadas MODIS nocturnas que MIROVA lista y no tenemos | No lo medí |
| 111, decisión 18 | fracción MODIS NRT en el audit semanal | No encontré ese campo en `auto_audit_weekly.py`. Medido aparte: desde el 2 de noviembre, todo estándar salvo el día en curso y el record de 416 |
| §10, §11.6 | anexo del audit del 2026-11-09 | Escrito en la rama de #955; #955 sigue en borrador (415) |

## 8. SEGUIMIENTOS (visto fuera de mi eje, sin perseguir)

- **Frente B, VIIRS.** El plazo de 29 protegidas se juntaría en unas 11 noches en cada VIIRS, casi todo Chillán. `15_ritmo_protegidas_por_sensor.py`. CONFIRMADO el ritmo de MIROVA; SOSPECHA la duración, porque el plazo cuenta las que tienen record de la guardia.
- **Frente B.** El revert de #934 choca en 5 archivos de pruebas más cuando entran #974 o #983 (`10_revert_simulado.txt`). El mismo ensayo falta para revertir #974 y #983. CONFIRMADO lo primero.
- **Frente C, instrumento de la retrospectiva.** El campo `alertas_de_la_tabla_sin_pasada_nuestra` de `lectura.json` da «Lascar|MODIS: 52». Su ventana va del 2026-02-01 al 2026-10-16 y cuenta los meses entre tramos, donde la retrospectiva no tiene pasadas (`leer_retro.py` l. 344 a 355 de `ff8a39972`). Contra producción, en esa misma ventana, son 0 de 106 (`06_alertas_modis_sin_record.txt`). No sirve como medida de cobertura. CONFIRMADO.
- **Frente D, el día.** De las 16 pasadas MODIS con alerta de MIROVA desde el encendido, 5 son diurnas (12:15, 13:15, 20:40, 21:05 y 21:40 UTC; 2,8 a 24,0 MW, todas de Chillán). El sistema no procesa MODIS de día: no hay record, ni guardia, ni audit. Es por diseño (issue #813 abierto). CONFIRMADO el conteo.
- **NRT.** 8 corridas rojas del 3 al 5 de noviembre. En la que leí (42016780200, Copahue, 2026-11-05 11:10 UTC) todas las descargas dieron `FileExistsError` en los `partial_*` de earthaccess, 107 veces, y el paso llegó al tope de 50 minutos. La bitácora del 2026-11-03 23:18 decía «En el NRT, 0 casos». CONFIRMADO para esa corrida; las otras 7, SOSPECHA.
- **Avisos.** La guardia de MODIS corre con cron 17:40 UTC y arrancó entre las 21:05 y las 00:51 UTC en sus 8 corridas programadas (`D:\vrp-trabajo\temporales\s179-audit\insumos\runs_guardia-k-modis.json`). Una alerta de las 02:00 UTC llega al issue unas 19 a 23 horas después. La regla pide actuar «el mismo día UTC del issue» y alguien tiene que leerlo: la auditoría S175 (383) dice que el repositorio tiene 0 suscriptores. No lo volví a medir.
- **Protegida, dos definiciones.** La vigilancia de la guardia cuenta como protegida una fila sólo del OCR de 1 MW o más. El audit semanal la descarta si la tabla tiene esa pasada sin alerta (`tabla_sobre_ocr`). Desde el encendido no cambia nada: las 11 están en la tabla. Leído, no probado.
- **Ficha.** La fila v1.18 lleva fecha 2026-11-01 y el cambio de método rigió desde el 2026-11-02 (el cuerpo de la ficha sí lo dice).
- **Decisiones fuera de mi eje**, una línea cada una: encendido de VIIRS 375 y 750 (B1, B2, #974, #983) y regla de reversión de VIIRS con sus cotas; ROI B4 de VIIRS 750 (#939); lector re-sellado de V375-E; sombra y vista preliminar de los 34; arreglo del token en `pipeline/fetch.py` (#966); instrumental, candado, C-K y C-montaje de la retrospectiva; visualizador «como MIROVA»; prueba ciega de Codex; `mirova-tif-archive`; CLAUDE.md corto (#949).

## 9. SIN DATO

- **Por qué la vía descartó las dos pasadas de borde** y si el cráter estaba dentro del gránulo. Hace falta el MOD03 de esos gránulos (`MYD021KM.A2026308.0710` y `MOD021KM.A2026313.0055`). No hay llamadas a NASA en esta auditoría.
- **Si la confirmación en la imagen de MIROVA (regla §4.3) se puede hacer hoy.** No abrí `mirova-tif-archive`.
- **Si alguien recibe los issues de la guardia.** No lo medí.
- **Qué causó 7 de las 8 corridas rojas del NRT.** Abrí el log de 1.
- **Por qué la pasada de Planchón-Peteroa del 2026-11-02 01:15 no recibió su producto estándar.**
- **Si el tablero dibuja bien los records de la vía** y si los avisos salieron del sitio. No abrí un navegador.
- **El poder real de la cota de Muy Bajo.** Desde el encendido no hubo ninguna alerta MODIS entre 0,05 y 1 MW.
- **Qué pasa con la vía de MODIS en los 34 volcanes.**

## 10. FUERA DE ALCANCE

- Arreglar cualquiera de los hallazgos.
- VIIRS 375 y 750, salvo las dos mediciones que pasé a SEGUIMIENTOS.
- La física de la vía (si el código de MIROVA para VIIRS 750 llevado a MODIS es el que MIROVA usa en MODIS). No lo audité: lo que medí es su resultado contra lo que MIROVA publica.
- El día.
- El reemplazo de la historia más allá de su efecto sobre la guardia y sobre MODIS.

## 11. Archivos de esta auditoría

Todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\a\`.

| archivo | qué es |
|---|---|
| `INFORME.md` | este informe |
| `hallazgos.csv` | una fila por hallazgo |
| `01_inventario_entradas.py` y `.txt` | inventario de la bitácora |
| `02_vigilancia_en_la_base.py`, `.txt` y `.json` | la vigilancia de la guardia re-corrida sobre `438a60a1e`, pasada por pasada |
| `03_proyeccion_plazo.py` y `.txt` | cuándo se juntan las 29 |
| `04_mutaciones_vigilancia.py` y `.txt` | qué ve y qué no ve la vigilancia (C0, C1, M1 a M14) |
| `05_cobertura_guardia_y_censo_via.py` y `.txt` | censo de records de la vía y cobertura de la guardia |
| `06_alertas_modis_sin_record.py` y `.txt` | alertas de MIROVA sin record nuestro |
| `07_descarte_de_borde.py` y `.txt` | las dos pasadas de borde contra la tabla de MIROVA |
| `08_alertas_modis_por_cenit.py` y `.txt` | alertas de MIROVA según el ángulo de vista |
| `09_audit_semanal_con_mutaciones.py` y `.txt` | qué hace el audit semanal con una pérdida |
| `10_revert_simulado.sh` y `.txt` | el revert de #934, simulado |
| `11_censo_perfiles_via_modis.py` y `.txt` | perfiles con la vía de MODIS encendida |
| `12_sombra_primer_record.py` y `.txt` | noches de sombra antes del encendido |
| `13_ab_modd_discordantes.py` y `.txt`, `16_poblacion_ab_por_volcan.py` y `.txt` | el A/B de MOD-D |
| `14_nrt_rojos_desde_el_encendido.py`, `.txt` y los `14_api_*` | corridas del NRT (API de GitHub) |
| `15_ritmo_protegidas_por_sensor.py` y `.txt` | ritmo de protegidas por sensor |
| `99_escribir_hallazgos_csv.py` | genera `hallazgos.csv` con el módulo csv |
