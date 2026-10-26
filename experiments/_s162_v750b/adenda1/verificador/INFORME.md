# Informe del verificador: adenda 1 de V750-B (la pasada «ok» sin una caja del oráculo)

- Hora del servidor al inicio (`gh api -i repos/MendozaVolcanic/VRP-chile`, header Date): **Mon, 26 Oct 2026 01:54:02 GMT**.
- Commit medido (`git log -1 --format=%H`): **e7c56af0b2d5019e350e14bd23b98c940b33a1bf**, rama `claude/s162-viirs750-2-918174`.
- Modelo: Sonnet 5.5 (`claude-sonnet-5-5`).
- sha256 de `LISTA_CAMINOS_previa.md` (escrita antes de abrir `adenda1/`, 14 caminos): `21eb962c9a298af5bf761da80d4bd8a8c64465d020bf37e879bb3f6fbb14a01f`.
- Evaluador usado: `evaluar_d25.py` del scratchpad indicado, sha256 `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747` (coincide con el fijado en `analizar_v750b.py:48`).
- Árbol: `git diff s162-v750b-sellado HEAD -- analizar_v750b.py probe_v750b.py objetivos_v750b.py` está vacío; el analizador no fue editado. El PREREGISTRO sólo recibió líneas agregadas desde `1af6c3cd8` (+44, 0 borradas). Otra sesión editaba `experiments/_s162_v750a/` mientras yo medía (A112); yo sólo toqué esta carpeta de verificador (y el medidor del autor crea y borra `_mut_*.py` en `adenda1/`, ya borrados).
- Qué NO miré: el probe real con red (ver SIN DATO), un run real (no existe aún `objetivos_v750b.json` ni `sin_granulo_v750b.json`), las métricas y la regla §6 del analizador más allá de lo que toca la cobertura, el workflow `probe-s162-v750b.yml`, el historial de la «primera corrida del nulo».

## En una pantalla

1. **Veredicto: LISTO CON CAMBIOS (menores).** La afirmación central se sostiene: el hueco existe y lo reproduje; el compañero reproduce al analizador (sin cajas faltantes) y suma las pasadas sin caja como SIN DATO con el 2 % y el freno por protegida.
2. Reproducido: prueba verde 23/23, roja sin compañero (8 FALLAS), medidor 7/7 más identidad y control de caída. Diferencial aleatorio propio: 95 poblaciones contra el analizador real (modo A) y unas 310 contra un oráculo del §4 escrito aparte, **0 discrepancias**, más el borde exacto del 2 %.
3. **Lo que cambiaría antes del 2026-11-03**: (a) el comando de lectura de la adenda no corre tal cual desde ninguna carpeta (VAD-02); (b) una caja `null` hace que el compañero diga SUFICIENTE y luego el analizador reviente (VAD-03); (c) nada obliga mecánicamente a obedecer al compañero (VAD-01).
4. El nulo del autor es más flojo de lo que dice «7 de 7»: 7 mutaciones mías no equivalentes de la parte «idéntica al analizador» sobreviven a la batería (VAD-05). Hoy el código es correcto (lo medí aparte); el riesgo es de mantenimiento, no de esta lectura.
5. Con el probe sellado el caso no ocurre (leído en el código, no ejecutado); ningún hallazgo de gravedad 4 o 5.

