# Adenda del pre-registro del A/B diurno de VIIRS: repetirlo sobre K (tarea 1.32, D-10, issue #813)

Estado: **borrador, espera el verificador con contexto limpio y el sello de Nicolás** (2026-10-18). Nada de esta adenda
se despacha sin su «sí» y el candado `preregistro_aprobado=si` del workflow. Complementa a `PREREGISTRO.md`: todo lo que
esta adenda no cambia rige tal como está allí (fenómeno, ventanas, métricas, nulo, criterio, candado, desviaciones).

## 1. Por qué se repite

El A/B W2 a W6 corrió sobre el detector anterior (C0) y dio **NO ADOPTAR**, confirmado por verificador limpio
(`salidas/W2_W6_s154/evaluar_salida.txt` y `salidas/W2_W6_s154/verificador/INFORME.md`). Ese veredicto **no se traslada a
K**, el detector de la réplica desde el 2026-10-18 09:57:30 UTC (#850), porque de día el Test 1 integrado, que K quitó,
explica buena parte de lo que se midió (hallazgo H4 del verificador):

- dispara en 2.000 de las 2.077 publicaciones de VIIRS 375 en negativos diurnos limpios, y 987 de ellas vienen sólo de
  `test1_roi` (VIIRS 750: 389 de 731);
- 11 de las 22 alertas protegidas que el brazo diurno recupera en VIIRS 375 salen sólo del Test 1, incluidas las 8 de W2;
- el contrafactual que cuenta sólo los records `ctx_cluster` (sin aplicar la conectiva `max`) deja G1 W3 a W6
  cumpliendo (P = 0,001) y G2 fallando (1.142 publicaciones contra 20 permitidas en VIIRS 375; 357 contra 6 en VIIRS
  750). Con `max` el corte podría ser mucho mayor (SOSPECHA del verificador, no medida).

Si sobre K G1 cumple y G2 no, la regla del §6 da **DECIDE NICOLÁS CON M4**, no NO ADOPTAR. Por eso hay que medirlo.

## 2. Qué cambia (y nada más)

1. **Brazos.** Control `_s154_ab_diurno_k_control` (la réplica K tal cual) y diurno `_s154_ab_diurno_k_on` (K más
   `enable_daytime_viirs`). `tests/test_perfiles_diurno_k_s154.py` comprueba, resolviendo todas las constantes de
   `pipeline.profile`, que el control es idéntico a producción salvo nombre y directorio y que el diurno difiere sólo en
   la palanca (#856).
2. **Cableado.** El evaluador corre con `--brazos _s154_ab_diurno_k_control,_s154_ab_diurno_k_on --base k`: además de lo
   que ya exigía, cada log tiene que mostrar los tres flags de K (`ENABLE_TEST1_PATH` falso, `ENABLE_TESTS_23_PROSE_BRANCH`
   verdadero, `ENABLE_MODIS_B22_PRIMARY` verdadero). Un brazo que corrió con el Test 1 encendido sale como cableado roto
   y el A/B no se decide (arnés, comprobación `base_k`).
3. **El evaluador ya trae dos arreglos del verificador de W2 a W6**: el aviso de saturación A114 por sensor (#854) y el
   nulo barajado independiente del orden de recorrido (#855). Ninguno cambia el criterio.

Ventanas, métricas (M1 a M5), poblaciones, referencia congelada (el evaluador sigue exigiendo que la base de MIROVA
reproduzca `sustrato.json`), G2 y G3: **sin cambio**. Las ventanas siguen partidas en mitades (W2a/W2b ... W6a/W6b, como
en la corrida sobre C0). W1 se informa aparte, igual que antes.

## 3. Una decisión aparte para el sello: el cuantil del nulo en G1

El nulo de G1 es discreto. En la corrida sobre C0, con el muestreo de 10.000 barajados el p95 de W2 a W6 salió +0,2446,
y el cuantil exacto (convolución de hipergeométricas, calculado por el verificador) es +0,2760: el percentil cae en un
salto de la distribución. No cambió ese veredicto (D = +0,18), pero **en W3 a W6 D quedó exactamente en el p95**
(+0,2303 contra +0,2303, P(nulo ≥ D) = 0,106 y P(nulo > D) = 0,025 según el verificador). Con un empate, el resultado
lo decide el muestreo, no los datos.

- **Opción A (recomendada): cuantil exacto.** G1 cumple si P(nulo ≥ D) < 0,05, con la distribución exacta del nulo
  (suma por estrato de hipergeométricas, por convolución). Se implementa en el evaluador ANTES de despachar, con su
  prueba en el arnés (el muestreo actual tiene que coincidir con el exacto lejos de los saltos, y el exacto tiene que
  dar el valor del verificador en W2 a W6 sobre C0). Cambia el método del §5, por eso va al sello.
- **Opción B: dejarlo como está** (muestreo de 10.000, ahora determinista por #855) y declarar los empates como tales en
  el informe.

## 4. Despacho

- **Desde un tag fijo** (`s154-diurno-k-codigo`, puesto sobre `main` después del merge de esta adenda y, si se aprueba,
  del arreglo de la opción A), nunca desde `main` a secas: entre ventanas puede entrar código y dos ventanas medirían dos
  pipelines (A108; S152, desempates que dependen de la CPU).
- `brazos=["_s154_ab_diurno_k_control","_s154_ab_diurno_k_on"]`, `control=_s154_ab_diurno_k_control`, las diez medias
  ventanas de la corrida sobre C0, una por despacho y la siguiente recién cuando la anterior empezó (grupo `s151-ab-diurno`,
  un solo pendiente).
- **Después de que termine el reproceso histórico con K** (tarea 1.24, run 39125546355, de a 8 jobs): con el NRT (11) y
  el histórico (8) el tope de 20 jobs concurrentes queda sin margen.
- **Costo medido** sobre la corrida C0 (runs 38987988455, 39041204976, 39097155412): por media ventana y volcán, el
  control tarda unos 15 a 24 min y el brazo diurno unos 40 a 58 (máximo 66). Unas 15 h de runner por media ventana, del
  orden de **150 h** en total y **2 a 3 días de reloj** con `max-parallel: 3`. Sin el Test 1 puede cambiar; no está medido.
- Cobertura: leer `cobertura.txt` de cada corrida antes de mirar resultados; si falta una noche o un volcán, repetir ese
  job con el mismo tag y unir con `experiments/_s153_fk_v2/unir_ventana.py` (D-13).

## 5. Lo que esta adenda no decide

- Encender la rama diurna en producción: aunque saliera ADOPTAR, va por su propio ciclo (tag defensivo, R2 por píxel,
  verificador independiente, sí de Nicolás; reglas S33 y A45, §6 y §8 del pre-registro).
- El resultado sobre C0 no se reabre: queda como medido, con su salvedad.

## 6. Preguntas para el verificador de esta adenda

1. ¿Alguna diferencia entre los perfiles K y producción que la prueba de constantes no vea (algo que no viva en
   `pipeline.profile`, por ejemplo `volcanoes.yaml` o el código del commit)?
2. ¿El evaluador con `--base k` deja algún camino en que un brazo C0 pase el cableado?
3. ¿Las ventanas de antes de #850 son válidas para un A/B sobre K? (Los dos brazos son K y corren el mismo código; la
   referencia de MIROVA no cambia con nuestro detector.)
4. ¿La opción A está bien planteada como regla, y la prueba propuesta alcanza para confiar en el cálculo exacto?
