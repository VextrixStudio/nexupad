# Índice del pelotón

Una carpeta por agente. El identificador de la carpeta es el identificador de la credencial. Hay 32 agentes nombrados en la especificación: comando, cinco gerentes y los especialistas de cada equipo, incluidos los que §24 llama «may include» y los que §30 llama «possible specialists». Están nombrados, así que tienen sección. No se creó ningún agente que la especificación no nombre.

```text
SUPER_MANAGER_MZ0
|
+-- MANAGER_MZ1_RESEARCH
|     +-- BUSCADOR_MZ1
|     +-- ANALYST_MZ2
|     +-- TREND_MZ3
|     +-- SOURCE_VALIDATOR_MZ4
|
+-- MANAGER_MZ2_DESIGN
|     +-- APPLE_REVIEWER_MZ
|     +-- GOOGLE_REVIEWER_MZ
|     +-- SAMSUNG_REVIEWER_MZ
|     +-- MACOS_REVIEWER_MZ
|     +-- CRITIC_MZ
|
+-- MANAGER_MZ3_FRONTEND
|     +-- FRONTEND_CORE_MZ
|     +-- MOBILE_FRONTEND_MZ
|     +-- DESKTOP_FRONTEND_MZ
|     +-- COMPONENT_MZ
|     +-- ANIMATION_MZ
|     +-- ACCESSIBILITY_FRONTEND_MZ
|
+-- MANAGER_MZ4_BACKEND
|     +-- BACKEND_CORE_MZ
|     +-- DATABASE_MZ
|     +-- AUTH_MZ
|     +-- SYNC_MZ
|     +-- SECURITY_MZ
|     +-- API_MZ
|
+-- MANAGER_MZ5_QA
      +-- FUNCTIONAL_QA_MZ
      +-- VISUAL_QA_MZ
      +-- ACCESSIBILITY_QA_MZ
      +-- PERFORMANCE_QA_MZ
      +-- REGRESSION_QA_MZ
```

