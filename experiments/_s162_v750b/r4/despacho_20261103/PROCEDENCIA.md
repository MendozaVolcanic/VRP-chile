# V750-B: despacho del 2026-11-03

- Autorización: Nicolás, textual «Sí, despachar», relayada por la coordinadora S173.
- main del día: `152071e8e27462fae38aca6c6879befe88fa2f5d` (último commit 2026-11-03 09:48:57 UTC). Carpeta de V750-B del tag sellado
  `s167-v750b-adenda3-sellada` (`3da2c42f8`).
- `VRP_PROFILE` vacío; control de datos OK (fecha máxima VIIRS 750 2026-11-03 06:48, `--hasta 2026-11-02`).
- Generador sellado: salida 0, 6.022 objetivos, 0 sin gránulo. Suplementario: salida 0, control IGUALES 6.022 contra
  6.022, 20 `far_ref`, 0 sin gránulo. N-3: 4 protegidas que deciden, las 4 en O (las mismas del ensayo del 29-oct).
- sha256: sellada `7c9d3da5...ef393c582`, suplementaria `c4d75157...af9db256`, lista del run `9da82c4a...409ac970e`
  (6.042 pasadas). Detalle en `armar_salida.txt`; diff contra main fuera de V750-B y del workflow: vacío.
- Tag `s169-v750b-objetivos-20261103` (objeto `ef1d62833`, commit `94f67fd6c`). Despacho: push de ese commit a
  `refs/heads/s162-v750b-disparo` el 2026-11-03 09:55:59 UTC. Run `41615021658` (headSha `94f67fd6c`), 32 trozos,
  timeout 120 min, autenticación sólo por `EARTHDATA_TOKEN`.
- Sesgos escritos antes de leer: `experiments/_s162_v750b/SESGOS_CONOCIDOS_V750B.md` (commit `d38ea812a`).
