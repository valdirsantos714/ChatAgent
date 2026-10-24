"""Interpretação da resposta da IA e aplicação das ações nos arquivos do projeto."""

import os
import re

import pyperclip

from chatagent import files as project_files


def chave_caminho(caminho: str) -> str:
    """Normaliza um caminho para comparação."""
    return os.path.normcase(os.path.normpath(os.path.abspath(caminho)))


PADRAO_INICIO_CODIGO = re.compile(r'^-{2,5}>\s*c[óo]digo\s*:?\s*$', re.IGNORECASE)
PADRAO_MARCADOR = re.compile(r'^-{2,5}>\s*(Modificar|Criar|Ler|Deletar|Excluir|Apagar)\s*:?\s+(.+?)\s*$', re.IGNORECASE)


def eh_arquivo_markdown(caminho: str | None) -> bool:
    """Verifica se o caminho se refere a um arquivo Markdown (.md, .markdown)."""
    if not caminho:
        return False
    nome = os.path.basename(caminho).lower()
    ext = os.path.splitext(nome)[1].lower()
    return ext in ('.md', '.markdown') or nome in ('readme', 'readme.md')


def limpar_linhas_codigo(linhas: list[str], caminho: str | None = None) -> str:
    """
    Remove linhas vazias extras e cercas Markdown (```).

    Para arquivos comuns (não Markdown), remove completamente quaisquer cercas ```
    ou crases residuais geradas pela IA, garantindo que nunca sejam inseridas no código.
    Para arquivos Markdown (.md), preserva os blocos ``` internos do documento,
    removendo apenas o invólucro externo caso a IA tenha envelopado todo o conteúdo em ```markdown ... ```.
    """
    if not linhas:
        return ""

    inicio = 0
    while inicio < len(linhas) and not linhas[inicio].strip():
        inicio += 1

    fim = len(linhas)
    while fim > inicio and not linhas[fim - 1].strip():
        fim -= 1

    linhas = linhas[inicio:fim]
    if not linhas:
        return ""

    eh_md = eh_arquivo_markdown(caminho)

    if eh_md:
        # Para arquivos Markdown, preserva ``` internos.
        # Remove apenas se a IA tiver envelopado toda a resposta em ```markdown ... ```
        primeira = linhas[0].strip().lower()
        ultima = linhas[-1].strip()
        if (primeira.startswith('```markdown') or primeira.startswith('```md') or primeira == '```') and ultima.startswith('```') and len(linhas) >= 2:
            linhas = linhas[1:-1]
    else:
        # Para arquivos que NÃO são Markdown: JAMAIS permitir linhas de cercas ```
        novas_linhas: list[str] = []
        for l in linhas:
            l_strip = l.strip()
            # Descarta linhas que iniciam cerca de markdown (ex: ```, ```java, ```python, etc.) ou formadas só de crases
            if re.match(r'^`{3,}', l_strip) or (l_strip.startswith('`') and set(l_strip) == {'`'}):
                continue
            # Se a linha contiver cercas markdown residuais no final ou isoladas (ex: trecho```), remove
            if '```' in l:
                l = re.sub(r'\s*`{3,}\w*\s*', ' ', l).rstrip()
            novas_linhas.append(l)
        linhas = novas_linhas

    inicio = 0
    while inicio < len(linhas) and not linhas[inicio].strip():
        inicio += 1
    fim = len(linhas)
    while fim > inicio and not linhas[fim - 1].strip():
        fim -= 1

    linhas = linhas[inicio:fim]
    return "\n".join(linhas)


def eh_caminho_placeholder(caminho: str) -> bool:
    """Verifica se o caminho é apenas um exemplo ilustrativo ou placeholder (ex: <caminho>)."""
    c = caminho.strip().lower()
    if '<' in c or '>' in c:
        return True
    if 'caminho_absoluto' in c or 'caminho_do_arquivo' in c or 'caminho/do/arquivo' in c:
        return True
    return False