Ruta del informe: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174\experiments\_s162_v750b\adenda1\verificador\INFORME.md`

## Hallazgos (por gravedad)

### VAD-01 · Nada obliga a obedecer al compañero; el analizador sellado sigue emitiendo veredicto sin marca · gravedad 3 · confianza 4
- Dónde: PREREGISTRO_V750B.md, «Cómo se lee el 2026-11-03» (l. 303-313); `analizar_v750b.py:326-337` (compuerta) y `:198-200`.
- Qué pasa: la adenda dice «Sale 3 y dice INSUFICIENTE mientras el analizador dice SUFICIENTE: manda el compañero». Eso es un paso de procedimiento humano. El analizador no lee la salida del compañero: con una protegida sin caja (escenario D1) imprime `== cobertura: SUFICIENTE`, la compuerta queda ABIERTA y el veredicto sale sin la marca `[LEÍDO CON FALTANTES]` (esa marca sólo existe con `--leer-con-faltantes`). Si el lector olvida correr el compañero, o lo corre y no lo obedece, el veredicto se publica como limpio. El §9 del pre-registro (l. 193-196) tampoco incluye el compañero en el comando de lectura; la adenda sólo lo anuncia en un cartel al inicio y en su propio texto.
- Cómo se ve: `verificador/prueba_verde_salida.txt` línea D1 («D1 y cobertura SUFICIENTE con la protegida sin mirar») y `verificador/caja_none_salida.txt` (caso `ausente`: analizador `compuerta ... ABIERTA`, compañero distinto).
- Reproducir: `python experiments/_s162_v750b/adenda1/probar_adenda1.py --evaluador <evaluar_d25.py> --dest <tmp>`.
- Nota: no es un defecto del código; es la forma de la solución (compañero externo porque el analizador está sellado). Mitigación posible, sin editar el sello: que la coordinadora incluya el compañero como paso 0 escrito del comando de lectura y que, si da 3, se use `--leer-con-faltantes` con la lista en el motivo para que la marca salga en cada línea.

### VAD-02 · El comando de lectura de la adenda no corre tal cual desde ninguna carpeta · gravedad 2 · confianza 5
- Dónde: PREREGISTRO_V750B.md l. 306 (comando) y `objetivos_v750b.py:118,121` (dónde se escriben los archivos).
- Qué pasa: el comando mezcla rutas desde la raíz del repo (`experiments/_s162_v750b/adenda1/cobertura_cajas_v750b.py`, `--sin-granulo experiments/_s162_v750b/sin_granulo_v750b.json`) con una ruta relativa a la carpeta `_s162_v750b` (`--objetivos objetivos_v750b.json`, que el generador escribe en `experiments/_s162_v750b/`, y que es la convención del comando del §9 de `analizar_v750b.py`). Desde la raíz falla `FileNotFoundError: 'objetivos_v750b.json'`; desde `experiments/_s162_v750b` falla `can't open file ...\experiments\_s162_v750b\experiments\_s162_v750b\adenda1\cobertura_cajas_v750b.py`.
- Cómo se ve: la falla es ruidosa (traceback o error del intérprete), no silenciosa. Con rutas coherentes funciona: desde `experiments/_s162_v750b`, `python adenda1/cobertura_cajas_v750b.py --art ... --objetivos ... --sin-granulo ...` imprimió la cobertura sin error (probado con datos sintéticos de D1).
- Reproducir (desde la raíz del worktree): `python experiments/_s162_v750b/adenda1/cobertura_cajas_v750b.py --art x --objetivos objetivos_v750b.json --sin-granulo experiments/_s162_v750b/sin_granulo_v750b.json`.
- Cambio sugerido: rutas absolutas en el comando (la regla del usuario pide rutas completas de todos modos).

### VAD-03 · Una caja `null` hace que el compañero diga SUFICIENTE y después el analizador reviente · gravedad 2 · confianza 5
- Dónde: `cobertura_cajas_v750b.py:33-36` (`cajas_faltantes`), `analizar_v750b.py:208-209` (`set(CAJAS) <= set(oraculo)` mira llaves, no valores) y `:264` (`vrp()` hace `.get` sobre la caja), invocado desde `:358` (`metricas`).
- Qué pasa: para el analizador una pasada con la llave `B2` presente pero con valor `null` **sí está observada** (69 de 69 en mi escenario). El compañero la cuenta como «falta caja». El texto de la adenda dice «Una pasada que el compañero cuenta como "falta caja" queda fuera de las métricas igual que en el analizador», y eso es falso para este caso: queda **dentro**. Si no es protegida y está bajo el 2 %, el compañero dice SUFICIENTE (1 de 69), la lectura sigue, y el analizador revienta en la lectura completa con `AttributeError: 'NoneType' object has no attribute 'get'` (`analizar_v750b.py` l. 264, llamada desde l. 358).
- Cómo se ve: `verificador/caja_none_salida.txt`, bloque `none`: `ANALIZADOR rc 1 ... observadas: 69 ... AttributeError`, `COMPAÑERO rc 0 {'falta': 1, 'cob': 'SUFICIENTE'}`.
- Reproducir: `python verificador/ver_caja_none.py <evaluar_d25.py> <tmp> none`.
- Gravedad 2 porque falla fuerte (traceback) y no se pierde un veredicto silenciosamente; pero ocurre justo en el flujo «compañero verde, sigue el analizador», con el reloj de una lectura única. El escenario A5 de la batería prueba `None` sólo en una protegida (que cierra), no en una no protegida bajo el 2 %.

