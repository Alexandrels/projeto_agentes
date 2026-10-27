"""
Tela 3: Aprovacao da imagem gerada.
Exibe a imagem e permite aprovar ou reprovar com feedback.
"""

import streamlit as st

from src.graph import graph
from langgraph.types import Command
from src.ui.components import (
    exibir_titulo_etapa,
    exibir_midia,
    botoes_aprovacao,
    exibir_erro,
    exibir_sucesso,
    exibir_info,
)


def render():
    """Renderiza a tela 3."""
    exibir_titulo_etapa(
        "Etapa 3 - Aprovacao da Imagem",
        "Revise a imagem gerada e aprove ou solicite alteracoes.",
    )

    estado = st.session_state.get("graph_state")
    if not estado:
        exibir_erro("Estado nao encontrado. Volte ao inicio.")
        return

    imagem_url = estado.get("imagem_url")
    feedback_anterior = estado.get("imagem_feedback")

    if feedback_anterior:
        exibir_info(f"Feedback anterior: {feedback_anterior}")

    exibir_midia(
        url=imagem_url,
        legenda="Imagem gerada para o produto",
        tipo="imagem",
    )

    if not imagem_url:
        exibir_info("A imagem ainda nao foi gerada. Clique em 'Gerar imagem' na tela anterior.")
        return

    st.divider()
    st.markdown("### Deseja aprovar esta imagem?")

    resultado = botoes_aprovacao("imagem", "Informe o que gostaria de alterar na imagem:")

    if resultado["aprovado"] is True:
        # Retoma o grafo com aprovacao
        try:
            config = {
                "configurable": {
                    "thread_id": st.session_state.thread_id,
                }
            }

            resumo = graph.invoke(
                Command(resume={"aprovado": True}),
                config,
            )

            st.session_state.graph_state = resumo

            if resumo.get("descricao_aprovada") is not None or resumo.get("descricao_extraida"):
                st.session_state.current_page = "video"
                st.session_state.awaiting_approval = True
                exibir_sucesso("Imagem aprovada! Processando descricao...")
                st.rerun()
            else:
                st.session_state.current_page = "video"
                st.rerun()

        except Exception as e:
            exibir_erro(f"Erro ao aprovar imagem: {str(e)}")

    elif resultado["aprovado"] is False and resultado["feedback"]:
        # Retoma o grafo com reprovacao e feedback
        try:
            config = {
                "configurable": {
                    "thread_id": st.session_state.thread_id,
                }
            }

            resumo = graph.invoke(
                Command(resume={"aprovado": False, "feedback": resultado["feedback"]}),
                config,
            )

            st.session_state.graph_state = resumo
            exibir_sucesso("Feedback enviado. Imagem sera regenerada.")
            st.rerun()

        except Exception as e:
            exibir_erro(f"Erro ao enviar feedback: {str(e)}")