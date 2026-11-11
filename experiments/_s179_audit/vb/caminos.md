# Caminos por los que cada afirmación del frente B podría estar mal

Escrito antes de abrir ningún archivo citado (sólo leí el encargo VB.txt). Base: código main 438a60a1e,
documentos del loop 0472cd95e. Lo que aprenda después va al informe, no aquí.

## Caminos generales (valen para todas)

- G1. La copia local está atrasada: la instantánea D:\vrp-trabajo\temporales\s179-audit\main\ no es 438a60a1e,
  o el auditor leyó otro commit. Comprobar `git rev-parse` y comparar contra `git show 438a60a1e:<ruta>`.
- G2. Las líneas citadas drifteron: el archivo:línea apunta a otro contenido en 438a60a1e.
- G3. La vara es otra: el auditor juzga contra un borrador de regla cuando la sellada es otra versión (otro commit
  o rama), o contra un documento de loop/activo distinto de 0472cd95e.
- G4. El número viene transcrito a mano y no de un script; o el script mide otra cosa (otro sensor, otro perfil,
  otra ventana, otro predicado que no es el del tablero).
- G5. El denominador o la ventana no contienen el fenómeno (por ejemplo semanas sin actividad, volcanes fuera de cron).

## 451 (plazo de la reversión, 29 protegidas, 11 días, sólo Chillán)

- El «29» puede ser otro conteo (alertas totales, no protegidas; o protegidas de todos los sensores).
- La tasa de protegidas por día puede venir de una ventana con Chillán en erupción que no representa el futuro, o
  al revés: el plazo puede contarse en noches y no en días.
- vigilancia_guardia_modis.py puede no ser el script que aplica el plazo para VIIRS (puede haber un script
  vigilancia_guardia_viirs.py con su propia lógica de ventana).
- El plazo puede no «agotarse»: puede que la regla lo defina como ventana deslizante, no como presupuesto.

## 452 (cota (i) de VIIRS 375 calibrada 4,9 veces por debajo)

- «3 de 36 en 7,79 días» puede mezclar protegidas con alertas; la cota puede contar otra unidad (pasadas, noches).
- La línea 73 puede no ser la cota (i) o la cota puede leerse con otro umbral desde un YAML.
- La semana de la sombra puede no ser comparable (Chillán en erupción, régimen distinto). La razón 4,9 podría
  invertirse si la cota es «más de 14 en N días» con N distinto de 7,79.
- La sombra puede no ser la vía real (otro perfil, otro código).

## 453 (falsa alarma 4,5 a 5,9 % vs 12 a 28 %; la (ii) de V750 nace de un caso)

- El 12 a 28 % depende de qué incertidumbre se modele (intervalo de la tasa, prior); otro método da otro número.
- Las salidas citadas pueden ya declarar la incertidumbre y el auditor no lo vio.
- «Nace de un caso» puede ser falso si la cota (ii) viene de una distribución, no de un solo evento.

## 454 / DEC-15 (condiciones previas al merge no hechas; paso de nrt.yml movido)

- Las condiciones pueden estar hechas en una rama o PR fuera de main (en #974/#983), que el auditor no miró.
- nrt.yml:374-384 puede ya tener el paso, con otro nombre.
- LOOP_OBJETIVOS.md:645 puede tener una frase de Nicolás que autoriza el cambio (entonces habría decisión).
- La regla sellada puede decir «antes de encender» y no «antes del merge».

## 455 (ninguna protegida perdida descansa en Láscar y Chillán; seis volcanes sin ninguna)

- lectura.json vive en una rama (ff8a39972), no en main: puede haber una versión posterior.
- «Sin ninguna protegida» puede deberse a que no hubo actividad (correcto) o a que el instrumento no las cuenta.
- El conteo por volcán puede estar en otro campo del JSON que el auditor no leyó.

## 456 (magnitud de VIIRS sube 1,3 a 3,2 veces y el tablero sólo marca una línea)

- El 1,3 a 3,2 puede no estar medido sobre lo que el tablero publica (predicado de node), sino sobre vrp crudo.
- cambio_detector.js puede marcar algo más que una línea (nota, tooltip, banda).
- El spec de encendido puede declarar el salto como aceptado (decisión) y entonces no es defecto.

## 457 (revertir B1 tras B2 choca en 9 archivos, sin ensayo)

- Los «9 archivos» pueden ser archivos tocados por ambos, no conflictos reales de `git revert`.
- Puede existir un ensayo en una rama o en el cuerpo del PR.
- La regla l. 71 puede prescribir revertir ambos juntos (entonces el choque no aplica).

## 458 (#974 y #983 chocan con main en la ficha; CI anterior; numeración doble)

- `git merge-tree` con base equivocada da conflictos falsos; con los SHA de cabeza viejos da conflictos que el
  rebase ya resolvió.
- El CI puede haberse re-corrido después de #982/#984 (insumos pueden estar viejos).
- «Numeración de dos maneras» puede ser estilo y no error.

## 460 (la vía no escribe record en 4,9 % de pasadas V375; alerta débil no entra a cotas)

- 11 de 223 puede contar pasadas sin datos válidos (nubes, fuera de cobertura) que tampoco K escribe.
- La cota puede leer otra fuente (por ejemplo records de K en la guardia) que sí ve esa pasada.
- process_viirs.py:766-786 puede escribir un record por otro camino (fallback a K).

## 461 (revertir el mismo día UTC vs guardia corriendo tras medianoche, n 2)

- n=2 es muy poco; el cron declarado puede caer antes de medianoche y los atrasos ser de Actions.
- La regla l. 68 puede decir «día de Chile» o «al día siguiente».

## 463 (lector sellado de V375-E no está en main, nadie lo corre, pierde su brazo K)

- El lector puede estar en main con otro nombre o en loop/activo.
- Puede correrlo un workflow de vigilancia.
- «Pierde su brazo K» depende de si la guardia K de VIIRS sigue produciendo records K tras B1.

## DEC-6 (D2 V750, cota (ii) más de 2 juzgada DEBILITADA)

- «Debilitada» es un juicio; la regla puede justificar el 2 en otro lado.
- Las cotas implementadas en vigilancia_guardia_viirs.py pueden diferir de la regla (12 vs otro).

## DEC-14 (quita los 3 avisos, aplicada más ancha)

- Puede que Nicolás haya pedido algo más ancho después (otra frase).
- cambio_detector.js puede quitar sólo 3 avisos y el «más ancho» ser otra cosa (otro archivo).

## DEC-19 (veredicto retrospectiva V750 sin frase de Nicolás)

- La frase puede estar en un PR (comentario) o en la bitácora con otro nombre, fuera de LOOP_OBJETIVOS.md.
- La fila 4 puede no requerir decisión de Nicolás según la propia regla.

---
sha256 del contenido anterior a esta línea: 707c836b7a3ca68931d19eb285043710ea09554cc8701e4be63b8141df64df73
Hora del servidor al sellar: Date: Wed, 11 Nov 2026 01:54:31 GMT
