"""
SigaAcolhe — Banco de Dados Supabase.

Armazena sessões de conversa (anônimas) e métricas agregadas
para o painel RH na nuvem via Supabase.
"""

import os
import datetime
from supabase import create_client, Client

def _get_supabase() -> Client:
    """Retorna o cliente do Supabase."""
    url: str = os.environ.get("SUPABASE_URL", "")
    key: str = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        raise ValueError("Credenciais do Supabase não configuradas no .env")
    return create_client(url, key)


def iniciar_sessao() -> int:
    """Cria uma nova sessão e retorna o ID."""
    try:
        supabase = _get_supabase()
        data = supabase.table("sessoes").insert({
            "data_inicio": datetime.datetime.now().isoformat()
        }).execute()
        
        if data.data and len(data.data) > 0:
            return data.data[0]["id"]
        return -1
    except Exception as e:
        print(f"[ERRO SUPABASE INICIAR SESSÃO] {e}")
        return -1


def encerrar_sessao(
    sessao_id: int,
    nivel_risco_max: str,
    score_medio: float,
    categorias: dict,
    resumo_ia: str,
    total_mensagens: int,
    emocoes_detectadas: list,
):
    """Finaliza uma sessão com os dados coletados."""
    if sessao_id <= 0:
        return

    try:
        supabase = _get_supabase()
        
        res = supabase.table("sessoes").select("data_inicio").eq("id", sessao_id).execute()
        duracao = 0.0
        if res.data and len(res.data) > 0:
            inicio = datetime.datetime.fromisoformat(res.data[0]["data_inicio"]).replace(tzinfo=None)
            duracao = (datetime.datetime.now() - inicio).total_seconds() / 60.0

        supabase.table("sessoes").update({
            "data_fim": datetime.datetime.now().isoformat(),
            "duracao_minutos": round(duracao, 1),
            "nivel_risco_max": nivel_risco_max,
            "score_medio": round(score_medio, 2),
            "categorias": categorias, # Supabase aceita dict direto para JSON/JSONB
            "resumo_ia": resumo_ia,
            "total_mensagens": total_mensagens,
            "emocoes_detectadas": emocoes_detectadas # Supabase aceita list para JSON/JSONB/Array
        }).eq("id", sessao_id).execute()

        _atualizar_metricas_diarias(supabase, nivel_risco_max, categorias, score_medio)
    except Exception as e:
        print(f"[ERRO SUPABASE ENCERRAR SESSÃO] {e}")


def _atualizar_metricas_diarias(
    supabase: Client,
    nivel: str,
    categorias: dict,
    score: float,
):
    """Atualiza ou cria a métrica do dia."""
    hoje = datetime.date.today().isoformat()

    try:
        res = supabase.table("metricas_diarias").select("*").eq("data", hoje).execute()
        
        if res.data and len(res.data) > 0:
            row = res.data[0]
            total = row["total_sessoes"] + 1
            campo_nivel = f"sessoes_{nivel}" if nivel in ("neutro", "leve", "moderado", "alto") else "sessoes_neutro"
            novo_nivel_count = row.get(campo_nivel, 0) + 1

            cat_existentes = row.get("categorias_agregadas", {}) or {}
            for cat, valor in categorias.items():
                if cat in cat_existentes:
                    cat_existentes[cat] = cat_existentes[cat] + 1
                else:
                    cat_existentes[cat] = 1

            score_novo = ((row.get("score_medio_dia", 0.0) * row["total_sessoes"]) + score) / total

            supabase.table("metricas_diarias").update({
                "total_sessoes": total,
                campo_nivel: novo_nivel_count,
                "categorias_agregadas": cat_existentes,
                "score_medio_dia": round(score_novo, 2)
            }).eq("id", row["id"]).execute()
        else:
            cat_inicial = {}
            for cat, valor in categorias.items():
                cat_inicial[cat] = 1

            campos_nivel = {"sessoes_neutro": 0, "sessoes_leve": 0, "sessoes_moderado": 0, "sessoes_alto": 0}
            campo = f"sessoes_{nivel}" if f"sessoes_{nivel}" in campos_nivel else "sessoes_neutro"
            campos_nivel[campo] = 1

            supabase.table("metricas_diarias").insert({
                "data": hoje,
                "total_sessoes": 1,
                "sessoes_neutro": campos_nivel["sessoes_neutro"],
                "sessoes_leve": campos_nivel["sessoes_leve"],
                "sessoes_moderado": campos_nivel["sessoes_moderado"],
                "sessoes_alto": campos_nivel["sessoes_alto"],
                "categorias_agregadas": cat_inicial,
                "score_medio_dia": round(score, 2)
            }).execute()
    except Exception as e:
        print(f"[ERRO SUPABASE MÉTRICAS] {e}")



