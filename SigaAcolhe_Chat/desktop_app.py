"""
SigaAcolhe — Aplicação Desktop de Apoio Emocional (Chat Anônimo)
Interface nativa Windows com CustomTkinter.
Identidade visual: Teal/Turquesa, fundo claro, design limpo.
"""

import threading
import datetime
import time

import sys
import os

from dotenv import load_dotenv
if getattr(sys, 'frozen', False):
    load_dotenv(os.path.join(sys._MEIPASS, '.env'))
else:
    load_dotenv()

import customtkinter as ctk
from emotional_engine import EmotionalAnalyzer, EmpatheticResponder
from database import iniciar_sessao, encerrar_sessao

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

COLORS = {
    "bg_main": "#F0FDFA",
    "bg_card": "#FFFFFF",
    "bg_input": "#F0FDFA",
    "accent": "#0D9488",
    "accent_hover": "#0F766E",
    "accent_light": "#CCFBF1",
    "accent_dim": "#14B8A6",
    "text": "#1A1A2E",
    "text_muted": "#6B7280",
    "text_white": "#FFFFFF",
    "msg_bot_bg": "#F0FDFA",
    "msg_user_bg": "#E0F2FE",
    "risk_low": "#34D399",
    "risk_medium": "#FBBF24",
    "risk_high": "#F87171",
    "border": "#D1D5DB",
    "border_accent": "#99F6E4",
    "danger": "#EF4444",
    "danger_hover": "#DC2626",
}

INACTIVITY_TIMEOUT_MS = 5 * 60 * 1000  # 5 minutos


