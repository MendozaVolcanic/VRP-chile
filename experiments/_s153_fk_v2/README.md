# F/K V1 y V2 evaluadas con el instrumento fijado (S153, regla de adopción de K, #848)

- Instrumento: `evaluar_fk.py` y `unir_intentos.py` del commit `2766c198` (comprobado igual por contenido).
- Uniones: `unir_ventana.py` sobre los intentos de cada ventana (temporal de S153, `C:\Users\nmend\AppData\Local\Temp\claude\`):
  V1 `v1_38639658446\union_2766` (44 de 44 iguales a la unión anterior salvo la clave `_union_intentos`),
  V2a `v2a_38648773684\union_2766` (13 de 14 iguales; el 14.º difiere sólo en marcas de hora de proceso),
  V2b `v2b_39033530622\union` (intentos 1 y 2 = repetición 39068999603 de Llaima, Villarrica, Chaitén y Copahue;
  cobertura 6.147 contra 6.147, pareja).
- **Desviación de procedimiento**: el control de cableado exige que cada carpeta `--logs` traiga los 11 volcanes; la
  repetición de V2b trae 4. Se pasó `v2b_39033530622\logs_union` = logs del intento 1 con los del intento 2 encima
  (las líneas `FLAGS_BRAZO` de los 4 repetidos son idénticas entre intentos). La primera corrida, con las carpetas
  partidas, dio INDECIDIBLE sólo por eso (`v2_logs_partidos.log`).
- Salidas: `v1.log`/`v1.json`, `v2.log`/`v2.json`, `combinado.log`.
