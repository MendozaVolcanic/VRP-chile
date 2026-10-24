# S162 MOD-C: lote de negativos `neg_resto` del port MODIS, resultado

2026-10-24 (UTC). Run **40120713181** (rama `s162-negmodis-disparo`, commit `ffc1abc1b` = `5f40f604d` + workflow; commit
base del port `0e18e1053`, tag `s162-base-portes`). Artefactos en `C:\vrp-trabajo\temporales\s162_negmodis\run_40120713181\`
(108 MB, recortes nativos incluidos). Lectura con el lector pre-registrado `07_leer_lote.py` → `07_leer_lote_salida.txt`.
Pre-registro: `PREREGISTRO.md` (con las adendas 1 y 2). **Pendiente: verificador con contexto limpio del resultado.**

## En una pantalla

1. **Veredicto pre-registrado: INDECIDIBLE.** El port publica en **2 de 390** pasadas evaluables del estrato donde MIROVA
   miró y no vio nada y producción calla. Con la regla sellada (Jeffreys, n ≈ 400), sólo 0 confirmaba el «gana contra
   K»; de 1 a 7 queda INDECIDIBLE. ΔE total: punto **−18,1** (sigue a favor del port), IC 95 % **[−43,8; +40,1]**.
2. La tasa del port en el estrato es **0,51 %** cruda (0,53 % ponderada), del orden de lo que K publica en todos los
   negativos limpios (0,76 %). R3 (publicación ponderada en los 5.132 negativos) **REPRODUCE** (IC 0,14 % a 1,66 %).
3. Las dos publicaciones son de un solo píxel cerca de la cumbre: Láscar 2026-05-11 07:55 (0,30 MW, a 1 km del centro,
   cenit 38°) y Llaima 2026-07-24 01:05 (0,43 MW, a 2 km, cenit 63°). Láscar tiene una fuente persistente en el cráter:
   puede ser calor real que la tabla de MIROVA dejó en RUTINA; Llaima a 63° es una pasada muy oblicua. SOSPECHA las dos.
4. **Instrumento sano**: K re-corrido = lo publicado en 403 de 403; los 13 controles dan lo mismo que en S159 y las 11
   protegidas publican (incluidas las 3 de Chillán sobre 50°); recorte nativo guardado en las 403 evaluables.
5. **Lo que deja**: el «gana contra K» de MODIS sigue sin resolver por este estrato, pero ahora con su tasa medida
   (0,5 %, no la cota de 9,4 % de S159). Resolverlo pediría otro lote (decisión de Nicolás, §10 del pre-registro); el
   censo de MOD-D lo mide entero.

## Controles (leídos antes de x)

| control | resultado | denominador |
|---|---|---|
| cobertura (A108) | 413 de 413 con resultado; no evaluables: 8 «volcán fuera del gránulo» y 2 «escena inválida», fuera de n | 413 |
| K re-corrido = publicado | publica igual 403 de 403; `pc.vrp_mw` a 0,001 MW 403 de 403 | 403 evaluables |
| control de instrumento contra S159 | 13 de 13 iguales en npix; 11 de 11 protegidas publican | 13 |
| recorte nativo | guardado en 403 de 403 | 403 |
| prueba sin red del envoltorio (job `prueba`) | success | |

Los 7 trozos en rojo son los que tienen alguna pasada no evaluable, como prevé el §9 del pre-registro (el trozo sale
con código 2 y sube el artefacto igual); ningún trozo tuvo errores de proceso.

## Por estrato (informa)

Por volcán: Láscar 1 de 20, Llaima 1 de 38, los otros nueve 0 (Chaitén 0 de 45, Villarrica 0 de 40, Cordón Caulle 0 de
39, ...). Por cenit: 1 de 168 hasta 40°, 1 de 222 sobre 40°. Por plataforma: Aqua 1 de 200, Terra 1 de 190. Por tramo
#535: 2 de 308 antes, 0 de 82 desde. Partidas: 0 de 4. Contra K re-corrido en vez del publicado: x = 2 igual.

## Qué sigue

- **Verificador limpio** del resultado antes de darlo por aceptado.
- **MOD-E**: los 403 recortes nativos ya permiten la ablación real del bow tie (sobre negativos y los 11 controles
  protegidos), con un método de quitar duplicados sin huecos y la clasificación por costura de barrido.
- **MOD-D**: su censo mide el estrato entero (5.093) con el mismo port.