class SigaAcolheApp(ctk.CTk):
    """Janela principal do aplicativo SigaAcolhe."""

    def __init__(self):
        super().__init__()
        self.analyzer = EmotionalAnalyzer()
        self.responder = EmpatheticResponder()
        self.is_processing = False
        self.sessao_id = None
        self.total_mensagens = 0
        self.scores = []
        self.nivel_max = "neutro"
        self.todas_emocoes = []
        self.todas_categorias = {}
        self._inactivity_timer_id = None
        self._user_is_typing = False

        self.title("SigaAcolhe 💚 Sistema de Triagem em Saúde Mental")
        self.geometry("540x720")
        self.minsize(440, 580)
        self.configure(fg_color=COLORS["bg_main"])

        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._show_welcome_screen()


    def _show_welcome_screen(self):
        """Mostra a tela inicial com botão Iniciar."""
        self._clear_window()

        container = ctk.CTkFrame(self, fg_color=COLORS["bg_main"])
        container.pack(fill="both", expand=True)

        ctk.CTkLabel(container, text="", fg_color="transparent", height=60).pack()

        logo_frame = ctk.CTkFrame(container, fg_color="transparent")
        logo_frame.pack(pady=(0, 10))

        ctk.CTkLabel(
            logo_frame, text="🧠💚", font=ctk.CTkFont(size=56),
            fg_color="transparent",
        ).pack()

        ctk.CTkLabel(
            container, text="SigaAcolhe",
            font=ctk.CTkFont(family="Segoe UI", size=36, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            container, text="SISTEMA DE TRIAGEM EM SAÚDE MENTAL",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["text_muted"],
        ).pack(pady=(2, 20))

        desc = (
            "Olá! 👋\nComo você está se sentindo hoje?\n\n"
            "Este é um espaço seguro, anônimo e sem julgamentos.\n"
            "Estou aqui para ouvir você."
        )
        ctk.CTkLabel(
            container, text=desc,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color=COLORS["text"], justify="center", wraplength=380,
        ).pack(pady=(0, 30))

        opcoes_frame = ctk.CTkFrame(container, fg_color="transparent")
        opcoes_frame.pack(pady=(0, 30))

        for texto in ["Estou bem", "Me sinto ansioso(a)", "Preciso conversar"]:
            btn = ctk.CTkButton(
                opcoes_frame, text=texto, width=260, height=40, corner_radius=20,
                font=ctk.CTkFont(family="Segoe UI", size=13),
                fg_color=COLORS["bg_card"], hover_color=COLORS["accent_light"],
                text_color=COLORS["accent"], border_width=1,
                border_color=COLORS["border_accent"],
                command=lambda t=texto: self._start_chat_with_message(t),
            )
            btn.pack(pady=4)

        ctk.CTkButton(
            container, text="Fale comigo 💚", width=260, height=48,
            corner_radius=24,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_white"],
            command=self._start_chat,
        ).pack(pady=(0, 20))

        ctk.CTkLabel(
            container,
            text="Em caso de emergência, ligue 188 (CVV) • Atendimento 24h",
            font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"],
        ).pack(side="bottom", pady=15)


    def _start_chat(self):
        """Inicia uma nova sessão de chat."""
        self.sessao_id = iniciar_sessao()
        self.responder.limpar_historico()
        self.total_mensagens = 0
        self.scores = []
        self.nivel_max = "neutro"
        self.todas_emocoes = []
        self.todas_categorias = {}
        self._show_chat_screen()
        self.after(500, self._show_welcome_message)

    def _start_chat_with_message(self, mensagem: str):
        """Inicia chat e envia uma mensagem pré-definida."""
        self._start_chat()
        self.after(1500, lambda: self._send_predefined(mensagem))

    def _send_predefined(self, mensagem: str):
        """Envia uma mensagem pré-definida."""
        self.input_entry.insert(0, mensagem)
        self._handle_send()

    def _show_chat_screen(self):
        """Monta a tela de chat."""
        self._clear_window()

        self._create_header()
        self._create_chat_area()
        self._create_risk_indicator()
        self._create_input_area()

        self.bind("<Return>", lambda e: self._handle_send())
        self._reset_inactivity_timer()

    def _create_header(self):
        """Header com logo e botão encerrar."""
        header = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=0, height=60,
            border_width=0,
        )
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        inner = ctk.CTkFrame(header, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=8)

        title_frame = ctk.CTkFrame(inner, fg_color="transparent")
        title_frame.pack(side="left", fill="y")

        ctk.CTkLabel(
            title_frame, text="🧠💚", font=ctk.CTkFont(size=20),
            fg_color=COLORS["accent"], corner_radius=8, width=36, height=36,
        ).pack(side="left", padx=(0, 10))

        text_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        text_frame.pack(side="left")

        ctk.CTkLabel(
            text_frame, text="SigaAcolhe",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=COLORS["accent"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_frame, text="ESPAÇO SEGURO • ANÔNIMO",
            font=ctk.CTkFont(family="Segoe UI", size=8),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        ctk.CTkButton(
            inner, text="Encerrar ✕", width=90, height=32, corner_radius=16,
            font=ctk.CTkFont(size=12),
            fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
            text_color=COLORS["text_white"],
            command=self._handle_end_session,
        ).pack(side="right")

    def _create_chat_area(self):
        """Área de mensagens com scroll."""
        chat_container = ctk.CTkFrame(self, fg_color=COLORS["bg_main"], corner_radius=0)
        chat_container.pack(fill="both", expand=True)

        self.chat_scroll = ctk.CTkScrollableFrame(
            chat_container, fg_color=COLORS["bg_main"],
            scrollbar_button_color=COLORS["accent_dim"],
            scrollbar_button_hover_color=COLORS["accent"],
            corner_radius=0,
        )
        self.chat_scroll.pack(fill="both", expand=True, padx=8, pady=8)

    def _create_risk_indicator(self):
        """Indicador de nível de risco."""
        self.risk_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_main"], corner_radius=0, height=30)
        self.risk_frame.pack(fill="x", padx=20)
        self.risk_frame.pack_propagate(False)

        self.risk_label = ctk.CTkLabel(
            self.risk_frame, text="",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            corner_radius=12, height=26,
        )
        self.risk_label.pack(expand=True)
        self.risk_frame.pack_forget()

    def _create_input_area(self):
        """Área de input com botão enviar."""
        bottom = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0)
        bottom.pack(fill="x", side="bottom")

        ctk.CTkLabel(
            bottom, text="Espaço de apoio emocional. Em emergência, ligue 188 (CVV).",
            font=ctk.CTkFont(size=10), text_color=COLORS["text_muted"],
        ).pack(pady=(8, 6), padx=16)

        input_frame = ctk.CTkFrame(
            bottom, fg_color=COLORS["bg_input"], corner_radius=16,
            border_width=1, border_color=COLORS["border"],
        )
        input_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.input_entry = ctk.CTkEntry(
            input_frame, placeholder_text="Como você está se sentindo?",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            fg_color="transparent", border_width=0,
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["text_muted"], height=42,
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(16, 8), pady=4)

        self.input_entry.bind("<Key>", self._on_user_keystroke)

        self.send_btn = ctk.CTkButton(
            input_frame, text="➤", width=42, height=42, corner_radius=12,
            font=ctk.CTkFont(size=16),
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_white"],
            command=self._handle_send,
        )
        self.send_btn.pack(side="right", padx=(0, 4), pady=4)


    def _on_user_keystroke(self, event=None):
        """Chamado a cada tecla pressionada no input."""
        self._reset_inactivity_timer()

    def _reset_inactivity_timer(self):
        """Reseta o timer de inatividade."""
        if self._inactivity_timer_id is not None:
            self.after_cancel(self._inactivity_timer_id)
        self._inactivity_timer_id = self.after(
            INACTIVITY_TIMEOUT_MS, self._on_inactivity_timeout
        )

    def _on_inactivity_timeout(self):
        """Chamado quando o tempo de inatividade expira."""
        if self.input_entry.get().strip():
            self._reset_inactivity_timer()
            return
        self._add_message(
            "bot",
            "Parece que você está ocupado(a). Vou encerrar nossa conversa por aqui. "
            "Sempre que precisar, estarei aqui! Cuide-se 💚",
        )
        self.after(2000, self._end_session)


    def _add_message(self, sender: str, text: str, risk_level: str = "neutro"):
        """Adiciona uma bolha de mensagem ao chat."""
        is_bot = sender == "bot"

        msg_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        msg_frame.pack(fill="x", pady=(4, 4), padx=4)

        anchor = "w" if is_bot else "e"
        bubble_color = COLORS["msg_bot_bg"] if is_bot else COLORS["msg_user_bg"]
        border_color = COLORS["border_accent"] if is_bot else COLORS["border"]

        bubble = ctk.CTkFrame(
            msg_frame, fg_color=bubble_color, corner_radius=16,
            border_width=1, border_color=border_color,
        )
        bubble.pack(anchor=anchor, padx=(0 if is_bot else 40, 40 if is_bot else 0))

        content_frame = ctk.CTkFrame(bubble, fg_color="transparent")
        content_frame.pack(padx=14, pady=10)

        if is_bot:
            avatar_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            avatar_frame.pack(anchor="w", pady=(0, 4))
            ctk.CTkLabel(
                avatar_frame, text="💚 SigaAcolhe",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color=COLORS["accent"],
            ).pack(side="left")

        msg_label = ctk.CTkLabel(
            content_frame, text=text,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=COLORS["text"], wraplength=340, justify="left", anchor="w",
        )
        msg_label.pack(anchor="w")

        now = datetime.datetime.now().strftime("%H:%M")
        ctk.CTkLabel(
            content_frame, text=now, font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        ).pack(anchor="e" if not is_bot else "w", pady=(4, 0))

        self.after(100, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self.chat_scroll._parent_canvas.yview_moveto(1.0)

    def _show_welcome_message(self):
        welcome = (
            "Olá! Seja bem-vindo(a) ao SigaAcolhe 💚\n\n"
            "Sou um assistente de apoio emocional e estou aqui\n"
            "para ouvir você. Espaço seguro e anônimo.\n\n"
            "Como você está se sentindo hoje?"
        )
        self._add_message("bot", welcome)

    def _show_typing(self):
        self.typing_frame = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        self.typing_frame.pack(fill="x", pady=(4, 4), padx=4)

        bubble = ctk.CTkFrame(
            self.typing_frame, fg_color=COLORS["msg_bot_bg"],
            corner_radius=16, border_width=1, border_color=COLORS["border_accent"],
        )
        bubble.pack(anchor="w")

        self.typing_label = ctk.CTkLabel(
            bubble, text="  💚 digitando...  ",
            font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
            text_color=COLORS["text_muted"],
        )
        self.typing_label.pack(padx=14, pady=8)
        self._scroll_to_bottom()

    def _remove_typing(self):
        if hasattr(self, "typing_frame") and self.typing_frame.winfo_exists():
            self.typing_frame.destroy()

    def _update_risk_indicator(self, level: str):
        if level == "neutro":
            self.risk_frame.pack_forget()
            return

        labels = {
            "leve": ("● Nível leve", COLORS["risk_low"]),
            "moderado": ("● Nível moderado", COLORS["risk_medium"]),
            "alto": ("⚠ Nível alto", COLORS["risk_high"]),
        }
        text, color = labels.get(level, ("", COLORS["text_muted"]))
        self.risk_label.configure(text=text, text_color=color)
        self.risk_frame.pack(fill="x", padx=20, before=self.winfo_children()[-1])


    def _handle_send(self):
        text = self.input_entry.get().strip()
        if not text or self.is_processing:
            return

        self.is_processing = True
        self.send_btn.configure(state="disabled")
        self._reset_inactivity_timer()

        self._add_message("user", text)
        self.input_entry.delete(0, "end")
        self._show_typing()

        thread = threading.Thread(target=self._process_message, args=(text,), daemon=True)
        thread.start()

    def _process_message(self, text: str):
        try:
            analise = self.analyzer.analisar(text)
            resposta = self.responder.responder(analise, text)
            resposta = resposta.replace("**", "")

            nivel = analise["nivel"]
            score = analise["score"]

            self.total_mensagens += 1
            self.scores.append(score)
            self.todas_emocoes.extend(analise.get("emocoes_detectadas", []))

            for cat, count in analise.get("categorias_corporativas", {}).items():
                self.todas_categorias[cat] = self.todas_categorias.get(cat, 0) + count

            niveis_ordem = {"neutro": 0, "leve": 1, "moderado": 2, "alto": 3}
            if niveis_ordem.get(nivel, 0) > niveis_ordem.get(self.nivel_max, 0):
                self.nivel_max = nivel

        except Exception as e:
            print(f"[ERRO] {e}")
            resposta = "Desculpe, tive um problema. Pode tentar novamente? 💚"
            nivel = "neutro"

        self.after(0, self._show_response, resposta, nivel)

    def _show_response(self, resposta: str, nivel: str):
        self._remove_typing()
        self._add_message("bot", resposta, nivel)
        self._update_risk_indicator(nivel)
        self.is_processing = False
        self.send_btn.configure(state="normal")
        self.input_entry.focus()
        self._reset_inactivity_timer()


    def _handle_end_session(self):
        """Botão encerrar clicado pelo usuário."""
        self._add_message(
            "bot",
            "Obrigado por compartilhar comigo! Lembre-se: buscar ajuda "
            "é um ato de coragem. Cuide-se! 💚",
        )
        self.after(2000, self._end_session)

    def _end_session(self):
        """Finaliza a sessão e salva dados."""
        if self._inactivity_timer_id:
            self.after_cancel(self._inactivity_timer_id)

        if self.sessao_id and self.total_mensagens > 0:
            try:
                resumo = self.responder.gerar_resumo_sessao()
            except Exception:
                resumo = {"resumo": "", "categorias_sugeridas": {}}

            categorias_final = dict(self.todas_categorias)
            for cat, val in resumo.get("categorias_sugeridas", {}).items():
                if cat not in categorias_final:
                    categorias_final[cat] = val

            score_medio = sum(self.scores) / len(self.scores) if self.scores else 0

            encerrar_sessao(
                sessao_id=self.sessao_id,
                nivel_risco_max=self.nivel_max,
                score_medio=score_medio,
                categorias=categorias_final,
                resumo_ia=resumo.get("resumo", ""),
                total_mensagens=self.total_mensagens,
                emocoes_detectadas=list(set(self.todas_emocoes)),
            )

        self._show_welcome_screen()


    def _clear_window(self):
        """Remove todos os widgets da janela."""
        for widget in self.winfo_children():
            widget.destroy()



if __name__ == "__main__":
    app = SigaAcolheApp()
    app.mainloop()
