# Loop de VIIRS 375 (S162, sesión hija de la coordinadora «Retomar», local_4152952c)

Única fuente de verdad entre vueltas. Worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864`, rama
`claude/s162-viirs375-c1b864`. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` §4.
Carpeta del trabajo: `experiments/_s162_v375/`.

Reglas de esta sesión (las de la coordinadora, 2026-10-24): sólo este worktree y esta rama; no escribo
`tasks/LOOP_OBJETIVOS.md` ni archivos de las sesiones de instrumento, VIIRS 750 o MODIS; nada en `pipeline/` sin
pre-registro sellado, verificador limpio, tag defensivo y el sí de Nicolás (A45); **todo despacho de GitHub Actions se
pide a la coordinadora** (SendMessage a local_4152952c) con el pre-registro y la lista de brazos; ningún A/B nuevo antes
de que el instrumento entregue la cobertura contra la referencia (fase 0, PD0); sólo `EARTHDATA_TOKEN` (A71); nunca
`git stash`; `git add` por archivo; verificador con contexto limpio de otro modelo antes de aceptar cualquier resultado;
parada si C: o D: bajan de 3 GB. Puedo abrir sesiones propias (permiso de Nicolás vía coordinadora, 2026-10-24), cada
una en su worktree, con su archivo enlazado aquí, y avisando a la coordinadora con nombre e id; hoy no hay ninguna.

## Cola (en el orden del programa)

| id | qué | estado |
|---|---|---|
| V375-B | pre-registro del lote de negativos limpios neg_resto para el port (D-36, aprobado) | borrador listo en `041e7fc43`; verificador limpio corriendo; falta sello |
| V375-C | pre-registro de los 10 brazos de ROI (mismo lote que B) | borrador listo en `041e7fc43`; verificador corriendo; falta sello |
| V375-E | pre-registro del paquete V375 contra K, curva de cenit contra la de MIROVA | borrador listo; depende de PD1, PD3 y del evaluador común del instrumento (M con d′) |
| V375-D | números propios de 375 | sólo si B o C lo exigen (disparador en `PREREGISTRO_C.md` §5.3) |
| V375-F | Chillán sobre 3 MW (port 0,939, n 6) | después de V375-E |
| V375-A | etiqueta de protegida de cráter | la hace la sesión del instrumento; `evaluar.py --protegida-crater` la recibe |

Esperando de otros: cobertura contra la referencia de MIROVA (instrumento, `evaluar.py --cobertura`), V375-A
(instrumento), evaluador común con placebo y d′ (instrumento, para E), el despacho combinado de la fase 1 (coordinadora).

## Decisiones para Nicolás (con recomendación)

1. **Sellar V375-B y V375-C** después del verificador limpio. Recomendación: sí, con las correcciones que pida el
   verificador en una adenda.
2. **Tamaño del lote**: 709 pasadas nuevas (~4,9 h de runner, ~50 min de reloj con 8 en paralelo) para B y C juntos,
   o sólo los 400 negativos de B (~2,8 h). Recomendación: las 709; C sin sus 155 alertas bajo 1 MW nuevas no tiene con
   qué decidir la caja (S159 tenía 45 de 949).
3. **Marco**: el congelado de S159, hasta el 2026-10-21. Extenderlo hasta el 2026-11-02 12:59 UTC (antes del cese de
   Suomi NPP) sería una adenda con población nueva. Recomendación: no por ahora.

## Bitácora

### 2026-10-24 (vuelta 0, cierre)
- **Hecho**: `experiments/_s162_v375/` con selección (709 pasadas nuevas, semilla 162, 531 gránulos), brazos (10 cajas),
  runner (`probe_v375.py` + `probe-s162-v375.yml`, para la coordinadora), evaluador y tres borradores de pre-registro.
  Commit `041e7fc43`. Código del port de S159 traído de `ca034d66e` en `29d7a5bf4`.
- **Pruebas** (todas en verde): brazos recalculados sin red sobre las 149 grillas de S159 = runner de S159 en 149 de 149
  (M14, PIX7, SENS); escena sintética: foco débil en el cráter de Tupungatito invisible para M14 y visible para C13, C14,
  C21, M21, SENS, SENS_PT y CIRC; prueba de signos con pesos = la sellada de D-45 en 2.000 de 2.000 juegos; casos con
  respuesta conocida para P2, silencio, cota honesta, elección en T, pesos y decisión.
- **Humo del evaluador sobre el lote de S159 (ya visto)**: reproduce el informe de S159 con una implementación
  independiente (M14: recall bajo 1 MW 0,616 contra 0,618; SENS 0,905 y negativos 0,0481 contra 0,0480; neg_resto 0 de
  45). Controles nulo, NUNCA y PLACEBO en verde. **Cambió dos reglas, declaradas en `PREREGISTRO_C.md` §6**: el veto
  absoluto contra K bloqueaba a los diez brazos por las mismas 3 protegidas sólo OCR (pasó a veto relativo a M14 y el
  disparador de D cuenta la tabla sola), y se agregó desempate por caja más chica. Como ya vi los brazos nuevos sobre
  S159, **decide el lote S162 solo** y la unión confirma (§5.5).
- **Hallazgo de instrumento para V375-E**: el nulo de 750 (mismos pares ordenados por hora) no sirve en 375: el VRP de
  MIROVA baja de una pasada a la siguiente de la misma noche (mediana 0,818, n 365; ¿plataforma?, SOSPECHA). Nulo nuevo:
  pares de cenit parecido (< 5°) en orden al azar (MIROVA 0,98). Línea base de K medida: MIROVA cae 0,778 de la pasada
  menos oblicua a la más oblicua, K 0,573; razón doble 0,766 [0,722; 0,861], CAE MAS QUE MIROVA; sobre 50°, 0,733.
- Pendiente: verificador limpio (Sonnet) sobre los tres; resumen a la coordinadora en la carpeta de notas.
