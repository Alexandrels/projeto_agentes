#!/usr/bin/env python3
"""Reject environment files and likely credentials from the Git index."""

from __future__ import annotations

import os
import re
import subprocess
import sys

KNOWN_SECRET_PATTERNS = (
    re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)

CREDENTIAL_ASSIGNMENT = re.compile(
    r"""(?im)\b[A-Z0-9_]*(?:API[_-]?KEY|SECRET|ACCESS[_-]?TOKEN|AUTH[_-]?TOKEN|PASSWORD|PRIVATE[_-]?KEY|CLIENT[_-]?SECRET)[A-Z0-9_]*\b\s*[:=]\s*(['"]?)([^\s"'`,;#]{6,})"""
)
PLACEHOLDER_WORDS = re.compile(
    r"(?i)(?:your|sua|seu|example|placeholder|changeme|change_me|replace|dummy|sample|xxx|_aqui\b|<|>)"
)
REFERENCE_VALUE = re.compile(
    r"(?i)^(?:os\.|env\.|process\.env|api_key$|secret$|token$|password$|"
    r"[a-z_][a-z0-9_]*(?:_from_env|_env|_key|_secret|_token))"
)


def staged_paths() -> list[bytes]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [path for path in result.stdout.split(b"\0") if path]


def read_staged_file(path: bytes) -> bytes:
    result = subprocess.run(
        ["git", "show", f":{os.fsdecode(path)}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def is_forbidden_environment_file(path: str) -> bool:
    name = path.replace("\\", "/").rsplit("/", maxsplit=1)[-1]
    return name.startswith(".env") and name != ".env.example"


def contains_likely_secret(content: bytes) -> bool:
    text = content.decode("utf-8", errors="ignore")
    if any(pattern.search(text) for pattern in KNOWN_SECRET_PATTERNS):
        return True

    for match in CREDENTIAL_ASSIGNMENT.finditer(text):
        value = match.group(2).strip().rstrip(")]}")
        if not value or PLACEHOLDER_WORDS.search(value):
            continue
        if REFERENCE_VALUE.match(value):
            continue
        return True
    return False


def main() -> int:
    try:
        paths = staged_paths()
        failures: list[tuple[str, str]] = []
        for raw_path in paths:
            path = os.fsdecode(raw_path)
            if is_forbidden_environment_file(path):
                failures.append((path, "arquivos .env não podem ser commitados"))
                continue
            if contains_likely_secret(read_staged_file(raw_path)):
                failures.append((path, "possível chave, token ou credencial detectado"))

        if failures:
            print("Commit bloqueado por verificação de segurança:", file=sys.stderr)
            for path, reason in failures:
                print(f"  - {path}: {reason}", file=sys.stderr)
            print(
                "Remova os dados sensíveis do arquivo e do staging; nunca os imprima no terminal.",
                file=sys.stderr,
            )
            return 1

        print("Verificação de segurança passou: nenhum .env privado ou segredo detectado.")
        return 0
    except subprocess.CalledProcessError:
        print("Erro: não foi possível ler com segurança o conteúdo staged do Git.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
