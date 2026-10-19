

import os
from pathlib import Path
import re

import sys

import time
import ctypes

import pyautogui

import pyperclip

import pygetwindow as gw

pyautogui.FAILSAFE = True

pyautogui.PAUSE = 0.3

janela_chrome_alvo = None

SITES_IA = {

    '1': ('ChatGPT', 'https://chatgpt.com'),

    '2': ('Gemini', 'https://gemini.google.com/u/1/app'),

    '3': ('DeepSeek', 'https://chat.deepseek.com')

}


PASTAS_PROJETO_SELECIONADAS = []

DIRETORIOS_IGNORADOS = {
    '.git', '.idea', '.vscode', 'node_modules', 'target', 'build',
    'dist', 'out', '.gradle', '.mvn', '__pycache__', '.venv', 'venv',
    'coverage', '.angular', '.next', 'bin', 'obj'
}

EXTENSOES_TEXTO = {
    '.java', '.kt', '.kts', '.groovy', '.xml', '.yml', '.yaml', '.properties',
    '.json', '.md', '.txt', '.py', '.js', '.jsx', '.ts', '.tsx', '.html',
    '.css', '.scss', '.sass', '.sql', '.sh', '.bat', '.cmd', '.ps1', '.toml',
    '.ini', '.cfg', '.conf', '.gradle', '.tf', '.hcl', '.dockerfile', '.gitignore',
    '.env.example', '.feature', '.graphql', '.proto', '.vue', '.svelte', '.cs',
    '.go', '.rs', '.php', '.rb', '.c', '.h', '.cpp', '.hpp'
}

NOMES_TEXTO = {
    'pom.xml', 'mvnw', 'mvnw.cmd', 'gradlew', 'gradlew.bat', 'dockerfile',
    'makefile', '.gitignore', '.dockerignore', '.editorconfig', 'jenkinsfile',
    'procfile', 'license', 'readme', 'readme.md'
}

def obter_primeira_janela_chrome():
    """Localiza uma janela válida do Chrome sem alterar seu estado."""
    global janela_chrome_alvo

    try:
        user32 = ctypes.windll.user32
        janelas = [j for j in gw.getWindowsWithTitle("Chrome") if j.visible]

        for janela in janelas:
            try:
                hwnd = int(janela._hWnd)
                if hwnd and user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
                    janela_chrome_alvo = janela
                    return True
            except Exception:
                continue

        janela_chrome_alvo = None
        print("\n[ERRO] Nenhuma janela válida do Chrome foi encontrada.")
        print("Abra o Chrome manualmente e execute novamente.")
        return False

    except Exception as e:
        janela_chrome_alvo = None
        print(f"[ERRO] Não foi possível localizar o Chrome: {e}")
        return False


def focar_janela_alvo():
    """Traz o Chrome para frente sem maximizar, restaurar ou minimizar a janela."""
    global janela_chrome_alvo

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    if not obter_primeira_janela_chrome():
        return False

    try:
        hwnd = int(janela_chrome_alvo._hWnd)
        if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            janela_chrome_alvo = None
            print("[ERRO] A janela do Chrome não está disponível.")
            return False

        hwnd_foreground = user32.GetForegroundWindow()
        thread_atual = kernel32.GetCurrentThreadId()
        thread_foreground = (
            user32.GetWindowThreadProcessId(hwnd_foreground, None)
            if hwnd_foreground else 0
        )
        thread_chrome = user32.GetWindowThreadProcessId(hwnd, None)

        anexos = []
        try:
            for thread_id in {thread_foreground, thread_chrome}:
                if thread_id and thread_id != thread_atual:
                    if user32.AttachThreadInput(thread_atual, thread_id, True):
                        anexos.append(thread_id)

            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.3)
            return user32.GetForegroundWindow() == hwnd
        finally:
            for thread_id in reversed(anexos):
                user32.AttachThreadInput(thread_atual, thread_id, False)

    except Exception as e:
        janela_chrome_alvo = None
        print(f"[ERRO] Não foi possível focar o Chrome: {e}")
        return False

def abrir_site_em_nova_aba(site):

    """Abre um site em uma nova aba, preservando as abas existentes."""

    if janela_chrome_alvo is None and not obter_primeira_janela_chrome():

        return False

    if not focar_janela_alvo():

        return False

    pyautogui.hotkey('ctrl', 't')

    time.sleep(0.7)

    pyperclip.copy(site)

    pyautogui.hotkey('ctrl', 'v')

    pyautogui.press('enter')

    time.sleep(3)

    return True

