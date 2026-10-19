# ChatAgent 🤖

**Transforme assistentes de Inteligência Artificial do navegador em agentes capazes de atuar nos seus projetos de software.**

O **ChatAgent** é uma ferramenta desenvolvida em Python que amplia as possibilidades de uso de assistentes de IA acessados pelo navegador, permitindo que eles participem de fluxos de desenvolvimento mais agênticos (*agentic workflows*).

Em vez de apenas receber respostas e copiar códigos manualmente, você pode utilizar a IA para analisar o contexto de um projeto, propor modificações, criar arquivos e diretórios e editar códigos existentes, com controle sobre as alterações aplicadas.

A ferramenta também permite aproveitar serviços de IA que oferecem acesso gratuito pelo navegador, sem necessariamente depender de APIs pagas ou assinaturas adicionais. A disponibilidade e os limites de uso dependem de cada plataforma.

## ✨ Funcionalidades

- **Capacidades agênticas para IAs do navegador:** facilite a execução de tarefas de desenvolvimento em que a IA analisa o contexto e propõe ações concretas sobre os arquivos do projeto.
- **Criação de arquivos e pastas:** permita que a IA proponha novos arquivos e diretórios para organizar ou expandir o projeto.
- **Edição de código existente:** aplique modificações em arquivos cujo conteúdo tenha sido explicitamente enviado como contexto.
- **Automação do fluxo de desenvolvimento:** reduza o trabalho manual de copiar respostas, criar arquivos e transferir alterações entre a IA e o projeto.
- **Seleção de contexto:** escolha pastas e arquivos específicos para fornecer à IA as informações necessárias.
- **Envio da estrutura do projeto:** compartilhe a organização de diretórios e os nomes dos arquivos sem enviar automaticamente o conteúdo de todos eles.
- **Uso de diferentes assistentes:** trabalhe com as plataformas de IA compatíveis com o fluxo de automação configurado.
- **Controle das alterações:** revise e confirme as ações propostas antes de aplicá-las.

## 🚀 Benefícios

### 🧠 De respostas para ações

Assistentes convencionais geralmente entregam instruções ou trechos de código que precisam ser aplicados manualmente. Com o ChatAgent, as respostas podem seguir um fluxo estruturado de ações, permitindo criar arquivos, organizar diretórios e modificar códigos dentro do escopo autorizado.

### 💰 IA mais acessível

Aproveite as modalidades gratuitas de assistentes de IA disponíveis pelo navegador, sem necessariamente contratar uma API ou pagar por uma assinatura adicional.

O acesso gratuito está sujeito às regras de cada plataforma, incluindo limites de mensagens, disponibilidade de modelos e exigências de cadastro.

### ⚡ Mais produtividade

Automatize etapas repetitivas do desenvolvimento e concentre-se em tarefas como definir requisitos, avaliar soluções e revisar o código produzido.

### 📂 Contexto sob medida

Selecione o que a IA precisa conhecer sobre o projeto. Você pode compartilhar apenas a estrutura de uma pasta ou incluir o conteúdo completo de arquivos específicos.

### 🔒 Controle sobre o projeto

A ferramenta restringe a edição de arquivos existentes àqueles cujo conteúdo foi enviado explicitamente como contexto. As ações propostas podem ser revisadas antes de serem aplicadas.

## 🛠️ Tecnologias

- **Python:** desenvolvimento da ferramenta e automação do fluxo de trabalho.
- **Google Chrome:** acesso aos assistentes de IA pelo navegador.
- **Inteligência Artificial generativa:** análise de contexto, geração de código e proposição de alterações.

## 📋 Pré-requisitos

- Python instalado.
- Google Chrome instalado.
- Conexão com a internet.
- Acesso aos serviços de IA utilizados, incluindo cadastro quando exigido.
- Dependências do projeto instaladas.

> O ChatAgent não garante acesso ilimitado ou gratuito a todos os modelos. As condições dependem dos serviços utilizados.

## ⚙️ Como funciona

1. Execute o ChatAgent e escolha o modo de utilização.
2. Selecione a pasta do projeto e/ou os arquivos que deseja disponibilizar como contexto.
3. A ferramenta prepara as informações selecionadas e as envia ao assistente de IA pelo navegador.
4. A IA analisa o contexto e propõe ações, como editar código, criar arquivos ou criar diretórios.
5. O ChatAgent identifica as ações estruturadas na resposta.
6. Revise e confirme as alterações antes de aplicá-las ao projeto.

## 📂 Seleção de contexto

| Seleção | Informação disponibilizada à IA |
|---|---|
| Somente uma pasta | Estrutura de diretórios e nomes dos arquivos |
| Um ou mais arquivos | Conteúdo dos arquivos selecionados |
| Uma pasta e arquivos específicos | Estrutura da pasta e conteúdo dos arquivos selecionados individualmente |

**Importante:** selecionar uma pasta não significa enviar automaticamente o conteúdo de todos os seus arquivos. Para permitir a edição de um arquivo existente, selecione-o individualmente para incluir seu conteúdo no contexto.

## 💻 Instalação e execução

### 1. Clone o repositório

```bash
git clone <URL_DO_REPOSITORIO>
```

### 2. Entre no diretório

```bash
cd ChatAgent
```

### 3. Crie um ambiente virtual

```bash
python -m venv .venv
```

### 4. Ative o ambiente virtual

No Windows:

```powershell
.venv\Scripts\activate
```

### 5. Instale as dependências

Caso exista um arquivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 6. Execute o programa

```bash
python main.py
```

Substitua `main.py` pelo nome real do arquivo principal, caso seja diferente.

## 🔐 Segurança e boas práticas

- Não envie senhas, tokens, chaves privadas, certificados ou outros dados sensíveis.
- Revise as informações compartilhadas com os serviços externos de IA.
- Confira as ações propostas antes de aplicá-las.
- Utilize Git ou backups para recuperar alterações quando necessário.
- Verifique as políticas de segurança da sua organização antes de utilizar código corporativo.

## 🎯 Objetivo

O ChatAgent busca aproximar os assistentes de IA do trabalho prático de desenvolvimento, permitindo que eles participem de tarefas que vão além da geração de texto.

A proposta é oferecer uma maneira acessível de incorporar fluxos de trabalho agênticos ao desenvolvimento de software, combinando automação em Python, contexto seletivo e aplicação controlada de alterações em projetos.