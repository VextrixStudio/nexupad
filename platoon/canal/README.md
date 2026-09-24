# Canal

Sirve para que los agentes se sincronicen sin leerse las carpetas. Hay dos planos:

1. **Tablero.** Estado y una línea de actividad de cada agente. Lo ve cualquier credencial válida. No lleva el cuerpo del entregable ni secretos.
2. **Bandeja.** El mensaje completo llega solo al destinatario que la cadena de mando permite. Comando recibe copia de la coordinación entre frontend y backend.

El registro append-only está en `registro/actividad.jsonl`. Anota quién envió qué tipo, a quién y sobre qué tarea. No anota el cuerpo.

## Órdenes

Desde la raíz del repositorio. `--json` va antes del subcomando.

```bash
python3 platoon/canal/nexu_canal.py sincronizar \
  --agente SUPER_MANAGER_MZ0 --usar-secreto-local

python3 platoon/canal/nexu_canal.py estado \
  --agente BUSCADOR_MZ1 --usar-secreto-local \
  --status en_progreso \
  --actividad "Revisando el paquete asignado, sin afirmar fuentes no abiertas." \
  --task NXP-0001

python3 platoon/canal/nexu_canal.py publicar \
  --agente SUPER_MANAGER_MZ0 --usar-secreto-local \
  --archivo platoon/canal/ejemplos/asignacion.ejemplo.json \
  --simular

python3 platoon/canal/nexu_canal.py bandeja \
  --agente ANALYST_MZ2 --usar-secreto-local

python3 platoon/canal/nexu_canal.py compuerta consultar \
  --agente MANAGER_MZ5_QA --usar-secreto-local \
  --task NXP-0001

python3 platoon/canal/nexu_canal.py tarea \
  --agente MANAGER_MZ2_DESIGN --usar-secreto-local \
  --task NXP-0001
```

`--simular` valida y no escribe. Un archivo con `"_ejemplo": true` no se puede publicar como trabajo real.

Los estados admitidos son `inactivo`, `listo`, `asignado`, `en_progreso`, `bloqueado`, `en_revision`, `entregado` y `retrabajo`. La línea de actividad admite 240 caracteres: el entregable va en el handoff.

El protocolo de campos y de enrutado está en `protocolo.md`. El recorrido de una tarea está en `flujo.md`.