def preparar_campo_ia(nome_ia):

    """Orienta o usuário a posicionar o cursor no campo da IA."""

    print("\n" + "=" * 60)

    print(f"[PREPARAÇÃO] {nome_ia}")

    print("1. Aguarde a página terminar de carregar.")

    print("2. Clique dentro do campo de mensagem da IA.")

    print("3. Volte para este terminal.")

    input("4. Pressione ENTER quando estiver pronto para enviar: ")

def abrir_tres_sites():

    """Abre as três IAs, cada uma em uma nova aba."""

    print("\n[OK] Preparando as abas das três IAs...")

    for chave in ['1', '2', '3']:

        nome, site = SITES_IA[chave]

        if not abrir_site_em_nova_aba(site):

            print(f"[ERRO] Não foi possível abrir o {nome}.")

            return False

        print(f"[OK] {nome} aberto em uma nova aba.")

    print("\nAs três abas foram abertas.")

    print("Verifique se você está conectado às três IAs.")

    print(

        "Clique no campo de mensagem de CADA site antes de continuar, "

        "para que cada aba mantenha o foco correto."

    )

    input("Pressione ENTER quando terminar de preparar as abas: ")

    return True

def abrir_ia_escolhida():

    """Permite escolher uma única IA e abre somente o site selecionado."""

    print("\nQual IA deseja utilizar?")

    print("1. ChatGPT")

    print("2. Gemini")

    print("3. DeepSeek")

    print("0. Voltar ao menu principal")

    escolha = input("Escolha uma opção: ").strip()

    if escolha == '0':

        return 'voltar'

    if escolha not in SITES_IA:

        print("[ERRO] Opção inválida.")

        return None

    nome, site = SITES_IA[escolha]

    if not abrir_site_em_nova_aba(site):

        return None

    print(f"\n[OK] {nome} aberto em uma nova aba.")

    print("Não será necessário abrir as outras IAs.")

    preparar_campo_ia(nome)

    return escolha

def enviar_para_varias_abas(prompt):
    """Envia o prompt às três abas abertas pelo modo 1."""
    if not focar_janela_alvo():
        print("[ERRO] Não foi possível focar o Chrome.")
        return False

    pyperclip.copy(prompt)

    try:
        # Ctrl+9 seleciona a última aba do Chrome, mesmo quando há abas anteriores.
        pyautogui.hotkey("ctrl", "9")
        time.sleep(0.6)

        # As três abas abertas pelo programa estão no final:
        # DeepSeek, Gemini e ChatGPT, nesta ordem de navegação reversa.
        for indice in range(3):
            if indice > 0:
                pyautogui.hotkey("ctrl", "shift", "tab")
                time.sleep(0.5)

            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.4)
            pyautogui.press("enter")
            time.sleep(0.7)

        return True

    except Exception as e:
        print(f"[ERRO] Falha ao enviar o prompt às abas: {e}")
        return False

def enviar_para_uma_aba(prompt, atalho_aba=None):
    """Envia para a aba recém-aberta e ativa da IA escolhida."""
    if not focar_janela_alvo():
        print("[ERRO] Não foi possível focar o Chrome.")
        return False

    try:
        # A aba da IA escolhida acabou de ser aberta e permanece ativa.
        # Não usamos Ctrl+1/2/3, pois isso selecionaria abas antigas do Chrome.
        pyperclip.copy(prompt)
        time.sleep(0.3)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.4)
        pyautogui.press("enter")
        time.sleep(0.7)
        return True

    except Exception as e:
        print(f"[ERRO] Falha ao enviar a mensagem: {e}")
        return False

def ler_prompt_multilinha():

    print("\nDigite ou cole seu prompt abaixo.")

    print("Para enviar, digite '--env' em uma linha vazia.")

    linhas = []

    while True:

        try:

            linha = input()

            if linha.strip() == '--env':

                break

            linhas.append(linha)

        except EOFError:

            break

    return '\n'.join(linhas)

def separar_caminhos(entrada):
    """Separa caminhos por vírgulas ou quebras de linha."""
    caminhos = re.split(r'[,\r\n]+', entrada)
    resultado = []
    vistos = set()

    for caminho in caminhos:
        caminho = caminho.strip().strip('"').strip("'").strip()
        if not caminho:
            continue

        caminho = os.path.abspath(os.path.expanduser(caminho))
        chave = os.path.normcase(os.path.normpath(caminho))
        if chave not in vistos:
            vistos.add(chave)
            resultado.append(caminho)

    return resultado


