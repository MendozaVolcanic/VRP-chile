# Informe del verificador: re-sellado del lector de V375-E (S172)

CARPETA: D:/vrp-trabajo/temporales/ver_s172_relector/

## 1. Encabezado

- Hora del servidor: 2026-11-01 23:23 UTC al abrir, 23:59 UTC al cerrar la batería (`date -u`).
- Commit medido: aa3fdcf1e07a7cf5d653f688b5fff08801cd49c1, rama claude/s172-v375e-relector, worktree
  D:/vrp-trabajo/worktrees/s172-relector. Base del diff: tag s170-v375e-lector.
- Vara del código vivo: origin/main d3cd0b2aeee70b99fbc5bd90e5fd2b0dff284f54 (`git ls-remote origin main` a las 23:24 UTC
  coincide con el ref local; el pre-registro cita ffccf6c9f, repetí los `git grep` sobre el de hoy).
- Modelo: Sonnet 5.5 (claude-sonnet-5-5). Esfuerzo: no declarado por el arnés; no lo adivino.
- caminos.md escrito antes de abrir ningún archivo citado; sha256 del contenido previo a sus tres líneas finales:
  dccca35353dc9760940a843cf7741baca5791491b4e9db74a3097941388f0216 (hora 23:23:50 UTC). No lo edité después.
- Árbol quieto (A112): sha256 de leer_sombra_v375e.py, probar_sombra.py y mutar_sombra.py idénticos antes y después de la
  batería (arbol_antes.txt y `sha256sum` de las 23:59). El orquestador corría su propia identidad del nulo en paralelo en
  carpetas hermanas (`_mut_sombra_*`), que no tocan las fuentes.
