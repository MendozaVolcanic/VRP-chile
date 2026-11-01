# Caminos por los que cada afirmacion de la segunda vuelta podria estar mal (escrito ANTES de abrir ningun archivo citado)

Verificador D-42, vuelta 2. Worktree C:\vrp-trabajo\s159-evaluador, commit 452956cf8 (arbol limpio). Diff a verificar: 981cceda7..452956cf8.
Hora del servidor al empezar: Thu, 22 Oct 2026 15:30:35 GMT. Lo unico que mire: `git diff --stat` (nombres) y `git log --oneline -4`.
No abro el README del implementador hasta tener escritos los veredictos.

## Afirmacion 1: V42-02 cerrado (prueba nueva de contar; atrapa m07; corredor 30 de 30, control 75)

- La prueba nueva puede ejercitar `decidir_p2_bloques` y no `contar`: leer que llama a `X.contar` y mira `ver["P2|..."]` y `global_ventana` sobre ese `ver`.
- El sintetico «3 noches x 4 pasadas donde solo D se equivoca» puede no producir una calibracion FALLIDA (si el nulo diera falsos por cola bajo 5 % la prueba no distinguiria calibrado de sin calibrar): con 3 bloques del mismo signo los falsos son 12,5 % por cola, pero hay que comprobar que `contar` reciba contribuciones con bloques distintos (3 noches, no 1) y que las etiquetas (`lab`, `prot`) lleven a 12 discordantes todas de D.
- La prueba podria exigir INDECIDIBLE en `ver` pero pasar aunque m07 este activo si el resultado sin calibrar tambien fuera INDECIDIBLE (no lo es: seria PIERDE) o si la asercion mirara `det` en vez de `ver`.
- «atrapa m07 por asercion»: comprobar re-corriendo mi m07 contra las pruebas de hoy, y que la falla sea `AssertionError`, no otra excepcion.
- «30 de 30, control 75»: el corredor pudo agregar 2 mutaciones que ya atrapaba; mirar cuales son las 2 nuevas y si una es m07 tal cual (misma edicion). El control 75 = 73 + 2 pruebas nuevas: contar las pruebas nuevas.
- Copia local atrasada: el worktree esta en 452956cf8 pero el remoto podria tener mas; no es mi eje (git no se toca); lo anoto.

## Afirmacion 2: V42-04 cerrado (n_sorteos y semilla desde lo que calibrar_p2 uso; None si no corre)

- Pueden salir de los PARAMETROS de la llamada (lo que `decidir_p2_bloques` paso) y no de lo que `calibrar_p2` uso de verdad: si `calibrar_p2` devuelve lo que uso, bien; si `decidir_p2_bloques` escribe sus propias variables, un cambio dentro de `calibrar_p2` (otro default) seguiria sin verse. Leer de donde sale cada valor.
- «None si no corre»: ver que los dos caminos que no calibran (controles caidos y SIN SUSTRATO) dejen None y que `imprimir` no reviente con None (`%d` de un None).
- La prueba del oraculo compara `det["n_sorteos"] == N_SORTEOS`: con el cambio sigue valiendo solo si el valor efectivo es 1.000; la mutacion c2b (200 en la llamada) ahora deberia atraparse tambien por `n_sorteos`.
- Otros consumidores de `n_sorteos`/`semilla_calibracion` (imprimir, placebo_1pct, resumir) pueden asumir int y recibir None.

## Afirmacion 3: rojas 26 de 39 contra 5f986a209; la de V42-04 roja contra b57ecfe62

- 39 = 37 + 2 nuevas; las dos nuevas tienen que estar entre las 26 rojas contra 5f986a209 (si una pasa sobre el arbol viejo, no mide nada).
- «roja contra b57ecfe62»: el script tiene que haber sacado el evaluador de b57ecfe62 por `git show`, no una copia editada; y la falla tiene que ser por asercion (no AttributeError).
- Las salidas pudieron producirse con un borrador de la prueba (V29-02): re-corro con las pruebas commiteadas.

## Afirmacion 4: suite 2.417 y probar 31 de 31 con el arbol quieto

- 2.417 = 2.415 + 2: cuadra solo si las pruebas nuevas son 2 y ninguna se salta.
- «arbol quieto»: mirar status_antes_v42/despues_v42 (hora) contra las duraciones (mutaciones ~50 min + probar ~35 + suite ~6): si no caben en la ventana, corrieron en paralelo otra vez; los sha vigilan solo 7 archivos.
- Re-corro la suite sola al final y probar si hay tiempo.

## Afirmacion 5: V42-01, curva 1, 5, 10, 20 % y juicio del placebo

- «calibracion corrida en la mayoria de las celdas»: contar yo las celdas con `falsos_gana` no None por punto, ventana, regla y sensor (v05 adaptado).
- «GANA calibrada 0 de 20»: en celdas donde la calibracion corrio; y ver si algun GANA sin calibrar aparece (si el sin calibrar tampoco da GANA nunca, la calibracion no esta siendo probada contra un GANA).
- «PIERDE 75 a 100 % en VIIRS 375 con K»: por construccion. Apagar publicaciones de K al azar: cada publicacion de K es o alerta (apagarla = error nuevo de D, +1) o negativo limpio (apagarla = error que D deja de cometer, -1) u otra (sin aporte). Si en K las publicaciones son mayormente alertas (K es K porque ya publica poco en negativos limpios: la linea base post #535 tiene ~2,5 a 3,7 % de negativos limpios publicados en VIIRS 375), el neto esperado por pasada apagada es positivo y el placebo SIEMPRE perjudica a D: el control no puede fallar con K. Medirlo: fraccion de publicaciones de K en la ventana que son negativos limpios contra alertas (desde los JSONL: neto y n por semilla ya lo dicen: neto/n cerca de +1 => casi todas alertas).
- Lo que S160 temia («P2 premia publicar menos a ciegas») se dispara solo si entre lo apagado hay mas negativos limpios que alertas bajo 1 MW; con K eso no pasa por la composicion de las publicaciones, no por la regla. El placebo que SI podria fallar: apagar solo publicaciones en negativos limpios (D = K menos ruido verdadero: cualquier regla que mida errores lo premiara, y la pregunta pasa a ser si debe premiarlo), o apagar al azar sobre un brazo base que publique muchos negativos limpios (C0 o un K degradado), o el placebo complementario (encender publicaciones al azar en pasadas que K no publica).
- Los brazos «desde produccion»: ventana V1 tipo 2026-09-18 a 2026-10-18 (K real) y V2 2026-04-01 a 2026-06-12 (produccion de esa fecha NO es K: es el detector anterior o el historico reprocesado con K, segun `sustrato_k.unir_k`); anotar que sustrato tiene cada ventana.
- Semillas 20 por punto: regla de 3 => 0/20 no excluye 14 %.

## Riesgos del instrumento propio

- Copias para mutar en experiments/_mutv42b_<id>/, borradas; no editar nada del repo mientras corra pytest; pruebas commiteadas, no borradores.
- No correr evaluar_d25 sobre datos del A/B; solo sinteticos o produccion.

---
sha256 del contenido anterior a esta linea (`head -n -4 caminos.md | sha256sum`): fdaee9ebd2a0be25b6f20a9c5f4fde6fee3f8a8b04e17d33da57011e1be05ce7
Hora del servidor al cerrar caminos.md: Date: Thu, 22 Oct 2026 15:31:23 GMT
