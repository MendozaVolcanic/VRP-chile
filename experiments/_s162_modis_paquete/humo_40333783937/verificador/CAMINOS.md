# Caminos por los que el humo podria pasar por la razon equivocada

Escrito ANTES de mirar los datos (solo conocia la lista de artefactos y la salida resumida del evaluador).

1. El port no corrio y npix 0 se lee como "no publica": las 23 filas serian "ok" con npix=0, vrp=0 y grillas vacias o constantes. Se mira: npix/vrp por fila, que las grillas .npz tengan variacion real (no ceros), tamano de log del probe.
2. Run verde sin datos (tee sin pipefail, A141): el job reporta exito con el script caido. Se mira duracion, contenido de probe_0.log, recorridos_parte00.jsonl vacio (0 bytes: es esperado o delata un paso que no corrio?), recorrer_0.log.
3. K comparado contra si mismo: "k_produccion OK" y "S-1 n_ok 22" podrian ser identidad trivial (K calculado desde la misma grilla y comparado con el K del mismo jsonl). Se compara K contra data/ del repo (record persistido), no contra otro campo del jsonl.
4. Las 4 pasadas comunes con S159 no son las de S159: el evaluador dice "M MEJORA n 4" pero se cruza por indice o por clave equivocada. Se cruzan indices/fechas contra referencia_s159.
5. El contador INDECIDIBLE falla por otro motivo (p. ej. n negativos = 17 por un defecto de etiquetado, o un bug de clasificacion que oculta negativos) y no por tamano de muestra legitimo. Se recalcula el conteo de clases desde la referencia congelada.
6. Los logs son de otra corrida / otro commit: procedencia_0.txt y los logs de prueba podrian citar otro SHA o run. Se coteja SHA, run id, fechas.
7. Manifiesto usado distinto del del tag (el blob c3bc1c3... vs git ls-tree del tag); o el tag anotado apunta a otro commit que el worktree.
8. Bateria 37/37 "contra el real" pero el "vacio" 0/37 podria ser por un vacio que falla por otra razon (p. ej. falta de archivo, no por la logica); arnes 6/6 que pruebe algo trivial.
9. Los 5 granulos son de pasadas faciles (todas "igual" y sin discrepancia): el humo seria incapaz de detectar un defecto. Se mira qué pruebas pueden fallar y si hay variabilidad.
10. Pasos del job omitidos (continue-on-error, if: always()) que dejan el job verde con pasos fallidos.
11. VETADO en PM-geo5 y PM-b21 (P1 VETADO 1): ¿es un defecto o esperado? Afecta a la afirmacion 5 (INDECIDIBLE solo por cobertura y contador).
