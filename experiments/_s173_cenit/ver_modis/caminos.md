# caminos.md: por donde podria estar mal cada afirmacion del auditor de MODIS (S173, cenit, Chillan)

Escrito ANTES de abrir ningun archivo citado por el auditor (ni su INFORME.md, que no abro; ni sus scripts ni sus salidas). Fuente de las afirmaciones: el texto de la tarea (D:/vrp-trabajo/temporales/s173_aud/prompts/ver_cenit_modis.txt, sha256 ba29e499...). Lo que se aprenda despues va al INFORME.md, no aqui.

Contexto que tengo sin leer nada del auditor: CLAUDE.md del proyecto (D17 remuestreo abierta, D25 bow tie, D34 codigo MIROVA V750, K en produccion desde #850, MOD-D candidato aprobado en S164, `_interp_geo` de MODIS corrida 1 a 3 km, regla A110 del nulo, A90 denominador y ventana, A104 regimen #535, A119 calidad de la referencia, A93 radio sin acimut, A109 maldicion del ganador).

## Afirmacion 1: ablacion hacia atras sobre las 16 grillas del A/B de MOD-D en Chillan; con el fondo de anillo de K la razon sobre 30 grados cae de 1,075 a 0,014 (n 10) y bajo 30 de 0,926 a 0,47, perdiendo 5 de 16 publicaciones; el anillo esta 7 a 8 K mas tibio que la cumbre, sin tendencia con el cenit

- C1.1 El brazo "fondo de K" no reemplaza solo el fondo: puede cambiar tambien umbrales, mascara, halo o la seleccion de pixeles, y la caida se atribuye a la pieza equivocada (A110, brazo que no hace lo que dice).
- C1.2 El brazo de control (via "codigo MIROVA" sin cambio) no reproduce el record de produccion o del A/B de MOD-D: si el 1,075 de partida no coincide con lo publicado por el A/B, el arnes esta midiendo otra implementacion y la ablacion no habla de produccion.
- C1.3 n 10 sobre 30 grados y 6 bajo 30: con n asi la mediana se mueve con uno o dos casos; la diferencia 1,075 a 0,014 puede ser 10 ceros (no publicado = 0) tratados como razon 0 y no como "perdida". Hay que ver como se trata la publicacion perdida: si razon 0 entra a la mediana o se excluye.
- C1.4 "Razon" puede ser por noche, no por pasada (la tarea define razon por pasada, mismo minuto de Fecha_Satelite_UTC). Si las 16 grillas son por noche o el pareo con MIROVA usa fecha y no minuto, una pasada MODIS (Terra/Aqua) puede parearse con la alerta de la otra.
- C1.5 "Las 16 grillas" podrian no ser las 16 pasadas de MOD-D: pueden ser un subconjunto donde habia grilla guardada en disco (sesgo de seleccion: solo las que publico K o solo las que publicaron ambos).
- C1.6 La razon de MIROVA: cual VRP de MIROVA (tabla CONS vs OCR; A119: MODIS esta completo en tabla, pero la ventana podria cruzar tramos). Si el denominador es OCR o si se usa lectura B.
- C1.7 El cenit de cada grilla: de donde sale. Si la grilla no trae cenit y se toma de otro record (o del centro del gránulo y no del volcan), el corte a 30 grados puede estar mal asignado.
- C1.8 "7 a 8 K mas tibio que la cumbre": en que banda (21, 22, 31) y con que mascara; si la cumbre es el pixel central (que contiene el hot spot) comparar su BT contra el anillo mide la anomalia, no el sesgo del fondo. Y "sin tendencia con el cenit" con n 16 tiene poca potencia: Spearman con n 16 no ve pendientes moderadas. Pregunta 1 del instrumento: si hubiera tendencia, la veria?
- C1.9 Posible confusion de signo: anillo mas tibio que la cumbre implica que el fondo de anillo reduce el exceso; pero la "cumbre" fria es la nieve del volcan y la caida del VRP con fondo de anillo seria esperable a cualquier cenit, no solo sobre 30. Entonces por que la caida es mayor sobre 30? Puede ser que el area del pixel oblicuo diluya; hay que separar area de fondo.
- C1.10 Ventana temporal: las 16 grillas de MOD-D son de que fechas; si todas son de un tramo de erupcion de Chillan (S157 #878), el resultado no generaliza. A90: declarar ventana.
- C1.11 El script podria leer grillas de un directorio que ya no existe o que fue regenerado por el A/B de S162 con otro detector (A104: dos regimenes mezclados).
- C1.12 Recorte: si el A/B de MOD-D aplico un tope (D9, 5 MW) o el record de MIROVA esta en el banner con NONE (regla SN), la razon cambia.

## Afirmacion 2: sin remuestreo (lote S162, 1 km2 por pixel) las protegidas sobre 30 grados caen de 0,992 a 0,52 (Spearman -0,815), con cenit y volcan confundidos (oblicuas de Chillan, nadir de Lascar)

- C2.1 Confusion cenit-volcan: si las pasadas sobre 30 grados son todas de Chillan y las de nadir de Lascar, el Spearman mide "Chillan vs Lascar" y no el cenit. Comprobar: Spearman DENTRO de cada volcan, y barajado del cenit dentro del volcan y sensor (la tarea pide barajado dentro del sensor; yo ademas dentro del volcan). Si dentro de cada volcan no hay correlacion, la conclusion sobre D17 no se sostiene con este lote.
- C2.2 "Lote S162" puede haberse producido con el detector anterior a K o con otra configuracion (A104). Hay que ver que flags tenia ese lote y si es comparable con el brazo con remuestreo (que puede ser otro lote con otra fecha y otros flags: dos pipelines, A/B inválido).
- C2.3 "1 km2 por pixel" sin remuestreo: si ademas se apago el area nadir fija (`ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS`), el area crece con sec3 y la razon subiria, no bajaria. Que la razon BAJE sin remuestreo sugiere otra cosa: menos pixeles alertados (el pixel oblicuo de 1 km nominal cubre 2 a 5 km2 reales y MIROVA remuestrea a 1 km: tendria MAS pixeles de 1 km). Fisica: sin remuestreo el pixel oblicuo es uno; con remuestreo a 1 km un pixel oblicuo de 2x4 km se convierte en varias celdas de 1 km que se suman. Esa es la direccion esperada: sin remuestreo se pierden pixeles, y el VRP cae. Compatible con la afirmacion. Pero verificar que el brazo "con remuestreo" realmente remuestrea (flag leido de pipeline.profile, A89) y no solo que es otra corrida.
- C2.4 "Protegidas" (alerta de MIROVA de 1 MW o mas): el n sobre 30 grados; si son 5 o 6, el Spearman -0,815 puede salir de 6 puntos. Declarar n.
- C2.5 El 0,992 del brazo con remuestreo: de donde sale. Si es de produccion (MOD-D no esta en produccion; produccion lleva K sin remuestreo segun D17 abierta), entonces el brazo "con remuestreo" podria ser el A/B de MOD-D (16 pasadas) y el brazo "sin" el lote S162: dos poblaciones distintas, no una ablacion.
- C2.6 Pareo por pasada: el lote S162 puede estar pareado por noche. Revisar el minuto.
- C2.7 Ceros: si en el lote sin remuestreo hay pasadas con VRP 0 (no publicada), como entran. Un cero en la razon es "perdida", no "magnitud baja".
- C2.8 El cenit del record del lote S162: campo guardado o reconstruido. Si se reconstruyo desde MxD03 o desde la posicion del pixel y no desde el record, decirlo.

## Afirmacion 3: la geolocalizacion de 5 km tambien reproduce la caida (0,699 / 0,171); halo y cumulo no son palanca

- C3.1 "Geolocalizacion de 5 km" como pieza: la via "codigo MIROVA" usa `_interp_geo` (S151: corrida 1 a 3 km hacia el nadir, se agrava con el cenit). Un brazo que use la geolocalizacion de 5 km interpolada podria mover el ROI 1 a 3 km y perder el hot spot: eso no es "reproducir la caida por la misma causa", es otra caida por otra causa. Hay que ver si el 0,699 / 0,171 es "razon con 5 km" vs "razon con MxD03", y que direccion.
- C3.2 Si tanto el fondo (af. 1) como la geolocalizacion (af. 3) "reproducen la caida", entonces la ablacion no identifica una pieza: dos piezas distintas dan el mismo sintoma; eso debilita "esta pieza es la palanca". Mirar si las dos ablaciones son independientes o si el brazo de fondo usaba la geo de 5 km.
- C3.3 "Halo y cumulo no son palanca": cuanto cambia la razon con y sin halo; si el cambio es 0,000 exacto, sospechar que el flag no llego (A118, A116: un cero necesita un control que pueda dar distinto de cero).
- C3.4 n de cada brazo y si los brazos corren sobre las mismas 16 grillas.

## Afirmacion 4: produccion con la via el 2026-11-02 da 1,189 y 1,114 a 41,4 y 52,0 grados

- C4.1 "Produccion con la via": MOD-D esta en candidato aprobado (fase 3), no en produccion; que se encendio en #934 (bitacora S173 "sellos y encendido de MODIS"). Verificar que el record de produccion del 2026-11-02 trae la marca de la via y no es K.
- C4.2 Dos pasadas no son evidencia de nada sobre la tendencia; a 41 y 52 grados dan 1,19 y 1,11, lo que contradice una caida fuerte con el cenit (af. 1 y 2 hablan de 0,014 y 0,52 sobre 30 grados). O la via arregla la caida (y entonces que pieza la arregla) o la referencia de MIROVA de ese dia es OCR sin calibrar o la pasada esta pareada por noche.
- C4.3 Pareo con MIROVA del 2026-11-02: el scraper tiene la fila de esa pasada? El snapshot local esta al dia? Si no, la razon sale contra una fila de otra pasada.
- C4.4 La copia local de data/mirova_equivalent/ puede estar atrasada respecto de origin/main (A25): el record del 2026-11-02 verificado contra remoto.
- C4.5 Que cenit guarda el record (campo) y si es el del volcan o el del centro del granulo.

## Afirmacion 5: 03_ablacion.py de S162 solo aisla el bow tie

- C5.1 Leer el script de S162 (experiments/_s162.../03_ablacion.py) y ver que brazos tiene: si tiene flags de fondo, remuestreo, etc., la afirmacion es falsa. Si solo bow tie, confirmada. Riesgo: el script puede tener brazos por argumento de linea de comando que no se ven en el cuerpo (A89).
- C5.2 "Aisla" puede querer decir que el unico brazo que cambia una cosa es el bow tie, pero que los demas brazos cambian varias a la vez.

## Afirmacion 6: el workflow del PR cumple A43, A71, grupo propio y no hace push, y su prueba local pasa (con dos mutaciones no atrapadas)

- C6.1 A43: `"on":` entre comillas; verificar con yaml.safe_load que la clave es string.
- C6.2 A71: autentica solo por EARTHDATA_TOKEN y falla al instante si vacio; verificar que no use EARTHDATA_USERNAME/PASSWORD ni .netrc; que no reintente auth.
- C6.3 "Grupo propio": `concurrency.group` distinto de push-main; si no pushea, no necesita push-main, pero tiene que no chocar con el cron NRT por max-parallel y por la cuenta de Earthdata (un workflow paralelo al NRT puede bloquear la cuenta si falla auth, A71).
- C6.4 "No hace push": buscar `git push`, `gh api --method PUT/POST`, `actions/upload-artifact` (eso esta bien), `peter-evans`, `git commit`; tambien pasos que llamen scripts del repo que pusheen (scripts/*.sh, run_pipeline con --commit). Verificar permisos `permissions: contents: read`.
- C6.5 "Su prueba local pasa" con dos mutaciones no atrapadas: con 2 de N mutaciones no atrapadas, que mutaciones; si las no atrapadas son justo las de push o credencial, la prueba no vigila lo que importa (A110, S152: mutacion que cae no es atrapada).
- C6.6 Si el workflow lee un workflow_dispatch con inputs: que no escriba en data/ ni en pipeline/; que el data_subdir sea aislado.
- C6.7 Cron: si tiene `schedule`, choca con el presupuesto de la cuenta Earthdata; la tarea dice que no se despacha.
- C6.8 Que el workflow referencie scripts que existen en la rama (rutas correctas) y que el checkout sea de la rama del PR y no de main (el script no existe en main).

## Transversales

- T1 El commit de referencia: la rama f57972af6 esta un commit sobre main 5de08ebf6; si los scripts del auditor leen data/ del worktree local y ese worktree esta atrasado o adelantado, los numeros no se reproducen. Mido el sha de los archivos de entrada.
- T2 Regimen: Chillan entro en erupcion (S157, #878); la ventana del A/B de MOD-D y del lote S162 puede pisar el cambio de K (#850, 2026-10-18 en merge; datos reprocesados desde #883) y #535. A104.
- T3 Instrumento muerto: cada script debe tener un control positivo (una pieza que seguro cambia la razon). Si todos los brazos dan lo mismo, el arnes no esta cambiando nada.
- T4 El cenit: el record MODIS guarda que campo (busco `zenith`, `sensor_zenith`, `cenit` en los JSON). Si el auditor lo saco de otro lado, decirlo.
- T5 Pareo por pasada: mismo minuto de Fecha_Satelite_UTC. MODIS Terra y Aqua pueden pasar la misma noche con 90 min de diferencia; un pareo por noche los mezcla.
- T6 Un script que no corre es un resultado.
- T7 No puedo correr el pipeline MODIS localmente (pyhdf roto en Windows): lo que dependa de reprocesar no se puede reproducir aqui, solo leer salidas; declararlo como SIN DATO donde aplique.

## Que NO voy a mirar

- No despacho workflows ni uso credenciales.
- No leo INFORME.md del auditor ni informes de otros verificadores (ver_v375, ver_v750).
- No modifico nada fuera de C:/Users/nmend/vrp-wt/s173_cenit/ver_modis/.

---
SELLO: sha256 del contenido anterior a esta linea = 5330cd2d7fc4e01702f5cc85c8749b90599f4a56fc84edba436b9455690c878a ; hora del servidor (GitHub) = Tue, 03 Nov 2026 01:16:37 GMT
