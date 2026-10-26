# Verificador v3 del pre-registro V375-B2: control de vida, NO DECIDE por cobertura y línea «VEREDICTO B»

## Encabezado

- Hora del servidor al empezar: **Sat, 24 Oct 2026 20:12:27 GMT** (`gh api -i repos/MendozaVolcanic/VRP-chile`, header `Date`).
- Worktree: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs375-c1b864`, HEAD `0ce665854`.
- Versión 2 del pre-registro: `7ff23cc3a3814811d4530579ecc59d3554ae7f6f`. Versión 3: tag `s162-v375-b2-listo` = `ae65eaaaf5f8f200b56b5b8e09635e440fd290fb`.
- sha256 de `experiments\_s162_v375\b2\objetivos_v375_b2.json` en el árbol: `f3285f3ae46ad8433f87e9fc7ceaa8f210833806b32672554f3ba7f2d8a8b419` (coincide con el `f3285f3a…b419` del pre-registro §3).
- Modelo: Claude Fable 5.1, contexto limpio (sólo recibí el encargo; no leí la bitácora de S162 ni los informes de los verificadores v1 y v2).
- Qué NO miré: el resto del diseño de B2 (muestra, tamaño, pesos, regla de B, cuentas de la sección 3 y 4), el workflow más allá de cómo reparte las pasadas, y la prueba del autor (`prueba_control_vida\`), que NO leí ni corrí (la instrucción era hacer la mía primero; al terminar la mía no la abrí para no mezclar). Tampoco toqué nada fuera de `verificador_v3\` (comprobado con `git status --short`: sólo `?? experiments/_s162_v375/b2/verificador_v3/`). No hice commits ni despachos ni usé credenciales.
- Artefactos falsos (1,8 GB) fuera del repo: `C:\vrp-trabajo\temporales\s162_v375\verif_v3\<caso>\`. Disco al cerrar: C 38 GB libres, D 9,6 GB.

## En una pantalla

**CONFORME, con dos observaciones de gravedad 2 y una de gravedad 3 que no bloquean el despacho.** El control de vida 2.2b atrapa por sí solo (sin ayuda del recálculo 2.1) un port que no detecta nada, uno que detecta todo, uno con la magnitud doblada, uno muerto sólo en el CTL, uno que se cae en 3 de 20 del CTL y la ausencia total de artefactos del CTL: en los seis casos la línea «VEREDICTO B» de 4b dice INVALIDO POR INSTRUMENTO. La regla del 10 % del lote que decide da «VEREDICTO B: NO DECIDE» con 144 de 1.200 caídas. Con un lote sano y completo el instrumento queda OK y «VEREDICTO B: SILENCIO ACOTADO BAJO K», así que el control no bloquea siempre. La referencia del control sale de los artefactos del run S162 (`run_40116289866`), no del run que se prueba: 20 de 20 `ref_M14` comprobados contra los JSON, 16 con píxeles. Lo que queda abierto: el control existe sólo si el archivo de objetivos trae el lote CTL (con el `objetivos_v375_b2.json` de la v2, un port muerto sigue dando SILENCIO ACOTADO con el instrumento OK: la fuerza del arreglo vive en un archivo de datos, no en el evaluador), y el CTL sí entra a los denominadores de 2.1 y 2.2 aunque el texto diga «fuera de todo denominador».

## Caminos escritos ANTES de leer el delta (copiado de `CAMINOS_PREVIOS.md`, con su desenlace)

| # | camino | desenlace |
|---|---|---|
| 1 | el control compara el run consigo mismo | NO: `ref_M14` viene de `objetivos_v375_b2.json`, escrito por `seleccion_b2.py` leyendo `run_40116289866`; `comprobar_ref.py` lo cotejó contra esos JSON: 20 de 20 iguales |
| 2 | la referencia sale de la caché recalculada, no de lo que el runner escribió | NO: `evaluar.py:721` compara `arms[i]["M14"]` que para lotes no S159 es `r["port"]` del runner (`evaluar.py:647`), contra `ref_M14` del archivo; la caché sólo interviene en 2.1 |
| 3 | port muerto coincide por azar con pasadas en 0 | NO: 16 de las 20 tienen píxeles en S162; el caso `muerto` da «iguales 4; con píxeles 0» e INVALIDO |
| 4 | detecta todo / magnitud corrida pasa porque se compara algo binario | NO: compara `npix` exacto y `vrp_mw` a 1e-6 MW; `todo` y `magx2` dan INVALIDO. Límite declarado: un corrimiento bajo 1e-6 MW pasa (`magx1e7`), que es lo que la regla dice |
| 5 | las caídas del CTL se excluyen del 18 de 20 | NO: `ok_ctl` son las que están en `arms`; una caída no entra y cuenta contra el 90 % (`caida_ctl3` da 17 de 20 e INVALIDO) |
| 6 | umbral 18 de 20 deja pasar un port roto sólo en una clase de pasadas | PARCIAL, por diseño: 2 caídas pasan (`caida_ctl2`, ver tabla). El CTL tiene 11 Láscar, 3 Chillán, 2 Lastarria, 3 Chaitén, 1 Tupungatito, 1 Llaima; un port roto SÓLO para una plataforma o un tramo que no esté entre esas 20 no lo ve este control (SOSPECHA, no medido: no fabriqué ese caso) |
| 7 | el NO DECIDE no llega al veredicto | NO: `caida_lote12` imprime «VEREDICTO B: NO DECIDE (cobertura del lote que decide: ['cobertura_S162b_neg_resto'])» |
| 8 | la línea VEREDICTO B dice otra cosa que la regla | NO en lo probado: INVALIDO prevalece sobre NO DECIDE y sobre la decisión (`evaluar.py:856-861`); en `todo` la decisión del lote era ENCIENDE DE MAS y la línea dice INVALIDO |
| 9 | los ids 5000 a 5019 entran a algún denominador | SÍ, en parte: `armar` los excluye de las filas (`evaluar.py:250`) y la cobertura por clase no los cuenta (clase `control_vida` no está en la tupla), pero 2.1 y 2.2 sí los cuentan (hallazgo 2) |
| 10 | el evaluador decide sin CTL si el archivo no lo trae o los artefactos faltan | artefactos ausentes: NO (`sin_ctl` da 0 de 20 e INVALIDO). Archivo sin CTL: SÍ (hallazgo 1, `muerto_v2obj`) |
| 11 | tolerancia laxa o comparación agregada | NO: por pasada, `npix` exacto, 1e-6 MW (`TOL_RECALCULO_MW`, `evaluar.py:64`) |
| 12 | CTL ausente se trata como «no aplica» | NO cuando faltan los artefactos (INVALIDO); SÍ cuando falta en el archivo de objetivos (hallazgo 1) |
| 13 | la prueba del autor podría fallar por 2.1 y no por 2.2b | no la miré; la mía aísla 2.2b con la caché envenenada (abajo) |

## Método del paso 2 (cómo se fabricó el nulo)

`fabricar.py` (en esta carpeta) construye para cada caso una carpeta `C:\vrp-trabajo\temporales\s162_v375\verif_v3\<caso>\s162-v375-b2-N\` con `resultados_VIIRS375_NN.json` y `grilla_NNNN.npz` para los 1.220 ids de `objetivos_v375_b2.json`:

- Cada pasada del lote S162b (3000 a 4199) toma como donante un record ok de `neg_resto` de S162 **del mismo volcán** (la grilla es fija por volcán: 1 grilla distinta por volcán en los 1.929 objetivos de S162 + B2, comprobado), con el id cambiado y la grilla copiada byte a byte (mismo sha256).
- Cada pasada del CTL (5000 a 5019) copia el record y la grilla de su `id_ref`.
- La caché de brazos se traslada de `id_donante|sha` a `id_nuevo|sha` (`cache_lote.json` copiada a `cache_lote_copia.json`). Con `--cache-envenenada`, la entrada M14 de la caché lleva el port **fabricado**: eso simula que el código del evaluador está roto igual que el del runner, de modo que el recálculo 2.1 (que compara runner contra recálculo local) no puede ver la rotura y **sólo 2.2b puede atraparla**. En el caso sano el recálculo 2.1 corrió honesto y dio 19.627 de 19.627.
- `correr.sh <caso>` corre `evaluar.py` con el comando base del encargo (`--deciden S162b --neg-pub-de S162`, `--art-extra` apuntando al caso). Salidas: `salida_<caso>.txt` y `.json` en esta carpeta; resumen por lote en `lote_A.log`, `lote_B.log`, `lote_C.log`.

## Tabla caso por caso (paso 2 y 3)

| caso | qué se rompió | 2.1 recálculo | 2.2b (ok / iguales / con píxeles) | instrumento | VEREDICTO B obtenido | esperado | ¿correcto? |
|---|---|---|---|---|---|---|---|
| `sano` | nada; CTL copia S162 tal cual | 19.627 de 19.627 | 20 / 20 / 16 | OK | SILENCIO ACOTADO BAJO K | distinto de INVALIDO | sí (paso 3) |
| `muerto` (caché envenenada) | M14 en 0 en TODO B2 y CTL | 19.627 de 19.627 (no lo ve) | 20 / 4 / 0 | INVALIDO `['control_vida']` | INVALIDO POR INSTRUMENTO | INVALIDO | sí, **2.2b solo** |
| `muerto_honesto` (caché del donante) | igual que `muerto` | 19.593 de 19.627 (lo ve: `recalculo`) | 20 / 4 / 0 | INVALIDO `['recalculo','control_vida']` | INVALIDO POR INSTRUMENTO | INVALIDO | sí; 2.1 también lo atrapa, pero 2.2b dispara igual |
| `muerto_solo_ctl` (envenenada) | M14 en 0 sólo en las 20 del CTL; lote sano | 19.627 de 19.627 | 20 / 4 / 0 | INVALIDO `['control_vida']` | INVALIDO POR INSTRUMENTO | INVALIDO | sí |
| `todo` (envenenada) | M14 caliente fijo (5 px, 1,41 MW) en TODO | 19.627 de 19.627 | 20 / 1 / 20 | INVALIDO `['control_vida','control_nunca']` | INVALIDO POR INSTRUMENTO | INVALIDO | sí (la decisión del lote habría sido ENCIENDE DE MAS; la línea dice INVALIDO) |
| `magx2` (envenenada) | `vrp_mw` × 2, `npix` igual, en TODO | 19.627 de 19.627 | 20 / 4 / 16 | INVALIDO `['control_vida']` | INVALIDO POR INSTRUMENTO | INVALIDO | sí |
| `magx1e7` (envenenada) | `vrp_mw` × (1 + 1e-7), bajo la tolerancia | 19.627 de 19.627 | 20 / 20 / 16 | OK | SILENCIO ACOTADO BAJO K | pasa (límite declarado de 1e-6 MW) | sí, es el límite escrito en §4 |
| `caida_ctl3` | 3 CTL con `estado = error`, lote sano | 19.597 de 19.597 | 17 / 17 / 13 | INVALIDO `['control_vida']` | INVALIDO POR INSTRUMENTO | INVALIDO (17 < 18) | sí |
| `caida_ctl2` | 2 CTL con `estado = error`, lote sano | 19.607 de 19.607 | 18 / 18 / 14 | OK | SILENCIO ACOTADO BAJO K | pasa por diseño («al menos 18 de 20») | sí: el borde de la regla está donde el texto lo pone (18 pasa, 17 no) |
| `caida_lote12` | 144 de 1.200 del lote S162b con `estado = error`; CTL sano | 18.187 de 18.187 | 20 / 20 / 16 | OK, aviso `cobertura_S162b_neg_resto` | NO DECIDE (cobertura del lote que decide: ['cobertura_S162b_neg_resto']) | NO DECIDE | sí |
| `sin_ctl` | ningún artefacto del CTL (ni JSON ni grilla) | 19.427 de 19.427 | 0 / 0 / 0 | INVALIDO `['control_vida']` | INVALIDO POR INSTRUMENTO | INVALIDO | sí |
| `muerto_v2obj` | M14 en 0 en TODO, pero `--objetivos-extra` es el archivo de la **v2** (`7ff23cc3a`, sin CTL) | 19.427 de 19.427 | **no se imprime** (no hay CTL) | **OK** | **SILENCIO ACOTADO BAJO K** | debería no poder decidir | **NO**: es el agujero del verificador v2 tal cual, reaparece si el archivo no trae el CTL (hallazgo 1) |

Lectura de la columna «2.1»: en los casos con caché envenenada el recálculo sale 100 % igual al runner a pesar de la rotura, así que la invalidación es obra **sólo** del control de vida. Eso responde a la pregunta del encargo: el control atrapa por sí solo.

## Hallazgos

### H1. El control de vida existe sólo si el archivo de objetivos trae el lote CTL; el evaluador no exige que exista (gravedad 3, confianza 5)

- Dónde: `experiments\_s162_v375\evaluar.py:715-716` (`ctl = [...]; if ctl:`); `correr.sh muerto_v2obj b2/verificador_v3/objetivos_v2_7ff23cc3a.json` → `salida_muerto_v2obj.txt`.
- Qué pasa: con un port muerto (M14 en 0 en las 1.200) y el `objetivos_v375_b2.json` de la versión 2 (sin ids 5000 a 5019), el evaluador no imprime la línea 2.2b, deja el instrumento en OK y escribe «VEREDICTO B: SILENCIO ACOTADO BAJO K». Es exactamente la falla que el verificador v2 reprodujo. El arreglo está bien hecho, pero su fuerza depende de que el archivo de objetivos del run sea el v3: nada en `evaluar.py` falla si `--deciden` incluye un lote nuevo y no hay ningún lote CTL, ni comprueba que el CTL tenga al menos una pasada con `ref_M14[0] > 0`.
- Por qué importa: el workflow (`b2\probe-s162-v375-b2.yml:22`) lee `experiments/_s162_v375/b2/objetivos_v375_b2.json` del checkout de la rama de disparo. Si la rama de disparo se arma desde un commit anterior al tag, o si alguien regenera el archivo con `seleccion_b2.py` sin la carpeta `ART162` a mano (el script asume `C:/vrp-trabajo/...`, `seleccion_b2.py:34`), el lote corre sin control y el evaluador no avisa. Hoy el archivo del árbol sí trae las 20 (sha `f3285f3a…b419` comprobado).
- Reproducir: `sh correr.sh muerto_v2obj b2/verificador_v3/objetivos_v2_7ff23cc3a.json` tras `python -I fabricar.py --caso muerto --cache-envenenada --objetivos objetivos_v2_7ff23cc3a.json` (y renombrar la carpeta a `muerto_v2obj`).
- Qué cerraría el agujero (no lo implemento, verificar no es arreglar): que `evaluar.py` declare INVALIDO POR INSTRUMENTO cuando algún lote de `--deciden` no es S162 y no existe ningún objetivo con `lote == "CTL"` y `ref_M14[0] > 0`; y que la coordinadora compruebe el sha del archivo en el checkout del run antes de leer.

### H2. «Fuera de todo denominador» no es literal: el CTL entra a 2.1 y a 2.2 (gravedad 2, confianza 5)

- Dónde: `evaluar.py:623-650` (2.1 recorre `ok`, que incluye el CTL) y `evaluar.py:685-691` (2.2 recorre `arms`, que incluye el CTL); `PREREGISTRO_B2.md` §4 («fuera de todo denominador») y `seleccion_b2.py` comentario («no entran a ningún denominador»).
- Qué pasa: en el caso sano 2.1 da 19.627 = 7.427 (S159 + S162) + 1.220 × 10, y 2.2 da 2.067 = 847 + 1.220. Las 20 re-medidas se cuentan dos veces en esos dos controles (una como S162, otra como CTL). No cambia ningún veredicto: 2.1 y 2.2 son controles del instrumento, no la cuenta de B, y `armar` sí las excluye de las filas que deciden (`evaluar.py:250`). Pero el texto promete algo más fuerte de lo que el código hace, y una CTL que no reproduzca su propio recálculo invalidaría por `recalculo` además de por `control_vida`, lo cual es deseable pero no está dicho.
- Reproducir: `grep "2.1 recálculo\|2.2 K" salida_sano.txt`.

### H3. La regla del 10 % del lote que decide no mira la clase `neg_pub`, que viene de S162 (gravedad 1, confianza 4)

- Dónde: `evaluar.py:855` (`hueco` busca `cobertura_{l}_` sólo para `l in a.deciden`, o sea `S162b`); `neg_pub` del conjunto que decide sale de `--neg-pub-de S162`.
- Qué pasa: un hueco de cobertura en `neg_pub` de S162 produciría `cobertura_S162_neg_pub`, que no empieza por `cobertura_S162b_` y no da NO DECIDE. Hoy es inofensivo: S162 ya está medido (113 de 113 neg_pub ok, `salida_sano.txt:8`) y no se vuelve a correr. Lo anoto porque la regla escrita («si el lote que decide pasa el 10 %») y la implementada («si un lote de `--deciden`») no coinciden en el borde.

### H4. El umbral de 18 de 20 y la composición del CTL dejan sin vigilar roturas que afecten sólo a una plataforma o tramo (gravedad 2, confianza 3, SOSPECHA)

- Dónde: `objetivos_v375_b2.json` ids 5000 a 5019; `seleccion_b2.py:95-105`.
- Qué pasa: el CTL tiene 11 pasadas de Láscar, 3 de Chillán, 3 de Chaitén, 2 de Lastarria, 1 de Tupungatito y 1 de Llaima; no comprobé el reparto por plataforma (Suomi NPP, NOAA-20, NOAA-21) ni por tramo (T, O1, O2) porque está fuera del encargo, pero una rotura que sólo afecte a una combinación ausente de esas 20 no la ve este control, y una que afecte a 2 de las 20 tampoco (`caida_ctl2`, por diseño). Es un límite, no un defecto: el control está diseñado para «port muerto o dependencia rota», que afecta a todo, y para eso sobra. No fabriqué ese caso.

### H5. El CTL re-descarga el gránulo por patrón `{sn}.{tag}.{col}*`, no por nombre exacto (gravedad 2, confianza 4, SOSPECHA de falso INVALIDO)

- Dónde: `experiments\_s159\portes\probe_portes.py:104` (`_buscar(sn, ver, f"{sn}.{tag}.{col}*")`, toma `h[:1]`).
- Qué pasa: si LAADS reprocesó alguno de los 20 gránulos (o su geolocalización VJ103) entre el run S162 y el de B2, el runner bajaría un archivo distinto, los píxeles podrían moverse en 1e-6 MW o más y el control daría INVALIDO sin que el port esté roto. Es el error conservador (bloquea en vez de dejar pasar), y los nombres de S162 son de colección 021 estándar, pero conviene saberlo para no leer un INVALIDO del CTL como «port roto» sin mirar la lista `distintas` y el campo `archivos` de los dos runs.

### Lo que sostiene el CONFORME (positivos del cambio)

- `ref_M14` de los 20 coincide con `port.M14` del `id_ref` en los JSON de `run_40116289866` (npix, vrp, gránulo, hora, volcán, clase), 16 con píxeles y 4 en 0 (`comprobar_ref_salida.txt`). Ninguna CTL repite una pasada del lote S162b.
- El runner reparte `objs` con `n % 48` sin filtrar por lote (`probe_v375.py:133`), así que las 20 van en los trozos 0 a 19 del mismo run.
- M14 es reproducible entre máquinas a 1e-6 MW: el recálculo local en Windows reprodujo las 10 × 847 medidas del runner Linux de S162 (`resultado_run40116289866\evaluar_salida.txt:16`, 7.427 de 7.427), y `brazos.py` no tiene `argsort` ni `sort` (`grep`): el riesgo A152 de desempates por CPU no aplica a M14. Por eso la tolerancia de 1e-6 no debería invalidar un run sano.
- Prioridad de la línea «VEREDICTO B» (`evaluar.py:856-861`): INVALIDO > NO DECIDE > decisión del lote (si acuerda con la unión) > NO RESUELTO. Comprobado en `todo` (decisión ENCIENDE DE MAS, línea INVALIDO) y `caida_lote12` (decisión SILENCIO ACOTADO, línea NO DECIDE).
- Texto y código coinciden en los tres números del control: 18 de 20 (`len(ok_ctl) < 0.9 * len(ctl)` deja pasar exactamente 18), 1e-6 MW (`TOL_RECALCULO_MW`), «alguna con píxeles» (`not vivos`).

## SIN DATO

- No corrí ni leí `prueba_control_vida\` del autor; no puedo decir si su caso muerto cae por 2.1 o por 2.2b.
- No medí el reparto del CTL por plataforma ni por tramo (H4).
- No comprobé qué commit tiene la rama de disparo `s162-v375-b2-disparo` ni si existe: el encargo prohíbe despachar, y verificar el archivo que el run va a leer es tarea de la coordinadora (H1).
- (`caida_ctl2` quedó leído: 18 de 20, instrumento OK, SILENCIO ACOTADO BAJO K; no queda nada pendiente de las 12 corridas.)

## Archivos de esta carpeta

`CAMINOS_PREVIOS.md` · `comprobar_ref.py` + `comprobar_ref_salida.txt` · `fabricar.py` · `correr.sh` · `cache_lote_copia.json` · `objetivos_v2_7ff23cc3a.json` (extraído con `git show`, no editado) · `salida_<caso>.txt|json` · `stdout_<caso>.txt` · `lote_A.log`, `lote_B.log`, `lote_C.log`.
