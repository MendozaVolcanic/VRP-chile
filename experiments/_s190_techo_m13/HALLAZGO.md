# Techo de M13: 634 K es la especificación, no la saturación (S190, 2026-11-17)

Pendiente que dejó #1042 (H04 de Codex): «el Planck inverso de la radiancia M13 máxima es SIN DATO». Ya no lo es.

## Qué dice NASA (local, leído en la página renderizada, A95)

Fuente: `documentacion/JPSS_VIIRS_SDR_Radiometric_ATBD_RevC.pdf` (ATBD VIIRS Radiometric Calibration, Rev C,
2013-05-15).

- Tabla 2 (rango dinámico de bandas emisivas): M13 ganancia baja, Tmin 343 K, **Tmax 634 K**. Es la especificación
  del sensor; es el mismo número que cita Campus et al. 2022 (Tabla 1) y que usa el código.
- p. 80, texto bajo la Tabla 17: «the VIIRS design is to set saturation at approximately 1.2 times the signal of
  Tmax». La saturación del detector está por encima de 634 K.
- p. 80, Tabla 17 (límites de la LUT de temperatura de brillo): M13, **Highest Detectable EBBT 683 K** (1,5 veces la
  señal de Tmax, «to allow ample margin, since gain may drift»). Es lo más alto que la LUT oficial puede entregar.

## Cálculo (Planck monocromático a 4,05 µm, `M13_LAMBDA` de `pipeline/process_viirs_mod.py`)

| Señal | Temperatura de brillo |
|---|---|
| L(634 K) = 404,3 W m⁻² sr⁻¹ µm⁻¹ | 634 K |
| 1,2 × L(634 K), saturación de diseño | ≈ 655 K |
| 1,5 × L(634 K) | 683,2 K (la Tabla 17 dice 683: el cálculo coincide) |

## Consecuencia

- **Producción (almacén, `pipeline/store.py::BT_PHYSICAL_MAX_K_VIIRS750 = 634.0`, #1042):** un píxel M13 no
  saturado entre 634 y ≈ 655 K es físicamente posible y hoy se juzgaría «imposible»: su VRP sobre el tope de cordura
  se guardaría en 0 MW. Ningún record actual está en ese rango (#1042 lo midió: no hay record afectado).
- **Guardia K (`pipeline/process_viirs_mod.py::aplicar_techo_saturacion_mband`):** descarta como saturada toda BT
  M13 ≥ 633,5 K. La saturación real la marca el bit 2 del quality flag (que ya se lee); el corte por valor recorta
  entre 633,5 y ≈ 655 K. No es producción.

## Propuesta (A45, espera a Nicolás)

Subir el techo de VIIRS 750 en el almacén de 634 a **683 K** (Highest Detectable EBBT de la Tabla 17): todo lo que
pase de ahí no lo puede producir la LUT oficial y sí es imposible. Cita nueva: ATBD Radiometric Rev C, Tabla 17.
SIN VERIFICAR, a revisar en el mismo PR: si la vía (`pipeline/mirova_v750_codigo.py`) lee el bit de saturación del
quality flag de M13 (un `grep` de `quality|satur` en ese archivo no da lectura de M13; puede estar en el lector que
la llama). Si no lo lee, un píxel saturado entraría con la radiancia del tope y el techo de 683 K no lo atraparía.
La guardia K puede quedarse como está.
