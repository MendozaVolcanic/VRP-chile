# Bloque de arranque S128

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S127. Esa sesión desbloqueó el A/B de la corona —que
había salido inconcluso dos veces por un bug de cableado— y barrió un eje de
auditoría que ninguna de las tres anteriores había tocado.

Leé en este orden:
  1. docs/AUDIT_S127.md                (los 8 hallazgos, con sus guards)
  2. docs/S127_CORONA_RESULTADO.md     (el veredicto del 2×2, ya leído)
  3. docs/S126_COSTO_FILTRO_CONTEXTUAL.md   (la causa raíz: el fondo autorreferente)
  4. tasks/BLOQUE_ARRANQUE_S128.md     (esto)

⚠️ **Y si vas a hacer la auditoría S128, el prompt completo es otro archivo:**
`tasks/PROMPT_AUDITORIA_S128.md` — 494 líneas, tres fases, con el frente
bibliográfico armado para lanzar con agentes. Diseño y justificación en
`docs/superpowers/specs/2026-08-30-auditoria-s128-design.md`.

═══════════════════════════════════════════════════════════════════════════
EL 2×2 YA SE LEYÓ — veredicto NO ADOPTAR, y Láscar tiene camino
═══════════════════════════════════════════════════════════════════════════

Los dos brazos que faltaban corrieron sobre el código arreglado y el veredicto
está en `docs/S127_CORONA_RESULTADO.md`. Resumen:

| volcán | n | control | corona | ctx_off | corona+ctx_off |
|---|---|---|---|---|---|
| Villarrica | 8 | 0,832 ✓ | 0,877 ✓ | 1,315 ✓ | 0,912 ✓ |
| Planchón-Peteroa | 13 | 1,036 ✓ | 1,000 ✓ | 6,636 ✗ | 2,631 ✗ |
| Láscar | 36 | 0,501 ✗ | 0,569 ✗ | 0,635 ✗ | **1,242 ✓** |
| PCC | 22 | 0,728 ✓ | 0,726 ✓ | 1,141 ✓ | 1,036 ✓ |
| NdC | **3** | 1,543 ✗ | 1,167 ✓ | — | 16,467 ✗ |
| **en banda** | | 3/5 | **4/5** | 2/5 | 3/5 |

**NO ADOPTAR el brazo corona**: falla el criterio 2 (Villarrica sube 0,045 en vez
de bajar) y el 5 (8 detecciones perdidas de 2.179). El veredicto se lee, no se
interpreta.

**Pero leelo completo antes de darlo por cerrado**, porque hay tres matices que no
están en el titular:

  · Las 8 pérdidas son TODAS de un píxel, 0,021-0,042 MW, y **ninguna cae en noche
    con contraparte MIROVA**. Mecánicamente es la corona haciendo lo suyo.
  · El criterio 4 pasa **por empate en cero**: el evento NdC 06-16 no dispara en
    ninguno de los dos brazos. No lo leas como «la corona lo preserva».
  · La corona es el ÚNICO brazo que **sube** el conteo en banda (3/5 → 4/5) sin
    sacar a nadie.

**Lo nuevo de verdad**: la celda que nadie había corrido confirma el mecanismo de
S126. Corona + filtro contextual apagado lleva **Láscar de 0,501 a 1,242** — en
banda por primera vez en todo el frente de magnitud, exactamente como se predijo
(bajo fondo local un píxel de terreno se autocancela, así que vuelve seguro
incluir el segundo píxel que a Láscar le falta).

No generaliza: Planchón queda en 2,631 (su problema es el complejo multi-cráter,
A22, no el fondo autorreferente) y NdC da 16,467 con **n=3**, muestra demasiado
chica para usar.

**Frente abierto para S128**: acotar «corona + filtro apagado» para que cure a
Láscar sin romper a Planchón. Eso pide **separar los dos mecanismos**, no un
umbral más — y MISSION excluye lo per-volcán, así que el discriminante tiene que
ser físico y uniforme.

⚠️ Y una corrección al pre-registro que conviene recordar: predijo que la corona
sola le bajaría ~20 % a Láscar. **Subió 13,6 %** y ganó 3 detecciones. Es A18: el
preview read-only no predice el reproceso real.

