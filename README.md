# SigaAcolhe - Sistema de Triagem em Saúde Mental (NR-01)

> 🎓 **Projeto Acadêmico & Destaque de Portfólio (Engenharia de Prompt)**
> 
> Este projeto foi desenvolvido como parte de um trabalho universitário para a disciplina de **Engenharia de Prompt**. A arquitetura do sistema, a lógica de negócio, a integração de APIs e a interface foram orquestradas e implementadas com o auxílio avançado de Inteligência Artificial (através do agente autônomo **Antigravity**).
> 
> 🎯 **Para Recrutadores e Avaliadores:** 
> Este repositório é uma demonstração prática da minha capacidade de utilizar **IA Generativa de ponta a ponta** para criar um produto real. Ele evidencia habilidades em:
> - **Orquestração de LLMs** e Prompt Engineering (integração com Llama 3 via Groq API).
> - **Engenharia de Software** (separação de responsabilidades entre Desktop App e Painel Web).
> - **Desenvolvimento Python** (interfaces nativas com `CustomTkinter`).
> - **Banco de Dados em Nuvem** (modelagem e persistência utilizando `Supabase`).

O **SigaAcolhe** é um ecossistema corporativo focado no apoio emocional preventivo e na conformidade com as normas da NR-01 relativas a riscos psicossociais. Ele permite que os colaboradores tenham um espaço seguro e anônimo de desabafo (através de um Chat Desktop) enquanto fornece dados cruciais e agregados para o setor de RH tomar decisões embasadas (através de um Dashboard Web).

## Arquitetura do Projeto

O sistema foi modularizado em duas partes completamente independentes:

1. **`SigaAcolhe_Chat` (App Desktop)**
   - Aplicativo nativo em Python construído com `CustomTkinter`.
   - Interface limpa e acolhedora, desenvolvida para ser instalada em máquinas da empresa ou totens.
   - Motor de análise emocional avançado (conectado à API do Llama 3 via Groq) que identifica níveis de risco, padrões linguísticos e categorias corporativas (Burnout, Ansiedade, Depressão, Estresse Laboral, etc).
   - Comunica-se de forma assíncrona e segura com o Supabase.

2. **`SigaAcolhe_RH` (Painel Web)**
   - Dashboard 100% estático (HTML, CSS, JavaScript Vanilla).
   - Feito para ser hospedado gratuitamente em serviços como Netlify, Vercel ou GitHub Pages.
   - Comunica-se diretamente com o Supabase via API REST para buscar métricas diárias, nível de risco e apresentar recomendações preventivas automáticas.

## Tecnologias Utilizadas

- **Python 3.12+**
- **CustomTkinter** (Interface UI)
- **Supabase** (PostgreSQL Database e REST API)
- **Groq Cloud / Llama 3** (Processamento de Linguagem Natural e Motor Empático)
- **HTML5, CSS3, JS** (Painel de Gestão)

## Como Instalar e Rodar

### Para o Chat Desktop
```bash
cd SigaAcolhe_Chat
pip install -r ../requirements.txt
python desktop_app.py
```
*(Para facilitar a distribuição corporativa, você pode compilar o arquivo com o PyInstaller).*

### Para o Dashboard RH
O painel RH não necessita de um servidor back-end. Basta abrir o arquivo `index.html` em qualquer navegador ou hospedar a pasta `SigaAcolhe_RH` em um serviço de hospedagem estática.

## Configuração do Banco de Dados
O sistema utiliza o Supabase para armazenamento. Você precisa configurar as seguintes variáveis de ambiente no arquivo `.env` dentro da pasta `SigaAcolhe_Chat`, e no arquivo `js/supabase-config.js` dentro da pasta `SigaAcolhe_RH`.

```env
GROQ_API_KEY=sua_chave_groq
SUPABASE_URL=sua_url_supabase
SUPABASE_KEY=sua_chave_anon_supabase
```

## Conformidade com a NR-01
O painel cruza os dados anônimos coletados nas sessões e os categoriza em níveis de gravidade. Com base nisso, sugere ações de mitigação de risco (por exemplo, semanas de saúde mental, revisão de metas e distribuição de tarefas), garantindo que a empresa atue de forma ativa na saúde ocupacional dos seus funcionários.

## Avisos Legais
Este software é uma ferramenta de triagem e apoio inicial. **Ele não substitui o diagnóstico, acompanhamento ou tratamento médico especializado por psicólogos ou psiquiatras.** Em casos de emergência, sempre encaminhe o colaborador ao CVV (188) ou a uma emergência de saúde mental.