### VAD-04 · Caja `{}` (dict vacío) o sin `npix`/`vrp_mw`: ni el compañero ni el analizador la ven · gravedad 2 · confianza 5 (el efecto) / 4 (que importe)
- Dónde: `cobertura_cajas_v750b.py:36` (`isinstance(orc.get(c), dict)`), `analizar_v750b.py:120-121` (`record_cumulo`: `not o` o `not o.get("npix")` devuelve un record vacío).
- Qué pasa: una caja `{}` pasa el filtro del compañero (es dict) y del analizador (la llave existe). El analizador la interpreta como «ese brazo no publica nada». Con un `{}` en una protegida el brazo la pierde (P1, cae el brazo: sesgo conservador); con un `{}` en un negativo limpio el brazo no «publica» y su E baja, lo que lo favorece en P2. El docstring del compañero dice «o trae vacías», y el escenario A5 prueba sólo `None`.
- Cómo se ve: `verificador/caja_none_salida.txt`, bloque `vacio`: `observadas: 69 ... SIN DATO: 0`, compañero `falta: 0, SUFICIENTE`.
- Alcance: con el probe sellado no ocurre (`probe_v750b.py:86-99` (`oraculo_caja`) devuelve siempre el dict completo). Sólo aplica a «artefacto dañado pero legible», la misma familia que la adenda quiere cubrir.
- Reproducir: `python verificador/ver_caja_none.py <evaluar_d25.py> <tmp> vacio`.

### VAD-05 · El nulo del autor (7 de 7) no vigila la parte «idéntica al analizador»; 7 mutaciones mías no equivalentes sobreviven · gravedad 2 · confianza 5
- Dónde: `mutar_adenda1.py:20-30` y `probar_adenda1.py` (A4, A6 como única comprobación de identidad, con una población fija).
- Qué pasa: reproduje las 9 corridas del autor (identidad PASA, M1 a M7 ATRAPADA, control CAÍDA; `verificador/mutar_salida.txt`) y todas están atrapadas por aserciones semánticas (no por «lectura»). Pero la afirmación «reproduce exactamente la cuenta del analizador» descansa en A4 y A6, y mutaciones de una línea en esa parte pasan la batería (`verificador/ver_mutar_salida.txt`, `verificador/fuzz_mutantes_salida.txt`):

| mutación propia | batería del autor | distingue del compañero original |
|---|---|---|
| V2 `<=` pasa a `<` (borde exacto del 2 %) | pasa | sí (borde, 2 de 100) |
| V3 denominador sin restar `fuera` y `sin_crater` | pasa | sí (4 de 121 poblaciones) |
| V4 denominador sin sumar las sin gránulo | pasa | sí (149 objetivos, 2 error_K y 1 sin gránulo: original SUFICIENTE, mutante INSUFICIENTE; `ver_v4.py`) |
| V5 una protegida sin gránulo no frena | pasa | sí (1 de 121) |
| V6 una protegida SIN DATO del analizador no frena | pasa | sí (1 de 121) |
| V7 cuenta también las `sin_crater` sin cajas | pasa | sí (9 de 121) |
| V8 `dayflag` ausente deja de ser SIN DATO | pasa | sí (54 de 121) |
| V11 la línea «protegidas SIN DATO» siempre dice ninguna | pasa | sólo la salida impresa |
| V12 no nombra la caja faltante | atrapada (A1) | |
| V13 salida 3 pasa a 1 | atrapada | |

- V14 (`sg_ok or prot_sin`) es equivalente (cob_ok ya exige `not prot_sin`), la descarto. V9 es identidad de control.
- Impacto: hoy el compañero **es** correcto en todo eso (VERIFICADO LIMPIO 2 y 3); lo que falta es que la batería lo demuestre. Si alguien toca el compañero antes de la lectura, la batería no avisaría. Los mutantes que sobreviven van en dirección conservadora (cierran de más) salvo V3, V5, V6 y V8, que dejarían abrir la cobertura: V3 agranda el denominador, V8 deja de contar pasadas sin `dayflag`, y V5 y V6 dejan pasar una protegida SIN DATO.