def interpretar_resposta(texto_resposta: str) -> tuple[list[dict], list[str]]:
    """
    Interpreta marcadores de modificação, criação, deleção e leitura na resposta da IA.

    Suporta marcadores posicionados antes ou depois do código, variações de traços
    (--, ---, ----) e não falha se a IA aninhar blocos ou esquecer marcadores intermediários.

    Retorna uma tupla ``(acoes, leituras)`` onde:
    - ``acoes`` é a lista de ações a aplicar nos arquivos do projeto.
    - ``leituras`` é a lista de caminhos de arquivo que a IA solicitou ler.
    """
    linhas = texto_resposta.splitlines()
    acoes: list[dict] = []
    leituras: list[str] = []
    codigo_atual = False
    linhas_codigo: list[str] = []
    comando_pendente: dict | None = None

    def fechar_bloco_codigo(linhas_bloco: list[str], destino: dict | None) -> None:
        nonlocal comando_pendente
        if destino is None:
            # Verifica se dentro das linhas havia algum marcador não capturado
            for idx, l in enumerate(linhas_bloco):
                m = PADRAO_MARCADOR.match(l.strip())
                if m:
                    v = m.group(1).title()
                    if v in ['Excluir', 'Apagar']:
                        v = 'Deletar'
                    c = m.group(2).strip().strip('`"\' ')
                    if eh_caminho_placeholder(c):
                        continue
                    if v in ['Modificar', 'Criar']:
                        conteudo_parte = limpar_linhas_codigo(linhas_bloco[:idx], caminho=c)
                        t = 'modificar' if v == 'Modificar' else 'criar_arquivo'
                        acoes.append({'tipo': t, 'caminho': c, 'conteudo': conteudo_parte})
                        return
                    elif v == 'Deletar':
                        acoes.append({'tipo': 'deletar_arquivo', 'caminho': c, 'conteudo': None})
                        return

            conteudo_restante = limpar_linhas_codigo(linhas_bloco)
            if conteudo_restante:
                print("[AVISO] Bloco de código ignorado por falta de comando de arquivo associado.")
            return

        if eh_caminho_placeholder(destino['caminho']):
            print(f"[AVISO] Exemplo genérico ilustrativo ignorado: {destino['caminho']}")
            comando_pendente = None
            return

        caminho_destino = destino['caminho']
        verbo_destino = destino['verbo']

        if verbo_destino == 'Deletar':
            acoes.append({'tipo': 'deletar_arquivo', 'caminho': caminho_destino, 'conteudo': None})
        else:
            conteudo = limpar_linhas_codigo(linhas_bloco, caminho=caminho_destino)
            tipo = 'modificar' if verbo_destino == 'Modificar' else 'criar_arquivo'
            acoes.append({
                'tipo': tipo,
                'caminho': caminho_destino,
                'conteudo': conteudo
            })
        comando_pendente = None

    for linha in linhas:
        linha_limpa = linha.strip()

        # Verifica se é início de bloco de código
        if PADRAO_INICIO_CODIGO.match(linha_limpa):
            if codigo_atual:
                # A IA abriu um novo bloco antes de fechar o anterior: fecha com o que tínhamos!
                fechar_bloco_codigo(linhas_codigo, comando_pendente)
                linhas_codigo = []
            codigo_atual = True
            continue

        # Verifica se é marcador de comando ou leitura
        correspondencia = PADRAO_MARCADOR.match(linha_limpa)
        if correspondencia:
            verbo = correspondencia.group(1).title()
            if verbo in ('Excluir', 'Apagar'):
                verbo = 'Deletar'
            caminho = correspondencia.group(2).strip().strip('`"\' ')

            if not caminho or eh_caminho_placeholder(caminho):
                if eh_caminho_placeholder(caminho):
                    print(f"[AVISO] Exemplo genérico ilustrativo ignorado: {caminho}")
                continue

            if verbo == 'Ler':
                leituras.append(caminho)
                continue

            if verbo == 'Deletar':
                if codigo_atual:
                    fechar_bloco_codigo(linhas_codigo, comando_pendente)
                    codigo_atual = False
                    linhas_codigo = []
                    comando_pendente = None
                elif comando_pendente is not None and comando_pendente['verbo'] == 'Criar':
                    acoes.append({
                        'tipo': 'criar_pasta',
                        'caminho': comando_pendente['caminho'],
                        'conteudo': None
                    })
                    comando_pendente = None

                acoes.append({
                    'tipo': 'deletar_arquivo',
                    'caminho': caminho,
                    'conteudo': None
                })
                continue

            # Se estamos em bloco de código, o marcador finalizou este bloco (formato padrão: código depois comando)
            if codigo_atual:
                fechar_bloco_codigo(linhas_codigo, {'verbo': verbo, 'caminho': caminho})
                codigo_atual = False
                linhas_codigo = []
                comando_pendente = None
            else:
                # O marcador veio ANTES do código ou é criação de pasta
                if comando_pendente is not None and comando_pendente['verbo'] == 'Criar':
                    acoes.append({
                        'tipo': 'criar_pasta',
                        'caminho': comando_pendente['caminho'],
                        'conteudo': None
                    })
                comando_pendente = {'verbo': verbo, 'caminho': caminho}
            continue

        if codigo_atual:
            linhas_codigo.append(linha)

    # Final do texto: se ainda havia código aberto, fecha
    if codigo_atual:
        fechar_bloco_codigo(linhas_codigo, comando_pendente)
        comando_pendente = None

    # Se sobrou comando pendente sem código (ex: criar pasta)
    if comando_pendente is not None:
        if comando_pendente['verbo'] == 'Criar':
            acoes.append({
                'tipo': 'criar_pasta',
                'caminho': comando_pendente['caminho'],
                'conteudo': None
            })
        elif comando_pendente['verbo'] == 'Deletar':
            acoes.append({
                'tipo': 'deletar_arquivo',
                'caminho': comando_pendente['caminho'],
                'conteudo': None
            })
        comando_pendente = None

    if not acoes and not leituras:
        raise ValueError("Nenhuma ação ou solicitação de leitura válida foi encontrada na resposta.")

    return acoes, leituras


