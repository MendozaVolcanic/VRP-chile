# Caminos por los que los cuatro cambios v3 -> v3.1 podrian estar mal

Hora del servidor al escribir: Mon, 26 Oct 2026 14:32:53 GMT (gh api -i). Commit medido: 9700e4e0b5e543563d5ea5a2167202696b33c198.

## Cambio 1: reclasificar FALSO_POSITIVO diurno de la tabla a RUTINA con otra_como_negativo=True
- C1a. La reclasificacion toca tambien pasadas nocturnas (el filtro "diurno" no es diurno de verdad, o no mira el campo correcto).
- C1b. Toca el sensor equivocado (MODIS) o todos los sensores, no solo VIIRS.
- C1c. Se aplica tambien cuando otra_como_negativo=False, o al veredicto principal (variante A) y no solo a la variante.
- C1d. `_replace` (namedtuple) cambia mas que el estado: pierde/pisa otros campos (clase, vrp, distancia, fuente).
- C1e. Reclasifica FALSO_POSITIVO de OCR (no de la tabla), o FALSO_POSITIVO nocturnos que deben seguir siendo "otra".
- C1f. Se reclasifica antes de armar la tabla, pero cobertura/clase_p2 usan la lista original (dos poblaciones distintas).
- C1g. Pasadas con alerta y FP en la misma pasada: el FP reclasificado pierde la alerta (o la crea).
- C1h. Mutaciones del evaluador comun mutan el objeto compartido (efecto lateral sobre la lista del llamador).
## Cambio 2: placebo c del I6 cuenta GANA aparte, MAX_GANA_C = 4 (falla con >=5 de 40)
- C2a. El conteo de GANA no es el que juzga la regla (el placebo cuenta GANA de otra clase / de otra cara).
- C2b. El umbral 4 no sale de la binomial que dice el texto (n=40, p=?, nivel?).
- C2c. Falla con 5 o mas: off-by-one (> vs >=).
- C2d. El placebo c puede dar mas de 40 pares o menos de 40 (denominador).
- C2e. La compuerta ahora puede fallar por GANA pero el texto del I6 y el despacho dicen otra cosa.
- C2f. El placebo cuenta GANA aparte pero tambien deja pasar PIERDE (se relajo algo que antes frenaba).
## Cambio 3: textos del §5.1 (iii), §6.3, §6.4, §8, §14
- C3a. Texto contradice codigo (cifras, nombres de funcion, constantes).
- C3b. Texto contradice otra seccion no actualizada (§6.1, §6.2, §7, I6).
- C3c. Cifras de binomial/probabilidad mal.
## Cambio 4: sello 22 -> 29 archivos; git diff del §8 recorre todas las rutas
- C4a. El sello deja fuera un archivo que el evaluador lee (evaluador_comun.py, clase_mirova.py, banco_paridad, perfiles, workflow...).
- C4b. Algun sha256 no coincide con el blob en e5042a2e.
- C4c. El comando del §8 no funciona tal como esta escrito (rutas, comillas, sha256sum -c, formato).
- C4d. El conteo "29" no coincide con la lista real / sha256sum de archivos duplicados.
## Pruebas nuevas y mutaciones M57/M58/M59
- C5a. La prueba nueva pasa por la razon equivocada (p. ej. pasaria igual sin el cambio).
- C5b. Las mutaciones M57-M59 no son atrapadas por una asercion sino por una caida (A152).
- C5c. La suite completa no pasa.
