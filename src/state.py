"""
Estado compartilhado entre os agentes do grafo LangGraph.
Define todos os campos que trafegam entre as etapas do fluxo.
"""

from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict


class ProductVideoState(TypedDict):
    """
    Estado compartilhado por todos os nós do grafo.
    Cada campo representa uma informação que é atualizada
    conforme o fluxo avança pelas etapas.
    """

    # Etapa 1: Solicitação e imagem
    produto_nome: Optional[str]          # Nome do produto informado pelo usuário
    produto_descricao: Optional[str]     # Descrição ou links sobre o produto
    imagem_url: Optional[str]            # URL da imagem gerada
    imagem_aprovada: bool                # Flag de aprovação humana da imagem
    imagem_feedback: Optional[str]       # Feedback do humano sobre a imagem

    # Etapa 2: Validação da descrição
    descricao_extraida: Optional[str]    # Descrição estruturada extraída pelo LLM
    descricao_aprovada: bool             # Flag de aprovação humana da descrição
    descricao_feedback: Optional[str]    # Feedback do humano sobre a descrição

    # Etapa 3: Vídeo de 8 segundos
    roteiro_video: Optional[str]         # Roteiro gerado pelo LLM para o vídeo
    video_url: Optional[str]             # URL do vídeo gerado
    video_aprovado: bool                 # Flag de aprovação humana do vídeo
    video_feedback: Optional[str]        # Feedback do humano sobre o vídeo
    video_validacao: Optional[Dict[str, Any]]  # Resultado da validação FFmpeg

    # Etapa 4: Publicação ou salvamento
    destino: Optional[str]               # 'marketplace' ou 'local'
    marketplace_publicado: bool          # Flag de publicação no marketplace
    caminho_arquivo_local: Optional[str] # Caminho do arquivo salvo localmente
    nome_pasta_timestamp: Optional[str]  # Nome da pasta com timestamp (AAAA-MM-DD_HH-MM-SS-ms)

    # Identificação e auditoria
    job_id: Optional[str]                # Identificador único do trabalho
    thread_id: Optional[str]             # Identificador da thread do LangGraph
    criado_em: Optional[str]             # Timestamp de criação (ISO 8601)
    atualizado_em: Optional[str]         # Timestamp da última atualização (ISO 8601)
    versao: int                          # Versão do estado (incrementa a cada mudança)

    # Controle de fluxo e aprovações
    etapa_atual: str                     # Etapa corrente do grafo
    aprovacao_pendente: bool             # Indica se está aguardando aprovação humana
    erro: Optional[str]                  # Mensagem de erro se algo falhar
    metadados: Dict[str, Any]            # Metadados adicionais (timestamps, IDs, etc.)