# Secretos locales

Un archivo `{AGENTE}.token` por agente, modo 600. Git ignora `*.token`.

No los copies a entregables, al canal, a la memoria ni al chat de cierre. La especificación, sección 58, lo prohíbe. Cada agente solo usa el suyo, con `--usar-secreto-local` o con su variable `NEXUPAD_TOKEN_{AGENTE}`.

Rotar el propio: `python3 platoon/permisos/verificar.py rotar --agente ID --usar-secreto-local`.
Esa orden no imprime el secreto nuevo. Actualiza la huella en `huellas.json`.
