# Techo de M13: 634 K es la especificación, no lo más alto que entrega el L1B (S190, 2026-11-17)

Pendiente que dejó #1042 (H04 de Codex): «el Planck inverso de la radiancia M13 máxima es SIN DATO». Ya no lo es.
Todas las cifras se leyeron en la página renderizada a imagen (A95), no en la capa de texto, que desordena las
columnas de las tablas.

## Qué dice NASA (documentos locales)

`documentacion/JPSS_VIIRS_SDR_Radiometric_ATBD_RevC.pdf` (ATBD VIIRS Radiometric Calibration, Rev C, 2013-05-15):

- Tabla 2 (rango dinámico de bandas emisivas): M13 ganancia baja, Tmin 343 K, **Tmax 634 K**. Es la especificación
  del sensor y el mismo número que cita Campus et al. 2022 (Tabla 1).
- p. 81, texto que sigue a la Tabla 17: «the VIIRS design is to set saturation at approximately 1.2 times the signal
  of Tmax».
- p. 80, Tabla 17: M13, **Highest Detectable EBBT 683 K** (la columna Tmax de esa tabla también dice 683 para M13).
  En la p. 81 el texto define esa columna como 1,5 veces la señal de Tmax («to allow ample margin, since
  gain may drift from its design value»).

`documentacion/VIIRS_L1B_UserGuide_Aug2021.pdf`, p. 23 (impresa 23, índice 22 del PDF):

- «M-band 13 EV radiance»: uint16, rango válido 0 a **65527**, add offset 0,00108056, scale factor 0,008088269.
  Valores de bandera 65532 Missing_EV, 65533 Bowtie_Deleted, 65534 Cal_Fail; relleno 65535. **Ninguno es saturación.**
- «M-band 13 Brightness Temperature LUT»: máximo **665,9161 K**, mínimo 192,00003 K.
- La saturación va aparte, en los quality flags (valor 4 = Saturation; tabla de las I-bands, p. 22 impresa; en las M-bands 4 = Saturation y 128 = Some_Saturation, p. 24 impresa; las
  M-bands tienen su propio dataset «M-bands Quality flags»).

## Cálculo

Planck monocromático a 4,05 µm con `pipeline/mirova_v750_codigo.py::radiancia_a_temperatura` (la de la vía):

| Señal | Temperatura de brillo |
|---|---|
| L(634 K) = 403,41 W m⁻² sr⁻¹ µm⁻¹ (`temperatura_a_radiancia` de la vía) | 634 K |
| 1,2 × L(634 K), saturación de diseño | ≈ 655 K |
| DN 65527 → 530,0 W m⁻² sr⁻¹ µm⁻¹, lo más alto que el L1B codifica | **666,3 K** (la LUT de NASA da 665,9) |
| 1,5 × L(634 K) | 683,2 K (la Tabla 17 dice 683: coincide) |

## Consecuencia y arreglo

- **Almacén (`pipeline/store.py::BT_PHYSICAL_MAX_K_VIIRS750`):** con 634 K, un píxel M13 válido entre 634 y 666 K se
  juzgaba imposible y su VRP sobre el tope de cordura (50.000 MW) se guardaba en 0 MW. Pasa a **683 K**: sobre eso no
  hay píxel del L1B posible, y el DN máximo válido (666,3 K por la vía) queda debajo. Ningún record actual cambia: el
  techo sólo actúa sobre 50.000 MW y el máximo publicado es 248,32 MW (#1037).
- **Guardia K (`pipeline/process_viirs_mod.py::aplicar_techo_saturacion_mband`):** sigue descartando M13 ≥ 633,5 K. No
  es producción; se deja.

## Lo que queda abierto (fuera de este cambio)

- **La vía no lee la saturación de M13.** `leer_radiancia_l1b` pone en NaN los DN ≥ 65528 (las banderas de arriba), y
  ninguna de ellas es saturación. Un píxel saturado entra con su DN tope, unos 655 a 666 K, y aporta una VRP
  subestimada. Con 683 K se conserva (antes, con 634 K, se anulaba si pasaba 50.000 MW).
- **Qué hace MIROVA con un píxel saturado es SIN DATO.** El código publicado
  (`experiments/_s158_d17_diseno/osf_codigo_mirova/`) recibe la radiancia ya grillada; la lectura del L1B no está
  publicada. Tampoco tiene ningún tope de temperatura.
- **El factor de escala de M13 por archivo es SIN DATO.** La vía lo lee del atributo `scale_factor` de cada L1B
  (`leer_radiancia_l1b`), y la prueba usa el de la guía (0,008088269). Para que un píxel válido pase de 683 K, el
  factor de un archivo tendría que ser cerca de 14 % mayor. No hay L1B real en disco para comprobarlo (la nota
  «granule-dependent» de la guía marca la columna de las tablas de reflectancia, no la de M13).
- **Verificador independiente (contexto limpio, S190):** 7 de 7 afirmaciones confirmadas, la 4 con la condición de
  arriba; corrigió páginas citadas y el valor de L(634 K), ya arreglados aquí. Mutaciones: con techo 634 falla
  `test_techo_m13_no_anula_el_dn_maximo_valido_del_l1b`; con 700 fallan las dos de «sobre 683 K se anula».
  Renders y script en `D:\vrp-trabajo\temporales\s190\verif_techo\`.
