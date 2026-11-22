"""Módulo para busca e leitura de arquivos via Expressões Regulares (Regex) solicitadas pela IA."""

import os
import re
from pathlib import Path

from chatagent import files as project_files
from chatagent.constants import DIRETORIOS_IGNORADOS

MAX_MATCHES_PADRAO = 150
MAX_TAMANHO_ARQUIVO_PADRAO = 500_000  # 500 KB


def extrair_padrao_e_caminho_regex(corpo: str) -> tuple[str, str | None]:
    """
    Extrai o padrão regex e o caminho de destino (arquivo ou pasta) a partir do texto do comando.

    Formatos suportados:
    1. Com delimitador pipe (|):
       ``padrao: <regex> | caminho: <caminho>``
       ``<regex> | em: <caminho>``
       ``<regex> | <caminho>``
    2. Com aspas explícitas:
       ``"<regex>" em "<caminho>"``
       ``'<regex>' in '<caminho>'``
       ``"<regex>" em <caminho>``
    3. Formato natural com ' em ' ou ' in ':
       ``<regex> em <caminho>``
       ``<regex> in <caminho>``
    4. Formato invertido (caminho antes do padrão):
       ``<caminho> : <regex>``
       ``em <caminho> : <regex>``
    5. Apenas o padrão (busca na pasta do projeto padrão):
       ``<regex>``
    """
    texto = corpo.strip()

    # Formato 1: pipe (|)
    if '|' in texto:
        p1, p2 = texto.split('|', 1)
        p1 = p1.strip()
        p2 = p2.strip()
        p1 = re.sub(r'^(?:padrao|padrão|regex|pattern)\s*:\s*', '', p1, flags=re.IGNORECASE).strip()
        p2 = re.sub(r'^(?:caminho|alvo|pasta|diretorio|diretório|arquivo|em|in|path|target)\s*:\s*', '', p2, flags=re.IGNORECASE).strip()
        padrao = p1.strip('`"\'* ')
        caminho = p2.strip('`"\'* ') or None
        if caminho and caminho.lower() in ('projeto', 'pasta do projeto', 'projeto atual', '.', 'this'):
            caminho = None
        return _limpar_padrao_regex(padrao), caminho

    # Formato 2: aspas no padrão
    m_aspas = re.match(r'^["\'](.+?)["\']\s+(?:em|in)\s+["\']?(.+?)["\']?$', texto, re.IGNORECASE)
    if m_aspas:
        padrao = m_aspas.group(1).strip()
        caminho = m_aspas.group(2).strip().strip('`"\'* ')
        if caminho.lower() in ('projeto', 'pasta do projeto', 'projeto atual', '.', 'this'):
            caminho = None
        return _limpar_padrao_regex(padrao), caminho or None

    # Formato 4: formato invertido (caminho : padrão)
    m_inv = re.match(r'^(?:em\s+|in\s+)?([A-Za-z]:[\\/][^\s:]+|\.{1,2}[\\/][^\s:]+)\s*:\s*(.+)$', texto, re.IGNORECASE)
    if m_inv:
        caminho = m_inv.group(1).strip().strip('`"\'* ')
        padrao = m_inv.group(2).strip().strip('`"\'* ')
        padrao = re.sub(r'^(?:padrao|padrão|regex|pattern)\s*:\s*', '', padrao, flags=re.IGNORECASE).strip()
        if caminho.lower() in ('projeto', 'pasta do projeto', 'projeto atual', '.', 'this'):
            caminho = None
        return _limpar_padrao_regex(padrao), caminho or None

    # Formato 3: separador ' em ' ou ' in '
    m_em = re.search(r'\s+(?:em|in)\s+', texto, re.IGNORECASE)
    if m_em:
        padrao = texto[:m_em.start()].strip().strip('`"\'* ')
        caminho = texto[m_em.end():].strip().strip('`"\'* ')
        padrao = re.sub(r'^(?:padrao|padrão|regex|pattern)\s*:\s*', '', padrao, flags=re.IGNORECASE).strip().strip('`"\'* ')
        if caminho.lower() in ('projeto', 'pasta do projeto', 'projeto atual', '.', 'this'):
            caminho = None
        return _limpar_padrao_regex(padrao), caminho or None

    # Formato 5: apenas o padrão
    padrao = texto.strip('`"\'* ')
    padrao = re.sub(r'^(?:padrao|padrão|regex|pattern)\s*:\s*', '', padrao, flags=re.IGNORECASE).strip().strip('`"\'* ')
    return _limpar_padrao_regex(padrao), None


