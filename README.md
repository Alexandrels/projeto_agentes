# Criador de Vídeo de Produto - Sistema de Agentes com LangChain e LangGraph

Sistema de criação de imagens e vídeos de produtos com aprovação humana em cada etapa (human-in-the-loop), suporte a múltiplos LLMs trocáveis, validação de vídeo com FFmpeg (áudio obrigatório), persistência com SQLite e integração com marketplaces.

## Estrutura do Projeto

```
projeto_agentes/
├── .env.example              # Exemplo de variáveis de ambiente
├── .gitignore                # Arquivos ignorados pelo git
├── pyproject.toml            # Metadados do projeto
├── requirements.txt          # Dependências Python
├── run_ui.sh                 # Script para iniciar a interface
├── README.md                 # Este documento
├── data/                     # Banco de checkpoints do LangGraph (criado automaticamente)
├── output/                   # Pasta para vídeos salvos localmente
├── src/
│   ├── __init__.py
│   ├── config.py             # Factory de LLM trocável (OpenAI/Anthropic)
│   ├── state.py              # Estado compartilhado (TypedDict)
│   ├── storage.py            # Checkpointer SQLite (persistência)
│   ├── graph.py              # Grafo LangGraph compilado
│   ├── nodes.py              # Agentes/nós das 4 etapas + validação FFmpeg
│   ├── main.py               # Execução via linha de comando
│   ├── media/
│   │   ├── __init__.py
│   │   └── validator.py      # Validação de vídeo com FFmpeg (áudio obrigatório)
│   └── ui/
│       ├── __init__.py
│       ├── app.py            # Router principal da interface Streamlit
│       ├── components.py     # Componentes reutilizáveis da UI
│       └── pages/
│           ├── produto.py    # Tela 1: Nome do produto
│           ├── descricao.py  # Tela 2: Descrição/Links
│           ├── imagem.py     # Tela 3: Aprovação da imagem
│           ├── video.py      # Tela 4: Aprovação do vídeo (com validação FFmpeg)
│           └── destino.py    # Tela 5: Marketplace ou salvamento local
└── tests/                    # Testes automatizados (pendente de implementação)
    ├── unit/
    ├── integration/
    └── fakes/
```

---

## 1. Pré-requisitos

- Python 3.11 ou superior
- `venv` (módulo padrão do Python)
- **FFmpeg** instalado no sistema (obrigatório para validação de vídeo)
- Acesso à internet para instalação de pacotes e chamadas de API

### Instalar FFmpeg

```bash
# Debian/Ubuntu
sudo apt-get update && sudo apt-get install -y ffmpeg

# Verificar instalação
ffmpeg -version
ffprobe -version
```

---

## 2. Configuração do Ambiente

### Passo 1 - Acesse a pasta do projeto

```bash
cd /home/ale/ai_projetos/criar_videos/projeto_agentes
```

### Passo 2 - Crie o ambiente virtual

```bash
python3 -m venv .venv
```

### Passo 3 - Ative o ambiente virtual

```bash
# Linux/macOS:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

### Passo 4 - Instale as dependências

```bash
pip install -r requirements.txt
```

### Passo 5 - Configure as variáveis de ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e preencha com suas próprias chaves de API:

```env
# Provedor de LLM ativo (openai, anthropic, google, ollama)
LLM_PROVIDER=openai

# Chaves de API dos provedores de LLM
OPENAI_API_KEY=sua_chave_openai_aqui
ANTHROPIC_API_KEY=sua_chave_anthropic_aqui

# Modelo LLM padrão
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7

# Provedor de geração de imagem
IMAGE_PROVIDER=dalle3
OPENAI_IMAGE_API_KEY=sua_chave_openai_aqui

# Provedor de geração de vídeo
VIDEO_PROVIDER=runway
RUNWAY_API_KEY=sua_chave_runway_aqui

# Marketplace (opcional)
MARKETPLACE_API_URL=https://api.marketplace.exemplo.com
MARKETPLACE_API_KEY=sua_chave_marketplace_aqui
MARKETPLACE_SELLER_ID=seu_id_vendedor

# Pasta de saída para vídeos salvos localmente
OUTPUT_FOLDER=./output