### VAD-06 · «Roja por aserción sin el compañero» es roja sólo porque el archivo no existe · gravedad 1 · confianza 5
- Dónde: `probar_adenda1_rojo_salida.txt` (y mi reproducción `verificador/prueba_roja_salida.txt`).
- Qué pasa: sin el compañero salen 8 FALLAS, todas «lectura de la salida» (el script no existe); D1, el escenario que documenta el defecto del analizador, sale OK en rojo y en verde. La rojez no demuestra que la prueba detecte el defecto: demuestra que sin archivo no hay salida que leer. La frase del pre-registro es literalmente cierta (rc 1 con FALLAS, no un traceback de la prueba), pero sobrevende. El peso real de la prueba está en el nulo (VAD-05).
- Reproducir: `python probar_adenda1.py --companero .../NO_EXISTE.py --evaluador <ev> --dest <tmp>`.

### VAD-07 · «Sin cambiar ninguna regla» es una interpretación del §4, conservadora · gravedad 1 · confianza 3
- El §4 (l. 100-103) enumera lo SIN DATO: «pasada que no bajó, sin gránulo, grilla incompleta o error del brazo K». «Falta una caja del oráculo» no está en la lista literal; se subsume en «error del brazo». El umbral (2 %), el freno por protegida, el denominador y el código de salida 3 son las mismas expresiones del analizador (`cobertura_cajas_v750b.py:63-67` contra `analizar_v750b.py:233-234`). La extensión sólo puede cerrar más cobertura, nunca abrirla. Es una decisión de la coordinadora (D-48), no un error.

### VAD-08 · Otra forma de salir del denominador que la adenda no toca (por diseño del sello) · gravedad 2 · confianza 5 (ocurre) / 2 (que importe)
- `analizar_v750b.py:207,229-230,233`: una protegida `fuera` del gránulo o `sin_crater` (celdas sin dato en el 7×7 del cráter) sale del denominador y **no frena** la cobertura; sólo se imprime por nombre («protegidas no observadas»). Es el §4(a) tal como se selló, no la pasada «ok sin caja» de esta adenda. Mi oráculo del §4 coincide con el analizador en esto (0 discrepancias en las poblaciones con `sin_crater` y protegidas). Se anota porque es el único otro camino por el que una protegida deja de contar, y depende de que alguien lea esa línea.

## VERIFICADO LIMPIO (con su vara)

1. **El hueco existe en `analizar_v750b.py:205-209`**: `sin` (l. 206) exige `part is None` o `observada` con `dayflag != 0`; `no_obs` (l. 207) sólo `fuera`/`sin_crater`; `oks` (l. 208-209) exige las cinco llaves. Una pasada observada, nocturna y sin llave cae en ninguna. Vara: lectura del código más escenario propio `ausente` (`caja_none_salida.txt`): `observadas: 68 | SIN DATO: 0 | cobertura SUFICIENTE | compuerta ABIERTA` sobre 69 objetivos, y D1 de la batería (24 observadas de 25).
2. **El compañero reproduce al analizador cuando no falta ninguna caja**: diferencial aleatorio contra la salida real del analizador (modo A: SIN DATO, sin gránulo, lista de «protegidas SIN DATO» comparada como texto, veredicto de cobertura, y `observadas + no obs + SIN DATO = objetivos`): 15 + 20 + 30 + 30 poblaciones de modo A (las mitades de las corridas de 30, 40, 60 y 60 de `fuzz1` a `fuzz4_salida.txt`; las dos últimas con la versión final del script, que sí cubre SUFICIENTE e INSUFICIENTE, con y sin archivo de sin gránulo válido/ajeno/ausente, estados ok, error_K, grilla_incompleta, fuera, sin_granulo, error genérico, sin resultado, diurna, sin_crater, sin cobertura y `dayflag` ausente): **0 discrepancias**. Borde exacto del 2 % (2 de 100, 3 de 150, 2 de 101, 3 de 100): analizador y compañero iguales (`borde2_salida.txt`).
3. **Con cajas faltantes, el compañero coincide con un oráculo del §4 escrito aparte** (`ver_fuzz.py: oraculo`, no usa `partida()` del analizador): total, SIN DATO del analizador, falta caja, veredicto y código de salida (0 o 3): 0 discrepancias en todas las poblaciones (modos A y B, 190 en total) de las corridas `fuzz1` a `fuzz4` y en 121 poblaciones de `ver_fuzz_mut.py` para el original.
4. **Con el probe sellado el caso no debería ocurrir**: `probe_v750b.py:44-67` (`cajas()` devuelve siempre las cinco llaves, sin condicionales sobre la entrada) y `:166-169` (se escriben todas en el mismo bucle; cualquier excepción cae en `:192-193` con `estado = "error: ..."`, que es SIN DATO). Vara: lectura de código, no ejecución (ver SIN DATO). Las líneas citadas por la adenda (166-169) son exactas.
5. **Reproducción del autor**: `probar_adenda1.py --evaluador ...` → `TODOS LOS CHEQUEOS COMO SE ESPERA (23)` (`prueba_verde_salida.txt`); `mutar_adenda1.py` → identidad PASA, M1 a M7 ATRAPADA, control CAÍDA, `TODAS COMO SE ESPERA` (`mutar_salida.txt`, igual al del repo salvo la línea `rc=0` que añadí). Cada una de las 7 se atrapa por aserciones con nombre semántico (M2 por A5, M3 por A7, M5 por A6, M6 por A8, M4 por A1 y A3), no por «lectura».
6. **La adenda no edita ni el analizador sellado ni el probe**: `git diff s162-v750b-sellado HEAD` sobre los tres scripts está vacío; sha de `evaluar_d25.py` igual al de `analizar_v750b.py:48`.
7. **El texto de la adenda describe bien los scripts**, salvo el punto de VAD-03: 25 objetivos con 24 observadas en D1; siete mutaciones, copia sin mutar y mutación que sólo se cae; códigos de salida 0 y 3 (el 3 coincide con `analizar_v750b.py:337`); orden compañero antes del analizador; el compañero reutiliza `AB.partida`, `AB.cargar`, `AB.CAJAS`, `AB.MAX_SIN_DATO` por import en vez de copiarlos (sólo copia `sin`, `no_obs` y las líneas del archivo de sin gránulo, y esa copia es la que el diferencial valida).
8. **Efectos laterales**: el compañero sólo lee e imprime; no escribe archivos (el import del analizador no dejó `__pycache__` visible ni archivos nuevos fuera de mi carpeta, `git status`).
9. **Con cajas faltantes el compañero no abre lo que el analizador cierra**: en todas las poblaciones el veredicto del compañero es INSUFICIENTE cuando el del analizador lo es (diferencial 2 y 3); sólo puede agregar cierres.