def obter_resumo_geral(dias: int = 30) -> dict:
    """Retorna resumo geral dos últimos N dias."""
    try:
        supabase = _get_supabase()
        data_inicio = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()

        res = supabase.table("metricas_diarias").select("*").gte("data", data_inicio).execute()
        
        total = 0
        neutro = 0
        leve = 0
        moderado = 0
        alto = 0
        score_sum = 0
        categorias_total = {}

        if res.data:
            for row in res.data:
                total += row.get("total_sessoes", 0)
                neutro += row.get("sessoes_neutro", 0)
                leve += row.get("sessoes_leve", 0)
                moderado += row.get("sessoes_moderado", 0)
                alto += row.get("sessoes_alto", 0)
                
                score_sum += row.get("score_medio_dia", 0.0) * row.get("total_sessoes", 0)
                
                cats = row.get("categorias_agregadas", {}) or {}
                for cat, count in cats.items():
                    categorias_total[cat] = categorias_total.get(cat, 0) + count

        score_medio = (score_sum / total) if total > 0 else 0

        return {
            "total_sessoes": total,
            "sessoes_neutro": neutro,
            "sessoes_leve": leve,
            "sessoes_moderado": moderado,
            "sessoes_alto": alto,
            "score_medio": round(score_medio, 2),
            "categorias": categorias_total,
            "periodo_dias": dias,
        }
    except Exception as e:
        print(f"[ERRO SUPABASE RESUMO GERAL] {e}")
        return {
            "total_sessoes": 0, "sessoes_neutro": 0, "sessoes_leve": 0,
            "sessoes_moderado": 0, "sessoes_alto": 0, "score_medio": 0.0,
            "categorias": {}, "periodo_dias": dias
        }


def obter_tendencia(dias: int = 30) -> list:
    """Retorna métricas diárias para gráfico de tendência."""
    try:
        supabase = _get_supabase()
        data_inicio = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()

        res = supabase.table("metricas_diarias").select(
            "data, total_sessoes, sessoes_leve, sessoes_moderado, sessoes_alto, score_medio_dia, categorias_agregadas"
        ).gte("data", data_inicio).order("data").execute()

        resultado = []
        if res.data:
            for r in res.data:
                resultado.append({
                    "data": r["data"],
                    "total_sessoes": r.get("total_sessoes", 0),
                    "sessoes_leve": r.get("sessoes_leve", 0),
                    "sessoes_moderado": r.get("sessoes_moderado", 0),
                    "sessoes_alto": r.get("sessoes_alto", 0),
                    "score_medio": r.get("score_medio_dia", 0.0),
                    "categorias": r.get("categorias_agregadas", {}) or {},
                })
        return resultado
    except Exception as e:
        print(f"[ERRO SUPABASE TENDÊNCIA] {e}")
        return []


def obter_sessoes_recentes(limite: int = 20) -> list:
    """Retorna as sessões mais recentes para o painel RH."""
    try:
        supabase = _get_supabase()
        
        res = supabase.table("sessoes").select(
            "id, data_inicio, data_fim, duracao_minutos, nivel_risco_max, score_medio, categorias, resumo_ia, total_mensagens, emocoes_detectadas"
        ).not_.is_("data_fim", "null").order("data_fim", desc=True).limit(limite).execute()

        resultado = []
        if res.data:
            for r in res.data:
                resultado.append({
                    "id": r["id"],
                    "data_inicio": r["data_inicio"],
                    "data_fim": r["data_fim"],
                    "duracao_minutos": r.get("duracao_minutos", 0.0),
                    "nivel_risco_max": r.get("nivel_risco_max", "neutro"),
                    "score_medio": r.get("score_medio", 0.0),
                    "categorias": r.get("categorias", {}) or {},
                    "resumo_ia": r.get("resumo_ia", ""),
                    "total_mensagens": r.get("total_mensagens", 0),
                    "emocoes_detectadas": r.get("emocoes_detectadas", []) or [],
                })

        return resultado
    except Exception as e:
        print(f"[ERRO SUPABASE SESSÕES RECENTES] {e}")
        return []


