# S194: plan para usar los tres prompts de Nicolás (2026-11-22)

Nicolás compartió tres prompts genéricos (socio que pregunta primero, crítico despiadado, ingeniería inversa) y pidió
un plan con lo que nos sirva y sesiones paralelas para lo que falte. Este plan dice dónde rinde cada uno en VRP Chile
y qué se lanza ya.

## 1. Qué tomamos de cada prompt, adaptado al proyecto

| Prompt | Ya lo hacemos con | Qué agregamos | Regla de uso |
|---|---|---|---|
| **Socio que pregunta primero** | skill de brainstorming (una pregunta a la vez), `/retomar` | comando `/socio`: antes de diseñar, las 3 preguntas que más cambian el resultado, cada una con opciones y recomendación | sólo en pedidos abiertos de Nicolás (como «seleccionar áreas»); en el loop no se pregunta cada paso (memoria `feedback_s168_loop_no_preguntar`) |
| **Crítico despiadado** | verificador con contexto limpio, auditoría Codex, pre-registros, `devils-advocate` | comando `/critico`: **hasta** 5 debilidades, cada una con evidencia citable o marcada SOSPECHA; nunca rellenar para llegar a 5 | antes de llevarle a Nicolás un diseño o una decisión científica; nunca como sustituto del verificador limpio |
| **Ingeniería inversa** | plan S190 §7 (del veredicto hacia atrás) | aplicarlo a la meta grande, que no tiene camino escrito: **«OVDAS usa VRP Chile en lugar de mirovaweb.it»** | una vez, como documento vivo; se revisa en cada auditoría integral (A51) |

La trampa que hay que evitar en los tres: un número fijo («3 preguntas», «5 debilidades») empuja a inventar. En
este proyecto cada pregunta o debilidad lleva su evidencia o se marca SOSPECHA (A111).

## 2. Lo que se aplica ya

- **Socio, sobre las áreas del laboratorio:** las tres preguntas AR1, AR2 y AR4 del borrador
  `docs/superpowers/specs/2026-11-22-laboratorio-areas-design.md` se le hacen a Nicolás en este turno.
- **Crítico, sobre el mismo borrador:** hecho, §9 del borrador (5 debilidades con evidencia).
- **Ingeniería inversa de la independencia:** sesión paralela 1.

## 3. Sesiones paralelas (una por tema, sin archivos compartidos)

| # | Sesión | Prompt que usa | Sale | Checkout |
|---|---|---|---|---|
| 1 | Camino hacia atrás: OVDAS deja mirovaweb.it | ingeniería inversa + crítico | `docs/CAMINO_INDEPENDENCIA_MIROVA.md` (borrador, lo commitea la coordinadora) | compartido, sin commits |
| 2 | VIIRS de día, mirado en imagen (decisión 2 del bloque S194 §b) | crítico (sobre la hipótesis «es reflejo solar») | informe en `D:\vrp-trabajo\temporales\s194_viirs_dia\` | compartido, sólo lectura |
| 3 | Laboratorio paso 2: sellar el criterio del plan S190 §6 | crítico (sobre el criterio antes de sellar) | PR con el pre-registro | worktree propio |
| 4 | Avisos de Codex C1-101 y C1-106 (vigilancias) | | PR | worktree propio, **después de que #1090 entre** (comparten consumidores) |
| 5 | Marca de MIR perdida en el tablero (Codex C1-102, C1-V202) | | PR | worktree propio, **después de #1091** (mismo frontend) |

Las 4 y 5 esperan por conflicto de archivos; las 1 a 3 parten ya. El disco C: tiene unos 11 GB libres y cada
worktree ocupa ~1,7 GB: por eso 1 y 2 comparten el checkout sin escribir en él.

## 4. Cola de merges (coordinadora)

#1089 (v1.70, unión con #1086 resuelta en el mosaico) → #1088 (regla de merge en `CLAUDE.md`, sin ficha) → #1090
(día en MODIS, v1.71) → #1091 (marcador «calor en la cumbre», v1.72, une main antes).
