"""
Construção do grafo LangGraph com orquestração dos agentes.
Inclui interrupções para human-in-the-loop em cada etapa crítica.
"""

from typing import Literal

from langgraph.graph import StateGraph, END

from .storage import get_checkpointer

from .state import ProductVideoState
from .nodes import (
    node_solicitar_produto,
    node_gerar_imagem,
    node_processar_descricao,
    node_gerar_roteiro_video,
    node_gerar_video,
    node_decidir_destino,
    node_publicar_marketplace,
    node_salvar_local,
    node_erro,
)


# ---------------------------------------------------------------------------
# Funções de roteamento (condicionais)
# ---------------------------------------------------------------------------

def depois_gerar_imagem(state: ProductVideoState) -> Literal["aprovado", "reprovado", "erro"]:
    """
    Decide o próximo nó após geração de imagem com base na aprovação humana.
    """
    if state.get("erro"):
        return "erro"
    if state.get("imagem_aprovada"):
        return "aprovado"
    return "reprovado"


def depois_processar_descricao(state: ProductVideoState) -> Literal["aprovado", "reprovado", "erro"]:
    """
    Decide o próximo nó após processamento da descrição.
    """
    if state.get("erro"):
        return "erro"
    if state.get("descricao_aprovada"):
        return "aprovado"
    return "reprovado"


def depois_gerar_video(state: ProductVideoState) -> Literal["aprovado", "reprovado", "erro"]:
    """
    Decide o próximo nó após geração de vídeo com base na aprovação humana.
    """
    if state.get("erro"):
        return "erro"
    if state.get("video_aprovado"):
        return "aprovado"
    return "reprovado"


def depois_decidir_destino(state: ProductVideoState) -> Literal["marketplace", "local", "erro"]:
    """
    Decide se publica no marketplace ou salva localmente.
    """
    if state.get("erro"):
        return "erro"
    destino = state.get("destino")
    if destino == "marketplace":
        return "marketplace"
    return "local"


# ---------------------------------------------------------------------------
# Construção do grafo
# ---------------------------------------------------------------------------

def build_graph():
    """
    Constrói e retorna o grafo LangGraph compilado com checkpointer
    para suporte a human-in-the-loop (interrupções e retomadas).
    """

    workflow = StateGraph(ProductVideoState)

    # --- Nós ---
    workflow.add_node("solicitar_produto", node_solicitar_produto)
    workflow.add_node("gerar_imagem", node_gerar_imagem)
    workflow.add_node("processar_descricao", node_processar_descricao)
    workflow.add_node("gerar_roteiro_video", node_gerar_roteiro_video)
    workflow.add_node("gerar_video", node_gerar_video)
    workflow.add_node("decidir_destino", node_decidir_destino)
    workflow.add_node("publicar_marketplace", node_publicar_marketplace)
    workflow.add_node("salvar_local", node_salvar_local)
    workflow.add_node("erro", node_erro)

    # --- Arestas de entrada ---
    workflow.set_entry_point("solicitar_produto")

    # Fluxo principal
    workflow.add_edge("solicitar_produto", "gerar_imagem")

    # Após imagem: condicional baseado em aprovação humana
    workflow.add_conditional_edges(
        "gerar_imagem",
        depois_gerar_imagem,
        {
            "aprovado": "processar_descricao",
            "reprovado": "gerar_imagem",  # Regenera imagem com feedback
            "erro": "erro",
        },
    )

    # Após descrição: condicional baseado em aprovação humana
    workflow.add_conditional_edges(
        "processar_descricao",
        depois_processar_descricao,
        {
            "aprovado": "gerar_roteiro_video",
            "reprovado": "processar_descricao",  # Reprocessa com feedback
            "erro": "erro",
        },
    )

    # Fluxo de vídeo
    workflow.add_edge("gerar_roteiro_video", "gerar_video")

    # Após vídeo: condicional baseado em aprovação humana
    workflow.add_conditional_edges(
        "gerar_video",
        depois_gerar_video,
        {
            "aprovado": "decidir_destino",
            "reprovado": "gerar_roteiro_video",  # Regenera roteiro/vídeo com feedback
            "erro": "erro",
        },
    )

    # Após destino: condicional baseado na escolha humana
    workflow.add_conditional_edges(
        "decidir_destino",
        depois_decidir_destino,
        {
            "marketplace": "publicar_marketplace",
            "local": "salvar_local",
            "erro": "erro",
        },
    )

    # Finais
    workflow.add_edge("publicar_marketplace", END)
    workflow.add_edge("salvar_local", END)
    workflow.add_edge("erro", END)

    # Checkpointer persistente (SQLite) para suporte a human-in-the-loop
    # e retomada de execuções após interrupção ou reinício do processo.
    checkpointer = get_checkpointer()

    graph = workflow.compile(checkpointer=checkpointer)
    return graph


# Instância pronta para uso
graph = build_graph()