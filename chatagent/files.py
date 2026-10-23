"""Utilitários para listagem de arquivos e montagem do prompt de contexto."""

import os
from pathlib import Path

from chatagent.constants import DIRETORIOS_IGNORADOS, EXTENSOES_TEXTO, NOMES_TEXTO

# Estado global das pastas de projeto selecionadas na sessão atual.
PASTAS_PROJETO_SELECIONADAS: list[str] = []


def arquivo_e_textual(caminho: str) -> bool:
    """Indica se um arquivo é apropriado para ser enviado como texto à IA."""
    nome = os.path.basename(caminho).lower()
    extensao = os.path.splitext(nome)[1].lower()
    return extensao in EXTENSOES_TEXTO or nome in NOMES_TEXTO or nome.startswith('.env.')


def listar_arquivos_projeto(pasta: str, limite: int = 250) -> tuple[list[str], bool]:
    """Lista arquivos textuais do projeto, ignorando dependências e artefatos."""
    encontrados: list[str] = []

    for raiz, diretorios, arquivos in os.walk(pasta):
        diretorios[:] = sorted(
            d for d in diretorios
            if d.lower() not in DIRETORIOS_IGNORADOS
        )

        for nome in sorted(arquivos):
            caminho = os.path.join(raiz, nome)
            if not arquivo_e_textual(caminho):
                continue
            try:
                if os.path.getsize(caminho) > 300_000:
                    continue
            except OSError:
                continue
            encontrados.append(os.path.abspath(caminho))
            if len(encontrados) >= limite:
                return encontrados, True

    return encontrados, False


def gerar_estrutura_projeto(pasta: str, limite: int = 4000) -> str:
    """Gera uma árvore da estrutura do projeto sem incluir diretórios de build."""
    pasta = os.path.abspath(pasta)
    nome_raiz = os.path.basename(os.path.normpath(pasta)) or pasta
    linhas = [f'{nome_raiz}/']
    total = 0
    truncada = False

    for raiz, diretorios, arquivos in os.walk(pasta):
        diretorios[:] = sorted(
            d for d in diretorios
            if d.lower() not in DIRETORIOS_IGNORADOS
        )
        arquivos = sorted(arquivos)
        relativo = os.path.relpath(raiz, pasta)
        nivel = 0 if relativo == '.' else len(Path(relativo).parts)

        if relativo != '.':
            linhas.append('    ' * (nivel - 1) + '├── ' + os.path.basename(raiz) + '/')
            total += 1

        for nome in arquivos:
            prefixo = '    ' * nivel + '├── '
            linhas.append(prefixo + nome)
            total += 1
            if total >= limite:
                truncada = True
                break
        if truncada:
            break

    if truncada:
        linhas.append('... estrutura parcial: limite de itens atingido ...')

    return '\n'.join(linhas)


