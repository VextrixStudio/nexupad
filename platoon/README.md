# Pelotón de desarrollo de NexuPad

Esta es la carpeta única del sistema de agentes. No hay otra raíz. La especificación pedía la memoria de proyecto en `/docs/AI/`; el encargo pide una sola carpeta principal, y la propia especificación dice que, si ya hay una estructura equivalente, se adapta en lugar de duplicar. La memoria vive en `memoria/`. La decisión está registrada en `memoria/AGENT_DECISIONS.md`.

La especificación operativa, copiada sin reescribirla, está en [`agentes.md`](agentes.md). Si este README y esa especificación discrepan, manda la especificación.

## Qué hay aquí

| Ruta | Para qué |
| --- | --- |
| [`agentes/`](agentes/INDICE.md) | Una carpeta por agente, con sus tareas. Son 32: los que la especificación nombra. |
| [`permisos/`](permisos/README.md) | Credencial por agente, limitada a su módulo y a su sección. |
| [`canal/`](canal/README.md) | Flujo de asignación, entrega, revisión y tablero de estados. |
| [`memoria/`](memoria/README.md) | Los ocho artefactos de la sección 56, todavía sin trabajo de producto inventado. |
| [`lib/`](lib/politica.py) | El control que consultan las dos herramientas. No es una sección de ningún agente. |

El repositorio de producto, fuera de esta carpeta, sigue siendo solo `README.md`. No se asumió un framework. La inspección está en `memoria/ARCHITECTURE.md`.

## Agentes

La cadena es la de la especificación: el usuario habla con `SUPER_MANAGER_MZ0`; comando asigna solo a los cinco gerentes; cada gerente reparte dentro de su equipo. El índice con enlaces a cada `TAREAS.md` está en [`agentes/INDICE.md`](agentes/INDICE.md).

Ningún agente ha ejecutado todavía una tarea de producto. Su estado inicial es `listo`.

## Credenciales

Cada agente tiene un identificador público en `permisos/credenciales.json` y un secreto solo en `permisos/secretos/{AGENTE}.token`. Ese archivo está en `.gitignore`, modo 600, y no se imprime.

```bash
python3 platoon/permisos/verificar.py identidad --agente BUSCADOR_MZ1
python3 platoon/permisos/verificar.py comprobar \
  --agente BUSCADOR_MZ1 --usar-secreto-local \
  --ruta platoon/agentes/BUSCADOR_MZ1/entregables/nota.md \
  --operacion escribir
```

Hay un solo usuario de sistema en este entorno. El aislamiento es lógico: las herramientas lo aplican. No es una cuenta del sistema operativo por agente. El detalle, y lo que cada credencial no puede hacer, está en `permisos/ALCANCE.md`.

## Canal

El tablero sincroniza estado y una línea de actividad. El entregable viaja solo a la bandeja de quien debe recibirlo. Un especialista no lee la carpeta de otro; los cinco revisores de diseño tampoco se leen entre sí.

```bash
python3 platoon/canal/nexu_canal.py sincronizar \
  --agente MANAGER_MZ1_RESEARCH --usar-secreto-local
```

`--json`, si se usa, va antes del subcomando. El protocolo está en `canal/protocolo.md` y el flujo en `canal/flujo.md`.

## Qué no se hizo

No se consultó Mobbin, Figma ni ninguna fuente de la sección 6. No hay informe de investigación, ni diseño aprobado, ni implementación, ni QA de producto. Afirmar lo contrario violaría la sección 63. Esta carpeta deja el pelotón en condiciones de recibir el primer encargo, no lo ejecuta por adelantado.

## Comprobación del mecanismo

```bash
python3 platoon/canal/comprobar_canal.py
```

Esa orden usa una copia temporal. No escribe en el canal real y no prueba la aplicación: no hay aplicación. El resultado de la ejecución hecha el 2026-09-24 está en `memoria/QA_REPORTS.md`.
