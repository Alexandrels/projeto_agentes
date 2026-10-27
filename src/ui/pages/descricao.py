"""
Tela 2: Descricao ou links do produto.
Recebe a descricao/links e avanca para a etapa de imagem.
"""

import streamlit as st

from src.graph import graph
from src.ui.components import (
    exibir_titulo_etapa,
    campo_descricao_produto,
    botao_avancar,
    exibir_erro,
    exibir_sucesso,
)


def render():
    """Renderiza a tela 2."""
    exibir_titulo_etapa(
        "Etapa 2 - Descricao ou Links",
        "Informe a descricao do produto ou links que o descrevam.",
    )

    # Recupera nome do produto do estado
    estado = st.session_state.get("graph_state")
    nome_produto = estado.get("produto_nome") if estado else ""
    st.info(f"Produto: {nome_produto}")

    descricao = campo_descricao_produto()

    if botao_avancar("descricao", "Gerar imagem"):
        if not descricao or not descricao.strip():
            exibir_erro("Informe a descricao ou links antes de avancar.")
            return

        # Atualiza estado
        estado["produto_descricao"] = descricao.strip()
        estado["etapa_atual"] = "etapa_1_imagem"

        try:
            # Executa o gravo ate a primeira interrupcao (apos gerar imagem)
            config = {
                "configurable": {
                    "thread_id": st.session_state.thread_id,
                }
            }

            resultado = graph.invoke(estado, config)

            # Atualiza estado com o resultado
            st.session_state.graph_state = resultado

            # Verifica se esta aguardando aprovacao (interrupcao)
            if resultado.get("aprovacao_pendente") or resultado.get("imagem_url"):
                st.session_state.current_page = "imagem"
                st.session_state.awaiting_approval = True
                exibir_sucesso("Imagem gerada! Revise na proxima tela.")
                st.rerun()
            else:
                exibir_erro("Nao foi possivel gerar a imagem. Tente novamente.")

        except Exception as e:
            exibir_erro(f"Erro ao executar o fluxo: {str(e)}")