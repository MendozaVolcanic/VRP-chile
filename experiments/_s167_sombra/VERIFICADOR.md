# Verificador limpio del perfil de sombra (S167, 2026-10-29)

Modelo distinto del que escribió el cambio (Sonnet), contexto limpio: recibió el objetivo, las condiciones y las rutas,
no las conclusiones. Revisó el commit `989393d43` de la rama `claude/s167-perfil-sombra`.

**Veredicto: LISTO CON CAMBIOS.** Ninguna de las siete condiciones (producción intacta, carpeta propia, no corre
solo, sólo token, `"on":` entre comillas, costo medido, tres posiciones legibles) se rompe.

Lo que comprobó en verde, con evidencia: las 14 pruebas nuevas y 192 de guards vecinos; los dos perfiles resueltos
difieren sólo en nombre, descripción, carpeta y los tres flags (leídos de `thresholds:`, `pipeline/profile.py:902, 909,
933`); el almacén escribe sólo en `data/<DATA_SUBDIR>` (`pipeline/store.py:62, 239-249`) y la carpeta no está en
`.gitignore`; la fecha mínima no deja pasar records anteriores al 2026-11-03; el modo medir no commitea; los tres
sensores escriben las tres posiciones desde `procesar_grilla` (`pipeline/mirova_v750_codigo.py:704-748`) y el almacén
no las filtra (`pipeline/store.py:357`); la vía reemplaza a K con `return` antes de K.

## Hallazgos y qué se hizo

| n | gravedad | hallazgo | qué se hizo |
|---|---|---|---|
| 1 | 2 | El job puede quedar verde sin records de la vía: `run_pipeline.py` atrapa toda excepción por gránulo y sale 0; las caídas a K (`sin_grilla`, `sin_mxd03`, `geo_distinta`) no avisan | `scripts/revisar_sombra.py` como último paso (`always()`, después del commit): rojo con errores de gránulo, con records que no son de la vía o sin ningún record de la vía. 2 pruebas y 3 mutaciones atrapadas |
| 2 | 2 | El timeout de 60 min descansaba en una estimación y en una muestra de dos días; `nrt.yml` cita un peor job de 56 min | Paso de 75 min (1,3 × 56) y job de 100; la prueba ancla el piso al 56 observado, no a la estimación |
| 3 | 2 | Cifras de `COSTO.md` sin script: conteo de gránulos a mano, salida de `fases.py` sin guardar, CSV ignorado por `.gitignore`, «~4 min» sin derivación, cadencia horaria sin evidencia | `fases.py` cuenta los gránulos y su salida queda guardada; `tiempos_jobs.csv` con `git add -f`; `corridas_nrt_20261029.txt` para la cadencia (de paso corrigió 37 a 87 min por 31 a 91); la estimación queda derivada y rotulada ESTIMADO |
| 4 | 1 | La prueba de punta a punta ejercita sólo VIIRS 375 | Anotado en `COSTO.md` §4: MODIS y VIIRS 750 sobre gránulos reales los comprueba el despacho `medir=true` antes del encendido |
| 5 | 1 | La prueba por línea de comandos decodificaba stderr cp1252 como utf-8 (hilo lector muerto, prueba verde igual) | `PYTHONIOENCODING=utf-8` en esa llamada; las pruebas corren con esa advertencia convertida en error |
| 6 | 1 | Al encender, cada commit dispara `pages-deploy.yml` y publica la carpeta | Anotado en `COSTO.md` §4 para la decisión de encendido |
| 7 | 1 | `ventana()` no rechaza un `end` futuro; `cercano <= radiante` vale para la fixture, no en general | La prueba pasa a `cercano <= pico` (el pico es un píxel alertado, así que vale siempre). El `end` futuro no cambia nada: el pipeline no encuentra gránulos del futuro |
