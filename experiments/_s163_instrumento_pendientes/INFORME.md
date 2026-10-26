# Pendientes del instrumento (fase 0 del programa por sensor): placebos sobre producción, tarea 1.35 y huecos de NASA

Sesión hija de S163 (coordinadora relevada por S164), 2026-10-26. Cola original: `tasks/LOOP_INSTRUMENTO.md` de la rama
`claude/s162-instrumento-021324`; traspaso: `INSTRUMENTO_fase0_traspaso.md` (carpeta de notas de S162). Programa:
`docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §2 y §8. Módulo: `scripts/evaluador_comun.py`.
Pruebas: `tests/test_evaluador_comun_s163.py`. Nada en `pipeline/`, `data/` ni `frontend/`.

## Por qué hacía falta

Cada paquete del programa (el código de MIROVA por sensor) se va a juzgar con el evaluador común. Tres cosas impedían
leer bien ese juicio:

1. **No se sabía cuánto «decide» el instrumento solo.** Una prueba que da GANA o PIERDE por azar en un 10 % de los
   casos convierte cualquier A/B en una moneda. Los placebos de D-44 se habían corrido en S160 con el evaluador sellado
   de D25 y el P2 viejo (D-34); faltaba hacerlo con el evaluador común y el P2 de D-45, que es el que usarán los A/B
   nuevos.
2. **Un agregado esconde curvas.** El píxel oblicuo es más grande y más deformado; en VIIRS 375 nuestra magnitud contra
   MIROVA cae con el cenit del sensor. Un A/B con más pasadas de borde en un brazo se leería como efecto del detector.
   La tarea 1.35 pedía que auto-audit y evaluadores informen por tramo de cenit y por régimen; el auto-audit ya lo hacía
   desde #874, el evaluador no.
3. **Una pasada ausente no decía por qué.** Si MIROVA publicó una pasada y nosotros no la tenemos, puede ser que el
   gránulo llegó y no dejó record (legítimo para el evaluador: sale del denominador) o que NASA no lo entregó (hueco
   de cobertura, como el 2026-10-12, cuando CMR respondió vacío para NOAA-21 y Suomi NPP y el job dijo «Cobertura:
   completa»). Desde #909 el run deja esas incidencias en el JSON de cobertura, pero nadie las cruzaba con MIROVA.

## Pendiente 2: tarea 1.35 en el evaluador (estratos)

- `tramo_cenit(z)`: tramos de 10° (`z00-10`, ..., `z70-80`) como pide el programa (§2); sin cenit, `sin_cenit`. Los
  tramos de `banco_paridad.zbin` (cuatro, anchos) son otra definición y no se tocan.
- `regimen(instante)`: `antes_535`, `535_a_K`, `desde_K`, con los cortes del resto del proyecto (prueba de guarda contra
  `auto_audit_weekly.CORTE_535` y la hora de adopción que lee `vigilancia_sombra.leer_adopcion`, 2026-10-18 09:57:30).
  En producción esos cortes no separan detectores (todo el histórico es K desde #883): separan temporada y canal de
  referencia; en un brazo sí pueden separar detectores.
- El cenit de una pasada es el del record del **control** (mismo gránulo que el brazo); `cargar_lado` ahora lee
  `sensor_zenith_deg`.
- `metricas_por_estrato(T, control, brazos, estrato_de)`: pasadas, cobertura por lado, P1b, RUTINA y P2 (neto,
  discordantes, bloques) dentro de cada estrato; **informa, no decide**. Las cuentas suman el agregado (prueba de
  partición) y `cobertura()`, `p1b()` y `publicaciones_sobre_rutina()` dan lo mismo con y sin cenit (prueba de no
  regresión). El CLI agrega `estratos.cenit` y `estratos.regimen` a la salida.

## Pendiente 3: «no observado» frente a hueco de NASA

`causa_ausencia(f, lado, eventos)` y `huecos(T, eventos_por_lado)`, con el JSON de `run_pipeline.py --cobertura-json`
(CLI: `--cobertura NOMBRE=RUTA_O_GLOB`, repetible):

| causa | qué la produce | lectura |
|---|---|---|
| `hueco_nasa` | falla de búsqueda o descarga, L1B sin geolocalización o día parcial, del mismo volcán (o sin volcán) y día, en una plataforma del mismo sensor (o sin plataforma) | defecto de cobertura seguro |
| `busqueda_vacia` | `sin_granulos` en una plataforma del mismo sensor ese día | hueco probable: MIROVA tuvo la pasada, pero su CSV no trae plataforma |
| `sin_incidencia` | el run no registró nada para ese volcán, día y sensor | no observado legítimo (el gránulo llegó y no dejó record) o pérdida del proceso |
| `sin_registro_de_cobertura` | el lado no trae JSON de cobertura | causa desconocida |

El caso del 12-oct (logs reales: `SEARCH_DONE VIIRS_NOAA21_750 n_l1b=0`, Suomi NPP igual, NOAA-20 sí entregó) queda
como `busqueda_vacia` y el veredicto de cobertura sigue INVALIDO, igual que antes: esto **informa**, no cambia
`cobertura()`. Si un hueco de NASA debe invalidar un A/B es decisión del pre-registro (ver «Abierto»).

Límites:
- El NRT de producción no guarda `--cobertura-json` (`nrt.yml` no lo pasa), así que sobre producción la causa es
  siempre `sin_registro_de_cobertura`; sirve para los brazos de los A/B, cuyos workflows sí lo guardan.
- El evento es por volcán, día y plataforma, no por pasada (verificador): un solo gránulo fallido marca `hueco_nasa` a
  todas las ausencias de ese sensor ese día, y una búsqueda vacía de una de las tres plataformas marca `busqueda_vacia`
  a toda ausencia del sensor. Y al revés: si el filtro nocturno deja la lista vacía, `fetch` hace `continue` sin
  registrar nada y la ausencia queda `sin_incidencia`. El lector no usa `retiradas` ni `plataformas` del JSON (el cese
  de Suomi NPP del 2026-11-02 no se distingue de una plataforma muda).
- Un `--cobertura` con un nombre que no es un lado ahora es error de argumentos (antes se ignoraba sin aviso; lo
  encontró el verificador).

## Pruebas y mutaciones

- 22 pruebas nuevas. Roja primero (`roja_por_asercion.txt`: 16 de 17 en rojo con stubs vacíos; la que pasaba era la de
  no regresión, que debe pasar antes y después). La del nombre de `--cobertura` se vio roja por aserción antes de su
  arreglo.
- Mutaciones: **28 de 28 atrapadas por aserción**, con control de caída (`mutaciones.json`, `mutaciones_salida.txt`,
  arnés `experiments/_s162_instrumento/mutar.py`). En la primera corrida E1 cayó por un `KeyError`; se agregó una
  aserción sobre el conjunto de tramos antes de indexar. E24 a E28 son las que el verificador encontró vivas (el CLI
  podía no pasarles los días excluidos a `huecos` ni a los estratos, estratos sin ordenar) más la validación nueva.
  Quedan vivas, a sabiendas, las que sólo tocan el texto impreso (no hay prueba de la consola).
- Suite completa sobre árbol quieto (A112), commit `03df35b68`: 2549 pasan, 29 saltadas, 2 xfail, 0 fallas. Tras los
  arreglos del verificador, otra vez sobre árbol quieto (ver el PR).

## Pendiente 1: placebos de D-44 y de ganancia sobre producción (la línea base)

Script: `placebos_produccion.py` (semillas y repeticiones fijadas antes de correr, V42-22). Producción K de
`data/mirova_equivalent/` y referencia de `data/mirova_reference/` del commit `f391376a0` (sha256 en el JSON). Ventanas
del programa §2: T (tabla sola; VIIRS 2026-04-01 a 06-12, MODIS 2026-03-01 a 06-12) y O (2026-06-13 al último día de la
referencia, 2026-10-25, sin el 12, 13 y 17 a 20 de octubre), O con unión y con tabla sola. Regla de mínimas SN (D-9).
Sólo lectura; no se despachó nada. Duración: 5.452 s. Todos los números de abajo salen de `PLACEBOS_RESUMEN.md` y
`agrupar_placebo_c_salida.txt`, generados por los scripts.

**Identidad.** Producción contra su copia: 0 discordantes en P2 y 0 cruces en P1b en las 9 celdas. Es un control que
no puede fallar (la copia es el mismo dato, verificador): sólo dice que el armado no inventa diferencias.

**P2, tasa de falsos (placebo simétrico c).** Por celda (400 repeticiones) las estimaciones van de 0,5 % a 6,5 % por
cola, con intervalos que cruzan el 5 %. Agrupando las 14 combinaciones de celda y fracción independientes (la O con
tabla sola de VIIRS 750 y MODIS es el mismo sustrato que la unión y se deja fuera; el script lo comprueba):

| | GANA (falso) | PIERDE (falso) |
|---|---|---|
| todas | 229 / 5.600 = 4,09 % (IC95 3,60 a 4,64) | 174 / 5.600 = 3,11 % (IC95 2,68 a 3,59) |
| fracción 1,0 | 133 / 2.800 = 4,75 % (IC95 4,02 a 5,60) | 98 / 2.800 = 3,50 % (IC95 2,88 a 4,25) |

Las filas no son del todo independientes (O-unión y O-tabla de VIIRS 375 comparten casi todo el sustrato, y todas las
celdas usan las mismas semillas), así que el IC95 queda algo angosto. Variante estricta, sin ninguna celda O-tabla:
GANA 194 / 4.800 = 4,04 % (IC95 3,52 a 4,64), PIERDE 151 / 4.800 = 3,15 % (IC95 2,69 a 3,68).

Lectura: **P2 está calibrado sobre producción real**: por azar da un GANA falso en ~4 % de las lecturas y un PIERDE
falso en ~3 %, por sensor y ventana. Con tres sensores y dos ventanas, la probabilidad de al menos un falso en algún
lado no es despreciable; los pre-registros tienen que decir qué combinación decide.

**BLOQUEA sin ningún efecto: ~40 %** (hallazgo del verificador). Con el placebo simétrico, P2 da BLOQUEA (D-45: el neto
va en contra del brazo sin llegar a significancia) en 2.258 de 5.600 lecturas (40,3 %): es lo que pasa cada vez que el
neto sale positivo por azar. **Un BLOQUEA no es evidencia contra un brazo**; si un pre-registro lo usa como veto, su
tasa de falso veto es ~40 %, no 5 %.

**P2, poder (placebos a y b).** Con 25 % o más de las publicaciones tocadas, a da GANA y b da PIERDE en 36 a 40 de 40
en todas las celdas, salvo MODIS O con 25 %, donde b da SIN SUSTRATO en 40 de 40 (sólo 11 alertas bajo 1 MW
publicadas; con 50 % sí da PIERDE en 40 de 40). Con 10 %, VIIRS
750 y MODIS quedan SIN SUSTRATO en a (20 a 35 negativos publicados: tocar 10 % son 2 a 4 pasadas). VIIRS 375 detecta
efectos chicos; VIIRS 750 y MODIS sólo efectos de varias pasadas.

**P2 por estrato.** Por régimen funciona (falsos 1,5 % a 6,5 % por celda, 200 repeticiones). **Por tramo de 10° de
cenit casi siempre da SIN SUSTRATO** (75 de 78 filas, según el verificador): el placebo simétrico necesita bloques
noche-volcán con pasadas de los dos lados dentro del tramo, y un tramo de 10° tiene como máximo 6. Ojo: esa exigencia
es más estricta que el sustrato de P2 en un A/B real (un brazo real puede tener discordancias en bloques de un solo
lado), así que el SIN SUSTRATO del placebo no prueba que P2 no tenga sustrato por tramo; prueba que su calibración por
tramo no se puede medir con este placebo. Los tramos z30-40 y z60-70 de VIIRS 375 O dan el mismo 12/200 GANA: ambos
tienen 5 bloques de ±1 y la misma semilla, así que las secuencias de signos son idénticas (el verificador lo
reprodujo en 200 de 200); con 5 bloques sólo hay GANA por unanimidad (1/32 = 3,1 %), y 12/200 es un exceso de azar
(P = 0,024) contado dos veces, no un defecto.

**M (magnitud).** Identidad: NEUTRO en todas las celdas. **K×1,2 da MEJORA sin comparador** en la mayoría de las celdas
de VIIRS (la trampa R2-8: nuestra magnitud queda bajo MIROVA, así que inflarla parejo «se acerca») y **nunca MEJORA con
el comparador d′**; K×0,8 da EMPEORA con y sin comparador. Es cierto por construcción (con una ganancia pareja d′ es 0
idénticamente): el placebo prueba que el comparador cierra la trampa, no mide su poder para premiar un brazo bueno. Calibración de la regla simétrica sobre los pares de K×1,2:
falsos MEJORA y EMPEORA de 0,5 % a 5 %, salvo VIIRS 750 O en z50-60 (7 pares: 6 % y 7 %, INDECIDIBLE). La razón
K/MIROVA cae con el cenit en VIIRS 375 (O unión: de 0,81 en z00-10 a 0,40 en z60-70): es la curva que la tarea 1.35
quería dejar a la vista.

## Verificador con contexto limpio (Sonnet, 2026-10-26)

Informe en el scratchpad de la sesión (`...\scratchpad\verificador\INFORME.md`, fuera del repo). Ninguna gravedad 3.
A1 CONFIRMADA (cortes iguales a los del proyecto; partición comprobada sobre datos reales; B no es aditivo entre tramos
porque una noche-volcán se reparte, esperable). A2 CONFIRMADA EN PARTE (lector correcto contra JSON generado con las
funciones reales; límites de granularidad, anotados arriba). A3 CONFIRMADA EN PARTE (cinco mutaciones propias vivas: las
tres de comportamiento quedaron atrapadas con pruebas nuevas, E24 a E27; las dos del texto impreso siguen vivas). A4
CONFIRMADA EN PARTE (números recalculados exactos; BLOQUEA ~40 % no informado, ahora en el resumen; «máximo 5» era 6;
independencia, variante estricta agregada; simetría del placebo exacta y alfa real de los sorteos de la prueba hasta
5,24 % en B de 21 a 120). A5: la ventana O termina el 2026-10-25 (último día de la referencia; el programa llega al
2026-11-02); los días excluidos coinciden con D-29; `sin_cenit` sólo aparece en pasadas sin record del control, nunca
elegibles. Matiz: el régimen `535_a_K` junta el tramo de #571 (el auto-audit corta además ahí); la tarea pedía #535 y K.

## Abierto (decisiones o trabajo para otra vuelta)

1. **Si un hueco de NASA invalida un A/B.** Hoy se informa. Recomendación: que el pre-registro diga que una protegida
   ausente por `hueco_nasa` o `busqueda_vacia` en algún brazo (y presente en el control) es INVALIDO POR INSTRUMENTO
   (ya lo es por la regla de T1) y que el día se rescate de LAADS o se excluya en todos los brazos.
2. **Producción sin JSON de cobertura.** Agregar `--cobertura-json` a `nrt.yml` y guardarlo (artefacto) dejaría
   clasificar también las ausencias del control. Toca `.github/`, no `pipeline/`.
3. **P2 por tramo de cenit no se puede calibrar con el placebo c.** Si se quisiera decidir por tramo, haría falta otra
   unidad de bloque o tramos más anchos (los cuatro de `banco_paridad.zbin`), pre-registrado.
4. **Ruido entre runners.** Estos placebos miden la calibración de la prueba, no el ruido de reprocesar el mismo
   detector en dos máquinas (S152: `argsort` inestable según la CPU). Ese ruido sólo se mide con un brazo gemelo
   despachado (como el gemelo de D25).