═══════════════════════════════════════════════════════════════════════════
LO QUE ESPERA AL VEREDICTO (no antes, a propósito)
═══════════════════════════════════════════════════════════════════════════

  · **Piso VRP — YA SE PUEDE DECIDIR**. Estaba condicionado a leer el A/B de la
    corona, y el A/B está leído. La corona no desinfló el artefacto de los nevados
    lo suficiente como para cambiar el análisis, así que la recomendación de S126
    sigue en pie: **quitarlo** (hoy es un no-op que además miente) y **NO**
    aplicarlo a `pc.vrp_mw`, porque cortaría el cráter de Láscar e Isluga.
  · **Villarrica**: mide a 2,8 km del cráter incluso con actividad confirmada, y
    VIIRS 375 no ve su lava lake (contraste −0,73 K en el campo de MIROVA). Es
    artefacto, no señal → por A72 se arregla en el algoritmo. Si la corona
    funciona, buena parte debería caerse sola.
  · **D12** (FN MODIS): congelada, cierre formal pendiente de Nicolás.

═══════════════════════════════════════════════════════════════════════════
DECISIONES QUE ESPERAN A NICOLÁS
═══════════════════════════════════════════════════════════════════════════

  1. **~112 MB del probe S104** (`experiments/_s104_roi_probe/{anchor_a,anchor_b,
     baseline_mir,local_k*,nti_integral}`) siguen sin trackear. Son RESULTADO —
     respaldan A69— no intermedio. Commitear, dejar, o borrar para recuperar
     disco. ⚠️ Un tag defensivo A38 **no los protege**: para eso tendrían que
     estar en git primero.
  2. **Disco C al 98 %** (15 GB libres). La higiene de S127 dejó de ensuciar
     `git status` pero no liberó espacio — no se borró nada a propósito.

═══════════════════════════════════════════════════════════════════════════
LA AUDITORÍA S128 — armada y verificada como ejecutable
═══════════════════════════════════════════════════════════════════════════

Prompt completo: `tasks/PROMPT_AUDITORIA_S128.md`. Tres fases:

  **Fase 1 — la deuda, que es la puerta de entrada.** Los 28 pendientes (19 de
  S121 + 9 de S125, ya enumerados en el prompt). Dos de ellos son fundamento de
  decisiones vivas: el `r = −0,23` que sostiene «la máscara no es el driver del
  gap» NO tiene script, y A54.

  **Fase 2 — el eje exógeno**, que ninguna de las once auditorías usó: nuestros
  datos contra el archivo de TIF de MIROVA. Cinco sondas. La más filosa (P2):
  en los 11,6 días del archivo, Copahue, Lastarria y Tupungatito no tienen
  NINGUNA escena con contraste al cráter, y nosotros publicamos **91, 79 y 87**
  detecciones. Sería el primer falso positivo nuestro afirmado con evidencia
  EXTERNA en 127 sesiones.

  **Fase 3 — el frente bibliográfico**, marcado primordial por Nicolás y armado
  para lanzar con agentes. Faltan **tres papers del canon MIROVA** —el crítico es
  Coppola 2014, que es la autoridad que Laiolo cita para el sub-MW— y hay **24
  papers en el repo sin leer** que caen justo en los frentes abiertos, incluidos
  Frey 2008 (tests nocturnos de nube) y Coppola 2013 (fuente primaria de c_rad,
  que hoy citamos de segunda mano).

Verificado como ejecutable, no asumido: los 28 pendientes son localizables ·
`rasterio` instalado · el archivo TIF está local · nuestros records cubren su
ventana (1.551 records, 970 con vrp>0). Lo único que puede trabarse es la sonda
P4 (re-descarga de granules con el disco al 98 %).

**Y las tres reglas de método nuevas**, que salieron de medir las once auditorías
previas y están en `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md`:
  A. prohibido repetir el barrido general de 6-8 ejes (rindió 0 % y 8 %);
  B. cierre por GUARD, no por corrección (S127 es la única sin reincidencias);
  C. los pendientes se publican y son la puerta de entrada de la siguiente.

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ESTA ETAPA (las de S126 siguen, más una)
═══════════════════════════════════════════════════════════════════════════

  · **A89 (nueva)**: «no aparece en ningún lado» casi nunca significa que no esté.
    Un `grep` que no encuentra no falla: devuelve CERO, y el cero se lee como
    ausencia. Cinco falsos negativos en S127 por esto, en tres formas — parámetro
    vs clave del YAML, clave heredada por `extends:`, llamada calificada o
    renombrada en el import. **Las cinco veces el error fue de quien auditaba.**
  · Verificar flags leyendo `pipeline.profile`, NUNCA el YAML. Resuelve `extends:`,
    la sección correcta y los duplicados de una sola vez.
  · ESTRATIFICAR POR VOLCÁN, no sólo por sensor (una mediana agrupada invirtió el
    veredicto del brazo E en S125).
  · Un par por NOCHE, máximo de ambos lados.
  · Verificar el EFECTO sobre los datos, no confiar en que el cambio hizo lo que dice.
  · Helpers comunes en `experiments/_s126_lib.py`. Reusarlo.