def _limpar_padrao_regex(padrao: str) -> str:
    """Remove delimitadores estilo /pattern/ ou crases excedentes."""
    p = padrao.strip()
    m_barras = re.match(r'^/(.+)/([imsux]*)$', p)
    if m_barras:
        p = m_barras.group(1)
    return p


def resolver_caminho_alvo(alvo: str | None, pasta_padrao: str | None = None) -> str:
    """
    Resolve o caminho absoluto do alvo da busca (arquivo ou pasta).

    - Se alvo for None ou indicar a pasta do projeto: retorna pasta_padrao ou pasta selecionada.
    - Se for relativo: tenta relativo a pasta_padrao, depois relativo ao diretório atual.
    - Se for absoluto: normaliza e retorna diretamente (permitindo qualquer pasta do PC).
    """
    if not pasta_padrao:
        if project_files.PASTAS_PROJETO_SELECIONADAS:
            pasta_padrao = project_files.PASTAS_PROJETO_SELECIONADAS[0]
        else:
            pasta_padrao = os.getcwd()

    pasta_padrao = os.path.abspath(pasta_padrao)

    if not alvo or alvo.strip().lower() in ('projeto', 'pasta do projeto', 'projeto atual', '.', 'this', ''):
        return pasta_padrao

    alvo = alvo.strip().strip('`"\'* ')
    if alvo.endswith(('\\', '/')) and not re.match(r'^[a-zA-Z]:[\\/]+$', alvo):
        alvo = alvo.rstrip('\\/ ')

    if os.path.isabs(alvo):
        return os.path.normpath(alvo)

    # Tenta resolver relativo à pasta do projeto
    candidato = os.path.normpath(os.path.join(pasta_padrao, alvo))
    if os.path.exists(candidato):
        return candidato

    # Tenta resolver relativo ao diretório atual de execução
    candidato_cwd = os.path.normpath(os.path.abspath(alvo))
    if os.path.exists(candidato_cwd):
        return candidato_cwd

    return candidato


def buscar_em_arquivo(padrao_compilado: re.Pattern, caminho_arquivo: str, max_matches: int = 100) -> list[dict]:
    """Varre um arquivo linha a linha buscando ocorrências da expressão regular compilada."""
    matches: list[dict] = []
    conteudo: str | None = None

    for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
        try:
            with open(caminho_arquivo, 'r', encoding=enc, errors='replace') as f:
                conteudo = f.read()
            break
        except Exception:
            continue

    if conteudo is None:
        return matches

    linhas = conteudo.splitlines()
    for num_linha, linha in enumerate(linhas, start=1):
        try:
            if padrao_compilado.search(linha):
                matches.append({
                    'linha': num_linha,
                    'texto': linha.strip('\r\n'),
                })
                if len(matches) >= max_matches:
                    break
        except Exception:
            continue

    return matches


