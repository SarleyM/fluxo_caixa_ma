import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Produção Externa - BOIANI",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🏭"
)

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    .stApp { background-color: #111116; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1A1A22; border-right: 1px solid #303030; }
    h1, h2, h3 { color: #FFFFFF !important; }
    
    /* Métrica de Valor Líquido em destaque */
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
    
    div.stButton > button:first-child {
        background-color: #28A745;
        color: white;
        border-radius: 5px;
        width: 100%;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS (Mantendo a estrutura para leitura) ---
DB_NAME = "fluxo_caixa_v3.db"

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data DESC", conn)
    conn.close()
    if not df.empty:
        df['data_dt'] = pd.to_datetime(df['data'])
    return df

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 6])
with col_logo:
    st.image("https://raw.githubusercontent.com/oseas-rezende/caixa_app/main/logo_boiani.png", width=120)
with col_titulo:
    st.title("Relatório de Fechamento - Produção")

st.markdown("---")

# --- SIDEBAR (Filtros de Data) ---
with st.sidebar:
    st.markdown("### 🗓️ Período de Fechamento")
    data_inicio = st.date_input("Início", value=datetime(2026, 4, 1), format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", value=datetime(2026, 4, 28), format="DD/MM/YYYY")
    
    st.markdown("---")
    st.info("O fechamento considera toda a produção entregue no período acima.")

# --- TELA DE FECHAMENTO ---
df_base = carregar_dados()

if not df_base.empty:
    # 1. Seleção do Prestador
    # (No futuro, esses nomes virão da tabela de Cadastro de Prestadores)
    lista_prestadores = ["Selecione...", "Prestador A", "Prestador B", "Oficina Central", "Costura Express"]
    prestador_selecionado = st.selectbox("🎯 Selecione o Prestador para Fechamento", lista_prestadores)

    if prestador_selecionado != "Selecione...":
        st.markdown(f"## Detalhamento: {prestador_selecionado}")
        
        # Filtragem por data e prestador (Simulado na descrição por enquanto)
        mask = (df_base['data_dt'].dt.date >= data_inicio) & (df_base['data_dt'].dt.date <= data_fim)
        df_filtrado = df_base.loc[mask].copy()

        if not df_filtrado.empty:
            # 2. Cálculos Financeiros
            subtotal_bruto = abs(df_filtrado['valor'].sum()) # Soma da produção no período
            
            # Layout de Resumo
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.metric("Subtotal Produzido", f"R$ {subtotal_bruto:,.2f}")
            
            with c2:
                # CAMPO DE DESCONTO SOLICITADO
                desconto = st.number_input("Desconto (Adiantamentos / Avarias)", min_value=0.0, value=0.0, step=0.01, format="%.2f")
            
            with c3:
                valor_liquido = subtotal_bruto - desconto
                st.metric("LÍQUIDO A PAGAR", f"R$ {valor_liquido:,.2f}", 
                          delta=f"- R$ {desconto:,.2f}" if desconto > 0 else None, 
                          delta_color="inverse")

            st.divider()

            # 3. Tabela Detalhada do que compõe esse valor
            st.subheader("📋 Itens Produzidos no Período")
            
            # Formatando para exibição
            df_display = df_filtrado[['data', 'categoria', 'valor', 'descricao']].copy()
            df_display['valor'] = df_display['valor'].apply(lambda x: f"R$ {abs(x):,.2f}")
            
            st.table(df_display)

            # 4. Ações de Fechamento
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                if st.button("✅ Finalizar e Salvar Fechamento"):
                    st.success(f"Fechamento de {prestador_selecionado} salvo no histórico!")
                    # Aqui futuramente salvaremos em uma tabela 'fechamentos_concluidos'
            
            with col_btn2:
                # Exportação para PDF ou Excel do fechamento específico
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Fechamento')
                
                st.download_button(
                    label="📥 Baixar Comprovante (Excel)",
                    data=output.getvalue(),
                    file_name=f"fechamento_{prestador_selecionado}_{data_inicio.strftime('%d%m')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        else:
            st.warning(f"Nenhuma produção encontrada para {prestador_selecionado} neste período.")
    else:
        st.info("Escolha um prestador acima para visualizar o fechamento e aplicar descontos.")
else:
    st.error("Não há dados de produção carregados no sistema.")
