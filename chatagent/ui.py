"""Utilitários de interface com o usuário via terminal."""

import os
import re

from chatagent import files as project_files


def ler_prompt_multilinha() -> str:
    """Lê um bloco de texto multilinha até o delimitador ``--env``."""
    print("\nDigite ou cole seu prompt abaixo.")
    print("Para enviar, digite '--env' em uma linha vazia.")
    print("Para sair digite 'sair' em uma linha vazia \ne após isso em uma linha vazia digite --env")

    linhas: list[str] = []
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
