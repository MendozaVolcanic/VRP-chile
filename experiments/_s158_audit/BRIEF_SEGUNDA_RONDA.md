# Brief de la segunda ronda de la auditoría S158

> Aprobada por Nicolás el 2026-10-21 («si a todo pero no mandaremos correo a coppola aun, veamos si con estos
> alcanzamos la paridad con mirova y nuestros objetivos»). Escrito por la sesión que orquestó la primera ronda. Para que
> esta ronda sea independiente, este brief lista **afirmaciones y fuentes, no conclusiones**.

## Por qué existe

VRP Chile replica el sistema térmico MIROVA para 11 volcanes chilenos y apoya la alerta volcánica de SERNAGEOMIN.
MIROVA publicó el 2026-07-24 su código operacional de VIIRS 750 (copia verificada en
`experiments/_s158_d17_diseno/osf_codigo_mirova/`), y la primera ronda lo usó como vara. Varios hallazgos van a decidir
cambios en el pipeline, y en este proyecto los agentes ya se han equivocado antes (auditorías S138, S146, S150 y S155
lo registran). Nicolás quiere seguir de manera segura: antes de tocar el pipeline, una segunda ronda que **cambie el
método** y no sólo repita a los mismos agentes.

## Reglas de independencia

- No leas `docs/AUDIT_S158.md` ni los informes `experiments/_s158_audit/f*/INFORME.md` y `v*/INFORME.md` hasta haber
  escrito tus propias mediciones de cada afirmación. Después sí, para comparar, y la comparación es parte del entregable.
- Escribe tus scripts desde cero. Puedes leer el código del pipeline, los datos y el código de MIROVA; no copies scripts
  de la primera ronda.
- Usa subagentes de otro modelo que el de la primera ronda donde puedas (la primera usó Opus para F1, F3, F5, F6 y los
  verificadores, y Fable para F2 y F4).
- Antes de lanzar auditores, lee `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` y pega entero
  el bloque de `docs/_prompts/PREAMBULO-AUDITOR.md` en cada prompt. El plan de la primera ronda
  (`docs/PLAN_AUDITORIA_S158.md` §4) tiene un bloque común que sirve de modelo.

## Lo que hay que hacer

