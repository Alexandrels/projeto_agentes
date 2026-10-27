"""
Tela 5: Destino final - Marketplace ou Salvamento Local.
O usuario escolhe onde o video sera publicado ou salvo.
"""

import streamlit as st

from src.graph import graph
from langgraph.types import Command
from src.ui.components import (
    exibir_titulo_etapa,
    radio_destino,
    botao_avancar,
    exibir_erro,
    exibir_sucesso,
    exibir_info,
)


def render():
    """Renderiza a tela 5."""
    exibir_titulo_etapa(
        "Etapa 5 - Destino Final",
        "Escolha se deseja publicar o video em marketplace ou salvar localmente.",
    )

    estado = st.session_state.get("graph_state")
    if not estado:
        exibir_erro("Estado nao encontrado. Volte ao inicio.")
        return

    video_url = estado.get("video_url")
    if video_url:
        st.info(f"Video disponivel em: {video_url}")

    destino = radio_destino()

    if botao_avancar("destino", "Confirmar destino"):
        try:
            config = {
                "configurable": {
                    "thread_id": st.session_state.thread_id,
                }
            }

            # Envia a decisao de destino para o grafo
            escolha = "marketplace" if destino == "Publicar no marketplace" else "local"

            resumo = graph.invoke(
                Command(resume={"destino": escolha}),
                config,
            )

            st.session_state.graph_state = resumo

            if escolha == "marketplace":
                if resumo.get("marketplace_publicado"):
                    exibir_sucesso("Video publicado no marketplace com sucesso!")
                else:
                    exibir_erro("Nao foi possivel publicar no marketplace.")
            else:
                caminho = resumo.get("caminho_arquivo_local")
                pasta = resumo.get("nome_pasta_timestamp")
                if caminho:
                    exibir_sucesso(f"Video salvo com sucesso!")
                    st.markdown(f"**Pasta:** `{pasta}`")
                    st.markdown(f"**Arquivo:** `{caminho}`")
                else:
                    exibir_erro("Nao foi possivel salvar o video localmente.")

            st.divider()
            if st.button("Criar novo produto", type="primary"):
                # Limpa o estado e reinicia
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        except Exception as e:
            exibir_erro(f"Erro ao processar destino: {str(e)}")