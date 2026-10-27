"""
Factory de modelos LLM trocáveis.
Permite alternar entre OpenAI, Anthropic, Google e Ollama
via variável de ambiente LLM_PROVIDER sem reescrever código.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

load_dotenv()


class LLMFactory:
    """Factory para criação de instâncias de LLM por provedor."""

    @staticmethod
    def create_llm(
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """
        Cria uma instância de LLM baseado no provedor especificado.

        Args:
            provider: Nome do provedor (openai, anthropic, google, ollama).
                      Se None, usa LLM_PROVIDER do .env.
            model: Nome do modelo. Se None, usa LLM_MODEL do .env.
            temperature: Temperatura para geração. Se None, usa LLM_TEMPERATURE do .env.

        Returns:
            Instância de LangChain ChatModel configurada.

        Raises:
            ValueError: Se o provedor não for suportado ou chave de API não estiver configurada.
        """
        provider = provider or os.getenv("LLM_PROVIDER", "openai")
        model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        temperature = temperature if temperature is not None else float(
            os.getenv("LLM_TEMPERATURE", "0.7")
        )

        provider = provider.lower()

        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY não configurada no .env")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=api_key,
            )

        elif provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY não configurada no .env")
            return ChatAnthropic(
                model=model,
                temperature=temperature,
                anthropic_api_key=api_key,
            )

        elif provider == "google":
            # Placeholder para integração futura com Google (Gemini via langchain-google-genai)
            raise NotImplementedError(
                "Provedor 'google' ainda não implementado. "
                "Instale langchain-google-genai e adicione a integração aqui."
            )

        elif provider == "ollama":
            # Placeholder para Ollama (modelos locais)
            raise NotImplementedError(
                "Provedor 'ollama' ainda não implementado. "
                "Use ChatOllama do langchain_community quando necessário."
            )

        else:
            raise ValueError(
                f"Provedor de LLM não suportado: {provider}. "
                "Use: openai, anthropic, google ou ollama."
            )


# Configurações de provedores de mídia
IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "dalle3")
VIDEO_PROVIDER = os.getenv("VIDEO_PROVIDER", "runway")

# Configurações de marketplace
MARKETPLACE_API_URL = os.getenv("MARKETPLACE_API_URL", "")
MARKETPLACE_API_KEY = os.getenv("MARKETPLACE_API_KEY", "")
MARKETPLACE_SELLER_ID = os.getenv("MARKETPLACE_SELLER_ID", "")

# Pasta de saída
OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "./output")