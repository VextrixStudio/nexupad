#!/bin/sh
# Activa el hook que bloquea credenciales (especificación §58).
cd "$(git rev-parse --show-toplevel)" || exit 1
git config core.hooksPath platoon/hooks
echo "core.hooksPath=platoon/hooks"
