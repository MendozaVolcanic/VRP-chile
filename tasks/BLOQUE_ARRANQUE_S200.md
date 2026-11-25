# Bloque de arranque S200 (escrito por S199, 2026-11-25 ~11:00 UTC)

> El bloque anterior (S199, escrito por S198) queda como histórico en `tasks/BLOQUE_ARRANQUE_S199.md`. Detalle de S199
> en la bitácora `tasks/LOOP_OBJETIVOS.md` §6 (entrada S199, arriba), en la nota viva
> `D:\vrp-trabajo\temporales\s199\s199_nota_viva.md` y, para Codex, en
> `D:\vrp-trabajo\temporales\s199_r4\ESTADO_COORDINACION_R4.md`.
> **Estado fijado CON TRABAJO EN VUELO:** (1) un agente de S199 termina el PR de R4FEF-109/106 en
> `D:\vrp-trabajo\worktrees\s199-r4fef-carga` (rama `s199-r4fef-carga`, dos commits locales `74318dddf` y `a94dbfc31`
> sin subir a las 10:55 UTC; corría sus pruebas); (2) la tanda 5 del piso (junio, run 45548099776) corre en Actions
> SIN cadena viva: S199 la detuvo para que S200 la relance en su propio proceso (§f). S199 cerró a ~551 mil tokens
> por pedido de Nicolás («puedes continuar en una nueva sesión, genérala tú mismo que no esté anidada»).

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| `main` | ficha **v1.102** (#1117 a #1123 hoy) | `git show origin/main:docs/FICHA_SDA_VRP_CHILE.md` |
| Acta del Cierre II (rondas 2 y 3) | **en main** | #1117, `docs/ACTA_CIERRE_AUDITORIA_CODEX_2026-11-24.md` |
| F6-112 pasadas no medidas | **en main y verificado en producción** (11 `data/cobertura/*.json`; 1 no medida en Planchón) | #1119 |
| R3F3-V101 aviso fondo no estimado | **en main** (14 pasadas antiguas) | #1120 |
| Panel de miniaturas (R4FB-104/105/106/V202) | **en main, verificado en Pages** (Láscar 24-nov 05:06: «Anomalía lejana, 12 km») | #1121 |
| Marca «angulo_ausente» (F8-107/F3-102/R3F3-102) | **en main** con A45 de Nicolás; neutralidad reproducida (98 escenas, sha256 igual; control 3 distintas); 80.129 records con ángulos válidos; NRT 06:10 verde, 0 casos | #1122, tag `pre-s199-sin-angulo`, `D:\vrp-trabajo\temporales\s199\sin_angulo\` |
| Propuesta de re-sello del evaluador del piso | **en main, espera a Nicolás** | #1123, `experiments/_s196_lab_piso/PROPUESTA_RESELLO_S199.md` |
| PR R4FEF-109 y 106 (JSON roto apaga el tablero; caché de cobertura) | **a medias** (agente de S199) | rama `s199-r4fef-carga` |
| Codex ronda 4 | 5 frentes **verificados**; registro 395 filas; **falta el cierre informado** | `D:\codex-vrp\_salida\ronda4\`, `RESUMEN_R4_PARA_NICOLAS.md` (borrador: faltan E+F y D) |
| Barrido del piso | abril y mayo cerrados y contados; junio en curso; julio a noviembre detrás | `D:\vrp-trabajo\temporales\s198\barrido\cadena.log`, `salida_contar_piso_t{3,4}.txt` |
| Issues | #1124 y #1125 (sombras sin corrida programada verde en 26 h, abiertos 08:59); #1106 (auto-audit, cierra el 2026-11-30) | `gh issue list` |
| Sesiones | S197, S198 y codex-ronda3 **archivadas** (Nicolás: «Sí, archívalas») | |
| Disco | C: 35 GB, D: 17 GB (10:51 UTC) | `df -h` |

## b. Decisiones que espera Nicolás

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Re-sellar el evaluador del piso (R4FD-V201: hoy sale INVÁLIDO por construcción porque producción guarda MODIS de día desde el 2026-11-15; más R4FD-101, 102, 105) | re-sellar ahora / dejar | **Re-sellar ahora**, antes de mirar resultados (#1123 tiene el detalle); el barrido sigue juntando datos mientras tanto |
| 2 | R3F3-104: reprocesar las 23 históricas sin marca «no medido» (hoy declaradas en ficha y D36) | reprocesar (A45) / dejar declaradas | Dejar declaradas (ninguna es protegida) |
| 3 | `C:\Users\nmend\AppData\Local\Temp-1` a `Temp-228` (1,8 GB, no VRP) | borrar / dejar | Preguntar de qué programa son; si no sabe, borrar |
| 4 | Heredadas del bloque S198 §b.7 (radios del visor, resto §14 de #1103, independencia C1, R-W7, marcador, LdM, PAT de `settings.json`) | | las del bloque S198 |

**Preguntas de Nicolás de S199 sin respuesta explícita:** ninguna. «Sí, archívalas», el A45 de la marca «sin ángulo»
y «sigue con todo» se cumplieron.

## c. Lo aprendido

- **REGLA GENERAL (memoria `feedback_s199_tmp_pack_git.md`):** cuando C: se llena sin archivo grande nuevo, mirar
  `git count-objects -vH`: 16,6 GB de `tmp_pack_*` de repacks cortados. Borrar sólo los de días anteriores, sin git
  corriendo, y `git fsck --connectivity-only`.
- **REGLA GENERAL:** el ejecutable de Codex cambia de ruta con cada actualización del paquete (26.1117 a 26.1120 al
  reiniciarse la app): `lanzar_r4.sh` la resuelve en cada arranque con `Get-AppxPackage OpenAI.Codex` + `cygpath`.
- **REGLA GENERAL:** Python en Windows escribe CRLF en una tubería; un `\r` pegado rompe la aritmética de bash
  (`invalid arithmetic operator`) y la cadena siguió sin esperar. `sys.stdout.reconfigure(newline="\n")` en el script.
  Y otra vez: Python dentro de un heredoc de bash rompe las barras invertidas; usar Edit.
- **REGLA GENERAL:** un perfil ciego de Codex debe negar también el registro consolidado y las carpetas de los
  verificadores que viven en la raíz de la ronda (S199 lo detectó y corrigió antes del ciego de E+F; probar cada
  perfil con `codex sandbox -p <perfil> python _prueba_lectura.py <rutas>`).
- **Proyecto:** un workflow que publica una rama por corrida con push simple se traba al relanzar si el primer intento
  dejó la rama parcial (#1118). Y el vigilante de las sombras sólo cuenta corridas programadas: un despacho manual verde
  no cierra sus issues.
- **Proyecto:** el `motivo_vacio` de la vía va anidado en el record; contar motivos leyendo el texto o recorriendo el
  record entero (S199 contó «todo None» al buscarlo en el primer nivel).

## d. Problemas abiertos e hipótesis

- **CONFIRMADO:** la sombra de los 34 del 24-nov 22:58 falló en 10 volcanes del sur por `ReadTimeout` del CMR (23:31
  UTC, corte de circuito); la re-despachada de las 05:40 terminó verde a las 06:59. #1124 (sombra código MIROVA, otro
  workflow, rojo el 24-nov 23:47) y #1125 siguen abiertos porque el vigilante sólo cuenta corridas programadas.
- **SOSPECHA:** las corridas programadas de esta noche cierran #1124 y #1125 solas.
- **SOSPECHA:** los 9 trozos rojos del primer intento de mayo fueron el CMR (salida 3 por cobertura estricta; el log
  público no trae el detalle). Se recuperaron al relanzar.
- **SIN DATO:** si el agente de R4FEF termina y abre el PR; mirar la rama y `gh pr list`.
- **CONFIRMADO:** el 2026-11-22 la sombra de los 34 falló sólo en Callaqui; causa sin revisar.

## e. Ya cerrado, no rehacer

- Acta del Cierre II: aprobada y en main (#1117). Rondas 2 y 3 cerradas con límites.
- Ronda 4: A, B, C, E+F y D verificados y consolidados; no repetir los frentes. A y C sin g3 (sus g2 son excepciones
  que hoy no ocurren y no callan); B arreglado en #1121.
- Marca «sin ángulo»: hecha y verificada (#1122). Producción aislada del laboratorio (verificado en el frente D).
- Lo de §e del bloque S199 sigue valiendo.

## f. Prompt para S200

```
Retomas VRP Chile como sesión dueña del loop (S200). Español de Chile, sin guiones largos, rutas absolutas.
Si te abrió otra sesión, mcp__ccd_session_mgmt__detach_session("self"). S199 cerró y no trabaja más.
Nicolás (2026-11-25 ~10:50 UTC): «continua con el loop y los planes por sensor y también del experimental y auditoria
de codex». Antes autorizó seguir sin preguntar cada paso, hasta 900 mil tokens por sesión o sesiones paralelas.

1. Verifica antes de creer: git fetch --prune; ficha de main (esperado v1.102 o más); gh pr list; gh issue list; df.
   - PR de R4FEF-109/106: ¿hay PR desde la rama s199-r4fef-carga? Si no, mira D:\vrp-trabajo\worktrees\s199-r4fef-carga
     (git status, git log origin/main..HEAD): termina, prueba, empuja y abre el PR con su fila para la ficha. Mergéalo
     con D:\vrp-trabajo\temporales\s195\merge\uno.sh (siguiente versión de la ficha; escribe antes fila_<N>.txt allí).
   - Piso: ps -ef | grep cadena_piso. Si no hay cadena, relánzala en segundo plano:
     bash D:/vrp-trabajo/temporales/s199/cadena_piso_s199c.sh 45548099776 t5   (espera junio, despacha julio a nov)
   - #1124 y #1125: si siguen abiertos tras las corridas programadas de la noche, revisa la causa (sombra código MIROVA).
2. Lee tasks/BLOQUE_ARRANQUE_S200.md (rama loop/activo), la entrada S199 de tasks/LOOP_OBJETIVOS.md §6, y los planes
   por sensor y del experimental en tasks/LOOP_OBJETIVOS.md §1 a §5 (qué sigue en MODIS, VIIRS 375, VIIRS 750 y el
   laboratorio). Para Codex: D:\vrp-trabajo\temporales\s199_r4\ESTADO_COORDINACION_R4.md.
3. Trabajo, en orden:
   a. Codex ronda 4, cierre: refresca la copia D:\codex-vrp a main (refrescar_copia.py desde bfcef8406, y git archive
      de data/miniaturas y data/cobertura; fijar_base_r4.py con la base nueva), mide el cupo (cupo.py) y lanza
      bash D:/vrp-trabajo/temporales/s199_r4/esperar_r4.sh cierre vrp_r4 D:/vrp-trabajo/temporales/s199_r4/cierre_r4.txt 180 85 3
      en segundo plano. Luego verificador Claude limpio (hacer_verificador_r4.py), consolidar_r4.py, y completa
      D:\codex-vrp\_salida\ronda4\RESUMEN_R4_PARA_NICOLAS.md (faltan E+F, D y el cierre).
   b. Los planes por sensor y del experimental de LOOP_OBJETIVOS (lo que esté listo sin decisión de Nicolás).
   c. Si Nicolás responde §b.1 (re-sello del piso) con sí: PR del evaluador corregido con pruebas que fallen con el de
      hoy, hashes nuevos en el pre-registro.
   d. Una ronda 5 de Codex sólo si Nicolás la pide o el cierre de la 4 deja frentes abiertos sin dueño.
4. Reglas duras: A45; merges con uno.sh en serie (esperar el MERGED del anterior; ficha al mergear con la versión
   siguiente a la de main y la fecha UTC del merge; --match-head-commit); nada de git stash; git add por archivo; nunca
   experiments/_s176_codex/; temporales y worktrees en D:; números sólo de scripts; .md con newline=""; nada de python en
   heredoc con barras invertidas (Edit); un vigilante por corrida; nunca pedir ni recibir tokens por el chat; verificar
   cada PR por cuenta propia (pruebas, neutralidad, producción) antes de mergear.
5. Cierra con /cierre al llegar al umbral de contexto (550 mil; Nicolás autorizó hasta 900 mil) y deja el prompt de S201.
```