def criar_prompt_edicao(file_paths: list[str], user_prompt: str) -> str:
    """Monta o prompt completo com contexto de arquivos e pastas para a IA."""
    partes_arquivos: list[str] = []
    total_caracteres = 0
    limite_caracteres = 180_000
    arquivos_incluidos: list[str] = []

    for caminho in file_paths:
        try:
            with open(caminho, 'r', encoding='utf-8-sig') as arquivo:
                conteudo = arquivo.read()
        except UnicodeDecodeError:
            print(f'[AVISO] O arquivo não é texto UTF-8 compatível e foi ignorado: {caminho}')
            continue
        except OSError as erro:
            print(f'[AVISO] Não foi possível ler {caminho}: {erro}')
            continue

        bloco = f'Arquivo selecionado explicitamente: {caminho}\nConteúdo atual completo:\n{conteudo}\n'
        if total_caracteres + len(bloco) > limite_caracteres:
            print('[AVISO] O limite de contexto foi atingido; os arquivos restantes não serão enviados.')
            break

        partes_arquivos.append(bloco)
        arquivos_incluidos.append(caminho)
        total_caracteres += len(bloco)

    partes_estrutura: list[str] = []
    for pasta in PASTAS_PROJETO_SELECIONADAS:
        partes_estrutura.append(
            f'Estrutura do projeto selecionado ({pasta}):\n'
            f'{gerar_estrutura_projeto(pasta)}'
        )

    if not partes_arquivos and not partes_estrutura:
        raise ValueError('Não foi possível preparar arquivos ou pastas para enviar à IA.')

    regras = (
        'REGRAS OBRIGATÓRIAS (SIGA ESTRITAMENTE - VOCÊ DEVE RESPONDER COM OS COMANDOS):\n'
        '1. A estrutura da pasta é apenas uma lista de diretórios e nomes de arquivos; o conteúdo desses arquivos NÃO foi enviado.\n'
        '2. Somente os arquivos listados em CONTEÚDO DOS ARQUIVOS SELECIONADOS foram enviados com conteúdo completo.\n'
        '3. Modifique arquivos existentes somente quando seu conteúdo completo tiver sido enviado explicitamente. Não invente o conteúdo original de arquivos vistos apenas na estrutura.\n'
        '4. Se for necessário alterar um arquivo que aparece apenas na estrutura, você PODE e DEVE solicitar a leitura diretamente escrevendo ---> Ler seguido do caminho completo do arquivo.\n'
        '5. Você pode propor a criação de novos arquivos ou pastas dentro da pasta selecionada, usando os nomes e caminhos da estrutura como contexto.\n'
        '6. É OBRIGATÓRIO que suas alterações venham no formato exato de comandos. NUNCA responda apenas com texto explicativo livre sem comandos.\n'
        '7. Antes de CADA código retornado, coloque OBRIGATORIAMENTE ---> código: em uma linha separada.\n'
        '8. Não use cercas Markdown como ```java ou ```python.\n'
        '9. Depois do código de um arquivo existente, coloque ----> Modificar seguido do caminho completo exato.\n'
        '10. Para criar um arquivo novo, retorne o conteúdo completo precedido por ---> código: e finalize com --> Criar seguido do caminho completo do arquivo.\n'
        '11. Para criar uma pasta, escreva somente --> Criar seguido do caminho completo da pasta.\n'
        '12. Modifique ou crie recursos somente dentro das pastas selecionadas ou nos arquivos selecionados diretamente.\n'
        '13. Não é necessário retornar marcadores para arquivos que não precisam ser alterados.\n'
        '14. Não misture o conteúdo de arquivos diferentes, não invente caminhos e não inclua explicações entre os blocos de código.\n'
        '15. Se precisar ler o conteúdo de um arquivo antes de continuar, escreva ---> Ler seguido do caminho absoluto completo do arquivo em uma linha separada (sem bloco de código). O ChatAgent enviará o conteúdo na próxima mensagem automaticamente. Você pode solicitar vários arquivos de uma vez usando um marcador ---> Ler por linha.\n'
        '16. NUNCA COLOQUE UM BLOCO DE COMANDO DENTRO DO OUTRO! NUNCA abra um novo ---> código: sem antes ter finalizado o anterior com seu respectivo comando (----> Modificar ou --> Criar). Cada arquivo deve ser finalizado completamente antes de iniciar o próximo.\n\n'
    )

    estrutura = '\n\n'.join(partes_estrutura)
    conteudos = '\n\n'.join(partes_arquivos)
    partes_prompt = [regras]

    if estrutura:
        partes_prompt.append('ESTRUTURA DO PROJETO (somente nomes; nenhum conteúdo de arquivo foi enviado por causa da pasta):\n\n' + estrutura)

    if conteudos:
        partes_prompt.append('CONTEÚDO DOS ARQUIVOS SELECIONADOS EXPLICITAMENTE:\n\n' + conteudos)

    if arquivos_incluidos:
        partes_prompt.append('CAMINHOS DOS ARQUIVOS CUJO CONTEÚDO FOI ENVIADO:\n' + '\n'.join(arquivos_incluidos))

    partes_prompt.append('SOLICITAÇÃO DO USUÁRIO:\n' + user_prompt)
    return '\n\n'.join(partes_prompt)


