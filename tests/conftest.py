# S119: en Windows la consola default es cp1252; los mensajes runtime del pipeline
# (ej. _diag del breaker CMR en pipeline/fetch.py con "→") crashean con
# UnicodeEncodeError cuando la suite corre con -s (workaround S96) y un test
# ejercita ese path. En GH Actions (Linux, utf-8) no pasa. Reconfigurar stdout/err
# a utf-8 acá blinda la suite local sin tocar pipeline/ (A45).
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass
