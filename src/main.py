"""
Ponto de entrada da aplicação.
Exemplo de execução do grafo LangGraph com human-in-the-loop.

Para usar:
    python main.py
"""

import json
from src.graph import graph
from src.state import ProductVideoState


def inicializar_estado(produto_nome: str, produto_descricao: str) -> ProductVideoState:
    """
    Cria o estado inicial do grafo com os dados informados pelo usuário.
    """
    return ProductVideoState(
        produto_nome=produto_nome,
        produto_descricao=produto_descricao,
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


def executar_fluxo(produto_nome: str, produto_descricao: str):
    """
    Executa o grafo completo com configuração de thread para checkpoint.
    O config inclui um thread_id para permitir interrupções e retomadas
    (human-in-the-loop).
    """
    estado_inicial = inicializar_estado(produto_nome, produto_descricao)

    config = {
        "configurable": {
            "thread_id": "produto_video_001",
        }
    }

    print("\n" + "=" * 60)
    print("INICIANDO FLUXO DE CRIAÇÃO DE VÍDEO DE PRODUTO")
    print("=" * 60)

    try:
        # O grafo será executado até a primeira interrupção (human-in-the-loop)
        # ou até completar se não houver interrupções configuradas nos nós.
        # No LangGraph com interrupt(), a execução pausa e aguarda
        # uma chamada externa com graph.invoke(Command(resume=...), config).
        resultado = graph.invoke(estado_inicial, config)

        print("\n" + "=" * 60)
        print("FLUXO CONCLUÍDO")
        print("=" * 60)
        print(f"Estado final: {json.dumps(resultado, indent=2, default=str, ensure_ascii=False)}")

    except Exception as e:
        print(f"\nErro durante execução: {e}")


def retomar_apos_aprovacao(
    thread_id: str,
    aprovado: bool,
    feedback: str = None,
    destino: str = None,
):
    """
    Retoma a execução do grafo após aprovação humana.
    Útil quando o grafo foi interrompido por interrupt().

    Exemplo de uso após o usuário aprovar a imagem:
        retomar_apos_aprovacao("produto_video_001", aprovado=True)
    """
    config = {"configurable": {"thread_id": thread_id}}

    resume_data = {}
    if aprovado is not None:
        resume_data["aprovado"] = aprovado
    if feedback is not None:
        resume_data["feedback"] = feedback
    if destino is not None:
        resume_data["destino"] = destino

    comando = Command(resume=resume_data) if resume_data else None

    try:
        if comando:
            resultado = graph.invoke(comando, config)
        else:
            resultado = graph.invoke(None, config)

        print("\nFluxo retomado com sucesso.")
        print(json.dumps(resultado, indent=2, default=str, ensure_ascii=False))
        return resultado

    except Exception as e:
        print(f"Erro ao retomar fluxo: {e}")
        return None


if __name__ == "__main__":
    # Exemplo de execução com dados de produto
    NOME_PRODUTO = "Smartphone X100"
    DESCRICAO_PRODUTO = (
        "Smartphone com tela de 6.7 polegadas, câmera de 108MP, "
        "bateria de 5000mAh, processador octa-core, 256GB de armazenamento. "
        "Links: https://exemplo.com/produto/x100"
    )

    executar_fluxo(NOME_PRODUTO, DESCRICAO_PRODUTO)