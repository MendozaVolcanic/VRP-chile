# La máscara de nube ya está apagada en producción — y su A/B todavía no corrió

> Números de `experiments/_s126_cloudmask/01_efecto_en_produccion.py` →
> `01_efecto_en_produccion.json` (regla S91, ninguno transcrito a mano).
> Hora del servidor al escribir esto: 2026-08-29 14:13 UTC (A86).

## Qué pasó

El PR #535 (S125) sacó el umbral de la máscara de nube de un literal en el código
y lo pasó al perfil. Su comentario en `process_viirs.py` decía:

> "El cambio es NO-OP en producción a propósito: `mirova_equivalent.yaml` fija
> `cloud_mask_bt_k: 260.0` para preservar el comportamiento actual hasta que un
> A/B respalde apagarla."

**Eso es falso.** `mirova_equivalent.yaml` declara `cloud_mask_bt_k: 0.0` desde
**S29** (`git log -S cloud_mask_bt_k -- pipeline/profiles/mirova_equivalent.yaml`)
y el PR #535 **no tocó ese archivo** (`git show --stat 1888c1e3e -- …` sale vacío).

O sea: al mergear #535 el 2026-08-28 23:00 UTC, la máscara de nube de VIIRS 375
quedó **apagada en producción**. Han corrido 2 ciclos NRT desde entonces. Nadie lo
notó porque nada verificaba la afirmación del comentario.

## El fenómeno, y por qué la máscara hacía daño

A 3.200 m en invierno austral la nieve irradia en el mismo rango de temperatura de
brillo que el tope de una nube baja. El criterio `I05 < 260 K` no los distingue: le
parecen lo mismo. Y como el filtro se aplicaba a `roi_mask` además de a `bg_mask`,
en esas noches descartaba el cráter junto con el supuesto nublado.

El resultado operacional es el peor tipo de falso negativo: el record queda
grabado como "sin señal" cuando en realidad **no se miró**.

## Cuánto estaba cegando — medido sobre la data operacional

Indicador: `diag_n_bg_used_first_pass`, los píxeles que sobrevivieron para estimar
el fondo. Cero = noche ciega. Ventana previa 2026-08-10 → 2026-08-28.

| volcán | | n | mediana | mín | noches ciegas |
|---|---|---|---|---|---|
| Nevados de Chillán | antes | 86 | 8.204 | 0 | **17** |
| | después | 4 | 13.388 | 1.259 | 0 |
| Villarrica | antes | 90 | 7.473 | 0 | **7** |
| | después | 4 | 14.038 | 6.388 | 0 |
| Láscar | antes | 73 | 5.219 | 0 | **15** |
| | después | 2 | 13.178 | 8.931 | 0 |
| Planchón-Peteroa | antes | 82 | 5.358 | 0 | **25** |
| | después | 4 | 13.052 | 0 | 1 |
| Puyehue-Cordón Caulle | antes | 89 | 6.017 | 0 | **18** |
| | después | 4 | 14.325 | 6.811 | 0 |

**82 noches ciegas sobre 420 pasadas en 18 días — uno de cada cinco pases de
VIIRS 375 en los Tier A.** No eran 15 noches de Chillán: era ~20 % del sensor,
en todos los volcanes con nieve o altura.

**Limitación declarada**: el grupo posterior tiene sólo 2-4 pasadas por volcán, así
que la *magnitud* de la mediana no es robusta. Lo que sí es inequívoco es la
desaparición del mínimo en 0: un solo record con fondo no nulo en una noche que
antes cegaba ya lo demuestra, y hay 17 de 18.

## Cómo leerlo

Hay dos lecturas y las dos son ciertas.

**El destino es el correcto.** `MISSION.md` declara la máscara removida desde S27,
Laiolo 2026 dice textualmente que MIROVA NRT no aplica *"cloud-contamination
automatic filtering"*, y el perfil operacional lo viene declarando desde S29. El
drift era el código, no el perfil. #535 hizo que producción coincidiera con lo que
el proyecto decía hacer hace 97 sesiones.

**Pero se llegó sin la compuerta.** El cambio se mergeó creyendo que era inerte, el
A/B que debía decidirlo no había corrido, y el comentario dejó escrito en el código
un estado de producción que no era el real. Una sesión futura que lo leyera habría
concluido que la máscara sigue encendida.

## Qué se hizo al respecto

1. **Comentario corregido** en `process_viirs.py` con el estado real y la medición.
2. **Test de regresión** `tests/test_cloud_mask_operacional_s126.py`: fija el valor
   efectivo del perfil operacional para que moverlo sea una decisión consciente y no
   un efecto colateral. No pretende que `0.0` sea la respuesta — pretende que el
   cambio no vuelva a pasar inadvertido. Es la defensa durable que pide A63 y el
   antídoto a A87.
3. **A/B lanzado** (runs [33257081431](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/33257081431)
   y [33257082834](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/33257082834)),
   perfiles `_s125_cloudmask_{on,off}` sobre NdC + Villarrica + Láscar,
   2026-06-25 a 2026-08-24. Ya no decide si apagarla: **valida algo que está vivo**,
   y da la evidencia para sostenerla o para revertir.

## Lo que el A/B tiene que contestar ahora

La cara negativa que la máscara venía a cubrir sigue en pie y hay que medirla: sin
filtro, los topes de nube fríos entran al anillo de fondo, bajan `t_bg` e inflan la
magnitud. La pregunta ya no es "¿la apagamos?" sino **"¿cuánto cuesta tenerla
apagada, y ese costo justifica revertir?"**. Criterios:

- Magnitud contra MIROVA por volcán (no agrupada — lección S126).
- Detecciones nuevas sin contraparte, separando las noches recuperadas de las
  noches con nube real.
- `t_bg` en noches nubladas: cuánto baja y si arrastra la VRP.

## Regla que sale de esto

**Un cambio no es no-op porque el commit lo diga: es no-op si algo lo verifica.**
El PR #535 afirmó inercia sobre un valor de configuración que no leyó. Verificar
habría costado un comando (`VRP_PROFILE=mirova_equivalent python -c "import
pipeline.profile as p; print(p.CLOUD_MASK_BT_K)"`). Cuando un cambio declare que
preserva el comportamiento, ese enunciado va acompañado del test que lo comprueba
— si no, es una intención, no un hecho.
