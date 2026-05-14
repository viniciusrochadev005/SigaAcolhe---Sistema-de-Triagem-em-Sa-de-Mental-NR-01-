"""
Gerador de Respostas Empáticas com IA (Groq API) — SigaAcolhe.

Usa um LLM (Llama 3) via Groq para gerar respostas dinâmicas e naturais,
respeitando todas as regras obrigatórias de empatia e segurança.

O nível de risco (do analyzer) é passado ao prompt para que a IA
adapte o tom e a profundidade da resposta.
"""

import os

from groq import Groq


SYSTEM_PROMPT = """Você é o "SigaAcolhe", um assistente de apoio emocional e triagem em saúde mental no ambiente corporativo.
Seu papel é ser um ponto de escuta empática e acolhedora. Converse como um amigo querido que se importa de verdade.

- Fale de forma NATURAL, CALOROSA e CURTA, como num chat real entre amigos próximos.
- Use no máximo 2-3 frases por resposta. Seja breve e genuíno.
- Evite textos longos, listas ou parágrafos enormes.
- Use linguagem informal e acolhedora (mas não forçada).
- NÃO repita a mesma estrutura toda vez. Varie bastante.
- Responda como uma pessoa real que se importa, não como um robô.
- Use emojis com moderação (💚, 🤗, 🌿) para transmitir calor.
- Faça perguntas abertas gentis para entender melhor: "Quer me contar mais sobre isso?"

- Transmita que a pessoa NÃO está sozinha.
- Valide os sentimentos ANTES de qualquer coisa.
- Demonstre interesse genuíno pelo que ela está passando.
- Use frases como: "Que bom que você está compartilhando isso", "Faz total sentido se sentir assim".
- Evite "eu entendo" (pode soar vazio). Prefira "imagino como deve ser difícil".

- Você atua dentro de empresas como ferramenta de triagem em saúde mental.
- Se a pessoa mencionar trabalho, chefe, colegas, metas, prazos — explore com gentileza.
- Pergunte sobre o ambiente de trabalho naturalmente: "Como tem sido seu dia a dia no trabalho?"
- Identifique sinais de burnout, ansiedade, estresse laboral — mas NUNCA diagnostique.
- Lembre que buscar ajuda é um ato de coragem, não fraqueza.

- NUNCA dê diagnóstico médico/psicológico.
- NUNCA afirme condição clínica.
- Use linguagem de incerteza ("parece que...", "pelo que entendi...").
- Valide o sentimento antes de sugerir qualquer coisa.
- NUNCA minimize sofrimento, julgue ou dê ordens.
- Responda SEMPRE em português brasileiro.

- NEUTRO/LEVE: amigável, leve, incentive a conversa. "Que bom ter você aqui 💚"
- MODERADO: mais validação, perguntas abertas. Sugira pausas e autocuidado gentilmente.
- ALTO: máxima empatia + SEMPRE mencione CVV (188, gratuito, 24h, cvv.org.br). Segurança primeiro. "Você não está sozinho(a)."

"""

BOAS_VINDAS = (
    "Olá! Seja bem-vindo(a) ao SigaAcolhe 💚\n\n"
    "Sou um assistente de apoio emocional e estou aqui para ouvir você. "
    "Este é um espaço seguro, anônimo e sem julgamentos.\n\n"
    "Como você está se sentindo hoje?"
)