def buscar_em_pasta(
    padrao_compilado: re.Pattern,
    pasta: str,
    max_matches: int = MAX_MATCHES_PADRAO,
    max_tamanho: int = MAX_TAMANHO_ARQUIVO_PADRAO,
) -> tuple[dict[str, list[dict]], int, bool]:
    """
    Varre recursivamente uma pasta buscando arquivos textuais com ocorrências da regex.

    Retorna uma tupla ``(resultados_por_arquivo, total_matches, truncado)``.
    """
    resultados: dict[str, list[dict]] = {}
    total_matches = 0
    truncado = False

    for raiz, diretorios, arquivos in os.walk(pasta):
        diretorios[:] = sorted(
            d for d in diretorios
            if d.lower() not in DIRETORIOS_IGNORADOS
        )

        for nome in sorted(arquivos):
            caminho_arq = os.path.join(raiz, nome)
            if not project_files.arquivo_e_textual(caminho_arq):
                continue
            try:
                if os.path.getsize(caminho_arq) > max_tamanho:
                    continue
            except OSError:
                continue

            limite_restante = max_matches - total_matches
            matches_arq = buscar_em_arquivo(padrao_compilado, caminho_arq, max_matches=limite_restante)
            if matches_arq:
                caminho_abs = os.path.abspath(caminho_arq)
                resultados[caminho_abs] = matches_arq
                total_matches += len(matches_arq)

                if total_matches >= max_matches:
                    truncado = True
                    break

        if truncado:
            break

    return resultados, total_matches, truncado


def executar_busca_regex(item_busca: dict, pasta_padrao: str | None = None) -> dict:
    """Executa uma busca regex individual e retorna um dicionário com os detalhes e resultados."""
    padrao = item_busca.get('padrao', '').strip()
    alvo = item_busca.get('caminho')

    caminho_resolvido = resolver_caminho_alvo(alvo, pasta_padrao)

    print(f"\n[BUSCA REGEX] Padrão: '{padrao}'")
    print(f"              Alvo:   {caminho_resolvido}")

    try:
        padrao_compilado = re.compile(padrao, re.IGNORECASE | re.MULTILINE)
    except re.error as e:
        msg_erro = f"Expressão regular inválida '{padrao}': {e}"
        print(f"              [ERRO] {msg_erro}")
        return {
            'padrao': padrao,
            'alvo': caminho_resolvido,
            'sucesso': False,
            'erro': msg_erro,
            'tipo': 'erro',
        }

    if not os.path.exists(caminho_resolvido):
        msg_erro = f"O caminho especificado não existe: {caminho_resolvido}"
        print(f"              [ERRO] {msg_erro}")
        return {
            'padrao': padrao,
            'alvo': caminho_resolvido,
            'sucesso': False,
            'erro': msg_erro,
            'tipo': 'nao_encontrado',
        }

    if os.path.isfile(caminho_resolvido):
        matches = buscar_em_arquivo(padrao_compilado, caminho_resolvido, max_matches=MAX_MATCHES_PADRAO)
        total = len(matches)
        print(f"              Encontradas {total} ocorrência(s) no arquivo.")
        return {
            'padrao': padrao,
            'alvo': caminho_resolvido,
            'sucesso': True,
            'tipo': 'arquivo',
            'matches': matches,
            'total': total,
            'truncado': total >= MAX_MATCHES_PADRAO,
        }
    else:
        resultados, total, truncado = buscar_em_pasta(
            padrao_compilado,
            caminho_resolvido,
            max_matches=MAX_MATCHES_PADRAO,
            max_tamanho=MAX_TAMANHO_ARQUIVO_PADRAO,
        )
        num_arquivos = len(resultados)
        aviso = " [Limite máximo de ocorrências atingido]" if truncado else ""
        print(f"              Encontradas {total} ocorrência(s) em {num_arquivos} arquivo(s).{aviso}")
        return {
            'padrao': padrao,
            'alvo': caminho_resolvido,
            'sucesso': True,
            'tipo': 'pasta',
            'resultados_por_arquivo': resultados,
            'total': total,
            'num_arquivos': num_arquivos,
            'truncado': truncado,
        }


def executar_buscas_regex(buscas: list[dict], pasta_padrao: str | None = None) -> list[dict]:
    """Executa todas as buscas regex solicitadas pela IA em sequência."""
    resultados: list[dict] = []
    for item in buscas:
        res = executar_busca_regex(item, pasta_padrao=pasta_padrao)
        resultados.append(res)
    return resultados