def criar_prompt_leitura(caminhos_solicitados: list[str], user_prompt: str = '') -> str:
    """
    Monta a mensagem com o conteúdo dos arquivos solicitados pela IA via ``---> Ler``.

    Valida se os arquivos existem e podem ser lidos antes de incluí-los.
    Retorna o texto pronto para ser enviado à IA na próxima interação,
    incluindo as regras estritas e obrigatórias de resposta com comandos e códigos.
    """
    partes: list[str] = []
    nao_encontrados: list[str] = []

    for caminho in caminhos_solicitados:
        caminho = os.path.abspath(caminho)
        if not os.path.isfile(caminho):
            nao_encontrados.append(caminho)
            continue
        try:
            with open(caminho, 'r', encoding='utf-8-sig') as f:
                conteudo = f.read()
            partes.append(
                f'Arquivo solicitado via ---> Ler: {caminho}\n'
                f'Conteúdo atual completo:\n{conteudo}'
            )
        except UnicodeDecodeError:
            partes.append(
                f'Arquivo solicitado via ---> Ler: {caminho}\n'
                '[AVISO] O arquivo não pôde ser lido como texto UTF-8 compatível.'
            )
        except OSError as e:
            partes.append(
                f'Arquivo solicitado via ---> Ler: {caminho}\n'
                f'[AVISO] Erro ao ler o arquivo: {e}'
            )

    if nao_encontrados:
        aviso = 'AVISO: Os seguintes arquivos solicitados não foram encontrados:\n' + '\n'.join(
            f'  - {c}' for c in nao_encontrados
        )
        partes.append(aviso)

    if not partes:
        raise ValueError('Nenhum dos arquivos solicitados pôde ser lido.')

    instrucoes_obrigatorias = (
        '======================================================================\n'
        'ATENÇÃO: LEITURA DE ARQUIVO CONCLUÍDA - SIGA AS REGRAS OBRIGATÓRIAS!\n'
        'Você solicitou a leitura de arquivos via ---> Ler. Os conteúdos estão abaixo.\n'
        'É OBRIGATÓRIO responder usando os comandos específicos do ChatAgent!\n'
        'NÃO responda com explicações soltas ou texto livre sem comandos.\n'
        'SEMPRE use ---> código: antes de qualquer código e o comando correspondente.\n'
        '======================================================================\n\n'
        'REGRAS OBRIGATÓRIAS PARA SUA RESPOSTA:\n'
        '1. Antes de CADA bloco de código, coloque obrigatoriamente ---> código: em uma linha separada.\n'
        '2. Para MODIFICAR um arquivo existente:\n'
        '   ---> código:\n'
        '   (conteúdo completo do código aqui, sem crases markdown)\n'
        '   ----> Modificar CAMINHO_ABSOLUTO_DO_ARQUIVO\n'
        '3. Para CRIAR um novo arquivo:\n'
        '   ---> código:\n'
        '   (conteúdo completo do código aqui, sem crases markdown)\n'
        '   --> Criar CAMINHO_ABSOLUTO_DO_ARQUIVO\n'
        '4. Para CRIAR uma pasta (sem código):\n'
        '   --> Criar CAMINHO_ABSOLUTO_DA_PASTA\n'
        '5. Se ainda precisar ler outros arquivos antes de implementar:\n'
        '   ---> Ler CAMINHO_ABSOLUTO_DO_ARQUIVO\n'
        '6. PROIBIDO o uso de cercas Markdown (```). Coloque o código puro diretamente após ---> código:\n'
        '7. Não coloque comentários ou explicações entre os códigos.\n'
        '8. NUNCA COLOQUE UM BLOCO DE COMANDO DENTRO DO OUTRO! Finalize cada arquivo completamente com seu comando (----> Modificar ou --> Criar) antes de iniciar outro ---> código:. Nunca aninhe blocos de comando.\n'
        '9. IMPORTANTE: Use sempre o caminho absoluto real e exato do arquivo (por exemplo D:\\Projeto\\src\\Arquivo.java). NUNCA invente ou escreva textos literais como <caminho>.\n'
        '======================================================================'
    )

    secoes = [instrucoes_obrigatorias]

    if user_prompt and user_prompt.strip():
        secoes.append(
            'SOLICITAÇÃO ORIGINAL DO USUÁRIO QUE VOCÊ DEVE EXECUTAR AGORA:\n'
            f'{user_prompt.strip()}'
        )

    secoes.append(
        'CONTEÚDO DOS ARQUIVOS SOLICITADOS VIA ---> Ler:\n\n' + '\n\n'.join(partes)
    )

    lembrete_final = (
        '======================================================================\n'
        'LEMBRETE OBRIGATÓRIO FINAL:\n'
        'Com base nos conteúdos acima e na solicitação do usuário, responda AGORA\n'
        'obrigatoriamente utilizando os comandos (---> código:, ----> Modificar, --> Criar ou ---> Ler).\n'
        'NÃO envie resposta em texto livre sem os comandos!\n'
        '======================================================================'
    )
    secoes.append(lembrete_final)

    return '\n\n'.join(secoes)
