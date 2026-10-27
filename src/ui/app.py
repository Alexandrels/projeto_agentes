"""
Ponto de entrada da interface Streamlit.
Router de telas para o fluxo de criacao de video de produtos com human-in-the-loop.
"""

import streamlit as st

from src.ui.pages import produto, descricao, imagem, video, destino
from src.ui.components import exibir_erro


def inicializar_session_state():
    """Inicializa variaveis de sessao do Streamlit."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "produto"
    if "graph_state" not in st.session_state:
        st.session_state.graph_state = None
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    if "awaiting_approval" not in st.session_state:
        st.session_state.awaiting_approval = False


def router():
    """Roteia para a pagina correta baseado no current_page."""
    pagina = st.session_state.current_page

    if pagina == "produto":
        produto.render()
    elif pagina == "descricao":
        descricao.render()
    elif pagina == "imagem":
        imagem.render()
    elif pagina == "video":
        video.render()
    elif pagina == "destino":
        destino.render()
    else:
        exibir_erro(f"Pagina nao encontrada: {pagina}")
        st.session_state.current_page = "produto"


def barra_lateral():
    """Exibe barra lateral com status do fluxo."""
    with st.sidebar:
        st.title("Fluxo de Criacao")
        st.divider()

        etapas = [
            ("produto", "Nome do Produto"),
            ("descricao", "Descricao/Links"),
            ("imagem", "Aprovacao da Imagem"),
            ("video", "Aprovacao do Video"),
            ("destino", "Publicacao/Salvamento"),
        ]

        pagina_atual = st.session_state.get("current_page", "produto")

        for chave, nome in etapas:
            if chave == pagina_atual:
                st.markdown(f"**>>> {nome}** (atual)")
            else:
                st.markdown(f"- {nome}")

        st.divider()

        estado = st.session_state.get("graph_state")
        if estado:
            st.markdown("### Estado atual")
            st.markdown(f"- Produto: {estado.get('produto_nome', '-')}")
            st.markdown(f"- Imagem aprovada: {estado.get('imagem_aprovada', False)}")
            st.markdown(f"- Descricao aprovada: {estado.get('descricao_aprovada', False)}")
            st.markdown(f"- Video aprovado: {estado.get('video_aprovado', False)}")
            st.markdown(f"- Destino: {estado.get('destino', '-')}")

        st.divider()
        if st.button("Reiniciar fluxo", type="secondary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


def main():
    """Funcao principal da aplicacao."""
    st.set_page_config(
        page_title="Criador de Video de Produto",
        page_icon=":video_camera:",
        layout="wide",
    )

    inicializar_session_state()

    st.title(":video_camera: Criador de Video de Produto")
    st.markdown(
        "Sistema de criacao de imagem e video de produtos com "
        "aprovacao humana em cada etapa."
    )
    st.divider()

    barra_lateral()

    try:
        router()
    except Exception as e:
        exibir_erro(f"Erro na aplicacao: {str(e)}")


if __name__ == "__main__":
    main()