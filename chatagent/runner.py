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


def criar_prompt_resultado_comando(
    comando: str,
    pasta: str,
    saida: str,
    user_prompt: str = "",
) -> str:
    """Monta a mensagem a ser enviada à IA com o resultado do comando executado."""
    secoes = [
        "======================================================================",
        "RESULTADO DO COMANDO EXECUTADO PELO ChatAgent",
        "======================================================================",
        f"Comando executado: {comando}",
        f"Diretório: {pasta}",
        "",
        "Saída do comando (stdout + stderr):",
        "```",
        saida.strip(),
        "```",
        "======================================================================",
        "Com base nessa saída, continue sua análise e responda usando os",
        "comandos obrigatórios do ChatAgent (---> código:, ----> Modificar,",
        "--> Criar arquivo, --> Criar pasta, --> Deletar, ---> Ler,",
        "---> Executar) conforme necessário.",
        "======================================================================",
    ]

    if user_prompt and user_prompt.strip():
        secoes.insert(
            3,
            f"Solicitação original do usuário: {user_prompt.strip()}",
        )

    return "\n".join(secoes)
