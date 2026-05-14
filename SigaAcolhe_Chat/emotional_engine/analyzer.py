"""
Motor de Análise Emocional — SigaAcolhe.

Analisa a mensagem do usuário em 3 dimensões:
  1. Intensidade emocional (keywords detectadas)
  2. Linguagem utilizada (padrões linguísticos)
  3. Contexto implícito (combinação de sinais)

Inclui também detecção de categorias corporativas (NR-01):
  - Burnout, Ansiedade, Depressão, Estresse Laboral, Clima Organizacional

Regra de Prioridade: qualquer sinal de risco ALTO prevalece.
"""

import re
import unicodedata

from .keywords import (
    AUSENCIA_ESPERANCA,
    CATEGORIAS_CORPORATIVAS,
    KEYWORDS_ALTO,
    KEYWORDS_LEVE,
    KEYWORDS_MODERADO,
    PALAVRAS_ABSOLUTAS,
    PADROES_NEGATIVOS,
)


def _normalizar(texto: str) -> str:
    """Normaliza o texto: lowercase, remove acentos, espaços extras."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"\s+", " ", texto)
    return texto


def _contar_matches(texto_normalizado: str, lista_keywords: list[str]) -> int:
    """Conta quantas keywords da lista aparecem no texto."""
    count = 0
    for keyword in lista_keywords:
        keyword_norm = _normalizar(keyword)
        if keyword_norm in texto_normalizado:
            count += 1
    return count


def _detectar_frases_curtas_negativas(texto: str) -> bool:
    """Detecta se a mensagem contém frases curtas e negativas."""
    frases = re.split(r"[.!?;]+", texto)
    frases_curtas_negativas = 0
    for frase in frases:
        frase = frase.strip()
        palavras = frase.split()
        if len(palavras) <= 5 and len(palavras) > 0:
            negativas = ["nao", "não", "nem", "nunca", "nada", "ninguem", "ninguém"]
            if any(neg in frase.lower() for neg in negativas):
                frases_curtas_negativas += 1
    return frases_curtas_negativas >= 1


def _detectar_categorias_corporativas(texto_normalizado: str) -> dict:
    """
    Detecta categorias corporativas (NR-01) na mensagem.

    Returns:
        dict com categorias e suas contagens de matches.
        Exemplo: {"burnout": 3, "ansiedade": 1}
    """
    categorias_detectadas = {}

    for categoria, keywords in CATEGORIAS_CORPORATIVAS.items():
        matches = _contar_matches(texto_normalizado, keywords)
        if matches > 0:
            categorias_detectadas[categoria] = matches

    return categorias_detectadas


class EmotionalAnalyzer:
    """
    Analisa o conteúdo emocional de uma mensagem e classifica o nível de risco.

    Níveis de risco:
        - "alto": desesperança, risco à vida, perda de sentido
        - "moderado": sobrecarga, sofrimento intenso, repetição de dor
        - "leve": desconforto emocional, cansaço, desânimo
        - "neutro": sem sinais emocionais significativos
    """

    def analisar(self, mensagem: str) -> dict:
        """
        Analisa uma mensagem e retorna a classificação emocional.

        Args:
            mensagem: texto do usuário

        Returns:
            dict com:
                - nivel: "alto" | "moderado" | "leve" | "neutro"
                - score: float de 0.0 a 1.0
                - detalhes: dict com contagens de cada categoria
                - emocoes_detectadas: lista de emoções identificadas
                - categorias_corporativas: dict com categorias NR-01 detectadas
        """
        texto_norm = _normalizar(mensagem)
        texto_original = mensagem.lower().strip()

        matches_alto = _contar_matches(texto_norm, KEYWORDS_ALTO)
        matches_moderado = _contar_matches(texto_norm, KEYWORDS_MODERADO)
        matches_leve = _contar_matches(texto_norm, KEYWORDS_LEVE)

        matches_absolutas = _contar_matches(texto_norm, PALAVRAS_ABSOLUTAS)
        matches_negativos = _contar_matches(texto_norm, PADROES_NEGATIVOS)
        matches_desesperanca = _contar_matches(texto_norm, AUSENCIA_ESPERANCA)
        frases_curtas_neg = _detectar_frases_curtas_negativas(texto_original)

        categorias_corp = _detectar_categorias_corporativas(texto_norm)
        
        matches_moderado += categorias_corp.get("burnout", 0)
        matches_moderado += categorias_corp.get("depressão", 0)
        matches_moderado += categorias_corp.get("ansiedade", 0)
        matches_leve += categorias_corp.get("estresse_laboral", 0)
        matches_leve += categorias_corp.get("clima_organizacional", 0)

        emocoes = []
        if matches_alto > 0:
            emocoes.append("desesperança")
        if matches_desesperanca > 0:
            emocoes.append("ausência de esperança")
        if matches_moderado > 0:
            emocoes.append("sobrecarga emocional")
        if matches_leve > 0:
            emocoes.append("desconforto emocional")
        if matches_absolutas > 0:
            emocoes.append("pensamento absoluto")
        if matches_negativos > 0:
            emocoes.append("negatividade")
        if frases_curtas_neg:
            emocoes.append("expressão negativa breve")

        nomes_cat = {
            "burnout": "burnout",
            "ansiedade": "ansiedade",
            "depressão": "depressão",
            "estresse_laboral": "estresse laboral",
            "clima_organizacional": "clima organizacional negativo",
        }
        for cat in categorias_corp:
            nome = nomes_cat.get(cat, cat)
            if nome not in emocoes:
                emocoes.append(nome)

        if matches_alto > 0:
            nivel = "alto"
            score = min(1.0, 0.8 + (matches_alto * 0.05))
        elif matches_desesperanca >= 2:
            nivel = "alto"
            score = 0.75
        elif matches_moderado > 0:
            bonus = 0
            if matches_absolutas >= 2:
                bonus += 0.1
            if matches_negativos >= 2:
                bonus += 0.1
            if matches_desesperanca >= 1:
                bonus += 0.15
            if frases_curtas_neg:
                bonus += 0.05

            score = min(0.74, 0.45 + (matches_moderado * 0.05) + bonus)

            if score >= 0.7:
                nivel = "alto"
            else:
                nivel = "moderado"
        elif matches_leve > 0:
            bonus = 0
            if matches_absolutas >= 1:
                bonus += 0.05
            if matches_negativos >= 1:
                bonus += 0.05
            if frases_curtas_neg:
                bonus += 0.05

            score = min(0.44, 0.15 + (matches_leve * 0.04) + bonus)

            if score >= 0.4:
                nivel = "moderado"
            else:
                nivel = "leve"
        elif (matches_absolutas + matches_negativos) >= 2 or frases_curtas_neg:
            nivel = "leve"
            score = 0.15
        else:
            nivel = "neutro"
            score = 0.0

        return {
            "nivel": nivel,
            "score": round(score, 2),
            "emocoes_detectadas": emocoes,
            "categorias_corporativas": categorias_corp,
            "detalhes": {
                "keywords_alto": matches_alto,
                "keywords_moderado": matches_moderado,
                "keywords_leve": matches_leve,
                "palavras_absolutas": matches_absolutas,
                "padroes_negativos": matches_negativos,
                "ausencia_esperanca": matches_desesperanca,
                "frases_curtas_negativas": frases_curtas_neg,
            },
        }
