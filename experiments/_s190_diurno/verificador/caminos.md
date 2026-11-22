# Caminos por los que el veredicto del A/B diurno sobre la vía podría estar mal

Escrito por el verificador antes de abrir `eval\veredicto_salida.txt` y `eval\informativo_sin_i4b_salida.txt`.
Hora del servidor (gh api -i repos/MendozaVolcanic/VRP-chile): Sat, 21 Nov 2026 14:39:25 GMT.
Sha256 de los dos archivos en `caminos_sha256.txt`. Lo único que vi antes: el código del evaluador, la adenda V, el
pre-registro de S163 (§4 a §6, adenda 1), PREGUNTA_R_W7.md y los diffs entre el tag de código y dda72573f. El nombre
`informativo_sin_i4b` sugiere que alguien miró I4b; no sé qué dio.

## A. Datos de entrada (raíces armadas)
A1. Una raíz `eval\Wn` mezcla el control de una corrida con el brazo encendido de otra (reparación): el control y el
    diurno de un volcán no salen del mismo run, y la paridad nocturna (I3, I5) compara cosas distintas.
A2. Un volcán de una reparación no declarada en ORIGEN.txt, o una copia que no es la del run declarado (sha256 de
    los JSON distinto al del artefacto bajado).
A3. `cargar_brazo` deduplica por (volcán, sensor, hora) y se queda con la primera raíz: si un JSON trae records de
    otra ventana o duplicados, el primero gana en silencio.
A4. Records con `regimen.codigo_sha` de otro commit (artefacto de una corrida vieja) que I1 detectaría, o que I1 no
    ve porque el evaluador sólo revisa records dentro de ventanas.
A5. Logs ausentes en una raíz: I1 (a) se saltaría en silencio (problemas_de_logs salta si no hay `logs/`).

## B. Cobertura
B1. Noches perdidas por igual en los dos brazos (descarga fallida en ambos jobs): I3 compara control contra brazo y
    la referencia; si MIROVA no lista la pasada, nadie la echa de menos. Mirar los logs por fallas de descarga.
B2. Jobs que terminaron verdes sin datos (token vacío, NASA caída) en un brazo de un volcán.
B3. Cobertura diurna: el brazo diurno pierde pasadas de día que MIROVA tiene (I4), por hueco parcial de NASA que la
    regla (a)+(b') no excluye; MODIS no tiene regla de exclusión (la adenda 1 sólo nombra productos VIIRS).
B4. I4b falla por un volcán-sensor-día con pasadas diurnas de MIROVA donde el brazo no tiene record diurno: puede
    ser legítimo (la vía devuelve sin record cuando la escena se descarta, por ejemplo por reflejo, o por grilla) y la
    compuerta estaría midiendo otra cosa (que la vía no guarda record de una escena descartada), no cobertura.

## C. Días excluidos
C1. La lista no sale de (a)+(b'): consulta CMR con otra caja, otro producto, otras fechas o día UTC mal cortado.
C2. (b') contado sobre el brazo en vez del control, o sobre la unión.
C3. Un día excluido que tiene alertas diurnas de MIROVA (protegidas) y que, sin excluir, haría fallar o cambiaría
    el veredicto: la exclusión esconde algo que la regla no permite (por ejemplo excluir por hueco de una plataforma
    todo el día de los tres sensores, incluido MODIS).
C4. La regla excluye días de MODIS sin que la regla lo diga, o no excluye huecos MODIS (Terra/Aqua) que sí existen.

## D. Evaluador
D1. El diff entre el tag del instrumento y dda72573f toca algo más que R-W7 (o lo hace en módulos importados:
    evaluar_diurno_k, evaluador_comun, clase_mirova, banco_paridad, frontend/index.html, sustrato_via.json).
D2. El predicado del tablero (`isValidDetection`) del worktree no es el de producción en el tag de despacho.
D3. Clasificación día/noche: records diurnos con fecha UTC que cae en otro día que la pasada de MIROVA; pareo a
    ±120 s que falla de día (la hora de la vía puede ser la del gránulo y no la de la pasada).
D4. `zip(T, marcadas)` supone que `tabla_por_pasada` conserva el orden de las pasadas; si no, `es_dia` queda mal
    asignado.
D5. Records diurnos que cayeron a K (M6) sacados de la regla con sus pasadas: si son muchos, la regla mira un
    subconjunto sesgado.
D6. M8 (publicaciones sin fila) o M5 (magnitud) con un predicado o una tolerancia distintos a los sellados.
D7. R-CH, R-W7 y variantes de §6.4: una variante que da INVÁLIDO por compuerta podría arrastrar el final a DECIDE.
D8. I2: el marcador `dayflag` ausente en records de MODIS por cómo la vía lo guarda; o el control con records
    diurnos por crepúsculo (elevación > 0 con dayflag 0), que dispararía I2 sin ser un defecto.
D9. I5: noches distintas entre brazos por reprocesos de días distintos o por la ventana de la reparación.

## E. Lectura del veredicto
E1. Una compuerta que falla por un caso que no mide lo escrito (por ejemplo I4b por escenas descartadas) vuelve
    INVÁLIDO un resultado que, con la compuerta bien medida, sería otro; o al revés, una compuerta que pasa porque no
    puede fallar (instrumento ciego).
E2. La referencia congelada no es la del sustrato (sha256) o no cubre W7 completo.
E3. El veredicto por flag de VIIRS combina 375 y 750 mal (orden de precedencias DECIDE contra NO ADOPTAR).
