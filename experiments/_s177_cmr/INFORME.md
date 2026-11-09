# S177: ¿nuestro reproceso provoca los cortes de CMR del 2026-11-08?

Censo de GitHub Actions del 2026-11-01 al 2026-11-09 04:45 UTC: 162 intentos, 1.946 trabajos, 238.534 marcas de búsqueda
(`censo_cmr.py`, `analizar_cmr.py`, `desglose_cmr.py`; datos en `C:\Users\nmend\vrp-temporales\s177_cmr\`). Ninguna llamada a NASA.
Verificador limpio Sonnet en `C:\Users\nmend\vrp-temporales\s177_ver_cmr\INFORME.md`; el autor comprobó sus cifras centrales con
código propio (fallas por colección, primera y última falla, lentitud de NOAA-21 por día).

## Veredicto

**El reproceso no es la causa del corte. Si lo agrava: SIN DATO.**

## Qué pasó, como fenómeno

El buscador de NASA se puso lento para una familia de colecciones, las de VIIRS NOAA-21, y no para CMR entero. Es un problema del lado
del índice de esas colecciones, no de saturación general: nuestra carga pide por igual todas las colecciones, y en las mismas horas NOAA-20
respondió en 0,4 s. Cuando una búsqueda de NOAA-21 pasó de los 60 s de lectura, murió por ReadTimeout y el proceso perdió esos días.

## Evidencia

| Hecho | Cifra | Etiqueta |
|---|---|---|
| Fallas 11-08, 19 a 24 UTC, por colección | 305 de 306 son NOAA-21; 1 MODIS Aqua | CONFIRMADO, comprobado por autor y verificador |
| Inicio | primera lenta 19:11:32 y primera falla 19:15:03, las dos de `experimental-diario`, no del reproceso | CONFIRMADO |
| Misma carga sin daño, antes del corte | 18:00 a 19:00 UTC: 5,6 trabajos de reproceso en promedio, 1.188 consultas marcadas (máximo del periodo), sin fallas y p95 0,8 s | CONFIRMADO |
| Misma carga sin daño, después | 11-09 03:45 a 04:45 UTC: 4,5 trabajos de reproceso en promedio, 0 fallas, p95 0,7 s | CONFIRMADO |
| Episodio sin reproceso | 11-06 19:57 a 20:27 UTC, NOAA-21 lenta (mediana 33 a 40 s, máximo 62,1 s), 0 trabajos de reproceso, sin ReadTimeout | CONFIRMADO |
| Último evento | última falla 23:25:49, con 6 trabajos aún activos | CONFIRMADO |
| A favor de «agrava» | las 306 fallas caen dentro de las 6 h con 6 trabajos, y el 11-08 fue peor que el 11-06 (87 consultas NOAA-21 de 40 s o más contra 32; máximo 101,9 s contra 62,1 s) | n = 1 episodio; no decide |

## Correcciones a lo que se decía

- **El bloque S177 dice que el corte tocó guardia y sombra «mientras el NRT seguía verde».** El NRT no corrió de 19 a 23 UTC: entre la de las
  18:39 y la de las 23:25 no hay corridas, y esa brecha de unas 5 h ocurre todos los días (es la del horario, no un efecto del reproceso).
  Cuando corrió a las 23:25, sus búsquedas tardaron hasta 72,6 s (p95 60,4 s) y se salvó por poco.
- **Las sombras en rojo del 11-07 no son el mismo fenómeno.** Sombra de los 34: 1 conexión reseteada en un volcán (Lanín), no un ReadTimeout. Sombra de los 11: ConnectTimeout a
  `nrt3.modaps` en la descarga de MODIS Aqua, no búsqueda. Las fallas sin reproceso son 2 en 187 horas y ninguna es ReadTimeout.

## Lo que no se puede saber con esto

SIN DATO: el 11-08 sin reproceso; un umbral de carga; límites por token o IP (el censo sólo ve ReadTimeout, no registra 429 ni 503).

## Defectos del instrumento (verificador)

Las consultas por día exitosas no dejan marca, así que `consultas` subcuenta (SOSPECHA: unas 19.700 sin marca en el NRT contra 25.828 marcadas);
un proceso emite hasta 15 eventos por la misma causa, no son independientes; 54 de las 187 horas «sin reproceso» no tienen consultas; `reproc_medio`
contaba trabajos en cola (corregido en `analizar_cmr.py`). `timeout_nrt: 0` no quiere decir NRT sin afectación.

## Para D3 y D4

El riesgo medido no es que 6 trabajos saturen CMR, sino que el reproceso pierda días cuando NOAA-21 se pone lenta. Las pasadas NOAA-21 de F26 no entran a nada que
decida (`PREREGISTRO_RETRO_PAQUETE.md` §3.2), pero sí tumban el trabajo por la cobertura estricta. El remedio probado es `gh run rerun --failed`.
