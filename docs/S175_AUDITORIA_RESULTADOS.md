# Auditoría S175: resultados y traspaso (2026-11-08)

> ⚠️ S175 VX (marca A113, 2026-11-08). Copia en el repo del traspaso que quedó fuera de él, sin las rutas privadas. Se
> escribió antes de que terminaran VX, F4t y V4T, y sus resultados están en `docs/AUDIT_S175.md` §11. Lo que cambió desde
> entonces: 302, 108, 111 y 256 ya tienen verificador (302 quedó CONFIRMADO EN PARTE, ver la marca más abajo); la parte del
> token de F4 se hizo como F4t; F5b sigue en curso. El estado de CI de la tabla de PR es el de ese momento.

Sesión orquestadora: «Auditoría S174 de VRP Chile (post S160)», worktree `.claude/worktrees/relaxed-almeida-d17378`, rama
`claude/relaxed-almeida-d17378`.

## Estado

- Auditoría COMPLETA: 5 frentes (F0, F1, F2, F3, F5) con verificador de otro modelo. Síntesis: `docs/AUDIT_S175.md`.
- Plan sellado: `docs/PLAN_AUDITORIA_S175.md`, SHA_PLAN `a325ac8ff`. Base `752d348bc`; F1 con datos de `e75a7d52d`.
- 80 hallazgos de auditor, 43 verificados, ninguno refutado entero (155 refutado en su consecuencia). 37 sin verificar,
  publicados con conteo (puerta de S176). Líneas base rojas: todas reencontradas.
- Esfuerzo: los transcriptos muestran `output_config.effort` high en todos los pedidos; el `reasoning_effort` que
  declaran los agentes no es el nivel (memoria `feedback_s175_esfuerzo_en_transcripto`).

## PR (todos en borrador; el merge lo decide Nicolás)

| PR | qué | CI |
|---|---|---|
| #955 | auditoría S175 (síntesis, plan, `experiments/_s175_audit/`) | pytest falló por `test_g6` (INDEX.md sin AUDIT_S175); arreglado en `9da257d92`, CI nuevo corriendo |
| #956 | SINTOMAS (MODIS de producción es la vía), ficha CPLT v1.19, marca A113 en la regla de reversión, `.gitignore` para `hallazgos*.csv` | verde |
| #957 | recall por pasada, distancia de la tabla con origen común, D-9 en banco, VRP del OCR como piso (sesión `local_ad936bbb`) | verde |
| #958 | «MIROVA confirmó» por pasada ±120 s con D-9 en las tres vistas; 856 de 2.738 pierden la marca (sesión `local_4127542e`) | verde |
| #959 | vigilancia de la guardia MODIS por volcán y `sin_grilla`/`sin_mxd03` como K con aviso; M2, M6, M2c atrapadas (sesión `local_9066b242`) | verde |

## Respuesta de Nicolás medida

El truncado del VRP es del OCR, no de la tabla: en `latest_consolidado.csv` 141 de 142 alertas MODIS traen decimales;
en el OCR las 48 MODIS y las 95 VIIRS 750 son enteras. La protegida «perdida» Chillán MODIS 2026-10-30 07:15 (1,0 MW)
existe sólo en el OCR. Decisión 9 de AUDIT_S175 actualizada.

## Pendientes

1. Rotar `EARTHDATA_TOKEN` antes del 2026-11-27 (sólo Nicolás).
2. Anexo §10 de AUDIT_S175: audit semanal del 2026-11-09 09:00 UTC contra la regla §4 de reversión.
3. Rastro del descarte de borde de la vía (153): exige tocar `pipeline/process_modis.py`, A45 pendiente.
4. VIIRS 750 en cumbre (101, 102): sin camino desde que D25 no se adoptó; programa V750, sin urgencia.
5. Alerta #960 (sombra de los 34 sin corrida verde 26 h): la corrida del 2026-11-07 17:59 falló sólo en el job de Lanín
   (run 42398984848); causa no leída. Fuera de la auditoría.
6. Alertas #915 y #936 siguen abiertas a propósito (ver S174).

## Qué repetir o mejorar (recomendación)

No hace falta repetir ningún frente. Mejoras, en orden de valor por costo:
1. Verificar 4 de los 37 sin verificar que sostienen conclusiones: 302 (los aciertos por misma pasada son el mismo foco),
   108 (cola de campo sin tocar desde S160), 256 (memoria dice que MxD03 se ignora), 111 (nadie mide la fracción MODIS NRT).
   Un verificador Opus como subagente, unos 300 mil tokens.
   ⚠️ S175 VX (marca A113): hecho con VX. 302 quedó CONFIRMADO EN PARTE: lo medido es compatibilidad radial con la distancia
   de la tabla (714 de 715, nulo 93 %); «son el mismo foco» no está medido. Los otros tres, CONFIRMADOS.
2. Rehacer la posición de F5 después del 2026-09-22 con las láminas PNG Latest10NTI georreferenciadas contra un TIF
   anterior (F5 no lo hizo; I2 quedó en clase (iv) desde esa fecha).
   ⚠️ S175 (marca A113): en curso como F5b.
3. F4 (vencimientos simulando la ausencia) quedó recortado: hacerlo en la próxima auditoría A51.
   ⚠️ S175 (marca A113): la parte del token se hizo como F4t con V4T (`docs/AUDIT_S175.md` §11.3); el resto de F4 sigue
   recortado.
4. Volver a Fable como auditor (subagente con `effort: high`), que era el plan; en S175 F0, F2, F3 y F5 corrieron en Opus.
