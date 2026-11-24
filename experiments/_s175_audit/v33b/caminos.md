# caminos.md: por donde podria estar mal cada afirmacion (V33B, verificador)

Escrito ANTES de abrir ningun archivo citado. Solo se listaron carpetas (ls) y se leyeron
commits por hash con `git log -1` para situar las fechas. Despues de anotar el sha256 y la hora
del servidor al final, este archivo no se vuelve a editar: lo aprendido despues va a VERIFICACION.md.

Base: 752d348bc67190e53b610989877e2405d238a1bc (2026-11-07 03:38 UTC). origin/main local hoy:
cc32ab1fc (2026-11-08 12:36 UTC, 2 h antes de empezar; comprobar contra el remoto con una llamada).
loop/activo de referencia: 395af8034 (2026-11-07 00:31 -03). Los auditores citan ademas 06de6876a
para LOOP_OBJETIVOS.md, que NO es 395af8034: primer camino transversal, la version del documento que
citan puede no ser la que la tarea fija como referencia, y las lineas pueden haber corrido.

Caminos transversales a los 15:
- T1. La copia local de origin/main esta 2 h atrasada; un arreglo pudo entrar despues (verificar con la API).
- T2. Las lineas citadas se remapean por contenido (A101): una linea que no coincide no refuta, hay que buscar la frase.
- T3. Los scripts de los auditores pueden leer datos de un arbol que ya no esta (arbol_752d348bc en el temporal de f2): si no corren, es un resultado, no un veredicto sobre la afirmacion.
- T4. Afirmaciones sobre «fuera de main» cambian de verdad con cada merge: medir en base Y en origin/main de hoy, y decir en cual.
- T5. Un cero de un grep se lee como ausencia (A89): buscar variantes del nombre (#945 vs PR 945 vs «945»).

## F2-208 (fecha de parada de la sombra V375-E: noche 30 con datos, 2026-12-02 si no falta ninguna; 4 noches y 26 alertas al 2026-11-06)
- El lector cuenta noches con datos de la sombra, no noches calendario: si la sombra tiene huecos (NRT caido, volcan sin pasada), la fecha 2026-12-02 es un maximo teorico que el lector no promete.
- «noche» puede estar definida en UTC o en hora local de Chile en el yaml y de otra forma en el lector.
- La regla sellada (REGLA en _s168 o en el yaml) puede decir 30 noches, 30 pasadas o 30 dias: si la unidad es otra, la fecha cambia.
- El conteo «4 noches y 26 alertas» depende de la ventana --hasta y de que CSV de referencia se pase: con la referencia fija de la tarea puede dar otro numero.
- El lector citado esta «fuera de main»: el que corre en Actions (si alguno corre) puede ser otra version con otro criterio de parada.
- Gravedad 1: aunque sea cierto, mueve una fecha de calendario, no una alerta.

## F2-209 (el lector de la sombra no esta en la base ni en origin/main; solo tag y origin/claude/s172-v375e-relector)
- Puede haber entrado a main despues de la base (T1, T4): comprobar en origin/main de hoy.
- Puede existir con otro nombre o ruta en main (T5): buscar por contenido (una funcion caracteristica), no solo por el blob e720dbc46.
- El blob citado puede ser una version y en main vivir otra version del mismo archivo (distinto blob, mismo path).
- «merge-base --is-ancestor fc3912cb2 752d348bc» false no implica que el ARCHIVO no este: implica que ese COMMIT no esta.
- Que no este en main puede ser deliberado (lector de experimento que vive en su rama): la gravedad depende de si algo en main lo llama.

## F2-210 (dos protegidas de marzo sin record nuestro: Lascar 2026-03-11 06:18, Isluga 2026-03-10 04:54)
- El pareo usa TOL_S del banco; «sin record» puede ser «record a mas de TOL_S» (satelite distinto, hora de MIROVA con otra convencion).
- Puede que el record exista pero con otro satelite (NOAA-21 vs NOAA-20) y el banco no lo pareara por ese eje.
- Marzo 2026 puede estar fuera de la ventana de cobertura real de nuestros datos VIIRS 375 (A119: la referencia sirve desde marzo; nuestros datos por volcan pueden empezar despues), o un hueco de NRT: en ese caso es «sin pasada», no «perdida».
- La etiqueta protegida (>= 1 MW) puede venir del OCR y no de la tabla (A11, S159): mirar que canal la pone.
- El banco en la base y en origin/main pueden dar distinto si cambio TOL_S o etiquetar.
- La hora puede estar en hora local vs UTC en la fila de MIROVA.

## F2-211 (18 pasadas sin geometria de 1 MW o mas fuera del denominador protegido; 14 de Chillan en erupcion; 2 no publicadas)
- «Sin geometria» puede ser una etiqueta del scraper por fallo de OCR, no un dato de MIROVA (A11): entonces no son necesariamente alertas de MIROVA.
- La regla D-9 / etiquetar puede excluirlas a proposito (decision documentada), y lo que el auditor llama «fuera del denominador» es por diseno; igual conviene saber si estan publicadas por nosotros.
- El conteo depende de la ventana (2026-03-01 a 2026-11-07) y de que CSV se lea (consolidado del snapshot vs raiz: tienen distinto sha256).
- «2 no publicadas» depende del predicado del tablero ejecutado con node (A97), no de una reconstruccion: verificar como lo decidio el script.
- Chillan en erupcion puede tener pasadas sin geometria por saturacion o por falta de TIF (TIF congelados desde 2026-09-22): la causa cambia la gravedad.

## F2-213 (C-04 actualizado: Tupungatito 2026-09-28 05:18, distancia de MIROVA igual a la de su pasada de las 05:36; sigue abierto)
- El OCR puede llevar la distancia de otra pasada (S150, reference_ocr_imagen_de_otra_pasada): que dos pasadas compartan distancia puede ser artefacto del scraper, no dato de MIROVA.
- Puede que la de las 05:18 y la de las 05:36 sean el mismo gránulo visto por dos satelites (NOAA-20 y NOAA-21 o SNPP) y la distancia igual sea legitima.
- «Sigue abierto» depende de que C-04 este listado como abierto en algun documento: comprobar cual y en que version.
- El png_index.csv de insumos es del 2026-11-07; una imagen posterior pudo cambiarlo (no se puede verificar sin red: SIN DATO).
- La distancia igual puede ser cuantizacion a la celda de grilla (D15, A13), no copia.

## 255 (cola de decisiones §5 de loop/activo con cinco filas desfasadas: D-1, D-19, D-23, D-37, D-39)
- El commit citado (06de6876a) no es el de referencia (395af8034): comprobar en 395af8034 y en el loop/activo de hoy (6f2f56f04 local).
- «Desfasada» puede ser una lectura del auditor sobre el estado de la decision: hay que cotejar cada fila contra su fuente (PR mergeado, bitacora) y no contra otra fila del mismo documento.
- Las lineas 526 a 545 pueden haber corrido (T2).
- Puede que ya se haya actualizado en loop/activo de hoy (39fc626b8).

## 259 (D25 NO SE ADOPTA cerrado bajo una delegacion general D-48, no con una frase sobre D25)
- La frase especifica puede existir en otro documento (bitacora LOOP_OBJETIVOS, memoria project_s162_estado) y el auditor solo miro MIROVA_DIVERGENCES.md.
- La «delegacion general» D-48 puede estar redactada para cubrir exactamente ese caso: leer D-48 entera.
- Lineas 2863 a 2865 pueden haber corrido en origin/main de hoy.

## 260 (la A45 de #920, «Si, los tres apagados», quedo en el repo solo de segunda mano)
- La frase puede estar citada en mas de un lugar (bitacora, PR body en GitHub, mensaje del commit): «de segunda mano» depende de que fuente se considere primaria; un PR body es tambien segunda mano.
- El commit 4164d4547 puede no ser el squash de #920.
- La linea 2468 de 06de6876a puede no ser la de 395af8034.

## 261 (#895, R13 del sync, entro a main sin frase de Nicolas en la bitacora mientras D-39 lo pedia)
- D-39 puede pedir frase solo para pausar Mirova-v1, no para cambios del sync en este repo: leer D-39 entera.
- La frase puede estar en la bitacora con otra redaccion, o en el PR (merged_by distinto de Nicolas no prueba que no la haya dado).
- Las lineas 90 a 102 del yml pueden no ser R13.
- Que lo mergeara Claude esta permitido por A39 si no era alta criticidad.

## 262 (decision 3 de la sombra de los 34 implementada con radio max(4 km, inner) en vez de 4 km)
- La decision puede decir «4 km o el inner si es mayor» en otra linea de la bitacora que el auditor no cito.
- max(4, inner) con inner <= 4 en los 34 es identico a 4 km: si ningun volcan de los 34 tiene inner > 4, el efecto es cero (medir).
- El squash 438a010ab puede no ser #935.

## 263 (el texto sellado de la regla MOD-D cambio en una linea al sellarse; el archivo sigue llamandose BORRADOR)
- El cambio de una linea puede ser la propia marca de sello (fecha, sha): entonces es esperado, no defecto.
- El script sello_regla_modd.py puede comparar contra un sha que registro otro documento: verificar que sha y que texto.
- El nombre BORRADOR puede ser deliberado hasta la adopcion (MOD-D CANDIDATO, fase 3).

## 264 (#951 mergeado con CI rojo en la rama de V750, fuera de main)
- «CI rojo» puede ser un check no requerido o un workflow que no aplica a la rama.
- El squash c8152580b puede estar ya en main (T4).
- La rama puede tener un check rojo por un job que falla por el token vencido (A71), no por el cambio.

## 265 (el indice de memoria tiene desfasado el estado de S174: #945, #950, #951)
- La memoria esta fuera del repo (~/.claude/projects/...): el `git log --grep` propuesto mide el repo, no la memoria; el instrumento mide otra cosa.
- El MEMORY.md que yo cargue hoy ya dice «S174 CERRADA... #945, #952, #953 y #954»: puede estar corregido despues de la auditoria.
- project_s174_estado.md puede tener el detalle correcto aunque el indice este corto.

## 308 (el criterio «ninguna protegida perdida» no tiene casos en 5 de 11 volcanes)
- Que un volcan no tenga protegidas en la ventana es un hecho de la referencia (volcanes quietos), no un defecto del criterio: la gravedad depende de si alguien lo presenta como «cumple» en vez de «sin dato».
- Depende de la ventana del script f5_medir.py y del CSV de referencia (snapshot vs raiz).
- Puede haber protegidas en el OCR que la tabla no tiene (o al reves): contar por canal.
- El script puede no correr sin su pkl (f5_base.pkl) o sin red: T3.

## 310 (el ratio de magnitud de Lastarria V375 cambia de banda al restringirlo a la misma pasada)
- «Cambia de banda» depende de los cortes de banda de auto_audit_weekly.py l. 145: si el ratio esta cerca del borde, un cambio de pareo lo mueve sin que signifique nada fisico.
- Restringir a la misma pasada cambia el N: con N chico la mediana es inestable (declarar N).
- La pasada «misma» puede ser por TOL_S o por satelite; dos definiciones dan dos ratios.
- El dashboard puede no mostrar la banda; gravedad 1 si es invisible.

---
sha256 (antes de esta linea): 742bb50986ae4c6c896eee89818c5e82c0ed22b41e5dd61b6d8775145177b3dd
hora del servidor (github.com, header Date): Date: Sun, 08 Nov 2026 14:16:01 GMT
