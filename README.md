# ChatAgent 🤖

**Transforme assistentes de Inteligência Artificial do navegador em agentes capazes de atuar nos seus projetos de software.**

O **ChatAgent** é uma ferramenta desenvolvida em Python que amplia as possibilidades de uso de assistentes de IA acessados pelo navegador (ChatGPT, Gemini e DeepSeek), permitindo que eles participem de fluxos de desenvolvimento mais agênticos (*agentic workflows*).

Em vez de apenas receber respostas e copiar códigos manualmente, a IA pode analisar o contexto do seu projeto, **solicitar a leitura de arquivos adicionais dinamicamente**, propor modificações, criar novos arquivos e diretórios, tudo com revisão, confirmação e backup automático.

---

## ✨ Funcionalidades

- **Capacidades agênticas para IAs no navegador:** a IA recebe o contexto e pode interagir solicitando leituras e propondo modificações concretas.
- **Solicitação dinâmica de leitura (`---> Ler`):** ao enviar uma pasta, a IA recebe a estrutura dos diretórios e pode solicitar a leitura de qualquer arquivo que precise ver antes de codificar. O ChatAgent atende ao pedido e reenvia o conteúdo automaticamente em um loop interativo.
- **Edição, criação e exclusão de arquivos e pastas:** suporte a modificação de arquivos existentes no projeto, criação de novos arquivos de código, criação de estruturas de diretórios e deleção segura de arquivos obsoletos (`--> Deletar`).
- **Limpeza inteligente de cercas Markdown (```` ``` ````):** caso a IA inclua crases markdown no código retornado, o ChatAgent as remove automaticamente em qualquer tipo de arquivo (Java, Python, JS, etc.), preservando-as exclusivamente quando o destino for de fato um documento Markdown (`.md`).
- **Duas opções seguras para receber respostas longas:**
  - **Área de Transferência (Recomendado):** basta copiar a resposta na IA (`Ctrl+C`) e pressionar `Enter` no terminal. O ChatAgent lê direto da memória, sem limites de caracteres ou truncamento do console.
  - **Arquivo (`resposta_ia.txt`):** para códigos muito extensos, é possível colar a resposta diretamente no arquivo `resposta_ia.txt` e teclar `f` no terminal.
- **Auditoria de prompts enviados (`ultimo_prompt_enviado.txt`):** todo prompt gerado é salvo na raiz para consulta e conferência.
- **Modo 1 (Multi-IA):** envia o mesmo prompt simultaneamente para ChatGPT, Gemini e DeepSeek em abas separadas para comparação de soluções.
- **Modo 2 (Edição agêntica):** fluxo focado em edição de código, criação e exclusão de arquivos com a IA de sua escolha.
- **Segurança com backup e rollback:** antes de alterar ou deletar arquivos existentes, o ChatAgent cria backup em memória e solicita confirmação antes de gravar no disco.

---

## 🏗️ Estrutura do Projeto

O ChatAgent foi modularizado seguindo as boas práticas da comunidade Python:

```text
ChatAgent/
├── chatagent/
│   ├── __init__.py         # Inicialização do pacote
│   ├── browser.py          # Automação do Chrome, abas e envio
│   ├── constants.py        # URLs e definições dos assistentes de IA
│   ├── editor.py           # Parser tolerante, aplicação de ações e backups
│   ├── files.py            # Varredura de pastas, leitura e montagem de prompts
│   ├── modes.py            # Modos de operação (Multi-IA e Edição de Arquivos)
│   └── ui.py               # Leitura de prompts multilinha e seleção de contexto
├── main.py                 # Ponto de entrada da aplicação
├── requirements.txt        # Dependências do projeto
├── resposta_ia.txt         # Arquivo auxiliar para respostas extensas
└── README.md               # Documentação completa
```

---

## 🎯 Modos de Utilização

Ao iniciar o programa (`python main.py`), você escolhe entre dois modos:

### Modo 1: Enviar mensagem para três IAs
Abre abas dedicadas no Chrome para **ChatGPT**, **Gemini** e **DeepSeek**.
Ao digitar seu prompt e enviar (`--env`), o ChatAgent envia a mesma mensagem para as três plataformas simultaneamente, facilitando o brainstorming e a comparação de respostas.

### Modo 2: Edição e criação de arquivos
Permite selecionar uma pasta de projeto (ex: `D:\MeuProjeto`) e/ou arquivos específicos.

1. O ChatAgent gera a árvore de diretórios e o contexto dos arquivos.
2. Abre a IA escolhida e envia o prompt estruturado com instruções estritas.
3. Se a IA precisar ler arquivos adicionais da árvore, ela responde com `---> Ler caminho/arquivo`.
4. O ChatAgent lê os arquivos solicitados e reenvia o conteúdo à IA de forma automática.
5. Quando a IA entrega as alterações, você escolhe se deseja aplicar as ações propostas.

---

## 📜 Comandos Reconhecidos na Resposta da IA

O ChatAgent possui um analisador tolerante e inteligente que reconhece os seguintes marcadores estruturados:

| Marcador | Descrição |
|---|---|
| `---> código:` | Inicia um bloco de código (com ou sem acento, 2 a 5 traços). |
| `----> Modificar caminho/do/arquivo` | Modifica o arquivo especificado com o código do bloco anterior. |
| `--> Criar caminho/do/arquivo` | Cria um novo arquivo com o código fornecido (ou cria pasta se não houver código). |
| `--> Deletar caminho/do/arquivo` | Deleta o arquivo especificado (com confirmação do usuário e backup automático). |
| `---> Ler caminho/do/arquivo` | Solicita ao ChatAgent a leitura do conteúdo do arquivo na próxima iteração. |

> **Nota:** o analisador remove automaticamente cercas Markdown (```` ``` ````) de arquivos de código (como Java, Python, C#, JS) impedindo erros de sintaxe, mantendo-as apenas em arquivos Markdown (`.md`), além de ignorar placeholders genéricos ilustrativos.

---

## 📋 Pré-requisitos

- **Python 3.10+** instalado.
- **Google Chrome** instalado e aberto.
- Conta logada nos serviços de IA que desejar utilizar (ChatGPT, Gemini, DeepSeek).

---

## 💻 Instalação e Execução

### 1. Clone o repositório
```bash
git clone <URL_DO_REPOSITORIO>
cd ChatAgent
```

### 2. Crie e ative um ambiente virtual
No Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute o ChatAgent
```bash
python main.py
```

---

## 💡 Dicas de Uso

- **Para prompts multilinhas:** Digite ou cole seu texto no terminal e, ao terminar, digite `--env` em uma linha isolada para confirmar o envio.
- **Para sair de prompts multilinhas:** Digite `sair` e, em seguida, `--env`.
- **Respostas grandes da IA:** 
  - **Forma padrão:** Clique no botão "Copiar" da IA e apenas dê `Enter` no terminal (não precisa colar no terminal!).
  - **Via arquivo:** Cole o texto em `resposta_ia.txt` e digite `f` no terminal.
- **Auditoria:** Consulte `ultimo_prompt_enviado.txt` para conferir a mensagem exata montada com árvore e arquivos.

---

## 🔐 Segurança e Boas Práticas

- **Revisão obrigatória:** O ChatAgent sempre exibe as alterações propostas e solicita sua confirmação (`s/N`) antes de gravar no disco.
- **Backup automático:** Arquivos modificados têm seu conteúdo original preservado em memória durante a operação para rollback caso ocorra qualquer imprevisto.
- **Dados sensíveis:** Nunca envie senhas, chaves de API, arquivos `.env` ou certificados corporativos para assistentes públicos de IA.