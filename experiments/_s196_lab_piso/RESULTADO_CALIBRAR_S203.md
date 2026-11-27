# Resultado de `evaluar.py calibrar` sobre el barrido del piso completo (S203, 2026-11-27)

**Estado: ELEGIDO, s_A = 3,0 y piso_A = 0,0025.** No se adopta nada: fijar el valor en el perfil `laboratorio` y
encender la zona A es decisión de Nicolás (paso 4 del plan del laboratorio). Este archivo sólo guarda la corrida.

## Qué se corrió

- Evaluador: `experiments/_s196_lab_piso/evaluar.py` en `main` 4760736bf (re-sello S202 con tres frenos, #1136),
  desde un worktree limpio. Producción: `data/mirova_equivalent` de ese commit. Referencia de MIROVA bajada fresca
  el 2026-11-27 (sha256 en `resultado_calibrar_s203.json`, `referencia_mirova`).
- Entrada: la unión de las diez tandas del manifiesto (`unir_tandas.py --fin-esperado 2026-11-23`), 30.047 records por
  brazo en los nueve brazos, 0 problemas; el manifiesto de la unión es el de `main` (comparado entero).
- Antes de calibrar: escenas de validez distinta entre brazos (`medir_invalidas_por_brazo.py`,
  `salida_invalidas_por_brazo_s203.txt`) y chequeo externo R5C-103 del acta de la ronda 5
  (`chequeo_perfil_r5c103.py`, `salida_chequeo_r5c103_s203.txt`: cada carpeta trae sólo `regimen.perfil` de su
  brazo; un intercambio puesto a propósito, p250 en la carpeta de p200, sale MAL).

## Qué dio

- Tasas por noche negativa limpia y por pasada de cada sensor: `salida_tasas_calibrar_s203.txt` (de
  `resultado_calibrar_s203.json`, campo `tasas`). La regla sellada (PREREGISTRO §5) elige el menor piso cuya tasa por
  noche no supera 30 % con la comparación entera 10·publicadas <= 3·negativas.
- Controles que invalidan, todos en verde: cobertura y código iguales en los brazos; el control idéntico record a
  record al brazo sin zona y con las cuentas de producción; ningún brazo cambia records donde la zona no actúa
  (3.008 records de la ventana por brazo); réplica por noche de los frenos igual a las cuentas oficiales.
- Frenos del re-sello S202: las 2 escenas excluidas (Llaima MODIS Terra 2026-05-30 02:55 y Lastarria MODIS Terra
  2026-09-19 02:10, `fondo_no_estimado` en algunos pisos) no deciden su noche (freno 1), son 2 sobre 1.538 noches
  negativas del control, bajo el tope de 1 % (freno 2), y con la publicación quitada devuelta (1, en 0,00275) la
  elección es la misma (freno 3).
- Contraste: el evaluador del sello S200c (a41496d3a, sin muestra común) sobre la misma unión también da ELEGIDO
  0,0025; la única diferencia en las cuentas por noche es esa publicación de Llaima en 0,00275 (319 contra 318).
