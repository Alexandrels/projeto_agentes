"""
Tela 4: Aprovacao do video de 8 segundos.
Exibe o video (ou roteiro) e permite aprovar ou reprovar com feedback.
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
    """Renderiza a tela 4."""
    exibir_titulo_etapa(
        "Etapa 4 - Aprovacao do Video (8 segundos)",
        "Revise o video gerado e aprove ou solicite alteracoes.",
    )

    estado = st.session_state.get("graph_state")
    if not estado:
        exibir_erro("Estado nao encontrado. Volte ao inicio.")
        return

    video_url = estado.get("video_url")
    roteiro = estado.get("roteiro_video")
    feedback_anterior = estado.get("video_feedback")

    if feedback_anterior:
        exibir_info(f"Feedback anterior: {feedback_anterior}")

    if roteiro:
        st.markdown("### Roteiro do Video")
        st.text_area("Roteiro", value=roteiro, height=200, disabled=True, key="roteiro_exibicao")

    exibir_midia(
        url=video_url,
        legenda="Video gerado de 8 segundos",
        tipo="video",
    )

    if not video_url:
        exibir_info("O video ainda nao foi gerado. Aguarde o processamento anterior.")
        return

    st.divider()
    st.markdown("### Deseja aprovar este video?")

    resultado = botoes_aprovacao("video", "Informe o que gostaria de alterar no video:")

    if resultado["aprovado"] is True:
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
            st.session_state.current_page = "destino"
            st.session_state.awaiting_approval = False
            exibir_sucesso("Video aprovado! Escolha o destino na proxima tela.")
            st.rerun()

        except Exception as e:
            exibir_erro(f"Erro ao aprovar video: {str(e)}")

    elif resultado["aprovado"] is False and resultado["feedback"]:
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
            exibir_sucesso("Feedback enviado. Video sera regenerado.")
            st.rerun()

        except Exception as e:
            exibir_erro(f"Erro ao enviar feedback: {str(e)}")