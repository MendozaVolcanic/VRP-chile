# Caminos por los que cada afirmación podría estar mal (escrito ANTES de abrir ningún artefacto citado)

Verificador con contexto limpio del resultado del A/B MxD03 (MOD-B, S162). Recibí sólo título,
dónde mirar y la tarea R1 a R4. No he abierto evaluar_mxd03_salida.txt, resultado_mxd03.json,
vara_resultado.json, INFORME.md, los jsonl de tandas ni el código del evaluador. Lo único que vi
hasta ahora: el listado de nombres de archivo de las carpetas, el commit del worktree
(1aaaf709c, rama s162-mxd03-codigo) y la hora del servidor.

## R1. Censo completo y sellado (5.465 de 5.465, 24 partes, sin errores ni duplicados; K = data/, K2 = K)

1. **El instrumento mide otra cosa**: «5.465 de 5.465» puede ser el conteo de líneas de los jsonl,
   no de pasadas únicas de la población sellada. Si una pasada falta y otra está duplicada, el total
   coincide y el censo no está completo. Hay que cruzar clave por clave (volcán + hora UTC + plataforma)
   contra poblacion.json, en las dos direcciones.
2. **La población no es la sellada**: poblacion.json del worktree puede no ser la del commit del tag
   (ffbb36248). El evaluador «regenera la población con git merge-base contra origin/main»: si el
   worktree tiene data/ distinto del tag, la población regenerada puede diferir de la que corrieron
   las tandas. Comparar sha256 de poblacion.json contra MANIFIESTO.json y contra `git show ffbb36248:...`.
3. **Las tandas son de otro commit**: cada jsonl debería declarar el commit del arnés; si alguna
   parte corrió con otro commit (t1, t2, t3 son tres tandas distintas), la unión mezcla dos detectores
   (A104). Revisar el campo de commit de cada registro y de cada parte.
4. **«Sin errores» no es «sin huecos»**: un registro puede tener status ok y un brazo vacío (p. ej.
   MxD03 no bajado y el arnés devolviendo None en vez de error). Contar por brazo los records con
   contenido real, no sólo el status.
5. **K igual a data/ se comprobó contra la copia local atrasada**: data/ del worktree puede no ser el
   data/ de origin/main 80b819828 ni el del tag. «K = data/» hay que leerlo contra el sha del record
   de data/ que la tanda declara, no contra data/ de hoy.
6. **K2 igual a K es trivial por construcción**: si K2 es «volver a correr K con el mismo código», la
   igualdad sólo prueba determinismo del arnés, no que K reproduce producción. Mirar qué es K2
   exactamente y si usa la misma geometría que K (si ambos interpolan, no es control de nada).
7. **Igualdad comparada en campos poco sensibles**: «K2 = K en todas» puede comparar sólo `publica`
   (booleano) y no la magnitud ni la posición del cúmulo. Un empate booleano con magnitudes
   distintas sería ruido no detectado.
8. **Duplicados escondidos entre tandas**: si una parte corrió en t1 y se repitió en t2, el jsonl
   «sin humo» puede contener dos registros de la misma pasada con resultados distintos; la unión
   puede quedarse con el primero o el último sin decirlo. Contar claves repetidas entre partes.
9. **La copia de tandas en D:\temporales no es la que leyó el evaluador**: el autor pudo evaluar
   sobre otra ruta. sha256 de cada jsonl que yo copie contra lo que el resultado_mxd03.json declare.
10. **El recuento 24 partes**: 24 partes pueden ser 24 archivos aunque una parte esté truncada
    (log con fin abrupto). Mirar el final de cada log y el conteo esperado por parte.

## R2. Los 13 controles en verde

11. **Control que no puede fallar**: un control cuyo nulo no se midió (A110, A116). Para cada uno,
    preguntar: ¿qué input lo pondría en rojo? Si no existe tal input, es decoración. Candidatos:
    «predicado» (si compara el predicado de node contra sí mismo), «cableado» (si sólo comprueba
    que un flag existe y no que llega al cálculo), «arnés», «vara cruda».
12. **Geometría 2,581 km**: el número puede venir del mismo arnés que se audita (circular), o
    de un caso único. Comprobar de dónde sale, y si el MxD03 realmente mueve píxeles en el A/B
    (control positivo: alguna pasada con desplazamiento mayor que cero en el brazo MxD03).
13. **Re-etiquetado**: el control puede re-etiquetar con la misma referencia que ya usó
    (self-consistency), no con la congelada por sha256. Comparar sha256 de ref/ con MANIFIESTO.json.
14. **Procedencia**: podría comprobar sólo que el archivo MxD03 existe, no que el píxel del A/B
    sale de ese archivo (p. ej. el arnés podría caer silenciosamente a `_interp_geo` si falla el
    MxD03, y K = MXD03 en esas pasadas pasaría por «empate»).
15. **Cobertura**: puede estar medida sobre la ventana del job y no sobre la de los datos (A93, A108).
16. **Módulo de R**: no sé qué es; posible ambigüedad del nombre. Ver qué mide y si lo mide sobre
    los datos del A/B o sobre un fixture.
17. **Verde por excepción capturada**: un control que hace `try/except` y escribe «verde» si no
    hay excepción. Leer el código de cada control, no su salida.
18. **Controles corridos sobre una copia distinta (p. ej. el humo)** y reportados como si fueran
    sobre las tandas.

## R3. CUMPLE SIN DAÑO según §10 (P1 sin pérdida; P2 ≤ 35° empate ΔX −1 ruido 4; vara MXD03 MAS CERCA n 65; M neutro; P1b vacío; P2 > 35° ΔX −4)

