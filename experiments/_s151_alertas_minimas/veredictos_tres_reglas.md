# Decisión D-9: los veredictos ya publicados con las tres reglas

> Escrito el 2026-10-15, en `loop/d9-regla-sn`. Todo número sale de `veredictos_tres_reglas.py`, con su salida al
> lado (`veredictos_tres_reglas_salida.txt`). Ninguno está transcrito a mano.

## Qué se decidió y qué se probó

Nicolás aprobó el 2026-10-15 (issue #811) la regla **SN**: una alerta del scraper de VIIRS 375 con VRP de
0,05 MW o menos, que el banner de MIROVA llama NONE, cuenta como "MIROVA miró y no vio nada". Su condición fue
probar todas las opciones, así que cada resultado ya publicado se volvió a contar con cinco reglas, sobre las
**mismas** publicaciones de cada brazo (no se re-corrió ningún brazo):

- **original**: la etiqueta del scraper (lo de antes de D-9);
- **SN**: la decidida, con 0,05 exacto contado como "no vio nada";
- **SE**: estrato aparte (ni alerta perdida, ni acierto, ni negativo limpio);
- **SN_004** y **SE_004**: lo mismo con umbral 0,04, que deja 0,05 exacto como alerta. El estudio no pudo decidir
  0,05 (5 NONE y 5 VERY LOW en la muestra con banner), así que se informan las dos variantes.

El conteo usa la función única que quedó en el repo, `scripts/clase_mirova.py::aplicar_regla_minimas`, a
través del etiquetador compartido (`scripts/banco_paridad.py::indexar_referencia(regla_minimas=...)`).

**Controles.** La etiqueta original re-calculada coincide con la de cada tabla en el 100 % de las pasadas (meses
de VIIRS 375 y 750, Chillán). Con la regla original, SN y SE a 0,05, los totales son **exactamente** los de
`suma_salida.txt`, que el estudio calculó con una implementación propia escrita aparte (`suma_errores.py`): la
función única hace lo mismo que el estudio midió.

## La tabla

Suma de errores bajo 1 MW: alertas Muy Bajo sin publicar más publicaciones en negativos limpios, por pasada.

| resultado | brazos | original | SN | SE | SN_004 | SE_004 | ¿cambia el veredicto? |
|---|---|---|---|---|---|---|---|
| meses abril a agosto, VIIRS 375 | B / F | 860 / 134 | 904 / 138 | 852 / 109 | 888 / 134 | 853 / 115 | **no**: F gana en las cinco |
| meses abril a agosto, VIIRS 750 | B / F | 400 / 90 | 400 / 90 | 400 / 90 | 400 / 90 | 400 / 90 | **no** (la regla no toca VIIRS 750) |
| ídem, sensibilidad con umbral 0,15 MW en VIIRS 750 (del estudio) | B / F | 400 / 90 | 398 / 88 | 397 / 87 | | | **no** |
| Chillán, tres sensores | C0 / B / J / F=K=KE=KET | 52 / 17 / 23 / 7 | 55 / 17 / 23 / 6 | 52 / 15 / 21 / 5 | 52 / 16 / 22 / 6 | 52 / 16 / 22 / 6 | **no**: F, K, KE y KET empatan arriba en las cinco |
| techo del A/B de D22 (pérdidas recuperables) | | 14 | 5 | 5 | 8 | 8 | **sí, el techo cae** |

## Cómo leerlo

**Ningún veredicto de brazo cambia**, y eso tiene poco poder, como ya dijo el estudio (§3 de `README.md`): B y F
difieren de 6 a 8 veces y ningún tratamiento de 155 pasadas podía darlos vuelta. En Chillán F, K, KE y KET
empatan en las cinco reglas. Donde la regla sí puede decidir es entre brazos parecidos: el A/B de F y K contra
producción que corre ahora (`experiments/_s151_prereg_fk_11/`), cuyo evaluador informa las cinco reglas al lado
de la que decide (sección 10 de `evaluar_fk.py`).

**Lo que cambia es el techo de D22**: de 14 pérdidas recuperables quedan 5 con la regla decidida, 8 si 0,05
exacto se deja como alerta. La razón física: de las 14 alertas que `max` pierde por el camino de D22, 9 son de
0,05 MW o menos, o sea pasadas en que MIROVA, en su propia imagen, dice no ver anomalía.

**Implicancia para la tarea 1.3 (el A/B de D22): el umbral de equilibrio baja de 5,2 % a 1,8 %.** La tarea 1.3
concluyó que quitar la compuerta D22 sólo gana si reabre menos de 14 de los 271 negativos limpios que el mismo
camino puede reabrir (`experiments/_s151_d22_techo/salida.txt`). Con SN cambian las dos partes de esa razón
(`techo_d22_bajo_sn.py`, salida en `techo_d22_bajo_sn_salida.txt`):

| regla | lo que el A/B puede recuperar | negativos que puede reabrir | umbral de equilibrio |
|---|---|---|---|
| original | 14 | 271 | 5,2 % |
| SN (la decidida) | 5 | 277 | **1,8 %** |
| SN_004 (0,05 como alerta) | 8 | 275 | 2,9 % |

El denominador sube porque las pasadas que dejan de ser alerta, y otras de las mismas noches que quedan sin alerta,
pasan a ser negativos limpios del mismo estrato (B las publica, F no, y el record de B va por el camino D22): 6 con
SN, 4 con SN_004. Tres de las 6 son pérdidas de la lista de D22 (Chaitén 23-ago, Isluga 25-may y Tupungatito
22-abr), que con SN pasan de "alerta que el A/B recuperaría" a "negativo que el A/B reabriría". Control: con la
regla original la misma cuenta da los 271 del verificador (`docs/audit_s150/VERIFICADOR_PREREGISTRO_D22.md` H4).
Físicamente: lo que el A/B de D22 iba a recuperar era, en su mayoría, calor que MIROVA en su propia imagen dice no
ver; sin eso quedan 5 pasadas de 0,06 a 0,08 MW contra 277 pasadas que pueden encenderse. Refuerza no gastar ese A/B.
(La tarea 1.3 vive en `tasks/LOOP_OBJETIVOS.md`, en otra rama; su marca la pone el coordinador.)

**SN castiga a quien publica lo mínimo.** Con SN, F sube de 63 a 92 negativos limpios publicados en VIIRS 375:
las pasadas mínimas que F sí publicaba pasan a ser falsas alarmas. Con SE salen de la cuenta y la suma de F baja de
134 a 109. Las
dos son lecturas literales; SN es la decidida porque es la letra de la regla 3 del criterio de victoria.

## Archivos

- `veredictos_tres_reglas.py`: el conteo. Necesita la referencia congelada de los meses
  (`experiments/_s149_prereg_invierno/_congelado/<mes>/`, en `.gitignore`; se verifica contra el manifiesto).
  Uso: `python veredictos_tres_reglas.py --congelado-meses DIR > veredictos_tres_reglas_salida.txt`.
- `veredictos_tres_reglas_salida.txt`: la salida.
- `techo_d22_bajo_sn.py` y `techo_d22_bajo_sn_salida.txt`: el umbral de equilibrio de D22 con cada regla. Baja los
  records de B de las ramas `s146-ab/<run>` de S150 con `git archive` con ruta, a la carpeta de `--tmp`.
