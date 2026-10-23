"""Modos de operação do ChatAgent."""

from chatagent import browser, files as project_files
from chatagent.constants import SITES_IA
from chatagent.editor import processar_resposta_e_modificar_arquivos
from chatagent.files import criar_prompt_edicao, criar_prompt_leitura
from chatagent.ui import ler_prompt_multilinha, selecionar_arquivos


def preparar_campo_ia(nome_ia: str) -> None:
    """Orienta o usuário a posicionar o cursor no campo da IA."""
    print("\n" + "=" * 60)
    print(f"[PREPARAÇÃO] {nome_ia}")
    print("1. Aguarde a página terminar de carregar.")
    print("2. Clique dentro do campo de mensagem da IA.")
    print("3. Volte para este terminal.")
    input("4. Pressione ENTER quando estiver pronto para enviar: ")


def abrir_tres_sites() -> bool:
    """Abre as três IAs, cada uma em uma nova aba."""
    print("\n[OK] Preparando as abas das três IAs...")

    for chave in ['1', '2', '3']:
        nome, site = SITES_IA[chave]
        if not browser.abrir_site_em_nova_aba(site):
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


def abrir_ia_escolhida() -> str | None:
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
    if not browser.abrir_site_em_nova_aba(site):
        return None

    print(f"\n[OK] {nome} aberto em uma nova aba.")
    print("Não será necessário abrir as outras IAs.")
    preparar_campo_ia(nome)
    return escolha


# ---------------------------------------------------------------------------
# Modo 1 – Envio para múltiplas IAs
# ---------------------------------------------------------------------------

def modo_1_multiplas_ias() -> None:
    """Envia o mesmo prompt para as três IAs simultaneamente."""
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

        if browser.enviar_para_varias_abas(prompt):
            print("Mensagem enviada para as três IAs.")
        else:
            print("Não foi possível enviar para todas as abas.")
            break


# ---------------------------------------------------------------------------
# Modo 2 – Edição e criação de arquivos
# ---------------------------------------------------------------------------

def modo_2_edicao_arquivos() -> None:
    """Seleciona arquivos/pastas, envia contexto a uma IA e aplica as ações retornadas."""
    print("\n--- MODO 2: Edição e criação de arquivos ---")

    while True:
        file_paths = selecionar_arquivos()

        if file_paths is None:
            return

        print("\nArquivos de contexto selecionados:")

        if project_files.PASTAS_PROJETO_SELECIONADAS:
            print("Pastas de projeto:")
            for pasta in project_files.PASTAS_PROJETO_SELECIONADAS:
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
                full_message = criar_prompt_edicao(file_paths, user_prompt)
                with open("ultimo_prompt_enviado.txt", "w", encoding="utf-8") as f:
                    f.write(full_message)
            except Exception as e:
                print(f"[ERRO] Não foi possível ler os arquivos: {e}")
                continue

            print("\n[OK] Enviando arquivos e solicitação para a IA...")

            if not browser.enviar_para_uma_aba(full_message):
                print("[ERRO] Não foi possível enviar a mensagem.")
                continue

            print("-> Solicitação enviada (salva em 'ultimo_prompt_enviado.txt').")

            # Loop de leitura: reenvia automaticamente enquanto a IA pedir arquivos.
            while True:
                arquivos_para_ler = processar_resposta_e_modificar_arquivos(file_paths)

                if not arquivos_para_ler:
                    break

                # Monta e envia o conteúdo dos arquivos solicitados.
                try:
                    msg_leitura = criar_prompt_leitura(arquivos_para_ler, user_prompt=user_prompt)
                    with open("ultimo_prompt_enviado.txt", "w", encoding="utf-8") as f:
                        f.write(msg_leitura)
                except ValueError as e:
                    print(f"[ERRO] {e}")
                    break

                print("\n[OK] Enviando conteúdo dos arquivos solicitados à IA...")
                if not browser.enviar_para_uma_aba(msg_leitura):
                    print("[ERRO] Não foi possível enviar os arquivos solicitados.")
                    break
                print("-> Conteúdo enviado. Aguardando nova resposta da IA...")

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
