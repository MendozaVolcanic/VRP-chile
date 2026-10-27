# Notas de reproducción del verificador de la adenda 2 de V750-B

Todo se corre desde `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-viirs750-2-918174`
salvo lo del generador, que se corre desde el árbol de ensayo `C:\vrp-trabajo\temporales\v750b_supl_ensayo` (extraído de
`origin/main` `bd711db63`, con su `objetivos_v750b.json` y `ref/`). Evaluador del tag:
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile--claude-worktrees-s162-viirs750-2-918174\0c1274cb-99b4-4a91-a624-a9ed2be04812\scratchpad\evaluar_d25.py`
(sha256 `2e5576973ef1df6969f517c40bedc271f76db8a8b4756613e5004fc05d976747`, comprobado).

## Batería del autor (solo lectura)
    python experiments\_s162_v750b\adenda2\probar_adenda2.py --evaluador <evaluador> --dest C:\vrp-trabajo\temporales\v750b_ver2\bat
Salida: `bateria_autor_corrida_verificador.txt`. Ojo: P7 crea y borra `experiments\_s162_v750b\_p7_analizar_otro.py`.

## Pruebas propias (cada una declara sus dos preguntas del instrumento en su encabezado)
- `ver_t1_consistencia_radiante_vs_sellado.py`: lector «radiante» contra analizador sellado B0..B5 (VAD2-02).
- `ver_t1b_ancla_craterdesplazado.py [<lector mutado>]`: lo mismo con cráter corrido, canales decide y tabla; con la copia
  mutada M3 (`_m\m05_leer_posicion_v750b.py`, ruta absoluta) debe dar DISTINTO (VAD2-04).
- `ver_t4_separar_colision.py` (VAD2-01), `ver_t5_robustez.py`, `ver_t6_vara3_ocr.py` (VAD2-05),
  `ver_t7_escena_pico.py`, `ver_t8_escala.py`, `ver_t9_trozos_y_conteos.py` (VAD2-10 y cifras del §6).
- `ver_mutar.py [filtro]`: 30 mutaciones mías con la batería del autor como evaluador (unos 7 min); copias en `_m\`.
  Sale `ver_mutar_salida.txt` (identidades PASA, control CAIDA).

## Generador (VAD2-03 y VAD2-08), desde `C:\vrp-trabajo\temporales\v750b_supl_ensayo`
    python experiments\_s162_v750b\adenda2\objetivos_supl_v750b.py --data data\mirova_equivalent --ref-dest <carpeta> --hasta 2026-10-26 --sellado experiments\_s162_v750b\objetivos_v750b.json --dest <dest1>
Corrida sana (`logs\gen1.log`): 5841 contra 5841 IGUALES, 20 `far_ref`, 0 sin gránulo.
- VAD2-03: copiar a `<dest2>` un `objetivos_run_v750b.json` y un `objetivos_supl_v750b.json` previos y correr con `--hasta
  2026-10-25`: control «5803 contra 5841, DISTINTAS», salida 1, y los dos archivos viejos siguen ahí junto a un
  `poblacion_supl.json` nuevo (`logs\gen2.log`).
- VAD2-08: `--sellado` con una lista sin su primer objeto → salida 1 (`logs\g_sellada_menos1.log`); con una
  pasada `neg_limpio` pasada a `pos` protegida (misma clave) → IGUALES y escribe todo (`logs\g_sellada_lab_cambiada.log`).
  Las dos listas alteradas se armaron con unas líneas de Python sobre `objetivos_v750b.json` (sacar `s[0]`; cambiar `lab` y
  `protegida` del primer `neg_limpio`).
