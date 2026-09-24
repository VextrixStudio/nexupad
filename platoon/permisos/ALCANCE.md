# Alcance por módulo

La credencial restringe a la sección, no al pelotón entero. Lectura de la especificación, de la memoria y del tablero es común: sin eso no hay sincronización. Escritura, no.

| Módulo | Quién escribe | Dónde |
| --- | --- | --- |
| `comando` | `SUPER_MANAGER_MZ0` | su `entregables/` y `notas/`, y toda `memoria/` |
| `investigacion` | el gerente | su sección, más `memoria/RESEARCH.md` |
| `investigacion` | cada especialista | solo su `entregables/` y `notas/` |
| `diseno` | el gerente | su sección, más `DESIGN_SYSTEM.md` y `UX_DECISIONS.md` |
| `diseno` | cada revisor | solo su sección. No leen a los otros cuatro |
| `frontend` | gerente y especialistas | cada uno, solo su sección |
| `backend` | gerente y especialistas | cada uno, solo su sección |
| `calidad` | el gerente | su sección, más `memoria/QA_REPORTS.md` |
| `calidad` | cada especialista | solo su sección, y solo su compuerta |

## Secciones

Los nombres de sección están en `perfil.json` de cada agente y en `agentes/INDICE.md`. No se comparten. `qa-funcional` no abre `qa-visual`. `revision-apple` no abre `revision-google`. `datos` no abre `api`.

## Compuertas

No son archivos que un agente edite a mano.

| Compuerta | Quién puede ponerla en verdadero o PASS | Quién puede revocarla |
| --- | --- | --- |
| `DESIGN_APPROVED` | `MANAGER_MZ2_DESIGN`, con la tarea asignada a diseño | ese gerente, o comando |
| `FUNCTIONAL_QA` | `FUNCTIONAL_QA_MZ` | se invalida sola al salir de QA para retrabajo |
| `VISUAL_QA` | `VISUAL_QA_MZ` | igual |
| `ACCESSIBILITY_QA` | `ACCESSIBILITY_QA_MZ` | igual |
| `PERFORMANCE_QA` | `PERFORMANCE_QA_MZ` | igual |
| `REGRESSION_QA` | `REGRESSION_QA_MZ` | igual |

Un PASS exige tres comprobaciones concretas. «Looks good.» se rechaza. Comando no puede sellar QA ni aprobar el diseño en lugar del gerente.

## Código de producto

Ninguna credencial escribe fuera de `platoon/`. Cuando exista una aplicación y una tarea lo exija, la concesión la tiene que añadir quien mantiene esta política, en git, con un `task_id`. Un agente no se amplía el alcance a sí mismo: `matriz.json` no está en la lista de escritura de nadie.
