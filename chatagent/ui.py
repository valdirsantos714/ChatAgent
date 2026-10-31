"""Utilitários de interface com o usuário via terminal."""

import os
import re

from chatagent import files as project_files


ARQUIVO_PROMPT = "prompt.txt"


def ler_prompt_multilinha() -> str:
    """Lê um bloco de texto multilinha até o delimitador ``--env``.

    Para prompts grandes, o usuário pode digitar ``'f'`` ou ``'arquivo'`` para
    carregar o conteúdo do arquivo ``prompt.txt``, no mesmo estilo do
    ``resposta_ia.txt``.
    """
    print("\n" + "=" * 65)
    print("                    [AGUARDANDO O PROMPT]")
    print("=" * 65)
    print("Opção 1 – Digitar aqui no terminal:")
    print("  Digite ou cole seu prompt abaixo.")
    print("  Para enviar, digite '--env' em uma linha vazia.")
    print("  Para sair, digite 'sair' e depois '--env'.")
    print()
    print("Opção 2 – Via arquivo para prompts grandes:")
    print(f"  1. Salve o prompt dentro do arquivo '{ARQUIVO_PROMPT}'.")
    print("  2. Digite 'f' ou 'arquivo' aqui e pressione ENTER.")
    print("=" * 65)

    primeira_linha = input().strip()

    # Usuário quer usar o arquivo
    if primeira_linha.lower() in ['f', 'arquivo', 'file', 'txt']:
        caminho_arq = os.path.abspath(ARQUIVO_PROMPT)
        if not os.path.isfile(caminho_arq) or os.path.getsize(caminho_arq) == 0:
            try:
                open(caminho_arq, 'w', encoding='utf-8').close()
            except Exception:
                pass
            print(f"\n[INFO] Arquivo '{ARQUIVO_PROMPT}' preparado em:\n  {caminho_arq}")
            print("Salve o seu prompt dentro dele")
            input("e pressione ENTER aqui para continuar: ")

        try:
            with open(caminho_arq, 'r', encoding='utf-8-sig') as f:
                conteudo = f.read()
            if conteudo.strip():
                print(f"[OK] {len(conteudo):,} caracteres lidos de '{ARQUIVO_PROMPT}'.")
                return conteudo
            print(f"[AVISO] '{ARQUIVO_PROMPT}' está vazio. Continuando com digitação manual...")
        except Exception as e:
            print(f"[ERRO] Não foi possível ler '{ARQUIVO_PROMPT}': {e}. Continuando...")

    # Digitação manual: a primeira linha já foi lida, continua o restante
    linhas: list[str] = []
    if primeira_linha and primeira_linha.strip() != '--env':
        linhas.append(primeira_linha)

    if primeira_linha.strip() != '--env':
        while True:
            try:
                linha = input()
                if linha.strip() == '--env':
                    break
                linhas.append(linha)
            except EOFError:
                break

    return '\n'.join(linhas)


def separar_caminhos(entrada: str) -> list[str]:
    """Separa caminhos por vírgulas ou quebras de linha, removendo duplicatas."""
    caminhos = re.split(r'[,\r\n]+', entrada)
    resultado: list[str] = []
    vistos: set[str] = set()

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


def selecionar_arquivos() -> list[str] | None:
    """Aceita arquivos e pastas de projeto e prepara o contexto para a IA."""
    while True:
        print("\nInforme os caminhos dos arquivos ou pastas de projeto que deseja modificar.")
        print("Separe os caminhos por vírgulas ou quebras de linha.")
        print(r'Exemplo de arquivo: D:\Projeto\src\Main.java')
        print(r'Exemplo de pasta: D:\Projeto')
        print("Ao informar uma pasta, será enviada somente a estrutura do projeto, sem o conteúdo dos arquivos.")
        print("Para enviar o conteúdo de um arquivo, informe o caminho desse arquivo separadamente.")
        print("Digite '--env' em uma linha vazia para confirmar.")
        print("Digite 'voltar' para retornar ao menu principal.")

        linhas: list[str] = []
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
        project_files.PASTAS_PROJETO_SELECIONADAS = pastas

        unicos: list[str] = []
        vistos: set[str] = set()
        for caminho in arquivos:
            chave = os.path.normcase(os.path.normpath(caminho))
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(caminho)

        if not unicos and not pastas:
            print('[ERRO] Informe pelo menos um arquivo ou pasta válida.')
            continue

        return unicos