- No miré: la bitácora ni el borrador de MODIS (prohibidos); no corrí mutar_sombra.py (lo corre el orquestador); no hay
  datos de la ventana P (no existen); no abrí data/ de ningún volcán; no hay PR abierto de encendido de MODIS
  (`gh pr list --state open` da sólo #912 y #913), así que no vi el diff real de frontend/index.html ni de la guardia.
  Usé 1 llamada a la API de GitHub de 20.

## 2. En una pantalla

1. SELLABLE CON CAMBIOS. A1 a A4 se sostienen (CONFIRMADO); A5 CONFIRMADO EN PARTE: S01 a S08 atrapan lo que dicen y
   retirar R07 no deja nada sin vigilar, pero ninguna prueba ni mutación fija que cambiar `extends:` marque régimen
   (mi mutante X3 que lo ignora sobrevive, VR172-01).
2. La batería completa reprodujo 252 de 252 PASA (el tag daba 233: son 19 casos nuevos, no los 25 que dice §11.14, VR172-05).
3. Sobre los perfiles reales de origin/main, encender MODIS + guardia en perfil nuevo + workflow nuevo + test + index.html no
   marca régimen, y editar la aserción de la l. 110 sí (repo git real de juguete, control_s8 de punta a punta).
4. Dos vías indirectas que la lista de cinco claves no cubre: la herencia `extends` lleva un flag MxD03 de producción a la
   sombra y tumba la aserción del workflow (VR172-02), y el tiempo del job NRT es compartido entre sensores (VR172-04, SOSPECHA).
5. Cambios mínimos antes de sellar: una prueba y una mutación de `extends`, corregir 25 por 19 y escribir la herencia de MxD03 en §11.14.

## 3. Veredicto por afirmación

| Afirmación | Veredicto | Gravedad | Evidencia de esta sesión |
|---|---|---|---|
| A1 | CONFIRMADO (con dos vías indirectas declaradas) | 2 | `git grep` sobre origin/main: las constantes de las cinco claves sólo se usan en pipeline/process_modis.py (cuatro) y pipeline/process_viirs_mod.py (una); en pipeline/profile.py se leen con `_t.get(...)` l. 902, 909, 923 a 925; sin enumeración genérica del perfil en código de producción (sólo scripts/libro_de_cuentas.py:214 y tests). VR172-02 y VR172-04 son lo indirecto. |
| A2 | CONFIRMADO | 1 | prueba_a2_a4.py: 33 de 33 casos sobre ME_main.yaml y SO_main.yaml reales de origin/main (salida_prueba_a2_a4.txt); falla cerrada en aparece, desaparece, ilegible, vacío, lista, raíz, output, paths y sensors. Gravedad 1 por la igualdad de escalares (VR172-07). |
| A3 | CONFIRMADO | 1 | RAIZ = AQUI.parents[2] (l. 49); 16 de 16 sha256 del checkout coinciden con el sello; origin/main hoy coincide 15 de 16 (el que falta es leer_posicion_v375e.py, que no está en origin/main); control positivo: sello alterado y VRP_PROFILE ajeno hacen caer S0 (salida_prueba_a3_s0.txt, salida_prueba_a3_control.txt). Nada impone que se corra desde el tag, pero desde otro checkout S0 cae cerrado, no en silencio. |
| A4 | CONFIRMADO | 2 | prueba_a4_git.py y prueba_control_s8.py sobre un repo git de juguete con los archivos reales de origin/main: base a C1 (clave MODIS en producción, perfil guardia nuevo, workflow nuevo, test, index.html) da `[]` y control_s8 SIN CAMBIO; base a C2 (edita la aserción de la l. 110) da `['.github/workflows/sombra-codigo-mirova.yml']` y MARCA. La l. 110 de origin/main es la aserción (`sed`). El PR real no existe: SIN DATO sobre su contenido. |
| A5 | CONFIRMADO EN PARTE | 3 | Atrapa: mi re-medición independiente del subconjunto S8 (prueba_a5_mutantes_s8.py) da S01 a S08 ATRAPADA por aserción, X1, X2, X4 a X9 ATRAPADA, identidad sin rojos. No atrapa: X3 (ignorar `extends`) SOBREVIVE. R07: su línea ya no existe (0 ocurrencias) y su vigilancia pasa a S05 (cae en "(VL169-03) perfil ajeno no marca" y en la de ilegible) y a X1/X2 (cae en los casos "marca"). Las 146 mutaciones aplican exactamente una vez (salida_prueba_unicas.txt). |

Veredicto global: SELLABLE CON CAMBIOS.

1. Agregar a probar_sombra.py un caso "cambiar `extends:` de la sombra marca" y a mutar_sombra.py una mutación que lo ignore (VR172-01).
2. Corregir §11.14 ("25 casos nuevos" son 19) y de paso la cifra "230 de 230" de la ronda 3, que el tag declara como 233 (VR172-05).
3. Escribir en §11.14 la herencia de los flags MxD03 hacia la sombra y su aserción (VR172-02), o declarar que se acepta.
Ninguno exige tocar el comportamiento del lector.

## 4. Hallazgos (ordenados por gravedad)

### VR172-01
- TÍTULO: Nada fija que cambiar `extends:` marque régimen; un mutante que lo ignora sobrevive
- ARCHIVO:LÍNEA: experiments/_s168/v375e_sombra/probar_sombra.py l. 509 y 511 (`extends` sólo como relleno de los fixtures me0 y so0); experiments/_s168/v375e_sombra/leer_sombra_v375e.py l. 408 a 417 (y 429 la comparación); SCRIPT:SALIDA prueba_a5_mutantes_s8.py:salida_prueba_a5_mutantes_s8.txt (línea `MUT X3  SOBREVIVE`)
- QUÉ PASA: la sombra hereda toda la configuración de producción por `extends: mirova_equivalent` (origin/main pipeline/profile.py l. 47 a 67, fusión profunda), así que `extends` es el canal por el que el perfil de producción gobierna los records de VIIRS 375 de la sombra, justo el tipo de hueco de A89 que §11.14 dice cubrir. El código de hoy lo compara (mi caso "SO real con extends distinto" da True), pero ni la batería ni S01 a S08 lo vigilan: una refactorización que quite `extends` de la comparación deja las 252 pruebas en verde.
- CÓMO SE VE EN EL DASHBOARD: invisible. Un cambio del perfil padre dejaría de marcar régimen en la ventana P y la lectura saldría como si nada hubiera cambiado.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/ver_s172_relector && PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 python prueba_a5_mutantes_s8.py` (mutante X3: agrega `d.pop('extends', None)` tras el bucle de claves; no usa datos ni pasada).
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 3 (vigilancia que falta en el control que decide si la lectura de la sombra vale)

### VR172-02
- TÍTULO: Un flag MxD03 en true en producción llega a la sombra por herencia, tumba la aserción del workflow y no marca régimen
- ARCHIVO:LÍNEA: .github/workflows/sombra-codigo-mirova.yml l. 110 (en origin/main d3cd0b2ae); pipeline/profiles/sombra_codigo_mirova.yaml (extends l. 23, no declara los tres flags MxD03); leer_sombra_v375e.py l. 103 a 106; SCRIPT:SALIDA prueba_herencia.py:salida_prueba_herencia.txt
- QUÉ PASA: la sombra no declara los tres flags de MxD03; los hereda de producción. El programa los deja "aparte", pero cuando se enciendan en producción la sombra heredará True y la aserción `assert not (p.ENABLE_MODIS_GEO_MXD03 or ...)` de la l. 110 falla (medido: la sombra hereda geo = True y la aserción no pasaría). El job de la sombra muere antes de procesar nada, en los tres sensores, con lo que se pierden noches de VIIRS 375 de la ventana P. El lector no lo marca (las tres claves están en la lista), y el arreglo natural, editar esa aserción, sí marca.
- CÓMO SE VE EN EL DASHBOARD: invisible para el operador (la sombra no la lee el tablero); en el lector aparece como noches sin record de la vía, no como cambio de régimen. El job rojo en GitHub sí es ruidoso.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/ver_s172_relector && PYTHONUTF8=1 python -I prueba_herencia.py` (copia de profile.py y de los dos perfiles de origin/main en scratch_profile/; edita `enable_modis_geo_mxd03: true` en el padre).
- CONFIANZA: CONFIRMADO (herencia y aserción); el efecto sobre cuántas noches se pierden es SOSPECHA
- GRAVEDAD: 2 (ruidoso y reversible, pero rompe la ventana P sin marcar régimen)

### VR172-03
- TÍTULO: El S8 no compara .github/workflows/nrt.yml ni frontend/index.html
- ARCHIVO:LÍNEA: experiments/_s168/v375e_sombra/leer_sombra_v375e.py l. 95 (RUTAS_REGIMEN); .github/workflows/nrt.yml l. 179 y 195 (paso y `--profile mirova_equivalent`)
- QUÉ PASA: lo que el NRT hace con VIIRS 375 depende del workflow que lo corre (cron, matriz, timeout, argumentos) y lo que el operador ve depende del predicado de index.html. Ninguno de los dos está en RUTAS_REGIMEN; index.html sólo está en el sello S0, que fija la copia del propio lector, no la de main. Es anterior al commit y está fuera del diff, pero A3 y A4 apoyan la afirmación "el PR de MODIS cambia index.html y no marca" en ese vacío.
- CÓMO SE VE EN EL DASHBOARD: si el PR toca el predicado de publicación de VIIRS 375, el operador vería otra publicación sin que el S8 lo marque. Invisible para el lector.
- CÓMO REPRODUCIRLO: `git -C "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" show origin/main:.github/workflows/nrt.yml | sed -n 179,197p` y comparar con `RUTAS_REGIMEN`.
- CONFIANZA: SOSPECHA (el vacío está leído; que el PR real lo use no se puede ver, no existe)
- GRAVEDAD: 2

### VR172-04
- TÍTULO: El tiempo del job del NRT es compartido entre sensores: encender MODIS en K puede costar records de VIIRS 375 por timeout
- ARCHIVO:LÍNEA: .github/workflows/nrt.yml l. 69 y 179 (job 80 min, paso 50 min); scripts/run_pipeline.py l. 221 a 300 (MODIS, luego VIIRS, en el mismo proceso); experiments/_s167_sombra/COSTO.md l. 36 a 39 y 64 a 67
- QUÉ PASA: un solo proceso por volcán recorre las plataformas en orden; una excepción de MODIS no pasa a VIIRS (hay try por gránulo), pero un paso que se pasa de 50 min se mata completo. COSTO.md estima la parte de MODIS de la vía en 19 gránulos de 1,5 s (menos de un minuto, "no medido aparte") y dice que el camino completo de MODIS sólo lo puede medir un despacho. El peor job observado es de 56 min.
- CÓMO SE VE EN EL DASHBOARD: un volcán sin records de la noche en VIIRS 375, sin cambio de régimen marcado.
- CÓMO REPRODUCIRLO: lectura de los tres archivos citados; sin comando que lo mida (requiere un despacho).
- CONFIANZA: SOSPECHA
- GRAVEDAD: 2 (probabilidad baja por la estimación, efecto en el instrumento de alerta)

### VR172-05
- TÍTULO: §11.14 dice 25 casos nuevos; son 19 (y la cifra "230 de 230" de la ronda 3 es 233 en el tag)
- ARCHIVO:LÍNEA: experiments/_s162_v375/PREREGISTRO_E.md l. 1189; SCRIPT:SALIDA salida_bateria.txt, salida_bateria_tag.txt
- QUÉ PASA: diff de nombres de pruebas entre la salida del tag (233 PASA) y la de hoy (252 PASA): 19 líneas nuevas, todas "S8 (S172)". El código tiene 19 `chk` nuevos. Es una cifra de documento, no de comportamiento.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -c '^PASA' salida_bateria_tag.txt salida_bateria.txt` en CARPETA.
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### VR172-06
- TÍTULO: Renombrar un perfil no sale de `nombres_git`, pero lo ataja la comprobación del perfil de los records
- ARCHIVO:LÍNEA: leer_sombra_v375e.py l. 371 a 377 (`git diff --name-only`, l. 376) y l. 463 a 495 (`perf_malos`, l. 475); SCRIPT:SALIDA prueba_rename.py:salida_prueba_rename.txt, prueba_control_s8.py:salida_prueba_control_s8.txt
- QUÉ PASA: con detección de renombres, `--name-only` entrega sólo el nombre nuevo, que no está en PERFILES_REGIMEN, y diff_git da `[]` (idéntico en el lector del tag). Los records de la ventana traerían otro `regimen.perfil` y control_s8 marca por eso (caso "perfil renombrado": MARCA). Un borrado puro sí se detecta.
- CÓMO SE VE EN EL DASHBOARD: invisible; lo cubre el otro control.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/ver_s172_relector && PYTHONUTF8=1 python prueba_a4_git.py && PYTHONUTF8=1 python prueba_rename.py && PYTHONUTF8=1 python prueba_control_s8.py`
- CONFIANZA: CONFIRMADO
- GRAVEDAD: 1

### VR172-07
- TÍTULO: La igualdad de Python entre escalares YAML hace que 1, 1.0 y true no marquen como cambio
- ARCHIVO:LÍNEA: leer_sombra_v375e.py l. 429 (`perfil_sin_otro_sensor(viejo) != perfil_sin_otro_sensor(nuevo)`); SCRIPT:SALIDA prueba_tipos.py:salida_prueba_tipos.txt
- QUÉ PASA: `1 -> true`, `0 -> false` y `5 -> 5.0` dan marca=False (el control `1 -> 2` y `1 -> 'true'` dan True). Antes, con texto, marcaban. pipeline/profile.py convierte con float(), bool() e int() casi todo, así que el efecto es nulo en lo que leí, pero no revisé cada consumidor.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `cd D:/vrp-trabajo/temporales/ver_s172_relector && PYTHONUTF8=1 python prueba_tipos.py`
- CONFIANZA: CONFIRMADO (que no marca); SOSPECHA (que no tenga efecto)
- GRAVEDAD: 1

## 5. SEGUIMIENTOS (fuera de mi eje)

- El mutante X5 (cambiar `except Exception` por `except ValueError` en cambio_significativo) da CAIDA, no ATRAPADA, porque
  la prueba de "perfil ilegible" lanza ParserError en vez de fallar una aserción; el nulo no lo cuenta como atrapado.
  No está en el conjunto de 146, así que no afecta el resultado: lo dejo anotado (leer_sombra_v375e.py l. 430,
  confianza CONFIRMADO, gravedad 1).
- Nota, sin hallazgo: §11.14 dice que los 16 archivos del sello coinciden en el checkout del tag. Medí 16 de 16 en el worktree del
  commit; los cinco archivos del diff no están entre los 16, así que lo medido vale también para el tag.

## 6. VERIFICADO LIMPIO

- Consumidores de las cinco claves: `git grep -n -i <clave>` para cada una sobre origin/main d3cd0b2ae, excluyendo tests,
  experiments y docs (salida en la sesión, resumida en A1). Vara: el código de origin/main de hoy. Control positivo: la
  búsqueda encuentra `ENABLE_V750_CODIGO_MIROVA` en process_viirs_mod.py:75 y :504 y la lectura en profile.py:902. Si una
  clave se leyera con otro nombre, `-i` sobre clave y constante no la vería; por eso busqué además enumeraciones genéricas
  (`dir(`, `vars(`, `getattr(`, `startswith("ENABLE_`, `__dict__`) y lectores directos del YAML (`safe_load`, `profiles/`):
  sólo scripts/libro_de_cuentas.py:214, tests y el propio profile.py.
- store.py es por (sensor, datetime) y el marcador `via_codigo_mirova` se mira por record (store.py:357, :614): no hay
  estado compartido entre sensores en el almacén. `regimen` trae sólo perfil, codigo_sha y origen (store.py:93, :94).
- Etiquetas de VIIRS 375: banco_paridad.cargar_nuestros/etiquetar (l. 265 a 337) etiqueta cada pasada por su bucket y la
  referencia de MIROVA; ningún campo de MODIS entra. evaluador_comun filtra eventos de cobertura por sensor (l. 355 a 369).
- S0 (A3): ver tabla. 16 de 16 y control positivo en rojo.
- A2 por casos: 33 de 33 (los casos que deben marcar incluyen raíz, output, paths, sensors, ilegible en viejo y en nuevo, lista,
  vacío y `thresholds` lista). Control: la misma edición en una clave no listada marca.
- Escenario A4 con git real y control_s8: ver tabla; también "base a C2 marca" y "sha inexistente marca".
- Batería completa corrida una vez, en primer plano de mi sesión, sobre el árbol quieto: `PYTHONUTF8=1 python -I probar_sombra.py`
  da RESULTADO 252 de 252 (23:31 a 23:59 UTC) y los nombres coinciden uno a uno con el probar_sombra_salida.txt del commit.
  Vara: el propio código; la batería no prueba nada contra datos reales de la ventana P (no existen).
- 146 mutaciones, cada `viejo` aparece exactamente una vez en el lector (salida_prueba_unicas.txt), R07 retirada sin dejar
  la línea, RAMA = claude/s172-v375e-relector.

## 7. SIN DATO

- Contenido real del PR de encendido de MODIS (no hay PR abierto): si su diff de frontend/index.html toca el predicado de
  VIIRS 375, y cómo es la "guardia en un perfil nuevo" (si ese perfil nuevo lo corre el workflow de la sombra, sus records
  traerían otro `regimen.perfil` y control_s8 marcaría por `perf_malos`; no lo sé).
- El resultado del nulo de 146 mutaciones (lo corre el orquestador). Mi re-medición cubre sólo el subconjunto S8 y 6 mutantes propios.
- Costo real de MODIS en el job del NRT (VR172-04).

## 8. FUERA DE ALCANCE

- Calidad de la vía «código MIROVA» en sí, de V750 y de MODIS; cualquier lectura de la ventana P; el resto del lector (S1 a S10).

## 9. Archivos en CARPETA

caminos.md, prueba_a2_a4.py, prueba_a4_git.py, prueba_rename.py, prueba_control_s8.py, prueba_a3_s0.py, prueba_a3_control.py,
prueba_a5_mutantes_s8.py, prueba_unicas.py, prueba_herencia.py, prueba_tipos.py, cada uno con su `salida_*.txt`;
salida_bateria.txt (batería completa), salida_bateria_tag.txt (233 del tag), salida_bateria_commit_declarada.txt;
insumos/ (perfiles y workflow de origin/main), repo_juguete/, scratch_profile/, mut/, hallazgos.csv.