# Caminho do banco de checkpoints do LangGraph (SQLite)
LANGGRAPH_DB_PATH=./data/checkpoints.sqlite
```

> **Nota:** Se não tiver chaves de API reais, o sistema funcionará em modo simulação (gera URLs fictícias para teste do fluxo).

---

## 3. Como Executar

### Opção A - Interface Web (Streamlit) - RECOMENDADO

Execute os comandos a partir da raiz de `projeto_agentes/`, com o ambiente virtual ativado:

```bash
source .venv/bin/activate
PYTHONPATH=. streamlit run src/ui/app.py
```

`PYTHONPATH=.` permite que a aplicação encontre o pacote `src` ao iniciar pelo Streamlit.
No Windows, use o comando equivalente `set PYTHONPATH=.` antes de iniciar o Streamlit.

Como alternativa, use o script:

```bash
./run_ui.sh
```

A interface estará disponível em: `http://localhost:8501`

### Proteções para commits e envio ao GitHub

Os hooks do repositório bloqueiam commits na branch `main`, tentativas de enviar `main` diretamente ao remoto, arquivos `.env` (exceto `.env.example`) e conteúdo que pareça conter chaves de API ou outras credenciais. O hook de commit verifica o staging; o hook de push também verifica os arquivos dos commits que serão enviados, inclusive o histórico novo.

Ative os hooks em cada clone:

```bash
./scripts/install_git_hooks.sh
```

Antes de commitar, crie e use uma branch de trabalho, por exemplo `feature/minha-alteracao`. Confira os arquivos selecionados com `git status` e faça o commit nessa branch. Os hooks analisam o conteúdo, não apenas os nomes dos arquivos.

Essas verificações locais são uma camada de proteção: hooks podem ser ignorados com opções como `--no-verify` e não substituem regras de proteção configuradas no GitHub. Para proteger o remoto, configure uma ruleset/branch protection para `main` exigindo pull request e habilite secret scanning/push protection quando disponível. Se uma chave real já tiver sido compartilhada, revogue-a no provedor e gere outra; removê-la do commit atual não invalida a chave exposta.

### Opção B - Linha de Comando

```bash
python src/main.py
```

---

## 4. Fluxo de Uso pela Interface

### Tela 1 - Nome do Produto
1. Informe o nome do produto (ex: "Smartphone X100")
2. Clique em **"Iniciar fluxo"**
3. O sistema inicializa o estado do grafo LangGraph com um `job_id` e `thread_id` únicos

### Tela 2 - Descrição ou Links
1. Cole a descrição do produto ou links que o descrevam
2. Clique em **"Gerar imagem"**
3. O sistema executa o grafo até a primeira interrupção (após geração de imagem)

### Tela 3 - Aprovação da Imagem (Human-in-the-Loop)
1. Visualize a imagem gerada
2. Clique em **"Aprovar"** para continuar
3. Ou clique em **"Reprovar"** e informe o feedback para regeneração

### Tela 4 - Aprovação do Vídeo de 8 Segundos (Human-in-the-Loop)
1. Visualize o roteiro e o vídeo gerado
2. O sistema executa **validação automática com FFmpeg** antes da aprovação humana:
   - Duração próxima de 8 segundos
   - Presença de stream de vídeo
   - **Áudio obrigatório** (erro se nenhum stream de áudio for encontrado)
   - Codec de vídeo e áudio, container, dimensões
   - Checksum SHA-256 para integridade
3. Se a validação falhar, o fluxo é interrompido com erro e não avança para aprovação humana
4. Clique em **"Aprovar"** para continuar ou **"Reprovar"** com feedback

### Tela 5 - Destino Final
1. Escolha entre:
   - **"Publicar no marketplace"** → publica via API configurada (simulação)
   - **"Salvar localmente"** → salva na pasta `output/` com nome baseado em timestamp (`AAAA-MM-DD_HH-MM-SS-ms`)
2. Clique em **"Confirmar destino"**
3. Visualize o resultado final

---

## 5. Troca de Modelos LLM

O sistema suporta troca de provedores LLM sem alterar código. Edite o arquivo `.env`:

```env
LLM_PROVIDER=openai    # ou: anthropic, google, ollama
LLM_MODEL=gpt-4o-mini  # modelo específico do provedor
```

Provedores suportados na factory (`src/config.py`):
- **OpenAI** - ChatOpenAI
- **Anthropic** - ChatAnthropic
- **Google** - placeholder (implementação futura)
- **Ollama** - placeholder (modelos locais)

---

## 6. Persistência e Retomada (SQLite Checkpointer)

O grafo LangGraph usa **SqliteSaver** em vez de `MemorySaver`, permitindo:

- Retomada de execuções após interrupção ou reinício do processo
- Persistência de estados e aprovações em banco SQLite local
- Identificação de trabalhos via `job_id` e `thread_id`