def arquivo_e_textual(caminho):
    """Indica se um arquivo é apropriado para ser enviado como texto à IA."""
    nome = os.path.basename(caminho).lower()
    extensao = os.path.splitext(nome)[1].lower()
    return extensao in EXTENSOES_TEXTO or nome in NOMES_TEXTO or nome.startswith('.env.')


def listar_arquivos_projeto(pasta, limite=250):
    """Lista arquivos textuais do projeto, ignorando dependências e artefatos."""
    encontrados = []

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


def gerar_estrutura_projeto(pasta, limite=4000):
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


def selecionar_arquivos():
    """Aceita arquivos e pastas de projeto e prepara o contexto para a IA."""
    global PASTAS_PROJETO_SELECIONADAS

    while True:
        print("\nInforme os caminhos dos arquivos ou pastas de projeto que deseja modificar.")
        print("Separe os caminhos por vírgulas ou quebras de linha.")
        print(r'Exemplo de arquivo: D:\Projeto\src\Main.java')
        print(r'Exemplo de pasta: D:\Projeto')
        print("Ao informar uma pasta, será enviada somente a estrutura do projeto, sem o conteúdo dos arquivos.")
        print("Para enviar o conteúdo de um arquivo, informe o caminho desse arquivo separadamente.")
        print("Digite '--env' em uma linha vazia para confirmar.")
        print("Digite 'voltar' para retornar ao menu principal.")

        linhas = []
        while True:
            linha = input()
            if linha.strip() == '--env':
                break
            linhas.append(linha)

        entrada = '\n'.join(linhas).strip()
        if entrada.lower() in ['voltar', 'sair', 'exit']:
            return None

        caminhos = separar_caminhos(entrada)
        if not caminhos:
            print('[ERRO] Informe pelo menos um arquivo ou pasta.')
            continue

        invalidos = [c for c in caminhos if not os.path.isfile(c) and not os.path.isdir(c)]
        if invalidos:
            print('\n[ERRO] Os seguintes caminhos não existem:')
            for caminho in invalidos:
                print(f'  - {caminho}')
            print('Tente novamente.')
            continue

        pastas = [os.path.abspath(c) for c in caminhos if os.path.isdir(c)]
        arquivos = [os.path.abspath(c) for c in caminhos if os.path.isfile(c)]
        PASTAS_PROJETO_SELECIONADAS = pastas

        unicos = []
        vistos = set()
        for caminho in arquivos:
            chave = os.path.normcase(os.path.normpath(caminho))
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(caminho)

        if not unicos and not pastas:
            print('[ERRO] Informe pelo menos um arquivo ou pasta válida.')
            continue

        return unicos

def chave_caminho(caminho):

    """Normaliza um caminho para comparação."""

    return os.path.normcase(

        os.path.normpath(os.path.abspath(caminho))

    )

