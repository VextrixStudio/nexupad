# Arquitectura

Inspección: 2026-09-24. Método: listado del árbol de trabajo, `git log`, `git remote`. No se lanzó un build: no hay manifiesto que construir. No se asumió el stack. La sección 37 lo prohíbe.

## Qué hay

- Repositorio: `https://github.com/VextrixStudio/nexupad.git`
- Commit inspeccionado: `5198f41275bc1d7f393917477c8f1d1dd49ba7dc`
- Fecha de ese commit: 2026-04-13
- Mensaje: `Expand README with features and subscription plans`
- Archivo de producto fuera del pelotón: `README.md`
- Rama de esta sesión: `arena/01a0d42a-nexupad`

## Qué no hay

No hay `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, lockfile, ni otro manifiesto de dependencias. No hay framework identificable, rutas, componentes, estado, API, base de datos, autenticación, sincronización, tests, linter, formateador ni configuración de despliegue.

## Consecuencia para el pelotón

Frontend, backend y QA no tienen un módulo de producto sobre el que escribir. Sus credenciales no conceden rutas fuera de `platoon/`. Cuando aparezca código, se reinspecciona y se anota aquí lo que se vea. Hasta entonces, un entregable que nombre archivos de aplicación que no existen viola la sección 63.

## Pelotón

La estructura de agentes, permisos y canal es infraestructura de coordinación, no arquitectura de la aplicación. No se documenta como si NexuPad ya fuera un cliente React o un servicio con base de datos.
