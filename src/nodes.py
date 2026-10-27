"""
Agentes (nós) do grafo LangGraph.
Cada nó representa uma etapa do fluxo e inclui pontos de
interrupção para aprovação humana (human-in-the-loop).
"""

import os
import subprocess
import uuid
from datetime import datetime
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.types import interrupt, Command

from .config import LLMFactory, IMAGE_PROVIDER, VIDEO_PROVIDER, OUTPUT_FOLDER
from .state import ProductVideoState
from .media.validator import validar_video


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def gerar_nome_pasta_timestamp() -> str:
    """
    Gera nome de pasta baseado em data/hora com segundo e milissegundo.
    Formato: AAAA-MM-DD_HH-MM-SS-ms
    """
    agora = datetime.now()
    return agora.strftime("%Y-%m-%d_%H-%M-%S-%f")[:-3]  # milissegundos (3 dígitos)


def subprocess_gerar_video_teste(caminho_saida: str) -> bool:
    """
    Tenta gerar um vídeo de teste de 8 segundos com áudio usando FFmpeg.

    Retorna True se o vídeo foi gerado com sucesso, False caso contrário
    (FFmpeg não instalado ou falha na geração).
    """
    try:
        resultado = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                "-i", "testsrc=duration=8:size=640x480:rate=30",
                "-f", "lavfi",
                "-i", "sine=frequency=440:duration=8",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-shortest",
                caminho_saida,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return resultado.returncode == 0 and os.path.exists(caminho_saida)
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def solicitar_aprovacao_humana(mensagem: str, contexto: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interrompe a execução do grafo para aguardar aprovação humana.
    Retorna um Command com a decisão do humano ou levanta interrupção.

    No LangGraph moderno, usamos interrupt() para pausar e aguardar
    uma entrada externa (human-in-the-loop).
    """
    resposta = interrupt(
        {
            "mensagem": mensagem,
            "contexto": contexto,
            "aguardando_aprovacao": True,
        }
    )
    return resposta


# ---------------------------------------------------------------------------
# Etapa 1: Solicitação e Geração de Imagem
# ---------------------------------------------------------------------------

def node_solicitar_produto(state: ProductVideoState) -> ProductVideoState:
    """
    Nó inicial: recebe o nome do produto do usuário.
    Define a etapa atual e prepara o estado para geração de imagem.
    """
    print("\n[Etapa 1] Solicitação do produto")
    print("=" * 50)

    nome = state.get("produto_nome")
    if not nome:
        # Em produção, este valor viria de uma API/CLI. Aqui usamos valor do estado.
        raise ValueError("Nome do produto não informado no estado.")

    state["etapa_atual"] = "etapa_1_imagem"
    state["aprovacao_pendente"] = False
    state["erro"] = None

    print(f"Produto: {nome}")
    return state


def node_gerar_imagem(state: ProductVideoState) -> ProductVideoState:
    """
    Gera uma imagem de alta resolução do produto usando o provedor configurado.
    Depois interrompe para aprovação humana.
    """
    print("\n[Etapa 1] Gerando imagem de alta resolução...")
    print("=" * 50)

    produto_nome = state.get("produto_nome", "")
    produto_descricao = state.get("produto_descricao", "")

    # Monta prompt para geração de imagem
    prompt_imagem = (
        f"Imagem de alta resolução, qualidade profissional, produto: {produto_nome}. "
        f"Descrição: {produto_descricao}. "
        f"Fundo limpo, iluminação de estúdio, foco no produto, 4K, "
        f"fotografia comercial de e-commerce."
    )

    print(f"Prompt da imagem: {prompt_imagem[:200]}...")
    print(f"Provedor de imagem: {IMAGE_PROVIDER}")

    # Simulação de geração de imagem (substituir pela chamada real da API)
    # Exemplo: resposta = cliente_imagens.gerar(prompt_imagem)
    imagem_url = f"https://api.exemplo.com/imagens/{uuid.uuid4().hex[:8]}.png"
    state["imagem_url"] = imagem_url

    print(f"Imagem gerada: {imagem_url}")

    # --- HUMAN-IN-THE-LOOP: Aprovação da imagem ---
    decisao = solicitar_aprovacao_humana(
        mensagem="A imagem gerada está aprovada?",
        contexto={
            "etapa": "etapa_1_imagem",
            "imagem_url": imagem_url,
            "produto": produto_nome,
        },
    )

    # O interrupt retorna quando o humano responde
    aprovado = decisao.get("aprovado", False)
    feedback = decisao.get("feedback", None)

    state["imagem_aprovada"] = aprovado
    state["imagem_feedback"] = feedback

    if not aprovado:
        print(f"Imagem reprovada. Feedback: {feedback}")
        # Pode retornar para regeneração ou encerrar
        state["aprovacao_pendente"] = True
    else:
        print("Imagem aprovada!")
        state["aprovacao_pendente"] = False

    return state


# ---------------------------------------------------------------------------
# Etapa 2: Descrição do Produto
# ---------------------------------------------------------------------------

def node_processar_descricao(state: ProductVideoState) -> ProductVideoState:
    """
    Processa a descrição do produto (texto ou links) usando LLM
    para extrair características estruturadas.
    Depois interrompe para aprovação humana.
    """
    print("\n[Etapa 2] Processando descrição do produto...")
    print("=" * 50)

    produto_descricao = state.get("produto_descricao", "")
    produto_nome = state.get("produto_nome", "")

    # Usa LLM para extrair características
    llm = LLMFactory.create_llm()
    mensagens = [
        SystemMessage(
            content="Você é um especialista em copywriting para e-commerce. "
                    "Extraia as principais características do produto a partir "
                    "da descrição ou links fornecidos. Retorne apenas as "
                    "características principais em tópicos."
        ),
        HumanMessage(
            content=f"Produto: {produto_nome}\n"
                    f"Descrição/Links: {produto_descricao}"
        ),
    ]

    resposta = llm.invoke(mensagens)
    descricao_extraida = resposta.content if hasattr(resposta, "content") else str(resposta)

    state["descricao_extraida"] = descricao_extraida
    print(f"Descrição extraída: {descricao_extraida[:200]}...")

    # --- HUMAN-IN-THE-LOOP: Aprovação da descrição ---
    decisao = solicitar_aprovacao_humana(
        mensagem="A descrição extraída do produto está correta?",
        contexto={
            "etapa": "etapa_2_descricao",
            "descricao_extraida": descricao_extraida,
            "produto": produto_nome,
        },
    )

    aprovado = decisao.get("aprovado", False)
    feedback = decisao.get("feedback", None)

    state["descricao_aprovada"] = aprovado
    state["descricao_feedback"] = feedback

    if not aprovado:
        print(f"Descrição reprovada. Feedback: {feedback}")
        state["aprovacao_pendente"] = True
    else:
        print("Descrição aprovada!")
        state["aprovacao_pendente"] = False

    return state


# ---------------------------------------------------------------------------
# Etapa 3: Criação do Vídeo de 8 Segundos
# ---------------------------------------------------------------------------

def node_gerar_roteiro_video(state: ProductVideoState) -> ProductVideoState:
    """
    Gera o roteiro do vídeo de 8 segundos usando LLM,
    baseado na descrição aprovada e imagem do produto.
    """
    print("\n[Etapa 3] Gerando roteiro do vídeo (8 segundos)...")
    print("=" * 50)

    descricao = state.get("descricao_extraida", "")
    produto_nome = state.get("produto_nome", "")

    llm = LLMFactory.create_llm()
    mensagens = [
        SystemMessage(
            content="Você é um roteirista de vídeos curtos para redes sociais. "
                    "Crie um roteiro de exatamente 8 segundos para um vídeo "
                    "promocional de produto. Inclua narração, cenas e chamadas "
                    "para ação. Seja direto e impactante."
        ),
        HumanMessage(
            content=f"Produto: {produto_nome}\n"
                    f"Descrição: {descricao}"
        ),
    ]

    resposta = llm.invoke(mensagens)
    roteiro = resposta.content if hasattr(resposta, "content") else str(resposta)

    state["roteiro_video"] = roteiro
    print(f"Roteiro: {roteiro[:200]}...")

    return state


def node_gerar_video(state: ProductVideoState) -> ProductVideoState:
    """
    Gera o vídeo de 8 segundos usando o provedor de vídeo configurado.
    Executa validação FFmpeg (incluindo áudio obrigatório) antes da
    aprovação humana. Se a validação falhar, o fluxo é interrompido com erro.
    """
    print("\n[Etapa 3] Gerando vídeo de 8 segundos...")
    print("=" * 50)

    roteiro = state.get("roteiro_video", "")
    produto_nome = state.get("produto_nome", "")

    print(f"Provedor de vídeo: {VIDEO_PROVIDER}")
    print(f"Roteiro: {roteiro[:200]}...")

    # Simulação de geração de vídeo (substituir pela chamada real da API)
    video_url = f"https://api.exemplo.com/videos/{uuid.uuid4().hex[:8]}.mp4"
    state["video_url"] = video_url

    print(f"Vídeo gerado: {video_url}")

    # ------------------------------------------------------------------
    # Validação de vídeo com FFmpeg (antes da aprovação humana)
    # ------------------------------------------------------------------
    # Para simulação, cria um arquivo local temporário para validação.
    # Em produção, baixaria o vídeo de video_url para este caminho.
    caminho_video_local = os.path.join(
        OUTPUT_FOLDER, f"temp_{uuid.uuid4().hex[:8]}.mp4"
    )
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    try:
        # Tenta gerar um vídeo de teste com FFmpeg (8s, com áudio)
        # apenas se o FFmpeg estiver disponível no sistema.
        resultado_ffmpeg = subprocess_gerar_video_teste(caminho_video_local)
        if not resultado_ffmpeg:
            # FFmpeg não disponível ou falha ao gerar teste;
            # cria placeholder vazio para demonstração da validação.
            with open(caminho_video_local, "wb") as f:
                f.write(b"")

        resultado_validacao = validar_video(
            caminho_arquivo=caminho_video_local,
            duracao_esperada_segundos=8.0,
            tolerancia_segundos=0.5,
            audio_obrigatorio=True,
        )

        # Armazena metadados de validação no estado
        state["metadados"]["video_validacao"] = {
            "valido": resultado_validacao.valido,
            "duracao": resultado_validacao.duracao_segundos,
            "codec_video": resultado_validacao.codec_video,
            "codec_audio": resultado_validacao.codec_audio,
            "tem_audio": resultado_validacao.tem_audio,
            "checksum": resultado_validacao.checksum_sha256,
            "tamanho": resultado_validacao.tamanho_bytes,
            "erros": resultado_validacao.erros,
            "avisos": resultado_validacao.avisos,
        }

        if not resultado_validacao.valido:
            state["erro"] = (
                f"Vídeo inválido: {', '.join(resultado_validacao.erros)}"
            )
            state["video_aprovado"] = False
            # Remove arquivo temporário inválido
            if os.path.exists(caminho_video_local):
                os.remove(caminho_video_local)
            return state

        # Remove arquivo temporário após validação bem-sucedida
        if os.path.exists(caminho_video_local):
            os.remove(caminho_video_local)

    except Exception as exc:
        state["erro"] = f"Erro durante validação de vídeo: {str(exc)}"
        state["video_aprovado"] = False
        return state

    # --- HUMAN-IN-THE-LOOP: Aprovação do vídeo ---
    decisao = solicitar_aprovacao_humana(
        mensagem="O vídeo de 8 segundos está aprovado?",
        contexto={
            "etapa": "etapa_3_video",
            "video_url": video_url,
            "roteiro": roteiro,
            "produto": produto_nome,
            "validacao": state["metadados"].get("video_validacao", {}),
        },
    )

    aprovado = decisao.get("aprovado", False)
    feedback = decisao.get("feedback", None)

    state["video_aprovado"] = aprovado
    state["video_feedback"] = feedback

    if not aprovado:
        print(f"Vídeo reprovado. Feedback: {feedback}")
        state["aprovacao_pendente"] = True
    else:
        print("Vídeo aprovado!")
        state["aprovacao_pendente"] = False

    return state


# ---------------------------------------------------------------------------
# Etapa 4: Publicação ou Salvamento
# ---------------------------------------------------------------------------

def node_decidir_destino(state: ProductVideoState) -> ProductVideoState:
    """
    Pergunta ao humano se deseja publicar no marketplace ou salvar localmente.
    Interrompe para decisão humana.
    """
    print("\n[Etapa 4] Decidindo destino do vídeo...")
    print("=" * 50)

    decisao = solicitar_aprovacao_humana(
        mensagem="Deseja publicar o vídeo em marketplace ou salvar localmente?",
        contexto={
            "etapa": "etapa_4_destino",
            "video_url": state.get("video_url"),
            "produto": state.get("produto_nome"),
            "opcoes": ["marketplace", "local"],
        },
    )

    destino = decisao.get("destino", "local")
    state["destino"] = destino

    print(f"Destino escolhido: {destino}")
    return state


def node_publicar_marketplace(state: ProductVideoState) -> ProductVideoState:
    """
    Publica o vídeo no marketplace configurado.
    """
    print("\n[Etapa 4] Publicando no marketplace...")
    print("=" * 50)

    video_url = state.get("video_url", "")
    produto_nome = state.get("produto_nome", "")

    print(f"Vídeo: {video_url}")
    print(f"Produto: {produto_nome}")
    print(f"Marketplace API: {os.getenv('MARKETPLACE_API_URL', 'não configurado')}")

    # Simulação de publicação (substituir pela chamada real da API do marketplace)
    state["marketplace_publicado"] = True
    state["caminho_arquivo_local"] = None

    print("Vídeo publicado no marketplace com sucesso!")
    return state


def node_salvar_local(state: ProductVideoState) -> ProductVideoState:
    """
    Salva o vídeo em uma pasta local com nome baseado em
    data/hora (segundo e milissegundo).
    """
    print("\n[Etapa 4] Salvando vídeo localmente...")
    print("=" * 50)

    nome_pasta = gerar_nome_pasta_timestamp()
    pasta_completa = os.path.join(OUTPUT_FOLDER, nome_pasta)
    os.makedirs(pasta_completa, exist_ok=True)

    video_url = state.get("video_url", "")
    caminho_arquivo = os.path.join(pasta_completa, "video.mp4")

    # Simulação de download/salvamento (substituir por download real do vídeo)
    # Aqui apenas criamos um arquivo placeholder
    with open(caminho_arquivo, "w") as f:
        f.write(f"Placeholder do vídeo: {video_url}\n")

    state["caminho_arquivo_local"] = caminho_arquivo
    state["nome_pasta_timestamp"] = nome_pasta
    state["marketplace_publicado"] = False

    print(f"Vídeo salvo em: {caminho_arquivo}")
    print(f"Pasta: {nome_pasta}")
    return state


# ---------------------------------------------------------------------------
# Nó de erro
# ---------------------------------------------------------------------------

def node_erro(state: ProductVideoState) -> ProductVideoState:
    """Nó executado quando ocorre um erro no fluxo."""
    print(f"\n[ERRO] {state.get('erro', 'Erro desconhecido')}")
    return state