O banco é criado automaticamente em `./data/checkpoints.sqlite` (ou conforme `LANGGRAPH_DB_PATH` no `.env`).

---

## 7. Estrutura do Grafo LangGraph

O fluxo é orquestrado por LangGraph com os seguintes nós:

| Nó | Função | Aprovação Humana |
|----|--------|------------------|
| `solicitar_produto` | Recebe nome do produto | Não |
| `gerar_imagem` | Gera imagem de alta resolução | Sim (após geração) |
| `processar_descricao` | Extrai características com LLM | Sim (após extração) |
| `gerar_roteiro_video` | Cria roteiro de 8 segundos | Não |
| `gerar_video` | Gera vídeo via API + valida FFmpeg | Sim (após validação e geração) |
| `decidir_destino` | Pergunta marketplace vs local | Sim (escolha do usuário) |
| `publicar_marketplace` | Publica via API | Não |
| `salvar_local` | Salva com timestamp | Não |
| `erro` | Tratamento de erros | Não |

Interrupções são implementadas com `langgraph.types.interrupt()` e retomadas com `Command(resume=...)`.

---

## 8. Validação de Vídeo com FFmpeg

O módulo `src/media/validator.py` valida cada vídeo gerado antes da aprovação humana:

- **Duração:** próxima de 8 segundos (tolerância configurável, padrão 0.5s)
- **Áudio obrigatório:** erro se nenhum stream de áudio for encontrado
- **Stream de vídeo:** erro se não houver stream de vídeo
- **Codec:** identifica codec de vídeo e áudio
- **Container:** identifica formato (ex: MP4)
- **Integridade:** checksum SHA-256 e verifica que o arquivo não está vazio

Exemplo de resultado de validação armazenado no estado:

```json
{
  "valido": true,
  "duracao": 8.02,
  "codec_video": "h264",
  "codec_audio": "aac",
  "tem_audio": true,
  "checksum": "a1b2c3d4...",
  "tamanho": 1048576,
  "erros": [],
  "avisos": []
}
```

---

## 9. Salvamento Local

Quando o usuário escolhe "Salvar localmente", o vídeo é armazenado em:

```
output/AAAA-MM-DD_HH-MM-SS-ms/video.mp4
```

Exemplo: `output/2026-10-22_14-30-45-123/video.mp4`

O nome da pasta inclui ano, mês, dia, hora, minuto, segundo e milissegundo.

---

## 10. Solução de Problemas

### Erro: `externally-managed-environment` ao instalar dependências

Use o ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Erro: `ffprobe` não encontrado

Instale FFmpeg no sistema (veja seção 1).

### Erro de importação de módulos da UI

Execute a partir da raiz do projeto `projeto_agentes/`, ative o ambiente virtual e defina `PYTHONPATH=.`:

```bash
source .venv/bin/activate
PYTHONPATH=. streamlit run src/ui/app.py
```

### Chaves de API não configuradas

O sistema roda em modo simulação sem chaves reais, mas não conseguirá gerar imagens/vídeos reais. Configure pelo menos `LLM_PROVIDER` e a chave correspondente no `.env`.

---

## 11. Comandos Úteis

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar interface (a partir da raiz do projeto)
PYTHONPATH=. streamlit run src/ui/app.py

# Executar via linha de comando
python src/main.py

# Verificar dependências instaladas
pip list

# Sair do ambiente virtual
deactivate

# Verificar se FFmpeg está instalado
ffmpeg -version
ffprobe -version
```

---

## 12. Itens Pendentes (Plano de Conclusão)

O MVP está funcional, mas os seguintes itens estão pendentes para qualidade de produção:

| Item | Status | Prioridade |
|------|--------|------------|
| Persistência SQLite checkpointer | ✅ Implementado | - |
| Validação FFmpeg com áudio obrigatório | ✅ Implementado | - |
| Interface Streamlit (5 telas) | ✅ Implementado | - |
| Estrutura `.gitignore` e `pyproject.toml` | ✅ Implementado | - |
| Testes automatizados (pytest) | ⏳ Pendente | Alta |
| Integração real com marketplace | ⏳ Pendente | Alta |
| Segurança e SSRF | ⏳ Pendente | Média |
| Logs estruturados e observabilidade | ⏳ Pendente | Média |
| Idempotência e reconciliação | ⏳ Pendente | Média |
| Fallback não silencioso de provedores | ⏳ Pendente | Baixa |

---

## 13. Licença

Projeto desenvolvido para fins de demonstração e aprendizado em orquestração de agentes com LangChain e LangGraph.