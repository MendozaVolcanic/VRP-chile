# Caminos por los que cada afirmación del frente D podría estar mal

Escrito antes de abrir ningún archivo citado. Verificador VD, auditoría S179. No se edita después de sellarlo.

## 551. B1 enciende la posición «radiante»; la evidencia que lo autoriza es de «cercano»; con el predicado del tablero la vía calla 5 de 72 protegidas VIIRS 375 que K publica

- La vara es otra: «B1» puede no encender nada en producción (puede ser un flag que nadie lee, o un perfil distinto del operacional). Comprobar desde dónde se lee el flag (A89: desde `pipeline.profile`, no del YAML) y si el PR que lo enciende (#974 o #983) está mergeado o fuera de main.
- La posición «radiante» y «cercano» pueden ser dos nombres de la misma regla, o «cercano» puede ser un alias en un lado y otra cosa en otro. Leer las dos definiciones en código.
- La retrospectiva (leer_retro.py l. 1274) puede no fijar la posición «cercano»: la línea citada puede ser un valor por defecto que luego se sobrescribe por argumento o por el manifiesto de la corrida.
- Producción puede no escribir «radiante»: el valor puede venir de otro lado (perfil, variable de entorno del workflow).
- El «5 de 72» puede salir de una reconstrucción del predicado a mano y no de `banco_paridad.py::correr_node` sobre `frontend/index.html` de 438a60a1e.
- El denominador 72 puede no ser «protegidas» según `etiquetar` con D-9 y lectura A (≥ 1 MW), o la referencia usada no es la copia congelada que vale para la retrospectiva (CONS 811c4c07, OCR 01c9478d).
- «Que K publica» puede ser falso en alguna de las 5: K podría tampoco publicarlas, o la vía podría publicarlas en otra pasada pareada dentro de TOL_S.
- La ventana puede no contener el régimen (ventana que cruza #535 u otro cambio de régimen, A104).
- El script del auditor puede leer datos de una rama distinta a la que dice, o de la copia local atrasada.
- El instrumento mide «cercano» en vez de «radiante» (es decir, el auditor puede haber medido lo mismo que la retrospectiva y no la diferencia).

## 552. El paso MODIS del plan de reemplazo deja ciega la vigilancia de la guardia K de MODIS (nulo 167 a 0 pares, VERDE a VIGILANCIA_CIEGA)

- El plan de reemplazo puede no tocar los archivos que lee la vigilancia (otro `data_subdir`, otro campo).
- La vigilancia puede leer de la rama de la guardia (guardia K en su propio subdirectorio) y no del histórico de producción; si es así, reemplazar la historia de producción no la deja ciega.
- El «nulo 167» puede contar pares que el reemplazo no afecta (por ejemplo, records posteriores a la vía), y el cero puede salir de una simulación mal hecha del reemplazo y no del efecto real.
- «VIGILANCIA_CIEGA» puede ser un estado que ya existía antes del reemplazo (el instrumento ya estaba ciego) o el script puede devolverlo también por falta de datos locales (SIN DATO tomado como FALLA).
- El cero puede venir de que el script del auditor no encontró los archivos (instrumento muerto), no del reemplazo.
- El plan de reemplazo puede preservar los campos de K (por ejemplo, guarda el detector anterior en campos `k_*`) y la vigilancia los lee.
- Las líneas citadas pueden no corresponder a la lectura del nulo en 438a60a1e (copia local atrasada).

## 553. El paso VIIRS del plan de reemplazo corre el encendido de la regla sellada al 2026-11-08 18:04 UTC y borra el nulo de la guardia K de VIIRS (223 a 0 pares)

- La regla sellada puede anclar el encendido a otra cosa (fecha de merge, primer record con la vía) y no a la fecha de los datos; si el ancla no es un campo que el reemplazo cambia, el encendido no se corre.
- La regla puede estar en un borrador que no es la versión sellada (REGLA_..._BORRADOR.md); la sellada puede estar en otro archivo o commit.
- 2026-11-08 18:04 UTC puede no ser lo que da la regla con la historia reemplazada; puede ser la hora de otra cosa.
- La vigilancia VIIRS puede no ser `scripts/vigilancia_guardia_modis.py` (puede haber un script propio de VIIRS) y las l. 124-146 pueden ser lógica MODIS.
- El nulo 223 a 0 puede ser artefacto de la simulación (mismo riesgo que en 552).
- El plan de reemplazo puede no incluir VIIRS (puede ser sólo MODIS) o excluir explícitamente la ventana de la guardia.

## 554. El plan de reemplazo no cuenta qué deja de publicarse y se aplicaría sobre meses sin lectura contra MIROVA (P4)

- El plan (62ccb8830, fuera de main) puede tener una sección que sí cuenta lo que deja de publicarse, en otra línea o en un anexo; las l. 6-7 y 272-274 pueden no ser todo.
- «Sin lectura contra MIROVA» puede ser falso si existe una retrospectiva de la vía sobre esos meses (la retrospectiva S172 o la sombra) que el plan cita.
- MISSION.md l. 113 puede no exigir esa lectura, o exigirla sólo para cambios de detector y no para reprocesos.
- El plan puede ser un borrador sin decisión pendiente; si nadie va a aplicarlo sin otra compuerta, la gravedad baja.
- La versión del plan puede haber cambiado después de 62ccb8830 (otra rama, otro PR).

## DEC-1. «Sí, prepáralo» del 2026-11-02 00:30, juzgada APLICADA DISTINTO

- La frase puede no estar en la bitácora con esa hora o puede decir otra cosa (preparar no es ejecutar).
- El plan de los 34 puede no tener compuertas, o las compuertas pueden ser para el encendido operacional y no para una página preliminar.
- Lo hecho después puede ser un paso permitido por el plan (por ejemplo, la sombra previa misma).
- La línea 1621 puede pertenecer a otra entrada.

## DEC-7. Publicación de la página preliminar de los 34 (#972) sin frase de Nicolás citada, juzgada SIN RESPALDO

- Puede haber una frase de Nicolás en el PR #972, en la bitácora en otra línea, o en un bloque de arranque, que el auditor no encontró (el cero de un grep, A89/S127).
- La página puede no estar enlazada desde el tablero operacional (no visible para el operador), lo que baja la gravedad.
- El PR #972 puede no estar mergeado; la página puede no estar publicada.
- La regla «el loop no pregunta cada paso» (S168) puede cubrir pasos de publicación preliminar; leer qué exige.

## DEC-14. «Retro primero» del 2026-11-10 01:17, juzgada DEBILITADA (la condición se cumplió con «cercano» y producción escribe «radiante»)

- Mismos caminos que 551 sobre la posición.
- La frase de Nicolás puede no condicionar el encendido a la posición, o puede aceptar explícitamente la retrospectiva tal como estaba.
- La hora puede ser de otra frase.

## DEC-17. Orden de encendido del bloque S179 (3 noches de guardia, #974, #983, reemplazo después), juzgado SIN RESPALDO tal como está escrito

- Puede haber una frase de Nicolás que fija ese orden (por ejemplo «mergea #974 luego #983») en la bitácora o en un PR; la memoria S178 menciona «encendido espera 3 noches de guardia y "mergea #974" luego "#983"».
- «Tal como está escrito» puede referirse a un detalle (reemplazo después) que sí carece de frase, y el resto sí la tiene: posible CONFIRMADO EN PARTE.
- El bloque S179 en 0472cd95e puede diferir del de otra rama.

## Comunes a todas

- Copia local atrasada: usar las instantáneas en D:\vrp-trabajo\temporales\s179-audit\main (438a60a1e) y \loop (0472cd95e), comprobar su commit.
- Un número del auditor sin script que lo reproduzca no se cuenta.
- La vara de «decisión de Nicolás»: frase suya con hora en bitácora o PR; reenviada por otra sesión no cuenta.

---
Sellado: sha256 del contenido anterior a este pie = 5dcad87e7f540af9613bff9d97b443264915373a06f3f08f96d310a09c27d5fe ; hora del servidor (header Date de api.github.com) = Wed, 11 Nov 2026 01:59:02 GMT