def criar_prompt_edicao(file_paths, user_prompt):
    """Envia conteúdo apenas dos arquivos selecionados individualmente e estrutura das pastas."""
    partes_arquivos = []
    total_caracteres = 0
    limite_caracteres = 180_000
    arquivos_incluidos = []

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

    partes_estrutura = []
    for pasta in PASTAS_PROJETO_SELECIONADAS:
        partes_estrutura.append(
            f'Estrutura do projeto selecionado ({pasta}):\n'
            f'{gerar_estrutura_projeto(pasta)}'
        )

    if not partes_arquivos and not partes_estrutura:
        raise ValueError('Não foi possível preparar arquivos ou pastas para enviar à IA.')

    regras = (
        'REGRAS OBRIGATÓRIAS:\n'
        '1. A estrutura da pasta é apenas uma lista de diretórios e nomes de arquivos; o conteúdo desses arquivos NÃO foi enviado.\n'
        '2. Somente os arquivos listados em CONTEÚDO DOS ARQUIVOS SELECIONADOS foram enviados com conteúdo completo.\n'
        '3. Modifique arquivos existentes somente quando seu conteúdo completo tiver sido enviado explicitamente. Não invente o conteúdo original de arquivos vistos apenas na estrutura.\n'
        '4. Se for necessário alterar um arquivo que aparece apenas na estrutura, peça ao usuário que selecione esse arquivo e envie novamente a solicitação.\n'
        '5. Você pode propor a criação de novos arquivos ou pastas dentro da pasta selecionada, usando os nomes e caminhos da estrutura como contexto.\n'
        '6. Retorne o código COMPLETO somente dos arquivos existentes explicitamente enviados que realmente precisar modificar.\n'
        '7. Antes de cada código, coloque exatamente ---> código: em uma linha separada.\n'
        '8. Não use cercas Markdown como ```java ou ```python.\n'
        '9. Depois do código de um arquivo existente, coloque ----> Modificar seguido do caminho completo exato.\n'
        '10. Para criar um arquivo novo, retorne o conteúdo completo precedido por ---> código: e finalize com --> Criar seguido do caminho completo do arquivo.\n'
        '11. Para criar uma pasta, escreva somente --> Criar seguido do caminho completo da pasta.\n'
        '12. Modifique ou crie recursos somente dentro das pastas selecionadas ou nos arquivos selecionados diretamente.\n'
        '13. Não é necessário retornar marcadores para arquivos que não precisam ser alterados.\n'
        '14. Não misture o conteúdo de arquivos diferentes, não invente caminhos e não inclua explicações entre os blocos de código.\n\n'
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

def interpretar_resposta(texto_resposta):

    """

    Interpreta marcadores de modificação e criação.

    Um marcador --> Criar sem código representa uma pasta.

    Um marcador --> Criar precedido por ---> código: representa um arquivo.

    """

    linhas = texto_resposta.splitlines()

    acoes = []

    codigo_atual = None

    linhas_codigo = []

    padrao_marcador = re.compile(

        r'^(----> Modificar |--> Criar )(.+?)\s*$'

    )

    for linha in linhas:

        if linha.strip() == '---> código:':

            if codigo_atual is not None:

                raise ValueError(

                    "Foi encontrado um novo marcador de código antes "

                    "do término do bloco anterior."

                )

            codigo_atual = True

            linhas_codigo = []

            continue

        correspondencia = padrao_marcador.match(linha)

        if correspondencia:

            tipo = correspondencia.group(1).strip()

            caminho = correspondencia.group(2).strip()

            if not caminho:

                raise ValueError("Foi encontrado um caminho vazio.")

            if codigo_atual is not None:

                conteudo = '\n'.join(linhas_codigo)

                if linhas_codigo and linhas_codigo[-1] == '':

                    conteudo = '\n'.join(linhas_codigo[:-1])

                acoes.append({

                    'tipo': 'modificar' if tipo == '----> Modificar'

                    else 'criar_arquivo',

                    'caminho': caminho,

                    'conteudo': conteudo

                })

                codigo_atual = None

                linhas_codigo = []

            elif tipo == '--> Criar':

                acoes.append({

                    'tipo': 'criar_pasta',

                    'caminho': caminho,

                    'conteudo': None

                })

            else:

                raise ValueError(

                    f"O marcador de modificação não possui código: "

                    f"{caminho}"

                )

            continue

        if codigo_atual is not None:

            linhas_codigo.append(linha)

    if codigo_atual is not None:

        raise ValueError(

            "Um bloco de código não possui marcador final de arquivo."

        )

    if not acoes:

        raise ValueError("Nenhuma ação válida foi encontrada na resposta.")

    return acoes

def validar_acoes(acoes, file_paths):
    """Valida destinos e impede alterações fora do escopo selecionado."""
    esperados = {chave_caminho(p) for p in file_paths}
    raizes = [os.path.normcase(os.path.normpath(os.path.abspath(p))) for p in PASTAS_PROJETO_SELECIONADAS]
    destinos = set()
    modificados = set()

    def esta_no_escopo(caminho):
        chave = chave_caminho(caminho)
        if chave in esperados:
            return True
        for raiz in raizes:
            try:
                if os.path.commonpath([raiz, chave]) == raiz:
                    return True
            except ValueError:
                continue
        return False

    for acao in acoes:
        caminho = acao['caminho']
        if not os.path.isabs(caminho):
            raise ValueError(f'O caminho precisa ser absoluto: {caminho}')

        caminho = os.path.normpath(caminho)
        acao['caminho'] = caminho
        chave = chave_caminho(caminho)

        if chave in destinos:
            raise ValueError(f'Destino repetido na resposta da IA: {caminho}')
        destinos.add(chave)

        if not esta_no_escopo(caminho):
            raise ValueError(f'A IA tentou acessar um caminho fora do escopo selecionado: {caminho}')

        if acao['tipo'] == 'modificar':
            if not os.path.isfile(caminho):
                raise ValueError(f'O arquivo a modificar não existe: {caminho}')
            if chave not in esperados:
                raise ValueError(
                    f'A IA tentou modificar um arquivo cujo conteúdo não foi enviado explicitamente: {caminho}. '
                    'Selecione esse arquivo individualmente para permitir sua modificação.'
                )
            modificados.add(chave)
        elif acao['tipo'] == 'criar_arquivo':
            if os.path.exists(caminho):
                raise ValueError(
                    f'O arquivo que a IA quer criar já existe: {caminho}. '
                    'Nenhum arquivo será sobrescrito automaticamente.'
                )
        elif acao['tipo'] == 'criar_pasta':
            if os.path.exists(caminho) and not os.path.isdir(caminho):
                raise ValueError(f'O destino da pasta já existe como arquivo: {caminho}')

    if not modificados and not any(a['tipo'] in ('criar_arquivo', 'criar_pasta') for a in acoes):
        raise ValueError('A resposta não contém nenhuma alteração ou criação válida.')

def aplicar_acoes(acoes, file_paths):

    """Cria pastas e arquivos e modifica os arquivos selecionados."""

    validar_acoes(acoes, file_paths)

    print("\nA IA solicitou as seguintes ações:")

    for acao in acoes:

        print(f"  [{acao['tipo']}] {acao['caminho']}")

    confirmacao = input(

        "\nDeseja executar todas essas ações? (s/N): "

    ).strip().lower()

    if confirmacao != 's':

        print("Operação cancelada. Nenhum arquivo foi alterado.")

        return

    conteudos_originais = {}

    arquivos_criados = []

    pastas_criadas = []

    try:

        caminhos_backup = {
            os.path.abspath(a['caminho'])
            for a in acoes if a['tipo'] == 'modificar'
        }
        for caminho in caminhos_backup:
            with open(caminho, 'r', encoding='utf-8', newline='') as f:
                conteudos_originais[caminho] = f.read()

        # Cria primeiro as pastas explicitamente solicitadas.

        for acao in acoes:

            if acao['tipo'] != 'criar_pasta':

                continue

            caminho = acao['caminho']

            faltantes = []

            atual = caminho

            while atual and not os.path.exists(atual):

                faltantes.append(atual)

                pai = os.path.dirname(atual)

                if pai == atual:

                    break

                atual = pai

            os.makedirs(caminho, exist_ok=True)

            for pasta in reversed(faltantes):

                pastas_criadas.append(pasta)

        # Cria arquivos novos, incluindo suas pastas intermediárias.

        for acao in acoes:

            if acao['tipo'] != 'criar_arquivo':

                continue

            caminho = acao['caminho']

            pasta_pai = os.path.dirname(caminho)

            faltantes = []

            atual = pasta_pai

            while atual and not os.path.exists(atual):

                faltantes.append(atual)

                pai = os.path.dirname(atual)

                if pai == atual:

                    break

                atual = pai

            os.makedirs(pasta_pai, exist_ok=True)

            for pasta in reversed(faltantes):

                if pasta not in pastas_criadas:

                    pastas_criadas.append(pasta)

            with open(caminho, 'x', encoding='utf-8', newline='') as f:

                f.write(acao['conteudo'])

            arquivos_criados.append(caminho)

        # Modifica os arquivos existentes somente após criar os novos.

        for acao in acoes:

            if acao['tipo'] != 'modificar':

                continue

            caminho = acao['caminho']

            with open(caminho, 'w', encoding='utf-8', newline='') as f:

                f.write(acao['conteudo'])

    except Exception as e:

        print(f"\n[ERRO] Falha ao executar as ações: {e}")

        print("Tentando restaurar os arquivos existentes...")

        erros = []

        for caminho, conteudo in conteudos_originais.items():

            try:

                with open(caminho, 'w', encoding='utf-8', newline='') as f:

                    f.write(conteudo)

            except Exception as erro:

                erros.append(f"{caminho}: {erro}")

        for caminho in reversed(arquivos_criados):

            try:

                if os.path.isfile(caminho):

                    os.remove(caminho)

            except Exception as erro:

                erros.append(f"{caminho}: {erro}")

        for caminho in reversed(pastas_criadas):

            try:

                if os.path.isdir(caminho) and not os.listdir(caminho):

                    os.rmdir(caminho)

            except Exception as erro:

                erros.append(f"{caminho}: {erro}")

        if erros:

            print("[ATENÇÃO] Algumas operações de recuperação falharam:")

            for erro in erros:

                print(f"  - {erro}")

        else:

            print("Os arquivos existentes foram restaurados.")

        return

    print("\n[SUCESSO] Operação concluída!")

    for acao in acoes:

        print(f"  [{acao['tipo']}] {acao['caminho']}")

def processar_resposta_e_modificar_arquivos(file_paths):

    """Lê a resposta copiada e aplica as ações validadas."""

    print("\n" + "=" * 60)

    print("[AGUARDANDO RESPOSTA DA IA]")

    print("1. Copie a resposta COMPLETA da IA.")

    print("2. Volte ao terminal e pressione ENTER.")

    print("Digite 'cancelar' para ignorar.")

    print("=" * 60)

    resposta = input("Pressione ENTER após copiar a resposta: ").strip()

    if resposta.lower() == 'cancelar':

        print("Operação cancelada.")

        return

    texto_resposta = pyperclip.paste()

    try:

        acoes = interpretar_resposta(texto_resposta)

        aplicar_acoes(acoes, file_paths)

    except ValueError as e:

        print(f"\n[ERRO] Resposta inválida: {e}")

        print("Nenhuma ação foi executada.")

def modo_1_multiplas_ias():

    print("\n--- MODO 1: Enviar mensagem para várias IAs ---")

    if not abrir_tres_sites():

        return

    while True:

        prompt = ler_prompt_multilinha()

        if prompt.strip().lower() in ['sair', 'voltar', 'exit']:

            break

        if not prompt.strip():

            print("Prompt vazio ignorado.")

            continue

        if enviar_para_varias_abas(prompt):

            print("Mensagem enviada para as três IAs.")

        else:

            print("Não foi possível enviar para todas as abas.")

            break

def modo_2_edicao_arquivos():

    print("\n--- MODO 2: Edição e criação de arquivos ---")

    while True:

        file_paths = selecionar_arquivos()

        if file_paths is None:

            return

        print("\nArquivos de contexto selecionados:")

        if PASTAS_PROJETO_SELECIONADAS:
            print("Pastas de projeto:")
            for pasta in PASTAS_PROJETO_SELECIONADAS:
                print(f"  - {pasta} (estrutura será enviada à IA)")

        if file_paths:
            print("Arquivos selecionados individualmente (conteúdo será enviado):")
            for caminho in file_paths:
                print(f"  - {caminho}")
        else:
            print("Nenhum arquivo individual selecionado; somente a estrutura das pastas será enviada.")

        atalho_aba = abrir_ia_escolhida()

        if atalho_aba == 'voltar':

            return

        if atalho_aba is None:

            continue

        while True:

            user_prompt = ler_prompt_multilinha()

            if user_prompt.strip().lower() in ['sair', 'voltar', 'exit']:

                break

            if not user_prompt.strip():

                print("Prompt vazio ignorado.")

                continue

            try:

                full_message = criar_prompt_edicao(

                    file_paths, user_prompt

                )

            except Exception as e:

                print(f"[ERRO] Não foi possível ler os arquivos: {e}")

                continue

            print("\n[OK] Enviando arquivos e solicitação para a IA...")

            if not enviar_para_uma_aba(full_message, atalho_aba):

                print("[ERRO] Não foi possível enviar a mensagem.")

                continue

            print("-> Solicitação enviada.")

            processar_resposta_e_modificar_arquivos(file_paths)

            print("\nO que deseja fazer agora?")

            print("1. Alterar novamente os mesmos arquivos")

            print("2. Escolher outros arquivos")

            print("3. Voltar ao menu principal")

            proxima_acao = input("Escolha uma opção [Padrão: 2]: ").strip()

            if proxima_acao == '1':

                continue

            if proxima_acao == '2':

                break

            if proxima_acao == '3':

                return

            print("Opção inválida. Voltando à seleção de arquivos.")

            break

def menu_principal():

    """Exibe o menu sem abrir sites automaticamente."""

    while True:

        print("\n========================================")

        print("   CHATAGENT - v3.0.0")

        print("========================================")

        print("1. Enviar mensagem para três IAs")

        print("2. Editar arquivos e criar pastas/arquivos com uma IA")

        print("0. Sair")

        opcao = input("\nEscolha uma opção: ").strip()

        if opcao == '1':

            modo_1_multiplas_ias()

        elif opcao == '2':

            modo_2_edicao_arquivos()

        elif opcao == '0':

            print("Encerrando automação.")

            break

        else:

            print("Opção inválida! Tente novamente.")

if __name__ == "__main__":

    menu_principal()