```

---

## Estado al cerrar S127

**Suite**: 998 tests verdes. **NRT**: sano. **Operacional intacto**:
`corona375=False · corona_modis=False · ctx_filter=True · cloud_mask=0.0 · focal=True`.

**PRs mergeados**: #546 … #557 (trece).
**Tags defensivos**: `pre-s126-corona-viirs` (ya existía) · `pre-s127-wipe-corona-arms`.

### Lo que quedó PROBADO

| hallazgo | cómo se probó |
|---|---|
| **La corona se calculaba y se tiraba** | corrió en 1.179 de 1.278 records y sólo movió 15; los 1.164 restantes tenían `single_pixel_mode=True` |
| El invariante que lo demuestra | para un clúster de UN píxel, suma ≡ máximo; que el modo lo mueva sólo puede ser dos fondos distintos |
| **En MODIS era peor y latente** | `cluster_focal_vrp_mw` (ENCENDIDO) reasigna sin condición justo después → anulación del 100 %, sin marca |
| `sum()` de Python 3.12 no es el acumulador viejo | suma compensada de Neumaier, 1 ULP; se agregó `sum_cluster_vrp` naive para poder probar el no-op estricto |
| `single_pixel_mode` «NO afectados» | **falso para los 7**; Láscar 33,9 % es el más afectado, Tupungatito 7,5 % el menos |
| «el kernel nunca corre en producción» | falso: corre en 5 de los 11 Tier A |
| 2 claves bajo `paths:` que el código no lee | 31 de 51 perfiles; limpieza probada no-op sobre los 51 |
| El schema no tiene campos muertos | los 84 campos de producción tienen lector |
| 9 de 13 mecanismos asimétricos entre sensores | matriz nueva; nadie la había hecho |
| **D17 confirmada** | `get_grid_center()` sin llamador, regrid centrado en `volcano_lat/lon`, `ENABLE_UTM_REGRID` OFF |
| El job `merge` que se cancelaba | `group: push-main` a nivel job + GitHub mantiene 1 run pendiente por grupo |
| **El fix del merge FUNCIONA** | los dos `merge` corrieron a 8 min de distancia (09:50 y 09:58) y ninguno canceló al otro — primera prueba real |
| **El fix de la corona FUNCIONA** | mismos 1.179 records con corona, pero cambia **925** en vez de 15; 910 de ellos con `single_pixel_mode=True`, la población que se anulaba |

### Guards nuevos

- `test_corona_single_pixel_coherencia_s127` — el invariante del clúster de un píxel,
  la contra-prueba del bug, y el no-op bit a bit sobre 50 escenas con NaN.
- `test_guard_afirmaciones_de_alcance_s127` — prohíbe **declarar** una lista de volcanes
  afectados, permite **citarla** como historia (distingue por contexto).
- `test_guard_claves_fantasma_s127` — genérico: deriva de `profile.py` de qué sección se
  lee cada clave. Incluye un test que verifica que **el guard sigue mirando**, porque un
  guard que pasa por no encontrar nada da confianza falsa.

### Divergencias que cambiaron de estado

- **D14 CERRADA**: se sostiene el apagado de la máscara de nube, ratificado con el A/B en
  la mano. Recupera 176 de 181 noches ciegas. **No cierra el frente del artefacto**: de
  las 286 detecciones que destapó sólo 21 caen en noches que MIROVA confirma, a 2,4-2,7 km.

### Transparencia algorítmica (Res. CPLT N°372)

La cabecera FICHA de `single_pixel_mode.py` declaraba bajo **Limitaciones** que el ajuste
«no aplica a Villarrica». Villarrica tiene 3.025 records con el modo activo y 442
modificados. Era la copia más consecuente de las 14, porque «Limitaciones» es el campo que
un regulador lee para saber qué hace el sistema con un volcán dado. Corregida; ficha
publicable a **v1.4**.

### El patrón que ordena la sesión

**A89**: el cero de una búsqueda se lee como ausencia. Cinco instancias, tres formas, y
las cinco del lado de quien auditaba — dos de ellas con el texto correcto ya escrito en el
repo desde S72. La técnica se equivoca en la misma dirección que el defecto que busca, así
que un hallazgo de la forma «esto está muerto» exige verificación cruzada **antes** de
reportarse, no después.
