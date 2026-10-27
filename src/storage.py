"""
Configuração de persistência para LangGraph.

Substitui MemorySaver (memória volátil) por SqliteSaver,
permitindo retomada de execuções após interrupção ou reinício do processo.
"""

import os
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver


DB_PATH = os.getenv("LANGGRAPH_DB_PATH", "./data/checkpoints.sqlite")


def get_checkpointer():
    """
    Retorna uma instância de SqliteSaver configurada.

    Cria o diretório pai do banco de dados se não existir.
    O caminho do banco pode ser sobrescrito via variável de ambiente
    LANGGRAPH_DB_PATH.
    """
    diretorio = os.path.dirname(DB_PATH)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    return SqliteSaver(conn)