1. **Un segundo oráculo.** Port a Python de `MIROVA_VIIRS750_hotspot_detection.m` y `MIROVA_VIIRS750_VRP.m` escrito sin
   ver `experiments/_s158_oraculo_mirova/`. Control: la matriz de ejemplo es la pasada de Etna del 2023-05-19 00:54, y
   el OSF v2.5 (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv`)
   trae su resultado de producción (Npix 5, Tot_Lmir_hot 1,96534218, Tot_Lmir_bk 1,072886152, VRP 9.889.528 W). Después
   compara los dos oráculos en Etna y en escenas sintéticas que ejerzan los umbrales (K1, mínimos de fuera, segundo pase).
2. **Replicar estas afirmaciones** con mediciones propias (afirmación · dónde mirar):
   - El fondo del VRP de VIIRS 750 de producción es un escalar del anillo de 5 a 25 km con recorte a cero, y con los
     mismos píxeles de Etna da otra magnitud que el código · `pipeline/process_viirs_mod.py` (fondo y recorte), el `.m` de VRP.
   - Ese fondo deja en 0 MW cúmulos de cumbre de VIIRS 750 que el tablero oculta · `data/mirova_equivalent/*.json`,
     `frontend/index.html` (`isValidDetection`).
   - Con el fondo por píxel de MIROVA del OSF v2.5 sobre nuestros píxeles cambia la razón contra MIROVA en VIIRS 375
     · OSF v2.5 2025 contra nuestros records.
   - La razón de magnitud contra MIROVA cae con el cenit, y la caída es de conteo de píxeles · records contra el OSF y
     contra la referencia NRT (`latest_consolidado.csv`; antes, `scripts/calidad_referencia_mirova.py`, regla A119).
   - La compuerta `bt > t_bg + 3 K` del primer pase y el segundo pase están acoplados en VIIRS 750 · `pipeline/detection_context.py`.
   - El código de MIROVA corre el segundo pase siempre y sobre toda la escena · el `.m` de detección.
   - Cero gránulos en una búsqueda se registra como «Cobertura: completa» · `scripts/run_pipeline.py`, `pipeline/fetch.py`.
   - Al A/B de D25 (run 39530508296, datos en la rama `s146-ab/39530508296`) le falta el 2026-10-18 · `experiments/_s157_prereg_d25/`.
   - La métrica M del evaluador de D25 da MEJORA con un brazo placebo de ganancia constante · `experiments/_s157_prereg_d25/evaluar_d25.py`.
   - Sobre 50° de cenit el VRP de VIIRS 750 del OSF v2.5 no cumple la fórmula del código en una parte de las filas · OSF v2.5.
   - Rechazamos todo VIIRS 750 diurno y se perdieron alertas protegidas de Chillán · `pipeline/store.py`, referencia NRT.
   - MIROVA cuenta píxeles, no regiones · el `.m`, el OSF v2.5, `docs/MISSION.md` y el glosario de `CLAUDE.md`.
3. **Un meta-auditor de método.** Instrumentos de la primera ronda que no podían fallar, denominadores y ventanas mal
   declarados, propagación incompleta (A113), y lo que ningún frente miró: MODIS de punta a punta, `frontend/diario.html`
   y `mosaico.html`, `pipeline/store.py` entero.
4. **La prueba con gránulos chilenos.** El oráculo corrido sobre los L1B reales (VNP02MOD y VNP03MOD, o los de NOAA-20 y
   21) de unas 10 pasadas de VIIRS 750 con alerta de MIROVA, remuestreados a la grilla de MIROVA (la grilla de VIIRS 375
   de sus TIF está medida en `experiments/_s158_d17_diseno/grilla_tif_salida.txt`; la de 750 m, hipótesis del §4.1 de
   `docs/DISENO_D17_REMUESTREO_UTM.md`). Casos mínimos: Tupungatito VIIRS 750 en 0 MW (2026-03-01 05:36), Láscar
   2026-10-08 05:42 NOAA-20, Cordón Caulle 2026-10-10 05:54 NOAA-21, Chillán 2026-10-18 06:48. Es un workflow de sólo
   lectura en GitHub Actions: autentica sólo con `EARTHDATA_TOKEN` (regla A71, copiar el bloque `env` de
   `.github/workflows/nrt.yml`), no escribe en `data/`, no hace push a `main`. Para dispararlo sin mergear a `main`,
   mira cómo lo hizo el PR #880 (rama auxiliar de disparo). Nicolás aprobó despacharlo.
5. **Las marcas A113 pendientes**: la tabla de 22 afirmaciones y las 10 pruebas que lista
   `experiments/_s158_audit/f2/INFORME.md` §3, cada marca sólo después de verificarla tú.
6. **Una guía para que Nicolás revise con sus ojos** 3 a 5 casos en el tablero y en los TIF (qué abrir, dónde, qué
   debería verse si el hallazgo es cierto y qué si no).

## Límites

- No edites `pipeline/`, `data/` ni `frontend/` (A45). Documentos y `experiments/` sí, en tu rama.
- No envíes el correo a Coppola (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`): Nicolás decidió esperar.
- No leas el veredicto del A/B de D25.
- Español de Chile, sin guiones largos ni medios. Todo número con script, salida cruda, denominador y ventana.
- Todo en tu rama y en un PR borrador; el código de producción que haga falta después va en otro PR, con tag defensivo
  y el «sí» de Nicolás.

## Entregable

`docs/AUDIT_S158_R2.md`: para cada afirmación del punto 2, tu veredicto propio y, al final, la comparación con la
primera ronda (dónde coinciden, dónde no y por qué); el resultado del segundo oráculo; el informe del meta-auditor; el
resultado de la prueba con gránulos (o por qué no se pudo); las marcas hechas; y la guía de revisión visual. Cierra con
una respuesta directa a la pregunta de Nicolás: con lo que se sabe ahora, ¿qué falta para la paridad con MIROVA?
