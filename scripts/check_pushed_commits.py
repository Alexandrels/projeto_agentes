#!/usr/bin/env python3
"""Scan new commits being pushed for environment files and likely credentials."""

from __future__ import annotations

import os
import subprocess
import sys

from check_staged_secrets import contains_likely_secret, is_forbidden_environment_file

ZERO_SHA_PREFIX = "0000000000000000000000000000000000000000"


def git_output(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def commits_to_push(local_sha: str, remote_sha: str) -> list[str]:
    args = ["rev-list", local_sha]
    if not remote_sha.startswith(ZERO_SHA_PREFIX):
        args.append(f"^{remote_sha}")
    output = git_output(*args)
    return output.decode("ascii").splitlines()


def inspect_commit(commit: str, scanned_blobs: set[str]) -> list[tuple[str, str]]:
    entries = git_output("ls-tree", "-rz", "--full-tree", commit).split(b"\0")
    failures: list[tuple[str, str]] = []
    for entry in entries:
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", maxsplit=1)
        mode, object_type, object_id = metadata.decode("ascii").split()
        if object_type != "blob":
            continue

        path = os.fsdecode(raw_path)
        if is_forbidden_environment_file(path):
            failures.append((path, "arquivos .env não podem ser enviados"))
            continue

        if object_id in scanned_blobs:
            continue
        scanned_blobs.add(object_id)

        content = git_output("cat-file", "blob", object_id)
        if contains_likely_secret(content):
            failures.append((path, "possível chave, token ou credencial detectado"))
    return failures


def main() -> int:
    try:
        updates = [line.split() for line in sys.stdin.buffer.read().splitlines() if line.strip()]
        scanned_blobs: set[str] = set()
        failures: list[tuple[str, str, str]] = []

        for update in updates:
            if len(update) != 4:
                print("Push bloqueado: formato de atualização Git inválido.", file=sys.stderr)
                return 2
            _, raw_local_sha, _, raw_remote_sha = update
            local_sha = raw_local_sha.decode("ascii")
            remote_sha = raw_remote_sha.decode("ascii")
            if local_sha.startswith(ZERO_SHA_PREFIX):
                continue

            for commit in commits_to_push(local_sha, remote_sha):
                for path, reason in inspect_commit(commit, scanned_blobs):
                    failures.append((commit[:12], path, reason))

        if failures:
            print("Push bloqueado por verificação de segurança:", file=sys.stderr)
            for commit, path, reason in failures:
                print(f"  - {commit} ({path}): {reason}", file=sys.stderr)
            print(
                "Remova os dados sensíveis do histórico e revogue qualquer chave exposta.",
                file=sys.stderr,
            )
            return 1

        print("Verificação de segurança passou: commits a enviar sem .env privado ou segredos.")
        return 0
    except (subprocess.CalledProcessError, UnicodeDecodeError, ValueError):
        print("Erro: não foi possível verificar com segurança os commits a enviar.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