19. **La etiqueta «protegida» no es la sellada**: el pre-registro fija «1 MW o más» con lectura A
    y pareo ±120 s; el evaluador podría usar otro umbral (0,5 MW, o el VRP del record y no el de
    MIROVA) u otra ventana de pareo. Leer el umbral en evaluar_mxd03.py y compararlo con §6.
20. **P1 sin pérdida por falta de sustrato**: si ninguna protegida tiene su cúmulo movido por MxD03
    (o si ninguna protegida es MODIS en la ventana), «sin pérdida» es trivial. Contar protegidas
    MODIS, y cuántas tienen desplazamiento no nulo en el brazo MxD03 (R4 dice 48: comprobarlo).
21. **P2 «ruido 4» como umbral de empate**: ¿de dónde sale el 4? Si es el ruido medido en K2 vs K,
    y K2 vs K da 0 por determinismo, el ruido declarado sería otro. Si el 4 se fijó después de ver
    ΔX = −1, el empate está hecho a medida (A115). Comprobar que el 4 está en el pre-registro sellado.
22. **ΔX cuenta records y no pasadas** (A94): el pre-registro puede definir la unidad como pasada
    (noche MODIS) y el evaluador contar records; o al revés.
23. **El corte de 35° se lee de otro lado**: el ángulo cenital del sensor puede venir del record de
    producción (K) y no del brazo MxD03, o ser el del píxel pico y no el de la pasada. Si el 35° se
    aplica a una variable distinta de la sellada, los estratos se mezclan.
24. **Direccionalidad de ΔX**: «ΔX −1» podría ser (MXD03 − K) o (K − MXD03). Si el signo está al
    revés, «−4 no positivo» pasa a +4 y cambia el §10.
25. **Vara MXD03 MAS CERCA por construcción**: la vara compara distancia de nuestro cúmulo al de
    MIROVA; si la referencia de MIROVA está georreferenciada con terreno (MxD03 o equivalente) y K
    con `_interp_geo`, MXD03 gana por compartir el sistema de referencia, no por ser mejor. También:
    si la vara usa `Distancia_km` del CSV (radio escalar sin acimut, A93), «más cerca» puede ser
    coincidencia de radios. Y si el n de 65 son los casos en que se mueve y se compara contra el
    propio brazo, hay maldición del ganador (A109). Ver vara_mxd03.py y vara_viirs_mxd03.json (¿la
    vara es VIIRS? ¿se compara MODIS con una referencia VIIRS?).
26. **n 65 con qué denominador**: 65 pares de cuántos posibles; si el resto se excluye por un
    criterio que correlaciona con el brazo, hay sesgo de selección.
27. **M NEUTRO**: ¿qué mide M (magnitud)? Si el A/B no cambia el área de píxel (nadir fijo A66), la
    magnitud sólo cambia por qué píxeles entran al cúmulo; «neutro» puede ser por construcción si
    el cúmulo no cambia de miembros.
28. **P1b vacío**: ¿qué es P1b? Si es «protegidas que pasan de summit a far», vacío puede venir de
    que `distance_class` se deriva del record K y no se recalcula para MXD03.
29. **Empate en P2 por brazos iguales**: si en muchas pasadas el brazo MxD03 cayó a `_interp_geo`
    (camino 14), ΔX tiende a 0 artificialmente. El control positivo es imprescindible: pasadas donde
    los brazos difieren en publicación, y que esas difieran por geometría.
30. **§10 leído distinto**: el veredicto compuesto puede estar mal derivado de las piezas (p. ej.
    §10 puede exigir que la vara NO sea «K MAS CERCA», o exigir algo sobre P2 > 35°). Leer §10
    completo y recomponer el veredicto a mano.

## R4. Lo que condiciona y no cambia el veredicto (P4: 158 cúmulos movidos, 48 protegidas; signo distinto de P2 sin Cordón Caulle)

31. **158 y 48 con denominador y ventana**: 158 cúmulos movidos de cuántas pasadas con cúmulo; 48
    protegidas de cuántas protegidas; qué umbral de «movido» (¿> 0 m? ¿> 1 celda?).
32. **Sin Cordón Caulle cambia el signo**: si al quitar un volcán el signo de ΔX cambia, el resultado
    agregado depende de un volcán (A126-estilo estratificar por volcán). Comprobar ΔX por volcán;
    si Cordón Caulle domina la muestra, el «empate» no es robusto y el §10 puede no contemplar
    este caso (¿lo dice el pre-registro?).
33. **P4 debería condicionar más de lo que dice**: si 48 protegidas se mueven y P1 «no pierde»
    porque la publicación no depende de la posición (predicado del tablero sólo mira distancia al
    inner), puede haber protegidas que pasan a `far` en MXD03 y P1 no lo vea (ligado a 28).

## Transversales

34. **Hora/commit**: artefactos generados después del commit del tag con código distinto (ver
    mtime vs fecha del tag).
35. **Copia local atrasada**: D:\vrp-trabajo\s162-mxd03 puede estar adelantado o atrasado respecto
    del tag; el evaluador se corre desde ahí. Verificar `git diff ffbb36248 HEAD -- experiments/_s162_mxd03`.
36. **El evaluador regenera la población y la población regenerada difiere de la corrida** (ligado a 2).
37. **La ref que leo no es la congelada**: comparar sha256 de cada archivo en ref/ con MANIFIESTO.json.
38. **La lectura del autor (INFORME.md) no se abre hasta después de este archivo**: cumplido; no lo
    he abierto.

---
sha256 (del contenido anterior a esta línea): ad03b0a0796955393c1d21182f1b9a9dd23946e3667561933234d4d538937ff2
Hora del servidor (GitHub, header Date): Date: Sat, 24 Oct 2026 20:33:02 GMT
