"""
Validação de arquivos de vídeo usando FFmpeg / ffprobe.

Regras de validação:
- Duração próxima do esperado (padrão: 8 segundos)
- Presença de stream de vídeo
- Áudio obrigatório (configurável)
- Código de vídeo e container identificados
- Arquivo não vazio e não corrompido
"""

import hashlib
import json
import os
import subprocess
from typing import Any, Optional

from dataclasses import dataclass, field


@dataclass
class VideoValidationResult:
    """Resultado da validação de um arquivo de vídeo."""

    valido: bool
    duracao_segundos: Optional[float] = None
    largura: Optional[int] = None
    altura: Optional[int] = None
    codec_video: Optional[str] = None
    codec_audio: Optional[str] = None
    formato_container: Optional[str] = None
    tem_audio: bool = False
    tamanho_bytes: Optional[int] = None
    checksum_sha256: Optional[str] = None
    erros: list = field(default_factory=list)
    avisos: list = field(default_factory=list)


def calcular_checksum(caminho_arquivo: str) -> str:
    """Calcula o hash SHA-256 de um arquivo para verificação de integridade."""
    sha256 = hashlib.sha256()
    with open(caminho_arquivo, "rb") as f:
        for bloco in iter(lambda: f.read(8192), b""):
            sha256.update(bloco)
    return sha256.hexdigest()


def obter_informacoes_video(caminho_arquivo: str) -> dict:
    """
    Extrai metadados de um arquivo de vídeo usando ffprobe.

    Retorna dicionário com chaves 'format' e 'streams'.
    Levanta RuntimeError se o ffprobe falhar.
    """
    comando = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        caminho_arquivo,
    ]
    resultado = subprocess.run(
        comando, capture_output=True, text=True, timeout=30
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"ffprobe falhou: {resultado.stderr.strip()}")
    return json.loads(resultado.stdout)


def validar_video(
    caminho_arquivo: str,
    duracao_esperada_segundos: float = 8.0,
    tolerancia_segundos: float = 0.5,
    largura_esperada: Optional[int] = None,
    altura_esperada: Optional[int] = None,
    audio_obrigatorio: bool = True,
) -> VideoValidationResult:
    """
    Valida um arquivo de vídeo contra os requisitos definidos.

    Parâmetros:
        caminho_arquivo: Caminho para o arquivo de vídeo.
        duracao_esperada_segundos: Duração alvo em segundos (padrão 8.0).
        tolerancia_segundos: Tolerância de variação da duração (padrão 0.5s).
        largura_esperada: Largura esperada em pixels (opcional).
        altura_esperada: Altura esperada em pixels (opcional).
        audio_obrigatório: Se True, exige presença de stream de áudio.

    Retorna:
        VideoValidationResult com o resultado da validação.
    """
    erros: list = []
    avisos: list = []

    if not os.path.exists(caminho_arquivo):
        return VideoValidationResult(
            valido=False,
            erros=["Arquivo não encontrado"],
        )

    tamanho_bytes = os.path.getsize(caminho_arquivo)
    checksum = calcular_checksum(caminho_arquivo)

    try:
        info = obter_informacoes_video(caminho_arquivo)
    except Exception as exc:
        return VideoValidationResult(
            valido=False,
            tamanho_bytes=tamanho_bytes,
            checksum_sha256=checksum,
            erros=[f"Erro ao ler metadados com ffprobe: {str(exc)}"],
        )

    formato = info.get("format", {})
    formato_container = formato.get("format_name")
    duracao_str = formato.get("duration")
    duracao_segundos = float(duracao_str) if duracao_str else None

    streams = info.get("streams", [])
    stream_video = next(
        (s for s in streams if s.get("codec_type") == "video"), None
    )
    stream_audio = next(
        (s for s in streams if s.get("codec_type") == "audio"), None
    )

    codec_video = stream_video.get("codec_name") if stream_video else None
    codec_audio = stream_audio.get("codec_name") if stream_audio else None
    largura = stream_video.get("width") if stream_video else None
    altura = stream_video.get("height") if stream_video else None
    tem_audio = stream_audio is not None

    # --- Validações ---

    if not stream_video:
        erros.append("Nenhum stream de vídeo encontrado no arquivo.")

    if duracao_segundos is None:
        erros.append("Duração do vídeo não pôde ser determinada.")
    else:
        diferenca = abs(duracao_segundos - duracao_esperada_segundos)
        if diferenca > tolerancia_segundos:
            erros.append(
                f"Duração {duracao_segundos:.2f}s difere do esperado "
                f"{duracao_esperada_segundos}s por mais de {tolerancia_segundos}s."
            )
        elif diferenca > 0:
            avisos.append(
                f"Duração {duracao_segundos:.2f}s "
                f"(esperado {duracao_esperada_segundos}s)."
            )

    if audio_obrigatorio and not tem_audio:
        erros.append(
            "Áudio é obrigatório. Nenhum stream de áudio encontrado no vídeo."
        )

    if largura_esperada is not None and largura != largura_esperada:
        erros.append(
            f"Largura {largura} diferente da esperada {largura_esperada}."
        )

    if altura_esperada is not None and altura != altura_esperada:
        erros.append(
            f"Altura {altura} diferente da esperada {altura_esperada}."
        )

    if not codec_video:
        erros.append("Codec de vídeo não identificado.")

    if tamanho_bytes == 0:
        erros.append("Arquivo vazio (0 bytes).")

    return VideoValidationResult(
        valido=len(erros) == 0,
        duracao_segundos=duracao_segundos,
        largura=largura,
        altura=altura,
        codec_video=codec_video,
        codec_audio=codec_audio,
        formato_container=formato_container,
        tem_audio=tem_audio,
        tamanho_bytes=tamanho_bytes,
        checksum_sha256=checksum,
        erros=erros,
        avisos=avisos,
    )