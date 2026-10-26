# Revisión de W1 (run 40364164845, Láscar, 2026-03-01 a 2026-03-20), antes de despachar W2 a W6

Fecha: 2026-10-26, sesión `diurno-k-prereg`. W1 es informativa (PREREGISTRO.md §3 y §8): sirve para medir la duración
del brazo diurno sobre K y para estrenar el instrumento con datos reales. Este archivo no toca nada sellado. Salidas
crudas en la rama `s151-ab-diurno/40364164845` (`experiments/_s151_ab_diurno/salidas/40364164845/`).

## Duración y decisión del §8

- Control: 16:58:09 a 17:29:22 UTC (31 min). **Brazo diurno: 16:58:09 a 18:26:36 UTC (88 min 27 s).** Recolectar: 2 min.
- Regla del §8: 88,45 × 1,45 × 1,3 = 166,7 min, que cabe en 300. **W2 a W6 van enteras: 5 despachos de 22 jobs.**
- Costo con esta medida: 88,45 min para 20 días de Láscar son 4,4 min por volcán-día en el brazo diurno y 1,6 en el
  control (31 min / 20 días), contra 5,5 y 2,2 que estimaba el §8 con la corrida sobre C0. Para 11 volcanes × 83 días,
  unas 55 h de runner, unas 18 h de reloj con `max-parallel: 3` (Láscar puede no ser representativo; SOSPECHA).

## Cobertura y cableado (lo que se mira antes de cualquier número)

- `cobertura.txt` del run: noche pareja (183 y 183, 0 faltan, 0 sobran); el brazo diurno trae 74 pasadas diurnas de
  VIIRS 375 y 73 de VIIRS 750, el control ninguna; sin MODIS diurno.
- Cableado de K (I1): las líneas `FLAGS_BRAZO` de los dos jobs dicen lo declarado (0 problemas); los 513 records traen
  `regimen.codigo_sha` = 68687d2d4b73bb0527da18a2c886a6dcc241a0ac (el commit sellado); 0 records con el Test 1.
- La palanca actuó (I2): 147 records diurnos con `diag_umbrales_diurnos`, 0 nocturnos.
- Noche (I5): mismos records en los dos brazos y misma publicación y magnitud; 0 records con otros campos distintos.

## La compuerta I4c falla en W1, por un hueco de NASA

Con la tabla de MIROVA (A119: antes del 2026-06-13 decide sólo la tabla), al brazo diurno le faltan 3 de 37 pasadas
diurnas de VIIRS 375 y 4 de 40 de VIIRS 750. Con la vara nocturna de producción (p_sup 0,0011 y 0,0059) eso es
INVÁLIDO POR INSTRUMENTO.

Causa, comprobada en tres lados:
1. **Las siete son del 10, 11 y 12 de marzo.** Fuera de esos días faltan 0 de 64 pasadas diurnas y 0 de 46 nocturnas
   VIIRS.
2. **A la noche le pasa lo mismo**: en esos tres días al control le faltan 1 pasada nocturna de VIIRS 375 y 1 de VIIRS
   750 (I3 no lo marca porque no son protegidas).
3. **El log del brazo** muestra que para esos días el archivo estándar no trae los gránulos de Suomi NPP y el respaldo
   NRT tampoco (`VNP02IMG_NRT v2 2026-03-10..2026-03-12 n=0`, ídem `VNP03IMG`, `VNP02MOD`, `VNP03MOD`). Y **el catálogo
   CMR de NASA** (consultado hoy, caja -72,5 -39,5 a -67,5 -23,0) no tiene ningún gránulo de `VNP02IMG` ni de
   `VNP02MOD` esos tres días.

O sea: es un hueco permanente del archivo de NASA para Suomi NPP, común a los dos brazos, y no un defecto de la rama
diurna. Repetir el job no lo arregla (el remedio que el §5 da para I4).

## W2 a W6

El mismo catálogo CMR tiene gránulos **todos los días** de W2 a W6 en los seis productos (`VNP02IMG`, `VJ102IMG`,
`VJ202IMG`, `VNP02MOD`, `VJ102MOD`, `VJ202MOD`), sobre la misma caja. No se espera que I4c caiga por un día entero sin
datos; un hueco parcial (algunos gránulos de un día) no está descartado.

## Lo que el pre-registro sellado no dice (para decidir, no aplicado)

El §5 no prevé un hueco permanente del archivo de NASA. Propuesta de desviación, a registrar en el §11 sólo si la
aprueban la coordinadora o Nicolás: cuando I4 falle, las pasadas sin record que caen en días en que CMR no tiene
gránulos de esa plataforma, y en que el control también pierde pasadas nocturnas, se excluyen de los dos brazos como
días excluidos (el mecanismo `excluir_dias` del evaluador, como D-29) y se declaran; I4 se recalcula sin ellas, y si
sigue fallando es INVÁLIDO. Para W1 eso deja la ventana del 1 al 20 de marzo sin el 10, 11 y 12.

## Lo que W1 dice del brazo (informativo, no decide; Láscar, sólo la tabla)

VIIRS 375: publica 4 de 5 protegidas diurnas y 4 de 18 negativos diurnos limpios; caso e, DECIDE NICOLÁS CON M4.
VIIRS 750: no publica nada de día (0 de 36 negativos, sin alertas de MIROVA); SIN CAMBIO. Q_n de Láscar de noche es alto
(3 de 4) y no es comparable con el de 11 volcanes. Nada de esto se lee como resultado: W1 es una ventana, un volcán y un
tramo de calidad de la referencia distinto.

Script: `revisar_w1.py` (en esta carpeta).
