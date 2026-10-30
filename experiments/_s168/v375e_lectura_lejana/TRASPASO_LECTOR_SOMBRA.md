# Traspaso: lector de la sombra de V375-E (§9.8 y §10 de PREREGISTRO_E.md)

> **Estado al 2026-10-30 01:30 UTC: el verificador del lector dio SELLABLE CON CAMBIOS con UN hallazgo de gravedad 3.**
> Informe: `experiments/_s168/v375e_sombra/verificador/INFORME.md` (Sonnet, sobre `c44665603`; re-corrió la batería, 104
> de 104). No hay sello ni tag del lector. El nulo (`mutar_sombra.py`) sigue sin correr. Lo que queda, en este orden:
> arreglar §11 y el código (propuesta abajo), agregar a `mutar_sombra.py` las 14 mutaciones que el verificador cree que
> sobreviven, re-correr la batería, el nulo cuando haya cupo pesado (`--hilos 1`), un verificador corto de otro modelo
> sobre el delta, tag anotado del lector, INFORME.md y aviso a S169 (`local_b1bfa049`). Todo antes del 2026-11-03 15:00
> UTC. Ningún dato de la ventana P antes de que S169 se lo lleve a Nicolás.
>
> **Propuesta de arreglo por hallazgo** (de esta sesión, sin aplicar; quien siga puede cambiarla, pero tiene que quedar
> escrita antes de abrir datos):
>
> | hallazgo | gravedad | propuesta |
> |---|---|---|
> | VS168-01 el corte que decide queda libre | 3 | `--desde` tiene que ser exactamente 2026-11-03 (S1 con `==`). El corte que decide es la primera noche en que se alcanza la parada: el lector la calcula y lee sólo hasta ella aunque `--hasta` sea posterior. Antes de la parada imprime sólo controles y los contadores de la parada, **sin ninguna lectura** (así no hay cortes provisionales que mirar). `--salida` y `--json` se niegan a sobrescribir un archivo existente y llevan la fecha del corte en el nombre |
> | VS168-02 con un control caído se imprime el detalle de S7 | 2 | con controles caídos sólo se imprime qué control cayó (nombre y motivo genérico), sin conteos ni nombres de pasadas; la batería lo comprueba buscando los conteos, no sólo «== población» |
> | VS168-03 una protegida SIN DATO que K publica sale de P1 | 2 | cuenta como perdida en (a) (conservador) y se lista por nombre; S7 en `pos_prot` sin tolerancia o con aviso aparte |
> | VS168-04 el régimen no está fijado | 2 | `--commit` obligatorio; un control S8 compara con git `pipeline/` entre `c42ee0eb7` (#926) y el commit de los records: si la vía o el perfil de la sombra cambiaron, LECTURA NO LEGIBLE y decide Nicolás. S0 suma el sha de `banco_paridad.py`, `clase_mirova.py`, `referencia_mirova_unificada.py` y del propio lector, y el de `frontend/index.html` se informa |
> | VS168-05 la referencia pierde filas y tiene rezago | 2 | la referencia se baja una sola vez para el corte que decide, al menos 2 días después de su última noche, y su sha queda en la salida; filas que el scraper pierda después no cambian nada |
> | VS168-06 (c) SIN SUSTRATO da NO CUMPLE | 2 | en la sombra, (c) SIN SUSTRATO pasa a DECIDE NICOLÁS (§5.4, última frase); INDECIDIBLE sigue sin cumplir |
> | VS168-07 los controles de la curva no se corren para K | 2 | correrlos también para K; si caen en K, (d) pasa a DECIDE NICOLÁS |
> | VS168-08 la batería no ata (b), (c), (d) ni S6 | 2 | aserciones sobre el valor de cada criterio y del estado en `analizar`, S6 en rojo y la rama sin `neg_pub` |
> | VS168-09 a 14 | 1 | ver el informe; los más útiles: no publicar sin distancias se cuenta y se informa (11), radiante sin `estado` impreso (13) |

> **Estado al 2026-10-30 01:15 UTC** (lo sigue haciendo esta misma sesión, por pedido de la coordinadora S169). Hecho y
> empujado en `claude/s168-v375e-sello`: el texto del lector como §11 de `PREREGISTRO_E.md` (borrador, sin sellar), el
> lector `experiments/_s168/v375e_sombra/leer_sombra_v375e.py`, su batería `probar_sombra.py` (104 de 104) y el nulo
> `mutar_sombra.py` (55 mutaciones, **sin correr**: espera cupo pesado del equipo, MOD-D hasta ~09:15 UTC). Lanzado el
> verificador limpio (Sonnet) sobre `c44665603`; su informe va a `experiments/_s168/v375e_sombra/verificador/INFORME.md`.
> Falta: arreglar lo que traiga el verificador, correr el nulo (`python -I mutar_sombra.py --hilos 1`) y poner sus
> cifras en §11.10, tag anotado del lector, INFORME.md y aviso a S169 (`local_b1bfa049`). Nada de datos de la ventana
> P hasta que S169 se lo lleve a Nicolás.

Escrito el 2026-10-30 (S168, sesión hija de VIIRS 375) para quien escriba el lector de la sombra. Rama de partida:
`claude/s168-v375e-sello` (punta `2a4880665` o posterior). Plazo: antes de la primera corrida con datos de la ventana P,
el **2026-11-03 a las 15:00 UTC** (`.github/workflows/sombra-codigo-mirova.yml` en `main`, #926). Reglas duras de siempre:
nada en `pipeline/`, `data/` ni `frontend/`; nada a `main`; ningún despacho; ningún dato de la ventana P abierto antes de
que Nicolás apruebe el lector.

## Qué hay que hacer

Un lector que lea la sombra y decida el §5.4 del paquete con el brazo **cercano** (decisión de Nicolás, §10), con radiante
al lado rotulado «posterior a la lectura». Orden: pre-registro del lector (texto, como sección nueva del pre-registro o
documento aparte que §9.8 cite), código, batería sintética, mutaciones, tag, verificador limpio de otro modelo, Nicolás.

## Lo que ya existe y conviene reusar (no reimplementar)

En `experiments/_s162_v375/e_adenda2/leer_posicion_v375e.py` (sellado, tag `s168-v375e-cuerpo-sellado`):
`distancias_desde_record` (los tres brazos desde un record; cercano = menor `dist_km` de `anomaly_pixels`),
`pares_magnitud`, `magnitud`, `estado_c`, `curva`, `estado_d_sombra`, `criterios_retro`, `regla_adopcion`, `no_veta_n3`.
Y sin cambios: `experiments/_s162_v375/evaluar.py` (sha256 LF `2126b743…bc66`), `curva_cenit.py`,
`scripts/evaluador_comun.py`. Importarlas por ruta y fijar su sha256, como hace el lector sellado con `evaluar.py` (C4).

## Insumos de la sombra (comprobado en `origin/main` `c42ee0eb7`)

- Records en `data/sombra_codigo_mirova/<Volcán>.json` (perfil `pipeline/profiles/sombra_codigo_mirova.yaml`). Los de la
  vía VIIRS 375 traen `via_codigo_mirova: True`; uno con `"sin_grilla"` no entra al brazo (§7.4).
- `anomaly_pixels` trae **todos** los alertados con `fila`, `col` y `dist_km` (redondeada a 0,01 km,
  `pipeline/mirova_v750_codigo.py` l. 726 a 732); el almacén no los toca para la vía (`pipeline/store.py` l. 362, 401 y
  455). La prueba `tests/test_sombra_codigo_mirova_s167.py` l. 300 a 306 ya lee los tres brazos así.
- K: lo que publica producción en `data/mirova_equivalent/`. MIROVA: la referencia de Mirova-v1, **congelada por hash en
  cada corte de lectura** (§3.3). Calidad de la referencia por canal y fecha: `scripts/calidad_referencia_mirova.py` (A119).

## Lo que el pre-registro del lector tiene que fijar antes de ver datos

1. **Población y pesos**: la ventana P empieza el 2026-11-03, sin Suomi NPP (otro régimen, §3.3). No hay muestreo, así
   que cada pasada pesa 1. N-3 (§8.13) no aplica (es para antes del 2026-10-09), pero se deja la función por si aparece
   una fila vieja. Clases (protegida, bajo 1 MW, negativo limpio, `far_tabla`) con las mismas definiciones que la
   retrospectiva (`seleccion.py`, `banco_paridad`, regla SN de D-9).
2. **Parada** (§3.3): 30 noches o 40 alertas de MIROVA que decidan, lo que llegue último. Decir qué es «alerta que decide»
   y cómo se cuenta en cada corte. Cada corte de lectura deja el hash de la referencia.
3. **Cercano decide, radiante informa**, rotulado «posterior a la lectura» (§10). Pico no se lee.
4. **VA168-08, el borde**: contar las pasadas cuyo cercano queda a menos de 0,005 km del radio interior. Tratarlas con
   la regla inclusiva sobre el valor redondeado (como la prueba de la sombra) y decir antes qué pasa si alguna decide un
   criterio (propuesta: se informa por nombre y, si cambia el estado de un criterio, DECIDE NICOLÁS).
5. **VA168-01**: si cae cualquier control (las listas incluidas), el lector sale 3 **sin imprimir nada del marco**. En el
   lector sellado, C3 se calcula en `main` y no corta la impresión: el lector nuevo tiene que cortar, con prueba y
   mutación.
6. **VA168-02, los controles de la curva del §4**: nulo de cenit parecido, sesgo de plataforma, ganancia pareja y
   ganancia que crece con el cenit (todos en `curva_cenit.py`, probados sobre K en
   `experiments/_s162_v375/linea_base_curva_salida.txt`). Fijar qué le pasa al criterio (d) si fallan (propuesta: NULO
   SESGADO o sesgo de plataforma, (d) DECIDE NICOLÁS; ganancia que crece sin mover D, la curva no se lee y (d) DECIDE
   NICOLÁS).
7. **VA168-03 y 04** (dejar escrito lo que ya hace el código): (d) exige además que la curva de K no sea SIN SUSTRATO
   ni NULO SESGADO; en (c) la marca A104 manda sobre EMPEORA. En la ventana P no hay tramos T, O1 y O2: decir si A104 se
   reemplaza por un corte propio (por ejemplo, la mitad temprana contra la tardía) o no aplica.
8. **Las reservas de la lectura** (verificador `experiments/_s168/v375e_lectura_lejana/verificador/INFORME.md`):
   VL168-01 y 04, el costo de cercano en las pasadas lejanas. Proponer una línea que informe, sin decidir, cuántas
   `far_tabla` de la ventana P publica cercano contra radiante y K; que decida es una decisión de Nicolás.
9. **La regla del §9.7 (d) en la sombra** ya está en `estado_d_sombra`; el lector la usa tal cual.

## Pruebas y verificación

- Batería sintética (records de sombra fabricados, el predicado del tablero con node como en `probar_adenda2.py`, la
  referencia fabricada), en verde y en rojo para cada control y cada rama de la tabla.
- Nulo por mutaciones de una línea, contando como atrapada sólo la que una aserción caza (una caída no cuenta), con
  identidad y control de caída. El de la adenda 3 tardó unas 2 h con dos hilos: coordinar el cupo pesado con la
  coordinadora (hoy lo ocupan MOD-D y V750-A).
- Tag anotado sobre el commit del lector, empujado; verificador limpio de otro modelo con sólo rutas y sha; después,
  Nicolás antes de abrir datos de la ventana P.
