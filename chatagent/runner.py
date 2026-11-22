"""Execução de comandos shell solicitados pela IA via subprocess."""

import subprocess
import sys


def executar_comando(comando: str, pasta: str) -> str:
    """Executa um comando shell na pasta indicada e retorna a saída combinada (stdout + stderr).

    Args:
        comando: O comando a ser executado (ex: ``mvn test``, ``python manage.py migrate``).
        pasta:   Diretório de trabalho onde o comando será rodado.

    Returns:
        String com toda a saída do processo (stdout e stderr combinados),
        seguida de um rodapé com o código de retorno.
    """
    print(f"\n[EXEC] Rodando: {comando}")
    print(f"       Diretório: {pasta}")
    print("-" * 60)

    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            cwd=pasta,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,  # 5 minutos de limite
        )
        saida = resultado.stdout or ""
        codigo = resultado.returncode

    except subprocess.TimeoutExpired:
        saida = "[ERRO] O comando excedeu o tempo limite de 5 minutos e foi encerrado."
        codigo = -1

    except Exception as e:
        saida = f"[ERRO] Não foi possível executar o comando: {e}"
        codigo = -1

    # Exibe a saída no terminal para o usuário acompanhar
    print(saida if saida.strip() else "(sem saída)")
    print("-" * 60)
    print(f"[EXEC] Código de retorno: {codigo}")

    rodape = f"\n--- Código de retorno: {codigo} ---"
    return saida + rodape


def criar_prompt_resultado_comandos(
    resultados: list[dict],
    pasta: str,
    user_prompt: str = "",
) -> str:
    """Monta a mensagem a ser enviada à IA com o resultado de um ou mais comandos executados.

    Args:
        resultados: Lista de dicionários contendo ``{"comando": str, "saida": str}``.
        pasta: Diretório onde os comandos foram executados.
        user_prompt: Prompt original do usuário.
    """
    total = len(resultados)
    secoes = [
        "======================================================================",
        "RESULTADO DA EXECUÇÃO DE COMANDOS PELO ChatAgent",
        "======================================================================",
        f"Diretório de trabalho: {pasta}",
    ]

    if user_prompt and user_prompt.strip():
        secoes.append(f"Solicitação original do usuário: {user_prompt.strip()}")

    secoes.append("")

    for indice, item in enumerate(resultados, start=1):
        cmd = item.get("comando", "")
        saida_cmd = item.get("saida", "").strip()
        prefixo = f"[Comando {indice} de {total}]" if total > 1 else "[Comando executado]"
        secoes.extend([
            f"{prefixo}: {cmd}",
            "Saída (stdout + stderr):",
            "```",
            saida_cmd if saida_cmd else "(sem saída)",
            "```",
            "",
        ])

    secoes.extend([
        "======================================================================",
        "Com base no resultado da execução acima, continue sua análise e",
        "responda usando os comandos obrigatórios do ChatAgent (---> código:,",
        "----> Modificar, --> Criar arquivo, --> Criar pasta, --> Deletar,",
        "---> Ler, ---> Buscar regex, ---> Executar) conforme necessário.",
        "======================================================================",
    ])

    return "\n".join(secoes)


def criar_prompt_resultado_comando(
    comando: str,
    pasta: str,
    saida: str,
    user_prompt: str = "",
) -> str:
    """Monta a mensagem a ser enviada à IA com o resultado do comando executado."""
    return criar_prompt_resultado_comandos(
        [{"comando": comando, "saida": saida}],
        pasta=pasta,
        user_prompt=user_prompt,
    )
