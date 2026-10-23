"""Automação da janela e abas do Chrome."""

import ctypes
import time

import pyautogui
import pyperclip
import pygetwindow as gw

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

_janela_chrome_alvo = None


def obter_primeira_janela_chrome() -> bool:
    """Localiza uma janela válida do Chrome sem alterar seu estado."""
    global _janela_chrome_alvo

    try:
        user32 = ctypes.windll.user32
        janelas = [j for j in gw.getWindowsWithTitle("Chrome") if j.visible]

        for janela in janelas:
            try:
                hwnd = int(janela._hWnd)
                if hwnd and user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd):
                    _janela_chrome_alvo = janela
                    return True
            except Exception:
                continue

        _janela_chrome_alvo = None
        print("\n[ERRO] Nenhuma janela válida do Chrome foi encontrada.")
        print("Abra o Chrome manualmente e execute novamente.")
        return False

    except Exception as e:
        _janela_chrome_alvo = None
        print(f"[ERRO] Não foi possível localizar o Chrome: {e}")
        return False


def focar_janela_alvo() -> bool:
    """Traz o Chrome para frente sem maximizar, restaurar ou minimizar a janela."""
    global _janela_chrome_alvo

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    if not obter_primeira_janela_chrome():
        return False

    try:
        hwnd = int(_janela_chrome_alvo._hWnd)
        if not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
            _janela_chrome_alvo = None
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
        _janela_chrome_alvo = None
        print(f"[ERRO] Não foi possível focar o Chrome: {e}")
        return False


def abrir_site_em_nova_aba(site: str) -> bool:
    """Abre um site em uma nova aba, preservando as abas existentes."""
    if _janela_chrome_alvo is None and not obter_primeira_janela_chrome():
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


def enviar_para_varias_abas(prompt: str) -> bool:
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


def enviar_para_uma_aba(prompt: str) -> bool:
    """Envia para a aba recém-aberta e ativa da IA escolhida."""
    if not focar_janela_alvo():
        print("[ERRO] Não foi possível focar o Chrome.")
        return False

    try:
        # A aba da IA escolhida acabou de ser aberta e permanece ativa.
        # Não usamos Ctrl+1/2/3, pois isso selecionaria abas antigas do Chrome.
        pyperclip.copy(prompt)
        time.sleep(0.4)
        pyautogui.hotkey("ctrl", "v")

        # Se o prompt for grande, concede mais tempo para a caixa de texto do navegador processar
        espera_colagem = 1.2 if len(prompt) > 5000 else 0.4
        time.sleep(espera_colagem)

        pyautogui.press("enter")
        time.sleep(0.7)
        return True

    except Exception as e:
        print(f"[ERRO] Falha ao enviar a mensagem: {e}")
        return False