class EmpatheticResponder:
    """
    Gera respostas empáticas dinâmicas usando Groq API (Llama 3).
    Mantém histórico de conversa para contexto.
    """

    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=api_key) if api_key else None
        self.historico: list[dict] = []

    def responder(self, analise: dict, mensagem_usuario: str) -> str:
        """
        Gera uma resposta empática via IA.

        Args:
            analise: resultado do EmotionalAnalyzer.analisar()
            mensagem_usuario: texto original do usuário

        Returns:
            str: resposta empática gerada pela IA
        """
        if not self.client:
            return (
                "Desculpe, estou com um problema técnico no momento. "
                "Se precisar de ajuda urgente, ligue 188 (CVV). 💚"
            )

        nivel = analise.get("nivel", "neutro")
        emocoes = analise.get("emocoes_detectadas", [])
        categorias = analise.get("categorias_corporativas", {})

        contexto_risco = (
            f"[CONTEXTO INTERNO — NÃO INCLUIR NA RESPOSTA]\n"
            f"Nível de risco detectado: {nivel.upper()}\n"
            f"Emoções identificadas: {', '.join(emocoes) if emocoes else 'nenhuma específica'}\n"
            f"Categorias corporativas: {', '.join(categorias.keys()) if categorias else 'nenhuma'}\n"
            f"Score: {analise.get('score', 0)}\n"
            f"Adapte sua resposta conforme o nível de risco indicado acima."
        )

        self.historico.append({"role": "user", "content": mensagem_usuario})

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": contexto_risco},
        ]

        messages.extend(self.historico[-20:])

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=200,
                top_p=0.9,
            )

            resposta = response.choices[0].message.content.strip()

            self.historico.append({"role": "assistant", "content": resposta})

            return resposta

        except Exception as e:
            print(f"[ERRO Groq API] {e}")
            if nivel == "alto":
                return (
                    "Percebo que você pode estar passando por um momento muito difícil. "
                    "Seus sentimentos são válidos e importantes. "
                    "Se precisar de apoio, o CVV (188) está disponível 24h. 💚"
                )
            return (
                "Obrigado por compartilhar isso comigo. "
                "Estou aqui para ouvir você. Quer me contar mais? 💚"
            )

    def gerar_resumo_sessao(self) -> dict:
        """
        Gera um resumo da sessão de conversa usando a IA.

        Returns:
            dict com:
                - resumo: texto resumido da conversa
                - categorias_sugeridas: categorias emocionais detectadas
        """
        if not self.client or len(self.historico) < 2:
            return {
                "resumo": "Sessão muito curta para gerar resumo.",
                "categorias_sugeridas": {},
            }

        prompt_resumo = """Analise esta conversa e forneça um resumo BREVE (máximo 3 frases) sobre:
1. O estado emocional geral do usuário
2. Os principais temas/problemas mencionados

Depois, classifique em categorias com uma pontuação de 0.0 a 1.0:
- burnout (esgotamento por trabalho)
- ansiedade
- depressão
- estresse_laboral
- clima_organizacional

Responda EXATAMENTE neste formato JSON (sem markdown, sem ```):
{"resumo": "texto do resumo aqui", "categorias": {"burnout": 0.0, "ansiedade": 0.0, "depressão": 0.0, "estresse_laboral": 0.0, "clima_organizacional": 0.0}}

Coloque 0.0 para categorias não detectadas. Use valores entre 0.1 e 1.0 apenas para categorias claramente presentes na conversa."""

        messages = [
            {"role": "system", "content": prompt_resumo},
        ]
        messages.extend(self.historico[-20:])

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
                max_tokens=300,
                top_p=0.9,
            )

            texto = response.choices[0].message.content.strip()

            import json
            texto = texto.replace("```json", "").replace("```", "").strip()
            resultado = json.loads(texto)

            categorias = {
                k: v for k, v in resultado.get("categorias", {}).items()
                if v > 0
            }

            return {
                "resumo": resultado.get("resumo", "Sem resumo disponível."),
                "categorias_sugeridas": categorias,
            }

        except Exception as e:
            print(f"[ERRO Resumo] {e}")
            return {
                "resumo": "Não foi possível gerar o resumo automático.",
                "categorias_sugeridas": {},
            }

    def limpar_historico(self):
        """Limpa o histórico de conversa (para nova sessão)."""
        self.historico.clear()

    @staticmethod
    def boas_vindas() -> str:
        """Retorna a mensagem de boas-vindas do sistema."""
        return BOAS_VINDAS
