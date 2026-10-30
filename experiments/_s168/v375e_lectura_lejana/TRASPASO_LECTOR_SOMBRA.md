# Traspaso: lector de la sombra de V375-E (§9.8 y §10 de PREREGISTRO_E.md)

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
