// Configuração do Supabase (Apenas Leitura no Frontend)
// Como é um app de RH, estas chaves ficam visíveis no JS client side (Anon Key).
// Em um ambiente produtivo real com dados sensíveis, RLS (Row Level Security) 
// deve estar habilitado para garantir que apenas usuários logados (Auth Supabase) vejam.
// Para este escopo, a proteção é a tela de login simples.

const SUPABASE_URL = 'https://scbxxuabwbsuqzizertx.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjYnh4dWFid2JzdXF6aXplcnR4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc2NTUwNjUsImV4cCI6MjA5MzIzMTA2NX0.KaRE3t7qydAkSHgjuEtfepgZr1b7ltIe2bHVRvLMLc4';

// Precisamos importar o script do Supabase no HTML: 
// <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
// Isso cria a global `supabase`

// Instância global do Supabase
window.supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
