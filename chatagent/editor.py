"""Interpretação da resposta da IA e aplicação das ações nos arquivos do projeto."""

import os
import re
import shutil

import pyperclip

from chatagent import files as project_files


def chave_caminho(caminho: str) -> str:
    """Normaliza um caminho para comparação."""
    return os.path.normcase(os.path.normpath(os.path.abspath(caminho)))


PADRAO_INICIO_CODIGO = re.compile(
    r'^(?:[\s/\\#*>\-]|<!--)*-{2,5}>\s*\*?c[óo]digo\s*\*?:?[\\/\s\-*>]*(?:-->)?$',
    re.IGNORECASE
)
PADRAO_MARCADOR = re.compile(
    r'^(?:[\s/\\#*>\-]|<!--)*-{2,5}>\s*\*?(Modificar\s+arquivo|Modificar|Criar\s+arquivo|Criar\s+pasta|Criar\s+diret[óo]rio|Criar_arquivo|Criar_pasta|Criar_diret[óo]rio|Criar|Deletar\s+arquivo|Deletar\s+pasta|Deletar_arquivo|Deletar_pasta|Deletar|Excluir\s+arquivo|Excluir\s+pasta|Excluir|Apagar\s+arquivo|Apagar\s+pasta|Apagar|Remover\s+arquivo|Remover\s+pasta|Remover|Ler\s+arquivo|Ler)\s*\*?:?\s+(.+?)\s*\*?(?:-->)?$',
    re.IGNORECASE
)


def normalizar_verbo(verbo_bruto: str) -> str:
    """Normaliza o verbo extraído pelo PADRAO_MARCADOR."""
    v = verbo_bruto.strip().lower().replace('_', ' ')
    if 'criar pasta' in v or 'criar diretorio' in v or 'criar diretório' in v:
        return 'Criar_Pasta'
    if 'criar arquivo' in v:
        return 'Criar_Arquivo'
    if v == 'criar':
        return 'Criar'
    if 'modificar' in v or 'alterar' in v or 'editar' in v or 'atualizar' in v:
        return 'Modificar'
    if 'ler' in v:
        return 'Ler'
    if any(p in v for p in ['deletar pasta', 'excluir pasta', 'apagar pasta', 'remover pasta']):
        return 'Deletar_Pasta'
    if any(p in v for p in ['deletar arquivo', 'excluir arquivo', 'apagar arquivo', 'remover arquivo']):
        return 'Deletar_Arquivo'
    if any(p in v for p in ['deletar', 'excluir', 'apagar', 'remover']):
        return 'Deletar'
    return verbo_bruto.title()