## SIN DATO

- **El probe sellado no se pudo ejecutar** en este worktree: `probe_v750b.py:36` importa `probe_n` de `experiments/_s159/n/`, que está en `origin/main` (`git ls-tree` lo muestra) pero no en este árbol (`ls experiments/_s159/` sólo trae `mirova_v1_auditoria`). Por eso «con el probe sellado no ocurre» está respaldado por lectura de código, no por una corrida de `procesar_granulo` ni de `--sin-red`.
- **Run real**: no existen `objetivos_v750b.json` ni `sin_granulo_v750b.json` en el árbol; probé el compañero con poblaciones sintéticas en el formato del probe (el mismo que usa la batería del autor) y con la estructura de objetivos de `bateria_regla_v750b.py`, no con artefactos de un run.
- **«La primera corrida del nulo dejó pasar dos»** (texto de la adenda): sin historial verificable (un solo commit de la adenda); no lo medí.
- **Plataforma**: todo corrió en Windows 11, Python 3.12; no probé el comportamiento de rutas ni de codificación en el computador donde se lea el 2026-11-03.
- **Veredicto completo del analizador** (métricas §6, controles) más allá de la cobertura: sólo lo recorrí donde la caja `null` lo hace caer (VAD-03); el resto es de otra verificación.
- **Si `--leer-con-faltantes` con la lista del compañero queda bien marcado** en las líneas de veredicto: no lo probé con un caso donde el compañero cierre y el analizador lea (VAD-01), sólo con el caso `none`.

## Archivos de esta verificación (todos en esta carpeta)

`LISTA_CAMINOS_previa.md` · `ver_fuzz.py` (diferencial aleatorio contra el analizador y contra un oráculo del §4) · `ver_fuzz_mut.py`, `ver_fz_generar.py`, `_fz_V*.py` (mutaciones propias) · `ver_mutar.py` (mutaciones contra la batería del autor) · `ver_v4.py`, `ver_borde2.py`, `ver_caja_none.py` · salidas: `prueba_verde_salida.txt`, `prueba_roja_salida.txt`, `mutar_salida.txt`, `ver_mutar_salida.txt`, `fuzz1..4_salida.txt` (1 y 2 corridos con versiones intermedias del script; 3 y 4 con la final), `fuzz_mutantes_salida.txt`, `borde2_salida.txt`, `caja_none_salida.txt`.
