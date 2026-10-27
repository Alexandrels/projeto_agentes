"""
Componentes reutilizaveis da interface Streamlit.
"""

import streamlit as st


def exibir_titulo_etapa(etapa: str, descricao: str):
    """Exibe o cabecalho de uma etapa do fluxo."""
    st.markdown(f"## {etapa}")
    st.markdown(f"**{descricao}**")
    st.divider()


def exibir_midia(url: str, legenda: str, tipo: str = "imagem"):
    """Exibe imagem ou video com legenda."""
    if url:
        if tipo == "imagem":
            st.image(url, caption=legenda, use_column_width=True)
        elif tipo == "video":
            st.video(url)
            st.caption(legenda)
    else:
        st.info(f"{legenda} nao disponível.")


def botoes_aprovacao(chave: str, feedback_label: str = "Feedback (opcional)"):
    """
    Exibe botoes de aprovacao e reprovacao com campo de feedback.
    Retorna dicionario com: aprovado (bool ou None), feedback (str ou None).
    """
    resultado = {"aprovado": None, "feedback": None}

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Aprovar", key=f"aprovar_{chave}", type="primary"):
            resultado["aprovado"] = True

    with col2:
        if st.button("Reprovar", key=f"reprovar_{chave}"):
            resultado["aprovado"] = False

    if st.session_state.get(f"reprovado_{chave}", False):
        feedback = st.text_area(
            feedback_label,
            key=f"feedback_{chave}",
            height=100,
        )
        if st.button("Enviar feedback", key=f"enviar_feedback_{chave}"):
            resultado["aprovado"] = False
            resultado["feedback"] = feedback
            st.session_state[f"reprovado_{chave}"] = False
    elif resultado["aprovado"] is False:
        st.session_state[f"reprovado_{chave}"] = True
        st.rerun()

    return resultado


def botao_avancar(chave: str, label: str = "Avancar"):
    """Botao de avancar para proxima tela."""
    return st.button(label, key=f"avancar_{chave}", type="primary")


def exibir_erro(mensagem: str):
    """Exibe mensagem de erro."""
    st.error(mensagem)


def exibir_sucesso(mensagem: str):
    """Exibe mensagem de sucesso."""
    st.success(mensagem)


def exibir_info(mensagem: str):
    """Exibe mensagem informativa."""
    st.info(mensagem)


def campo_nome_produto() -> str:
    """Campo de entrada para nome do produto."""
    return st.text_input(
        "Nome do produto",
        placeholder="Ex: Smartphone X100",
        key="input_nome_produto",
    )


def campo_descricao_produto() -> str:
    """Campo de entrada para descricao ou links do produto."""
    return st.text_area(
        "Descricao do produto ou links",
        placeholder="Cole aqui a descricao ou links separados por virgula...",
        height=200,
        key="input_descricao_produto",
    )


def radio_destino() -> str:
    """Radio para escolher entre marketplace e salvamento local."""
    return st.radio(
        "Como deseja prosseguir com o video?",
        options=["Publicar no marketplace", "Salvar localmente"],
        key="radio_destino",
    )