def validar_acoes(acoes: list[dict], file_paths: list[str]) -> None:
    """Valida destinos e impede alterações fora do escopo selecionado."""
    esperados = {chave_caminho(p) for p in file_paths}
    raizes = [
        os.path.normcase(os.path.normpath(os.path.abspath(p)))
        for p in project_files.PASTAS_PROJETO_SELECIONADAS
    ]
    destinos: set[str] = set()
    modificados: set[str] = set()
    deletados: set[str] = set()

    def esta_no_escopo(caminho: str) -> bool:
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
            modificados.add(chave)
        elif acao['tipo'] == 'criar_arquivo':
            if os.path.exists(caminho):
                # Se o arquivo já existe no escopo, trata como modificação
                acao['tipo'] = 'modificar'
                modificados.add(chave)
        elif acao['tipo'] == 'criar_pasta':
            if os.path.exists(caminho) and not os.path.isdir(caminho):
                raise ValueError(f'O destino da pasta já existe como arquivo: {caminho}')
        elif acao['tipo'] == 'deletar_arquivo':
            if not os.path.exists(caminho):
                raise ValueError(f'O arquivo a deletar não existe: {caminho}')
            if os.path.isdir(caminho):
                raise ValueError(f'O caminho a deletar é um diretório, use apenas para arquivos: {caminho}')
            deletados.add(chave)

    if not modificados and not deletados and not any(a['tipo'] in ('criar_arquivo', 'criar_pasta') for a in acoes):
        raise ValueError('A resposta não contém nenhuma alteração, criação ou deleção válida.')


def aplicar_acoes(acoes: list[dict], file_paths: list[str]) -> None:
    """Cria pastas e arquivos, modifica e deleta os arquivos selecionados."""
    validar_acoes(acoes, file_paths)

    print("\nA IA solicitou as seguintes ações:")
    for acao in acoes:
        print(f"  [{acao['tipo']}] {acao['caminho']}")

    confirmacao = input("\nDeseja executar todas essas ações? (s/N): ").strip().lower()
    if confirmacao != 's':
        print("Operação cancelada. Nenhum arquivo foi alterado.")
        return

    conteudos_originais: dict[str, str] = {}
    arquivos_criados: list[str] = []
    pastas_criadas: list[str] = []
    arquivos_deletados: list[str] = []

    try:
        caminhos_backup = {
            os.path.abspath(a['caminho'])
            for a in acoes if a['tipo'] in ('modificar', 'deletar_arquivo')
        }
        for caminho in caminhos_backup:
            with open(caminho, 'r', encoding='utf-8', newline='') as f:
                conteudos_originais[caminho] = f.read()

        # Cria primeiro as pastas explicitamente solicitadas.
        for acao in acoes:
            if acao['tipo'] != 'criar_pasta':
                continue

            caminho = acao['caminho']
            faltantes: list[str] = []
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

        # Deleta os arquivos solicitados após modificações e criações.
        for acao in acoes:
            if acao['tipo'] != 'deletar_arquivo':
                continue
            caminho = acao['caminho']
            if os.path.isfile(caminho):
                os.remove(caminho)
                arquivos_deletados.append(caminho)

    except Exception as e:
        print(f"\n[ERRO] Falha ao executar as ações: {e}")
        print("Tentando restaurar os arquivos existentes...")

        erros: list[str] = []

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


def limpar_buffer_teclado() -> None:
    """Esvazia o buffer de entrada do console no Windows para evitar que texto colado vaze para outros menus."""
    try:
        import msvcrt
        while msvcrt.kbhit():
            msvcrt.getch()
    except Exception:
        pass


ARQUIVO_RESPOSTA_PADRAO = "resposta_ia.txt"


