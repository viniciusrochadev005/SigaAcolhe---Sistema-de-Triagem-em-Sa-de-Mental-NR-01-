/**
 * SigaAcolhe RH — Lógica do Dashboard
 * Busca dados diretamente do Supabase e renderiza os gráficos e recomendações.
 */

document.addEventListener('DOMContentLoaded', async () => {
    // Se não estiver logado ou na página errada, ignora
    if (localStorage.getItem('rh_logged_in') !== 'true' || !document.getElementById('main-content')) {
        return;
    }

    const sb = window.supabaseClient;
    const periodSelect = document.getElementById('period-select');
    
    // Obter dias da URL (?dias=30) ou usar o valor do select
    const urlParams = new URLSearchParams(window.location.search);
    let dias = parseInt(urlParams.get('dias')) || parseInt(periodSelect.value);
    periodSelect.value = dias;

    periodSelect.addEventListener('change', (e) => {
        window.location.href = `?dias=${e.target.value}`;
    });

    try {
        await carregarDados(sb, dias);
        document.getElementById('loading').style.display = 'none';
        document.getElementById('main-content').style.display = 'block';
    } catch (err) {
        console.error("Erro ao carregar dados:", err);
        document.getElementById('loading').innerHTML = `<p style="color:red">Erro ao conectar com o banco de dados. Verifique sua chave no supabase-config.js.</p>`;
    }
});

async function carregarDados(sb, dias) {
    const dataInicio = new Date();
    dataInicio.setDate(dataInicio.getDate() - dias);
    const dataIso = dataInicio.toISOString().split('T')[0];

    // 1. Buscar métricas diárias
    const { data: metricas, error: errMetricas } = await sb
        .from('metricas_diarias')
        .select('*')
        .gte('data', dataIso)
        .order('data', { ascending: true });

    if (errMetricas) throw errMetricas;

    // 2. Buscar sessões recentes
    const { data: sessoes, error: errSessoes } = await sb
        .from('sessoes')
        .select('*')
        .not('data_fim', 'is', null)
        .order('data_fim', { ascending: false })
        .limit(10);

    if (errSessoes) throw errSessoes;

    // Processar os dados
    const resumo = compilarResumo(metricas);
    
    atualizarCards(resumo);
    renderizarGraficoCategorias(resumo.categorias);
    renderizarGraficoTendencia(metricas);
    renderizarRecomendacoes(resumo);
    renderizarSessoesRecentes(sessoes);
}

function compilarResumo(metricas) {
    let total = 0, neutro = 0, leve = 0, moderado = 0, alto = 0;
    let scoreSum = 0;
    let categorias = {};

    metricas.forEach(row => {
        const t = row.total_sessoes || 0;
        total += t;
        neutro += row.sessoes_neutro || 0;
        leve += row.sessoes_leve || 0;
        moderado += row.sessoes_moderado || 0;
        alto += row.sessoes_alto || 0;
        
        scoreSum += (row.score_medio_dia || 0) * t;

        const cats = row.categorias_agregadas || {};
        for (const [cat, count] of Object.entries(cats)) {
            categorias[cat] = (categorias[cat] || 0) + count;
        }
    });

    return {
        total, neutro, leve, moderado, alto,
        score_medio: total > 0 ? (scoreSum / total) : 0,
        categorias
    };
}

function atualizarCards(resumo) {
    document.getElementById('total-sessoes').textContent = resumo.total;
    document.getElementById('sessoes-leve').textContent = resumo.leve + resumo.neutro;
    document.getElementById('sessoes-moderado').textContent = resumo.moderado;
    document.getElementById('sessoes-alto').textContent = resumo.alto;

    const scoreDiv = document.getElementById('score-value');
    const scoreBar = document.getElementById('score-bar');
    
    scoreDiv.textContent = (resumo.score_medio * 10).toFixed(1) + '/10';
    scoreBar.style.width = (resumo.score_medio * 100) + '%';
    
    if (resumo.score_medio < 0.4) {
        scoreDiv.style.color = 'var(--success)';
        scoreBar.style.backgroundColor = 'var(--success)';
    } else if (resumo.score_medio < 0.7) {
        scoreDiv.style.color = 'var(--warning)';
        scoreBar.style.backgroundColor = 'var(--warning)';
    } else {
        scoreDiv.style.color = 'var(--danger)';
        scoreBar.style.backgroundColor = 'var(--danger)';
    }
}

