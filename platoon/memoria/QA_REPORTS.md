# Informes de QA

No hay QA de producto. No hay aplicación, ni diseño aprobado, ni flujos de notas, calendario, tareas, búsqueda, ajustes, autenticación o sincronización que ejecutar. Las cinco compuertas de producto no están en PASS. No se declaran en PASS.

## 2026-09-24 — Comprobación del canal y de los permisos

Objeto: el mecanismo de secciones y de sincronización del pelotón. No el producto.

Orden ejecutada, desde la raíz del repositorio:

```bash
python3 platoon/canal/comprobar_canal.py
```

La orden copia el pelotón a un directorio temporal. No escribe en el canal real.

Hubo dos ejecuciones fallidas, del propio mecanismo, antes de la que se registra como válida:

1. Ocho fallos. `priority` exigía 12 caracteres y el ejemplo de la sección 40 es `high`. La normalización de rutas trataba `../` de forma insegura.
2. Dos fallos, ya corregido lo anterior. `TASK` exigía 12 caracteres y `NXP-0101` tiene 8. El caso de ruta fuera del pelotón miraba solo la excepción, no el dictamen `permitido: false`.

Esas dos ejecuciones no se cuentan como PASS. Se corrigió el canal y el caso de prueba. La tercera ejecución, la que vale, terminó así:

```text
PASS  credencial propia aceptada
PASS  credencial ajena rechazada
PASS  agente desconocido rechazado
PASS  especialista escribe en su sección
PASS  especialista no reescribe sus tareas asignadas
PASS  especialista no escribe en otra sección
PASS  especialista no lee la carpeta de otro especialista
PASS  gerente lee a su equipo y no al equipo ajeno
PASS  gerente no reescribe el entregable de su equipo
PASS  investigación escribe solo su memoria
PASS  comando no lee secretos ni escribe el control
PASS  ruta fuera del pelotón rechazada
PASS  el contenido con un secreto se rechaza
PASS  cadena de mando, handoff interno y sello vacío
PASS  compuerta de diseño, UI mayor y revocación
PASS  revisores independientes
PASS  coordinación backend-frontend con copia a comando
PASS  QA por dueño, sello vacío y cierre solo de comando
PASS  retrabajo invalida las compuertas de QA
PASS  tablero público sin cuerpos ni secretos
PASS  ejemplo no publicable y CLI de permisos
comprobaciones fallidas: 0
```

Salida de proceso: 0.

Esto no es `FUNCTIONAL_QA = PASS` ni ninguna otra compuerta de la sección 43. Ningún agente de QA fue quien lo ejecutó: lo ejecutó la orquestación de este montaje, sobre el canal, antes de que hubiera una tarea `NXP-` real. Queda aquí para no afirmar después que no se comprobó, ni afirmar que se comprobó otra cosa.
