# Flujo de sincronización

```text
Usuario
  → SUPER_MANAGER_MZ0          registra el encargo y crea NXP-####
      → un gerente             solo el del módulo que toca
          → su especialista    delegación con assignee
              → gerente        handoff §41, o revisión si es crítico o QA
          → SUPER_MANAGER_MZ0  el gerente no salta a otro módulo
      → siguiente gerente      reasignación, con las compuertas que apliquen
      → MANAGER_MZ5_QA         las cinco compuertas, cada una por su dueño
      → cierre                 solo si todas están en PASS
```

## Qué ve cada uno

| Quién | Qué se sincroniza |
| --- | --- |
| Cualquier agente autenticado | Tablero: estado, línea de actividad, tarea asociada. Compuertas: valor, no el entregable ajeno. |
| El destinatario | El cuerpo del mensaje, en su bandeja. |
| El gerente | Además, las carpetas de su equipo, en lectura. |
| Comando | Todo el pelotón menos los secretos, más la copia de la coordinación frontend/backend. |

Un revisor de diseño no ve el informe de otro revisor antes de entregar el suyo. Un especialista de QA no sella la compuerta de otro. El tablero no sirve para colar el entregable: la línea de actividad se corta a 240 caracteres.

## Recorrido de una UI mayor

1. Comando asigna investigación a `MANAGER_MZ1_RESEARCH`, si la sección 54 la exige.
2. El equipo de investigación entrega hacia arriba. Comando reasigna a `MANAGER_MZ2_DESIGN`.
3. Los cinco críticos informan solo a diseño. Diseño sintetiza y, con evidencia, pone `DESIGN_APPROVED = TRUE`.
4. Solo entonces comando puede asignar la implementación a `MANAGER_MZ3_FRONTEND` con `ui_change: major`.
5. Si backend tiene que cambiar un comportamiento visible, `MANAGER_MZ4_BACKEND` coordina con frontend. Comando ve la copia.
6. Comando reasigna a QA. Cada especialista fija su compuerta. Un fallo vuelve a comando, comando al gerente responsable, y las compuertas de QA se invalidan.
7. Comando cierra, con el informe de la sección 62 hacia el usuario. El canal no redacta ese informe solo.

## Lo que este flujo no es

No es la sincronización en la nube de las notas. No es un chat libre entre los 32. No sustituye la inspección del repositorio: hoy esa inspección ya está escrita en `memoria/ARCHITECTURE.md` y dice que no hay aplicación.
