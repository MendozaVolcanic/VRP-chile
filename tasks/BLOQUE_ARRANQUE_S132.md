# Bloque de arranque S132

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S131. Esa sesión hizo dos cosas: trazó el frente del
remuestreo (es una LEY DE ÁREA, no hace falta regrid para la magnitud) y corrió la
auditoría integral de 6 ejes que pidió Nicolás al pasar a Fable 5.1 (PR #581).

Leé en este orden:
  1. tasks/BLOQUE_ARRANQUE_S132.md        (este bloque)
  2. docs/AUDIT_S131.md                    (consolidado; §4 = decisiones de Nicolás)
  3. docs/s131/agentes/MAGNITUD.md §2-§3   (el área explica el gradiente entero)
  4. docs/s131/agentes/DASHBOARD.md Parte B (lo que le falta al operador)
  5. docs/s131/agentes/GROUND_TRUTH_ESPACIAL.md §Hallazgos (MODIS far→summit = artefacto)

═══════════════════════════════════════════════════════════════════
NADA CORRIENDO. Verificar que PR #581 quedó mergeado (gh pr view 581).
═══════════════════════════════════════════════════════════════════

LO QUE S131 DEJÓ PROBADO
· El ÁREA DE PÍXEL explica el gradiente cenital COMPLETO en VIIRS (por pasada 0,77→0,45
  sin corregir; 0,79-0,87 plano con la ley del ATBD; mediana global 0,58→0,82). Lo que
  sobra es un déficit UNIFORME ~0,82 = fondo Eq. 6 + suma/clúster (R1/R2 de S125 siguen
  vivos: MODIS degradado a 1 píxel en el 48,9 %).
  ⚠️ El «f requerido 2,93×» de la mañana de S131 (y el 0,740→0,253 de S130) emparejaba
  cada pasada contra el MÁXIMO DE LA NOCHE de MIROVA. Por pasada es 1,72. LA UNIDAD DE
  COMPARACIÓN ES LA PASADA. `experiments/_s131_audit/magnitud/03_pares_por_pasada.py`.
· A67 («el área multiplica el Test 1») NO tiene respaldo en el código actual: la ley de
  área cambia sólo la magnitud.
· En VIIRS el bow-tie lo hace el sensor (`process_viirs.py:80`); en MODIS sí es trabajo real
  y ahí el gradiente NO está probado (50 pares, un volcán). NO extrapolar a MODIS.
· Lo que ve el operador para VIIRS375 NO es `pc.vrp_mw`: `USE_F5_CORE` default (0,68 vs
  0,58 contra MIROVA; coincide 5,7 %) y el número no se persiste.
· El GeoTIFF de MIROVA NO sirve para arbitrar POSICIÓN (control: 4,80 km de error vs su
  propia Distancia_km). Sólo confirma cuando el máximo cae sobre el edificio (V375: nuestro
  clúster a 228 m = 0,61 px).
· El far→summit de MODIS ES ARTEFACTO: el máximo MIR absoluto está a 21 km del cráter y el
  de MIROVA a 20,8 km (ρ 0,023): a 1 km el MIR absoluto no ve el volcán ni para ellos.
  1.073/1.233 detecciones MODIS con clúster ≤2 km quedan `far`. A72 → algoritmo, no display.
· NHI-v1 (SWIR S2+Landsat, 10/11 Tier A) es tercer juez CONSUMIBLE: confirmó el FN A77 de
  NdC; nuestras detecciones sin MIROVA = actividad crónica (A54). Contexto, no gate.
· FICHA SDA tenía 3 falsedades (MOD14; zonas de exclusión; NTI «mitigado»). Corregidas
  con guards. 16 falsas / 13 obsoletas en total (T9). 8 guards nuevos.

DECISIONES QUE ESPERAN A NICOLÁS (AUDIT_S131 §4) — no las tomes vos
  1. Limpiar 1.635 sellos de piso + 28 vrp_tir_mw: PRIMERO `git tag -a pre-s131-data-hygiene`
     (el clasificador bloqueó crearlo en S131 — NO existe), después
     `python experiments/_s131_audit/limpiar_sellos_data.py --apply`, quitar los xfail de
     G3/G7 en tests/test_guard_declarado_vs_efectivo_s131.py, commit data.
  2. M15 saturación 423,0 → 343,0 K (`process_viirs_mod.py:193-196`, Campus 2022 T1). A45.
  3. Una sola magnitud publicada: persistir `display_vrp_mw` o volver default a pc.vrp_mw.
  4. `distance_class` MODIS desde `primary_cluster` (A/B reproc real, 65 TP no pueden bajar).
  5. A/B del ÁREA: área desde lat/lon del propio granule (sin modelo; incluye saltos de
     agregación), flag OFF, 3 brazos (control · área · área+corona Eq.6), criterio
     pre-registrado: bin 50°+/nadir en 0,9-1,1 POR PASADA; ≥6/8 vols en banda V375;
     0 noches MIROVA perdidas; pares >2 ≤10 %. Tag A45. NO extender a MODIS.
  6. B22 primaria en MODIS (`process_modis.py:492-495`, Coppola 2016a l.141-144). A45.
  7. Higiene disco (documentacion/ duplicados 101,9 MB; experiments/_s104_roi_probe 113 MB). A38.
  8. Rotar el PAT de ~/.claude/settings.json.

FRONTEND PENDIENTE (DASHBOARD.md Recomendaciones, todas frontend puro):
  R3 columna MIROVA en la tabla + contador en tarjeta (dato en r._mirova_confirmed) ·
  R5 T MAX/T FONDO en tarjeta · R7 arrancar en volcán con data · R8 marcar cap 5,00 MW ·
  R11 «qué NO ve este sistema» + enlace FICHA · R12 anomalía relativa a la línea base del
  volcán · R13 «próxima pasada esperada». Y R14 `region` en volcanoes.yaml · R15/R16
  volcanic_features.yaml + marcador «extension» alcanzable · R17 sello de tiempo de proceso.
  Verificar SIEMPRE en navegador real (preview vrp-frontend, 8091) y después en el sitio.

REGLAS DE ESTA ETAPA
  · Un docstring no es una medición (A89 le pasó a un agente: «un par por (volcán, fecha,
    bucket)» y el código colapsaba al máximo de la noche).
  · Toda sonda con veredicto lleva control de instrumento ANTES (GeoTIFF y NHI se midieron
    contra sí mismos primero).
  · Corregir texto sin guard no cierra nada (regla B). Los guards derivan la verdad del
    código, no fijan listas.
  · Flags: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`.
  · Un agente por eje, modelo según el juicio que exige; los briefs con «verificalo vos,
    no lo des por cierto» + una evidencia por hallazgo + sin transcribir razonamiento.
```

---

## Estado al cerrar S131

**Suite**: 1054 passed · 3 skipped · 2 xfail (strict, esperan la limpieza de datos).
**PR**: #581 (`s131-audit-fixes`). **NRT**: 27/27 verdes en 7 días; timeout de job subido
a 80 min. **Dashboard**: fixes verificados en navegador local; el sitio publicado se
actualiza con el merge (pages-deploy).

**Docs nuevos**: `docs/AUDIT_S131.md`, `docs/s131/REMUESTREO_LEY_DE_AREA.md`,
`docs/s131/agentes/{MAGNITUD,DASHBOARD,DECLARADO_VS_EFECTIVO,PENDIENTES_INFRA,
GROUND_TRUTH_ESPACIAL,OTRO_SENSOR}.md`. **Scripts**: `experiments/_s131_audit/<eje>/`,
`experiments/_s131_remuestreo/`. **Guards**: `tests/test_guard_declarado_vs_efectivo_s131.py`.

### El patrón que ordena la sesión

**Tres veces en un día el número cambió con la definición** — f requerido (emparejamiento),
«MIROVA plano» (por noche vs por pasada), y en S130 A81 (denominador). A90 se extiende al
eje de emparejamiento. Y **los ejes exógenos rindieron en el control, no en el veredicto**:
el GeoTIFF se refutó a sí mismo antes de arbitrar; NHI se midió contra su basal antes de
adjudicar. Ninguna de las dos sondas habría sobrevivido sin ese paso previo.