def gerar_recomendacoes(resumo: dict) -> list:
    """Gera recomendações automáticas baseadas nos dados agregados."""
    recomendacoes = []
    total = resumo.get("total_sessoes", 0)

    if total == 0:
        return [
            {
                "tipo": "info",
                "icone": "📊",
                "titulo": "Sem dados suficientes",
                "descricao": "Ainda não há sessões registradas. Incentive os funcionários a usarem o SigaAcolhe.",
            }
        ]

    categorias = resumo.get("categorias", {})
    pct_alto = (resumo["sessoes_alto"] / total * 100) if total > 0 else 0
    pct_moderado = (resumo["sessoes_moderado"] / total * 100) if total > 0 else 0

    cat_total = sum(categorias.values()) if categorias else 1

    for cat, count in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
        pct = (count / cat_total * 100) if cat_total > 0 else 0

        if cat == "burnout" and pct >= 25:
            recomendacoes.append({
                "tipo": "warning",
                "icone": "🔥",
                "titulo": f"Burnout detectado em {pct:.0f}% das conversas",
                "descricao": (
                    "Recomendação: Contratar palestra sobre gestão do estresse e equilíbrio trabalho-vida. "
                    "Avaliar distribuição de carga de trabalho entre as equipes."
                ),
            })
        elif cat == "ansiedade" and pct >= 20:
            recomendacoes.append({
                "tipo": "warning",
                "icone": "😰",
                "titulo": f"Ansiedade presente em {pct:.0f}% das conversas",
                "descricao": (
                    "Recomendação: Avaliar prazos e metas. Considerar programa de mindfulness "
                    "ou meditação guiada no ambiente de trabalho."
                ),
            })
        elif cat == "depressão" and pct >= 15:
            recomendacoes.append({
                "tipo": "danger",
                "icone": "💙",
                "titulo": f"Sinais de depressão em {pct:.0f}% das conversas",
                "descricao": (
                    "Recomendação: Disponibilizar atendimento psicológico aos funcionários. "
                    "Considerar parceria com especialistas em saúde mental."
                ),
            })
        elif cat == "estresse_laboral" and pct >= 25:
            recomendacoes.append({
                "tipo": "warning",
                "icone": "⚡",
                "titulo": f"Estresse laboral em {pct:.0f}% das conversas",
                "descricao": (
                    "Recomendação: Revisar processos de trabalho. Promover pausas regulares "
                    "e atividades de descompressão."
                ),
            })
        elif cat == "clima_organizacional" and pct >= 20:
            recomendacoes.append({
                "tipo": "warning",
                "icone": "🏢",
                "titulo": f"Problemas de clima organizacional em {pct:.0f}% das conversas",
                "descricao": (
                    "Recomendação: Realizar pesquisa de clima. Promover treinamento de liderança "
                    "e comunicação para gestores."
                ),
            })

    if pct_alto >= 10:
        recomendacoes.insert(0, {
            "tipo": "danger",
            "icone": "🚨",
            "titulo": f"URGENTE: {pct_alto:.0f}% de sessões com risco alto",
            "descricao": (
                "Alto volume de casos críticos. Acionar equipe de saúde ocupacional imediatamente. "
                "Considerar disponibilizar linha direta com psicólogo."
            ),
        })

    if pct_moderado >= 40:
        recomendacoes.append({
            "tipo": "warning",
            "icone": "⚠️",
            "titulo": f"{pct_moderado:.0f}% de sessões com risco moderado",
            "descricao": (
                "Volume significativo de sofrimento moderado. Organizar rodas de conversa "
                "e ações preventivas conforme NR-01."
            ),
        })

    recomendacoes.append({
        "tipo": "info",
        "icone": "📋",
        "titulo": "Conformidade NR-01 — Riscos Psicossociais",
        "descricao": (
            f"Período analisado: {resumo['periodo_dias']} dias | "
            f"{total} sessões registradas | "
            f"Score médio: {resumo['score_medio']:.2f}. "
            "Mantenha o monitoramento contínuo conforme exigido pela NR-01."
        ),
    })

    return recomendacoes
