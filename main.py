"""Ponto de entrada do ChatAgent."""

from chatagent.modes import modo_1_multiplas_ias, modo_2_edicao_arquivos


def menu_principal() -> None:
    """Exibe o menu principal e delega para os modos disponíveis."""
    while True:
        print("\n========================================")
        print("   CHATAGENT - v2.0.0")
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