function renderizarGraficoCategorias(categoriasData) {
    const ctx = document.getElementById('categorias-chart').getContext('2d');
    
    const labels = Object.keys(categoriasData).map(k => {
        const names = {
            'burnout': 'Burnout', 'ansiedade': 'Ansiedade',
            'depressão': 'Depressão', 'estresse_laboral': 'Estresse Laboral',
            'clima_organizacional': 'Clima Organizacional'
        };
        return names[k] || k;
    });
    const values = Object.values(categoriasData);

    if (labels.length === 0) {
        document.getElementById('categorias-chart').outerHTML = '<div class="empty-state">Sem dados no período.</div>';
        return;
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Ocorrências',
                data: values,
                backgroundColor: 'rgba(13, 148, 136, 0.2)',
                borderColor: '#0D9488',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            plugins: { legend: { display: false } }
        }
    });
}

function renderizarGraficoTendencia(metricas) {
    const ctx = document.getElementById('tendencia-chart').getContext('2d');
    
    if (metricas.length === 0) {
        document.getElementById('tendencia-chart').outerHTML = '<div class="empty-state">Sem dados no período.</div>';
        return;
    }

    const labels = metricas.map(m => {
        const [y, mm, d] = m.data.split('-');
        return `${d}/${mm}`;
    });
    const dataModerado = metricas.map(m => m.sessoes_moderado || 0);
    const dataAlto = metricas.map(m => m.sessoes_alto || 0);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Risco Alto',
                    data: dataAlto,
                    borderColor: '#EF4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.3, fill: true
                },
                {
                    label: 'Risco Moderado',
                    data: dataModerado,
                    borderColor: '#F59E0B',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.3, fill: true
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
            plugins: { legend: { position: 'top' } }
        }
    });
}

function renderizarRecomendacoes(resumo) {
    const container = document.getElementById('recomendacoes-container');
    const total = resumo.total;
    let recs = [];

    if (total === 0) {
        container.innerHTML = '<div class="rec-item info"><div class="rec-icon">📊</div><div class="rec-content"><h4>Sem dados</h4><p>Aguardando interações dos funcionários.</p></div></div>';
        return;
    }

    const pctAlto = total > 0 ? (resumo.alto / total) * 100 : 0;
    const catTotal = Object.values(resumo.categorias).reduce((a,b)=>a+b, 0) || 1;

    if (pctAlto >= 10) {
        recs.push({ tipo: 'danger', icon: '🚨', title: `Urgente: ${pctAlto.toFixed(0)}% com Risco Alto`, desc: 'Volume crítico. Avalie disponibilizar canal direto com psicólogo.' });
    }

    for (const [cat, count] of Object.entries(resumo.categorias).sort((a,b) => b[1]-a[1])) {
        const pct = (count / catTotal) * 100;
        if (cat === 'burnout' && pct >= 25) recs.push({ tipo: 'warning', icon: '🔥', title: `Sinais de Burnout (${pct.toFixed(0)}%)`, desc: 'Recomendação: Palestras de gestão de estresse e avaliação de carga.' });
        if (cat === 'ansiedade' && pct >= 20) recs.push({ tipo: 'warning', icon: '😰', title: `Ansiedade Alta (${pct.toFixed(0)}%)`, desc: 'Recomendação: Programa de mindfulness e revisão de prazos/metas.' });
        if (cat === 'depressão' && pct >= 15) recs.push({ tipo: 'danger', icon: '💙', title: `Depressão (${pct.toFixed(0)}%)`, desc: 'Recomendação: Parceria com especialistas em saúde mental.' });
    }

    if (recs.length === 0) {
        recs.push({ tipo: 'info', icon: '📋', title: 'Conformidade NR-01', desc: 'Métricas estáveis. Mantenha o monitoramento contínuo.' });
    }

    container.innerHTML = recs.map(r => `
        <div class="rec-item ${r.tipo}">
            <div class="rec-icon">${r.icon}</div>
            <div class="rec-content">
                <h4>${r.title}</h4>
                <p>${r.desc}</p>
            </div>
        </div>
    `).join('');
}

function renderizarSessoesRecentes(sessoes) {
    const container = document.getElementById('sessoes-recentes-container');
    
    if (sessoes.length === 0) {
        container.innerHTML = '<div class="empty-state">Nenhuma sessão registrada recentemente.</div>';
        return;
    }

    container.innerHTML = sessoes.map(s => {
        const data = new Date(s.data_fim).toLocaleString('pt-BR');
        let badge = s.nivel_risco_max || 'neutro';
        return `
            <div class="session-item">
                <div class="session-info">
                    <span class="session-date">${data}</span>
                    <span class="session-detail">${s.duracao_minutos} min • ${s.total_mensagens} msgs</span>
                </div>
                <span class="risk-badge ${badge}">${badge}</span>
            </div>
        `;
    }).join('');
}