def obter_resposta_da_ia() -> str:
    """
    Obtém a resposta da IA de forma segura, suportando:
    1. Área de transferência (o usuário apenas copia na IA e aperta Enter).
    2. Arquivo 'resposta_ia.txt' (ideal quando a resposta for gigantesca ou o usuário preferir).
    3. Proteção automática caso o usuário cole texto no terminal por engano.
    """
    print("\n" + "=" * 65)
    print("                 [AGUARDANDO A RESPOSTA DA IA]")
    print("=" * 65)
    print("Opção 1 (Recomendada - Rápida e sem limites):")
    print("  1. No navegador, copie a resposta da IA (botão Copiar ou Ctrl+C).")
    print("  2. Volte aqui e APENAS APERTE ENTER (deixe o campo em branco).")
    print("     -> O ChatAgent lê direto da memória com 100% dos dados completos!")
    print()
    print("Opção 2 (Via arquivo para respostas gigantescas):")
    print(f"  1. Cole a resposta dentro do arquivo '{ARQUIVO_RESPOSTA_PADRAO}'.")
    print("  2. Digite 'arquivo' (ou 'f') aqui e aperte ENTER.")
    print("=" * 65)
    print("Digite 'cancelar' para ignorar.")

    entrada = input("\nPressione ENTER para ler do Ctrl+C [ou digite 'f' para ele ler do arquivo (file) 'resposta_ia.txt']: ").strip()
    
    # Se o usuário colou texto longo diretamente no terminal, descarta o excesso do buffer do teclado
    if len(entrada) > 80 or "\n" in entrada:
        limpar_buffer_teclado()

    if entrada.lower() == 'cancelar':
        return ""

    if entrada.lower() in ['arquivo', 'f', 'file', 'txt']:
        caminho_arq = os.path.abspath(ARQUIVO_RESPOSTA_PADRAO)
        if not os.path.isfile(caminho_arq) or os.path.getsize(caminho_arq) == 0:
            try:
                with open(caminho_arq, "w", encoding="utf-8") as f:
                    pass
            except Exception:
                pass
            print(f"\n[INFO] O arquivo '{ARQUIVO_RESPOSTA_PADRAO}' foi preparado.")
            print(f"Cole a resposta da IA dentro dele ({caminho_arq}), salve o arquivo")
            input("e pressione ENTER aqui no terminal para continuar: ")

        try:
            with open(caminho_arq, "r", encoding="utf-8-sig") as f:
                conteudo = f.read()
            if conteudo.strip():
                print(f"[OK] {len(conteudo)} caracteres lidos com sucesso de '{ARQUIVO_RESPOSTA_PADRAO}'.")
                return conteudo
            print("[AVISO] O arquivo está vazio. Tentando ler da área de transferência...")
        except Exception as e:
            print(f"[ERRO] Falha ao ler '{ARQUIVO_RESPOSTA_PADRAO}': {e}. Usando área de transferência...")

    texto = pyperclip.paste()
    if texto and texto.strip():
        print(f"[OK] {len(texto)} caracteres lidos da memória (Ctrl+C).")
        return texto

    # Se o clipboard estiver vazio mas veio algo na digitação
    if entrada:
        return entrada

    print("[AVISO] A área de transferência parece vazia. Copie a resposta da IA novamente (Ctrl+C).")
    return ""


def processar_resposta_e_modificar_arquivos(file_paths: list[str]) -> list[str]:
    """
    Lê a resposta copiada da área de transferência ou arquivo e aplica as ações validadas.

    Retorna a lista de caminhos de arquivo que a IA solicitou ler via ``---> Ler``.
    Uma lista vazia indica que não há pedidos de leitura pendentes.
    """
    texto_resposta = obter_resposta_da_ia()

    if not texto_resposta or not texto_resposta.strip():
        print("Operação cancelada ou nenhuma resposta recebida.")
        return []

    try:
        acoes, leituras = interpretar_resposta(texto_resposta)
    except ValueError as e:
        print(f"\n[ERRO] Resposta inválida: {e}")
        print("Nenhuma ação foi executada.")
        return []

    if acoes:
        try:
            aplicar_acoes(acoes, file_paths)
        except ValueError as e:
            print(f"\n[AVISO] Validação das ações: {e}")
            print("Nenhuma alteração foi realizada nos arquivos.")
        except Exception as e:
            print(f"\n[ERRO] Falha ao aplicar ações: {e}")

    if leituras:
        print("\n[LEITURA] A IA solicitou o conteúdo dos seguintes arquivos:")
        for caminho in leituras:
            print(f"  - {caminho}")

    return leituras