| Agente | Rango | Módulo | Sección | Reporta a |
| --- | --- | --- | --- | --- |
| [SUPER_MANAGER_MZ0](SUPER_MANAGER_MZ0/TAREAS.md) | comando | comando | comando | usuario |
| [MANAGER_MZ1_RESEARCH](MANAGER_MZ1_RESEARCH/TAREAS.md) | gerente | investigacion | investigacion | SUPER_MANAGER_MZ0 |
| [MANAGER_MZ2_DESIGN](MANAGER_MZ2_DESIGN/TAREAS.md) | gerente | diseno | diseno | SUPER_MANAGER_MZ0 |
| [MANAGER_MZ3_FRONTEND](MANAGER_MZ3_FRONTEND/TAREAS.md) | gerente | frontend | frontend | SUPER_MANAGER_MZ0 |
| [MANAGER_MZ4_BACKEND](MANAGER_MZ4_BACKEND/TAREAS.md) | gerente | backend | backend | SUPER_MANAGER_MZ0 |
| [MANAGER_MZ5_QA](MANAGER_MZ5_QA/TAREAS.md) | gerente | calidad | calidad | SUPER_MANAGER_MZ0 |
| [BUSCADOR_MZ1](BUSCADOR_MZ1/TAREAS.md) | especialista | investigacion | busqueda | MANAGER_MZ1_RESEARCH |
| [ANALYST_MZ2](ANALYST_MZ2/TAREAS.md) | especialista | investigacion | analisis | MANAGER_MZ1_RESEARCH |
| [TREND_MZ3](TREND_MZ3/TAREAS.md) | especialista | investigacion | tendencias | MANAGER_MZ1_RESEARCH |
| [SOURCE_VALIDATOR_MZ4](SOURCE_VALIDATOR_MZ4/TAREAS.md) | especialista | investigacion | validacion-de-fuentes | MANAGER_MZ1_RESEARCH |
| [APPLE_REVIEWER_MZ](APPLE_REVIEWER_MZ/TAREAS.md) | especialista | diseno | revision-apple | MANAGER_MZ2_DESIGN |
| [GOOGLE_REVIEWER_MZ](GOOGLE_REVIEWER_MZ/TAREAS.md) | especialista | diseno | revision-google | MANAGER_MZ2_DESIGN |
| [SAMSUNG_REVIEWER_MZ](SAMSUNG_REVIEWER_MZ/TAREAS.md) | especialista | diseno | revision-samsung | MANAGER_MZ2_DESIGN |
| [MACOS_REVIEWER_MZ](MACOS_REVIEWER_MZ/TAREAS.md) | especialista | diseno | revision-macos | MANAGER_MZ2_DESIGN |
| [CRITIC_MZ](CRITIC_MZ/TAREAS.md) | especialista | diseno | critica-adversaria | MANAGER_MZ2_DESIGN |
| [FRONTEND_CORE_MZ](FRONTEND_CORE_MZ/TAREAS.md) | especialista | frontend | nucleo-frontend | MANAGER_MZ3_FRONTEND |
| [MOBILE_FRONTEND_MZ](MOBILE_FRONTEND_MZ/TAREAS.md) | especialista | frontend | frontend-movil | MANAGER_MZ3_FRONTEND |
| [DESKTOP_FRONTEND_MZ](DESKTOP_FRONTEND_MZ/TAREAS.md) | especialista | frontend | frontend-escritorio | MANAGER_MZ3_FRONTEND |
| [COMPONENT_MZ](COMPONENT_MZ/TAREAS.md) | especialista | frontend | componentes | MANAGER_MZ3_FRONTEND |
| [ANIMATION_MZ](ANIMATION_MZ/TAREAS.md) | especialista | frontend | movimiento | MANAGER_MZ3_FRONTEND |
| [ACCESSIBILITY_FRONTEND_MZ](ACCESSIBILITY_FRONTEND_MZ/TAREAS.md) | especialista | frontend | accesibilidad-frontend | MANAGER_MZ3_FRONTEND |
| [BACKEND_CORE_MZ](BACKEND_CORE_MZ/TAREAS.md) | especialista | backend | nucleo-backend | MANAGER_MZ4_BACKEND |
| [DATABASE_MZ](DATABASE_MZ/TAREAS.md) | especialista | backend | datos | MANAGER_MZ4_BACKEND |
| [AUTH_MZ](AUTH_MZ/TAREAS.md) | especialista | backend | autenticacion | MANAGER_MZ4_BACKEND |
| [SYNC_MZ](SYNC_MZ/TAREAS.md) | especialista | backend | sincronizacion | MANAGER_MZ4_BACKEND |
| [SECURITY_MZ](SECURITY_MZ/TAREAS.md) | especialista | backend | seguridad | MANAGER_MZ4_BACKEND |
| [API_MZ](API_MZ/TAREAS.md) | especialista | backend | api | MANAGER_MZ4_BACKEND |
| [FUNCTIONAL_QA_MZ](FUNCTIONAL_QA_MZ/TAREAS.md) | especialista | calidad | qa-funcional | MANAGER_MZ5_QA |
| [VISUAL_QA_MZ](VISUAL_QA_MZ/TAREAS.md) | especialista | calidad | qa-visual | MANAGER_MZ5_QA |
| [ACCESSIBILITY_QA_MZ](ACCESSIBILITY_QA_MZ/TAREAS.md) | especialista | calidad | qa-accesibilidad | MANAGER_MZ5_QA |
| [PERFORMANCE_QA_MZ](PERFORMANCE_QA_MZ/TAREAS.md) | especialista | calidad | qa-rendimiento | MANAGER_MZ5_QA |
| [REGRESSION_QA_MZ](REGRESSION_QA_MZ/TAREAS.md) | especialista | calidad | qa-regresion | MANAGER_MZ5_QA |

Las carpetas son planas a propósito: el alcance de cada credencial es una ruta, no un árbol heredado del gerente.
