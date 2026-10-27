#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    printf 'Erro: execute este script dentro de um repositório Git.\n' >&2
    exit 1
}

hooks_dir="$repo_root/.githooks"
if [[ ! -x "$hooks_dir/pre-commit" || ! -x "$hooks_dir/pre-push" ]]; then
    printf 'Erro: hooks ausentes ou sem permissão de execução em %s\n' "$hooks_dir" >&2
    exit 1
fi

git config --local core.hooksPath "$hooks_dir"
printf 'Hooks Git ativados para este clone: %s\n' "$hooks_dir"