def eh_provavel_arquivo(caminho: str) -> bool:
    """Verifica se o caminho se parece com um arquivo (possui extensão)."""
    nome = os.path.basename(caminho.rstrip('\\/ '))
    ext = os.path.splitext(nome)[1]
    return bool(ext)


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

    # Remove barras invertidas (\) residuais de escape no fim das linhas
    novas_linhas = []
    for l in linhas:
        # Descarta linha que contenha apenas barras invertidas
        if set(l.strip()) == {'\\'}:
            continue
        # Remove barras invertidas no final da linha (escape de quebra de linha gerado pela IA)
        l = re.sub(r'\\+\s*$', '', l)
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

    Suporta:
    - Criação explícita de arquivos: ``--> Criar arquivo <caminho>``
    - Criação explícita de pastas: ``--> Criar pasta <caminho>``
    - Marcador legado: ``--> Criar <caminho>`` (detecta arquivo via código/extensão ou pasta)
    - Modificação: ``----> Modificar <caminho>``
    - Deleção: ``--> Deletar arquivo <caminho>``, ``--> Deletar pasta <caminho>`` ou ``--> Deletar <caminho>``
    - Leitura: ``---> Ler <caminho>``
    - Marcadores antes ou depois do código, variações de prefixo (#, //, *, etc.).

    Retorna uma tupla ``(acoes, leituras)`` onde:
    - ``acoes`` é a lista de ações a aplicar nos arquivos do projeto.
    - ``leituras`` é a lista de caminhos de arquivo que a IA solicitou ler.
    """
    linhas = texto_resposta.splitlines()
    acoes: list[dict] = []
    leituras: list[str] = []
    codigo_atual = False
    linhas_codigo: list[str] = []
    linhas_buffer: list[str] = []
    comando_pendente: dict | None = None

    def fechar_bloco_codigo(linhas_bloco: list[str], destino: dict | None) -> None:
        nonlocal comando_pendente
        if destino is None:
            # Verifica se dentro das linhas havia algum marcador não capturado
            for idx, l in enumerate(linhas_bloco):
                m = PADRAO_MARCADOR.match(l.strip())
                if m:
                    v = normalizar_verbo(m.group(1))
                    c = m.group(2).strip().strip('`"\'* ')
                    if c.endswith(('\\', '/')) and not re.match(r'^[a-zA-Z]:[\\/]+$', c):
                        c = c.rstrip('\\/ ')
                    if eh_caminho_placeholder(c):
                        continue
                    if v == 'Criar_Pasta':
                        acoes.append({'tipo': 'criar_pasta', 'caminho': c, 'conteudo': None})
                        return
                    elif v in ('Criar_Arquivo', 'Modificar', 'Criar'):
                        conteudo_parte = limpar_linhas_codigo(linhas_bloco[:idx], caminho=c)
                        t = 'modificar' if v == 'Modificar' else 'criar_arquivo'
                        acoes.append({'tipo': t, 'caminho': c, 'conteudo': conteudo_parte})
                        return
                    elif v in ('Deletar', 'Deletar_Arquivo', 'Deletar_Pasta'):
                        t = 'deletar_pasta' if v == 'Deletar_Pasta' else ('deletar_arquivo' if v == 'Deletar_Arquivo' else 'deletar')
                        acoes.append({'tipo': t, 'caminho': c, 'conteudo': None})
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

        if verbo_destino == 'Criar_Pasta':
            acoes.append({'tipo': 'criar_pasta', 'caminho': caminho_destino, 'conteudo': None})
        elif verbo_destino in ('Deletar', 'Deletar_Arquivo', 'Deletar_Pasta'):
            t = 'deletar_pasta' if verbo_destino == 'Deletar_Pasta' else ('deletar_arquivo' if verbo_destino == 'Deletar_Arquivo' else 'deletar')
            acoes.append({'tipo': t, 'caminho': caminho_destino, 'conteudo': None})
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
                fechar_bloco_codigo(linhas_codigo, comando_pendente)
                linhas_codigo = []
            elif comando_pendente is not None and comando_pendente['verbo'] == 'Criar_Pasta':
                acoes.append({
                    'tipo': 'criar_pasta',
                    'caminho': comando_pendente['caminho'],
                    'conteudo': None
                })
                comando_pendente = None
            codigo_atual = True
            linhas_buffer = []
            continue

        # Verifica se é marcador de comando ou leitura
        correspondencia = PADRAO_MARCADOR.match(linha_limpa)
        if correspondencia:
            verbo = normalizar_verbo(correspondencia.group(1))
            caminho = correspondencia.group(2).strip().strip('`"\'* ')
            if caminho.endswith(('\\', '/')) and not re.match(r'^[a-zA-Z]:[\\/]+$', caminho):
                caminho = caminho.rstrip('\\/ ')

            if not caminho or eh_caminho_placeholder(caminho):
                if eh_caminho_placeholder(caminho):
                    print(f"[AVISO] Exemplo genérico ilustrativo ignorado: {caminho}")
                continue

            if verbo == 'Ler':
                leituras.append(caminho)
                continue

            if verbo in ('Deletar', 'Deletar_Arquivo', 'Deletar_Pasta'):
                if codigo_atual:
                    fechar_bloco_codigo(linhas_codigo, comando_pendente)
                    codigo_atual = False
                    linhas_codigo = []
                    comando_pendente = None
                elif comando_pendente is not None and comando_pendente['verbo'] == 'Criar_Pasta':
                    acoes.append({
                        'tipo': 'criar_pasta',
                        'caminho': comando_pendente['caminho'],
                        'conteudo': None
                    })
                    comando_pendente = None

                tipo_del = 'deletar_pasta' if verbo == 'Deletar_Pasta' else ('deletar_arquivo' if verbo == 'Deletar_Arquivo' else 'deletar')
                acoes.append({
                    'tipo': tipo_del,
                    'caminho': caminho,
                    'conteudo': None
                })
                linhas_buffer = []
                continue

            if verbo == 'Criar_Pasta':
                if codigo_atual:
                    fechar_bloco_codigo(linhas_codigo, comando_pendente)
                    codigo_atual = False
                    linhas_codigo = []
                    comando_pendente = None
                elif comando_pendente is not None and comando_pendente['verbo'] == 'Criar_Pasta':
                    acoes.append({
                        'tipo': 'criar_pasta',
                        'caminho': comando_pendente['caminho'],
                        'conteudo': None
                    })
                    comando_pendente = None

                acoes.append({
                    'tipo': 'criar_pasta',
                    'caminho': caminho,
                    'conteudo': None
                })
                linhas_buffer = []
                continue

            # Para comandos que criam arquivos ou modificam (Criar_Arquivo, Modificar, Criar):
            if codigo_atual:
                # Código veio ANTES do comando (formato padrão)
                fechar_bloco_codigo(linhas_codigo, {'verbo': verbo, 'caminho': caminho})
                codigo_atual = False
                linhas_codigo = []
                comando_pendente = None
                linhas_buffer = []
            elif any(l.strip() for l in linhas_buffer):
                # A IA gerou o conteúdo mas esqueceu do marcador inicial ---> código:
                fechar_bloco_codigo(linhas_buffer, {'verbo': verbo, 'caminho': caminho})
                linhas_buffer = []
                comando_pendente = None
            else:
                # Comando veio ANTES do código
                if comando_pendente is not None and comando_pendente['verbo'] == 'Criar_Pasta':
                    acoes.append({
                        'tipo': 'criar_pasta',
                        'caminho': comando_pendente['caminho'],
                        'conteudo': None
                    })
                comando_pendente = {'verbo': verbo, 'caminho': caminho}
                linhas_buffer = []
            continue

        if codigo_atual:
            linhas_codigo.append(linha)
        else:
            linhas_buffer.append(linha)

    # Final do texto: se ainda havia código aberto, fecha
    if codigo_atual:
        fechar_bloco_codigo(linhas_codigo, comando_pendente)
        comando_pendente = None

    # Se sobrou comando pendente sem código explícito
    if comando_pendente is not None:
        caminho_pend = comando_pendente['caminho']
        verbo_pend = comando_pendente['verbo']
        if verbo_pend == 'Criar_Pasta':
            acoes.append({
                'tipo': 'criar_pasta',
                'caminho': caminho_pend,
                'conteudo': None
            })
        elif verbo_pend == 'Criar_Arquivo':
            conteudo = limpar_linhas_codigo(linhas_buffer, caminho=caminho_pend) if any(l.strip() for l in linhas_buffer) else ""
            acoes.append({
                'tipo': 'criar_arquivo',
                'caminho': caminho_pend,
                'conteudo': conteudo
            })
        elif verbo_pend == 'Criar':
            # Formato legado: se há buffer de texto ou caminho parece arquivo, cria arquivo; senão pasta
            tem_buffer = any(l.strip() for l in linhas_buffer)
            if tem_buffer or eh_provavel_arquivo(caminho_pend):
                conteudo = limpar_linhas_codigo(linhas_buffer, caminho=caminho_pend) if tem_buffer else ""
                acoes.append({
                    'tipo': 'criar_arquivo',
                    'caminho': caminho_pend,
                    'conteudo': conteudo
                })
            else:
                acoes.append({
                    'tipo': 'criar_pasta',
                    'caminho': caminho_pend,
                    'conteudo': None
                })
        elif verbo_pend == 'Modificar':
            conteudo = limpar_linhas_codigo(linhas_buffer, caminho=caminho_pend) if any(l.strip() for l in linhas_buffer) else ""
            acoes.append({
                'tipo': 'modificar',
                'caminho': caminho_pend,
                'conteudo': conteudo
            })
        elif verbo_pend in ('Deletar', 'Deletar_Arquivo', 'Deletar_Pasta'):
            tipo_del = 'deletar_pasta' if verbo_pend == 'Deletar_Pasta' else ('deletar_arquivo' if verbo_pend == 'Deletar_Arquivo' else 'deletar')
            acoes.append({
                'tipo': tipo_del,
                'caminho': caminho_pend,
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
            if os.path.isdir(caminho):
                if not os.listdir(caminho):
                    # Pasta vazia existente (ex: criada por erro anterior). Será substituída em aplicar_acoes
                    pass
                else:
                    raise ValueError(f'O destino do arquivo já existe como uma pasta não vazia: {caminho}')
            elif os.path.isfile(caminho):
                # Se o arquivo já existe no escopo, trata como modificação
                acao['tipo'] = 'modificar'
                modificados.add(chave)
        elif acao['tipo'] == 'criar_pasta':
            if os.path.exists(caminho) and not os.path.isdir(caminho):
                raise ValueError(f'O destino da pasta já existe como arquivo: {caminho}')
        elif acao['tipo'] in ('deletar', 'deletar_arquivo', 'deletar_pasta'):
            if not os.path.exists(caminho):
                raise ValueError(f'O arquivo ou pasta a deletar não existe: {caminho}')
            if os.path.isdir(caminho):
                if any(chave == raiz for raiz in raizes):
                    raise ValueError(f'Não é permitido deletar a pasta raiz do projeto: {caminho}')
                acao['tipo'] = 'deletar_pasta'
            else:
                acao['tipo'] = 'deletar_arquivo'
            deletados.add(chave)

    if not modificados and not deletados and not any(a['tipo'] in ('criar_arquivo', 'criar_pasta') for a in acoes):
        raise ValueError('A resposta não contém nenhuma alteração, criação ou deleção válida.')


def aplicar_acoes(acoes: list[dict], file_paths: list[str]) -> None:
    """Cria pastas e arquivos, modifica e deleta os arquivos ou pastas selecionadas."""
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
    pastas_deletadas: list[str] = []

    backup_arquivos_deletados: dict[str, bytes] = {}
    backup_pastas_deletadas: dict[str, dict] = {}

    try:
        # Backup de arquivos a serem modificados
        for acao in acoes:
            if acao['tipo'] == 'modificar':
                caminho = os.path.abspath(acao['caminho'])
                with open(caminho, 'r', encoding='utf-8', newline='') as f:
                    conteudos_originais[caminho] = f.read()

        # Backup de arquivos individuais a serem deletados (em bytes para fidelidade total)
        for acao in acoes:
            if acao['tipo'] == 'deletar_arquivo':
                caminho = os.path.abspath(acao['caminho'])
                if os.path.isfile(caminho):
                    with open(caminho, 'rb') as f:
                        backup_arquivos_deletados[caminho] = f.read()

        # Backup de pastas a serem deletadas (estrutura de subpastas e todos os arquivos internos em memória)
        for acao in acoes:
            if acao['tipo'] == 'deletar_pasta':
                caminho_pasta = os.path.abspath(acao['caminho'])
                subpastas: list[str] = []
                arquivos_pasta: dict[str, bytes] = {}
                if os.path.isdir(caminho_pasta):
                    for raiz, dirs, files in os.walk(caminho_pasta):
                        for d in dirs:
                            subpastas.append(os.path.abspath(os.path.join(raiz, d)))
                        for f in files:
                            arq = os.path.abspath(os.path.join(raiz, f))
                            with open(arq, 'rb') as f_arq:
                                arquivos_pasta[arq] = f_arq.read()
                backup_pastas_deletadas[caminho_pasta] = {
                    'subpastas': subpastas,
                    'arquivos': arquivos_pasta,
                }

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
            # Se já existir uma pasta vazia com o mesmo nome do arquivo, remove-a antes de criar
            if os.path.isdir(caminho) and not os.listdir(caminho):
                print(f"[INFO] Substituindo pasta vazia existente pelo arquivo: {caminho}")
                os.rmdir(caminho)

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

        # Deleta as pastas solicitadas recursivamente com shutil.rmtree.
        for acao in acoes:
            if acao['tipo'] != 'deletar_pasta':
                continue
            caminho = acao['caminho']
            if os.path.isdir(caminho):
                shutil.rmtree(caminho)
                pastas_deletadas.append(caminho)

    except Exception as e:
        print(f"\n[ERRO] Falha ao executar as ações: {e}")
        print("Tentando restaurar os arquivos e pastas existentes...")

        erros: list[str] = []

        # 1. Restaura arquivos modificados
        for caminho, conteudo in conteudos_originais.items():
            try:
                with open(caminho, 'w', encoding='utf-8', newline='') as f:
                    f.write(conteudo)
            except Exception as erro:
                erros.append(f"{caminho}: {erro}")

        # 2. Remove arquivos criados durante a operação
        for caminho in reversed(arquivos_criados):
            try:
                if os.path.isfile(caminho):
                    os.remove(caminho)
            except Exception as erro:
                erros.append(f"{caminho}: {erro}")

        # 3. Remove pastas criadas durante a operação
        for caminho in reversed(pastas_criadas):
            try:
                if os.path.isdir(caminho) and not os.listdir(caminho):
                    os.rmdir(caminho)
            except Exception as erro:
                erros.append(f"{caminho}: {erro}")

        # 4. Restaura arquivos deletados avulsos
        for caminho, conteudo_bytes in backup_arquivos_deletados.items():
            if caminho in arquivos_deletados:
                try:
                    pasta_pai = os.path.dirname(caminho)
                    os.makedirs(pasta_pai, exist_ok=True)
                    with open(caminho, 'wb') as f:
                        f.write(conteudo_bytes)
                except Exception as erro:
                    erros.append(f"{caminho}: {erro}")

        # 5. Restaura pastas deletadas recursivamente (recria diretórios e arquivos)
        for caminho_pasta, dados in backup_pastas_deletadas.items():
            if caminho_pasta in pastas_deletadas:
                try:
                    os.makedirs(caminho_pasta, exist_ok=True)
                    for sub in dados['subpastas']:
                        os.makedirs(sub, exist_ok=True)
                    for arq_c, conteudo_bytes in dados['arquivos'].items():
                        os.makedirs(os.path.dirname(arq_c), exist_ok=True)
                        with open(arq_c, 'wb') as f:
                            f.write(conteudo_bytes)
                except Exception as erro:
                    erros.append(f"{caminho_pasta}: {erro}")

        if erros:
            print("[ATENÇÃO] Algumas operações de recuperação falharam:")
            for erro in erros:
                print(f"  - {erro}")
        else:
            print("Os arquivos e pastas existentes foram restaurados com sucesso.")

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
