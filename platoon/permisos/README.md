# Permisos

Cada agente tiene una credencial. La credencial abre su sección y nada más. La matriz legible, sin secretos, es `matriz.json`. El directorio público es `credenciales.json`. La huella SHA-256 del secreto, no el secreto, es `huellas.json`.

## Qué se entrega

| Pieza | Dónde | ¿Se confirma en git? |
| --- | --- | --- |
| Identificador público `cred_…` | `credenciales.json` | Sí |
| Secreto | `secretos/{AGENTE}.token`, modo 600 | No |
| Variable equivalente | `NEXUPAD_TOKEN_{AGENTE}` | No |
| Huella | `huellas.json` | Sí |

La sección 58 prohíbe exponer claves, contraseñas, tokens y credenciales. Por eso el secreto no está en el repositorio, no lo imprime `identidad` y el canal rechaza un mensaje que lo contenga.

## Cómo se usa

Desde la raíz del repositorio:

```bash
python3 platoon/permisos/verificar.py identidad --agente API_MZ
python3 platoon/permisos/verificar.py comprobar \
  --agente API_MZ --usar-secreto-local \
  --ruta platoon/agentes/API_MZ/entregables/contrato.md \
  --operacion escribir
python3 platoon/permisos/verificar.py leer \
  --agente API_MZ --usar-secreto-local \
  --ruta platoon/memoria/ARCHITECTURE.md
python3 platoon/permisos/verificar.py guardar \
  --agente API_MZ --usar-secreto-local \
  --ruta platoon/agentes/API_MZ/entregables/contrato.md \
  --contenido "Propuesta. No es un endpoint disponible."
python3 platoon/permisos/verificar.py rotar \
  --agente API_MZ --usar-secreto-local
```

`rotar` cambia el secreto propio, actualiza la huella y no imprime el valor nuevo. Nadie rota el secreto de otro: no lo tiene.

`--usar-secreto-local` lee únicamente `secretos/{el agente que firma}.token`. Pasar el secreto de otro agente produce «credencial rechazada».

## Qué no abre ninguna credencial

- `permisos/secretos/` de cualquiera, incluida la propia, por la vía de `leer`. El secreto se usa para autenticar, no para copiarlo a un entregable.
- `lib/`, `hooks/` y el canal, por `guardar`. El canal solo lo escribe `nexu_canal.py` después de autenticar.
- `TAREAS.md`, `perfil.json` y el índice. La tarea asignada no se reescribe el agente a sí mismo.
- El código de producto. Hoy no hay módulos de aplicación, y ninguna tarea ha concedido esa ruta.
- La carpeta de otro agente. Un gerente lee a su equipo y no escribe en ella.

## Límite honesto

Este entorno tiene un usuario de sistema. La separación no es una cuenta UNIX por agente. Quien ignore las herramientas y edite archivos a mano se sale del protocolo. El hook `hooks/pre-commit` impide confirmar un `.token` o un `.env`; no impide toda edición local. Para activarlo:

```bash
sh platoon/hooks/instalar.sh
```

El alcance por módulo está en `ALCANCE.md`.