def criar_prompt_resultado_regex(resultados: list[dict], user_prompt: str = "") -> str:
    """Monta a mensagem completa a ser enviada à IA com o resultado das buscas por regex solicitadas."""
    total_buscas = len(resultados)
    secoes = [
        "======================================================================",
        "RESULTADO DA BUSCA POR REGEX PELO ChatAgent",
        "======================================================================",
    ]

    if user_prompt and user_prompt.strip():
        secoes.append(f"Solicitação original do usuário:\n{user_prompt.strip()}\n")

    for idx, res in enumerate(resultados, start=1):
        prefixo = f"[Busca Regex {idx} de {total_buscas}]" if total_buscas > 1 else "[Busca Regex]"
        padrao = res.get('padrao', '')
        alvo = res.get('alvo', '')
        tipo = res.get('tipo', '')

        secoes.append(prefixo)
        secoes.append(f"Padrão regex: {padrao}")
        secoes.append(f"Alvo pesquisado: {alvo}")

        if not res.get('sucesso'):
            secoes.append(f"Status: [ERRO] {res.get('erro', 'Falha na busca')}")
            secoes.append("")
            continue

        if tipo == 'arquivo':
            matches = res.get('matches', [])
            total = res.get('total', 0)
            truncado = res.get('truncado', False)
            if total == 0:
                secoes.append("Resultado: Nenhuma ocorrência encontrada neste arquivo.")
            else:
                aviso_trunc = f" (Limite de {MAX_MATCHES_PADRAO} ocorrências atingido)" if truncado else ""
                secoes.append(f"Total de ocorrências: {total}{aviso_trunc}")
                secoes.append("Ocorrências encontradas:")
                for m in matches:
                    secoes.append(f"  Linha {m['linha']}: {m['texto']}")
        elif tipo == 'pasta':
            resultados_arquivos = res.get('resultados_por_arquivo', {})
            total = res.get('total', 0)
            num_arqs = res.get('num_arquivos', 0)
            truncado = res.get('truncado', False)

            if total == 0:
                secoes.append("Resultado: Nenhuma ocorrência encontrada nesta pasta.")
            else:
                aviso_trunc = f" (Limite de {MAX_MATCHES_PADRAO} ocorrências atingido)" if truncado else ""
                secoes.append(f"Total de ocorrências: {total} em {num_arqs} arquivo(s){aviso_trunc}")
                secoes.append("Ocorrências por arquivo:")
                for arq, lista_matches in resultados_arquivos.items():
                    secoes.append(f"\nArquivo: {arq} ({len(lista_matches)} ocorrência(s)):")
                    for m in lista_matches:
                        secoes.append(f"  Linha {m['linha']}: {m['texto']}")

        secoes.append("")

    secoes.extend([
        "======================================================================",
        "ATENÇÃO: RESULTADOS DA BUSCA DISPONÍVEIS - SIGA AS REGRAS OBRIGATÓRIAS!",
        "Com base nos resultados da busca por regex acima e na solicitação original:",
        "1. Se precisar ler o conteúdo completo de algum arquivo encontrado:",
        "   ---> Ler CAMINHO_ABSOLUTO_DO_ARQUIVO",
        "2. Se precisar de outra busca por regex:",
        "   ---> Buscar regex NOVO_PADRAO em CAMINHO",
        "3. Se precisar executar comandos shell no projeto:",
        "   ---> Executar COMANDO",
        "4. Se já tiver informações suficientes para implementar a solução:",
        "   Responda OBRIGATORIAMENTE utilizando os comandos de código do ChatAgent:",
        "   ---> código:",
        "   (conteúdo completo do arquivo, sem cercas ```)",
        "   ----> Modificar CAMINHO_ABSOLUTO",
        "   ou --> Criar arquivo CAMINHO_ABSOLUTO, --> Criar pasta ..., --> Deletar ...",
        "NÃO responda em texto livre sem os comandos!",
        "======================================================================",
    ])

    return "\n".join(secoes)
