"""
Tela 1: Nome do produto.
Recebe o nome do produto e inicializa o estado do grafo.
"""

import streamlit as st
import uuid

from src.graph import graph
from src.state import ProductVideoState
from src.ui.components import (
    exibir_titulo_etapa,
    campo_nome_produto,
    botao_avancar,
    exibir_erro,
    exibir_sucesso,
)


def inicializar_estado() -> ProductVideoState:
    """Cria o estado inicial vazio do grafo."""
    return ProductVideoState(
        produto_nome=None,
        produto_descricao=None,
        imagem_url=None,
        imagem_aprovada=False,
        imagem_feedback=None,
        descricao_extraida=None,
        descricao_aprovada=False,
        descricao_feedback=None,
        roteiro_video=None,
        video_url=None,
        video_aprovado=False,
        video_feedback=None,
        destino=None,
        marketplace_publicado=False,
        caminho_arquivo_local=None,
        nome_pasta_timestamp=None,
        etapa_atual="inicial",
        aprovacao_pendente=False,
        erro=None,
        metadados={},
    )


def render():
    """Renderiza a tela 1."""
    exibir_titulo_etapa(
        "Etapa 1 - Nome do Produto",
        "Informe o nome do produto para iniciar a criacao de imagem e video.",
    )

    nome = campo_nome_produto()

    if botao_avancar("produto", "Iniciar fluxo"):
        if not nome or not nome.strip():
            exibir_erro("Informe o nome do produto antes de avancar.")
            return

        # Inicializa estado do grafo
        estado_inicial = inicializar_estado()
        estado_inicial["produto_nome"] = nome.strip()

        # Gera thread_id unico para esta sessao
        thread_id = f"produto_{uuid.uuid4().hex[:8]}"

        # Salva no session_state
        st.session_state.graph_state = estado_inicial
        st.session_state.thread_id = thread_id
        st.session_state.current_page = "descricao"
        st.session_state.awaiting_approval = False

        exibir_sucesso(f"Produto '{nome}' registrado. Avancando para descricao...")
        st.rerun()