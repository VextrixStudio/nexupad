# Decisiones de agentes

Formato de la sección 57. Solo se registran decisiones de este montaje. No hay decisiones de producto.

## 2026-09-24 — Carpeta única

- Tarea: montar el pelotón.
- Decisión: toda la organización vive en `platoon/`. La memoria de la sección 56 está en `platoon/memoria/`, no en `/docs/AI/`.
- Motivo: el encargo exige una carpeta principal. La sección 56 pide adaptarse si ya hay una estructura equivalente, en lugar de duplicar.
- Agentes: orquestación de este montaje. Ningún especialista había sido activado.
- Alternativa: crear `/docs/AI/` en la raíz y, además, una carpeta por agente. Se descartó porque abre dos raíces.
- Consecuencia: los agentes leen la memoria dentro del pelotón. No hay una segunda copia que mantener.

## 2026-09-24 — Censo de 32 agentes

- Tarea: una carpeta por agente nombrado.
- Decisión: hay carpeta para comando, los cinco gerentes y todos los especialistas que la especificación nombra, incluidos los que la sección 24 introduce con «may include» y los que la sección 30 llama «possible specialists».
- Motivo: están nombrados y tienen responsabilidades atribuibles. No crearlos dejaría secciones sin dueño.
- Alternativa: crear solo los que tienen un encabezado propio. Se descartó porque `ACCESSIBILITY_FRONTEND_MZ` y los especialistas de backend quedarían fuera pese a estar en el organigrama.
- Consecuencia: `ACCESSIBILITY_FRONTEND_MZ` tiene la sección acotada a lo que la especificación realmente dice, y se deja escrito que no tiene lista propia. Las notificaciones no ganaron un agente nuevo: la sección 30 no lo nombra. Quedan en `BACKEND_CORE_MZ`.

## 2026-09-24 — Credenciales locales y aislamiento lógico

- Tarea: dar una credencial a cada agente, restringida a su sección.
- Decisión: secreto por agente en `permisos/secretos/`, gitignored, modo 600, con huella pública. Las herramientas `verificar.py` y `nexu_canal.py` aplican la matriz. Nadie escribe la matriz con su credencial.
- Motivo: la sección 58 prohíbe confirmar secretos. El entorno tiene un solo usuario de sistema; inventar cuentas UNIX no está en la especificación y no se hizo.
- Alternativa: commitear los tokens. Se descartó. Otra alternativa, afirmar aislamiento de sistema operativo, también: sería evidencia falsa.
- Consecuencia: quien edite archivos a mano se sale del protocolo. El hook de git solo bloquea confirmar secretos. El límite está escrito en `permisos/README.md`.

## 2026-09-24 — Canal con cadena de mando

- Tarea: un flujo que sincronice estados y actividades.
- Decisión: tablero público de estado; bandeja privada; handoff y asignación con los campos de las secciones 40 y 41; cruce de módulo solo por comando, salvo la coordinación frontend/backend de la sección 30, que se copia a comando; entregas internas de investigación que la especificación ordena; revisores de diseño sin lectura mutua.
- Motivo: sincronizar sin permitir que un especialista pise el dominio de otro, y sin convertir el tablero en un segundo entregable.
- Alternativa: una bandeja común con los cuerpos de todos los mensajes. Se descartó porque rompe la independencia de las críticas y la restricción de sección.
- Consecuencia: un agente solo trabaja una tarea que comando creó y su gerente le delegó.

## 2026-09-24 — No se empieza el producto

- Tarea: el encargo era la estructura, guiada por la especificación.
- Decisión: no se investiga, no se diseña y no se implementa NexuPad en este paso. No se modifica `README.md`.
- Motivo: no hay código que mejorar, la sección 1 prohíbe reescribir a ciegas, y la sección 54 no exige investigación para este montaje. El encargo restringe lo que no está en el documento o en la petición.
- Alternativa: generar una aplicación de notas para que el pelotón tenga algo que hacer. Se descartó.
- Consecuencia: el siguiente paso, cuando haya un encargo de producto, empieza por entender e inspeccionar de nuevo.

## 2026-09-24 — `priority` corto y `TASK` igual al identificador

- Tarea: que el canal acepte el formato escrito en la especificación.
- Decisión: `priority` puede ser `high`, como en el ejemplo de la sección 40. `TASK` puede ser el `task_id`.
- Motivo: exigir una frase de 12 caracteres rechazaba el ejemplo de la propia especificación.
- Alternativa: dejar el rechazo. Se descartó después de verlo fallar en la comprobación del canal.
- Consecuencia: el ejemplo `canal/ejemplos/asignacion.ejemplo.json` simula sin error. No crea una tarea real.
