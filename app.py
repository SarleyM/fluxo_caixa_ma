import streamlit as st
import pandas as pd
import sqlite3
import io
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Gestão Financeira Pro", layout="wide")

DB_NAME = "fluxo_caixa_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS movimentacoes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, tipo TEXT, categoria TEXT, valor REAL, descricao TEXT)''')
    conn.commit()
    conn.close()

def carregar_dados():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM movimentacoes ORDER BY data DESC", conn)
    conn.close()
    if not df.empty:
        df['data_dt'] = pd.to_datetime(df['data'])
    return df

init_db()

if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Filtros e Exportação")
    data_inicio = st.date_input("Início", datetime(2026, 4, 1), format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", datetime(2026, 5, 30), format="DD/MM/YYYY")
    
    st.divider()
    df_base = carregar_dados()
    if not df_base.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export = df_base.copy()
            df_export['data'] = pd.to_datetime(df_export['data']).dt.strftime('%d/%m/%Y')
            df_export[['data', 'tipo', 'categoria', 'valor', 'descricao']].to_excel(writer, index=False)
        st.download_button("📥 Baixar Relatório Excel", output.getvalue(), "fluxo_caixa.xlsx")

# --- CABEÇALHO ---
st.title("📊 Dashboard de Fluxo de Caixa")
st.markdown("---")

# --- FORMULÁRIO ---
titulo_form = "📝 Editando Registro" if st.session_state.edit_id else "➕ Novo Lançamento"
with st.expander(titulo_form, expanded=not st.session_state.edit_id):
    # Lógica de preenchimento para edição (simplificada para o exemplo)
    with st.form("form_financeiro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dt = c1.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        tp = c2.selectbox("Tipo", ["Receita", "Despesa"])
        vl = c3.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        cat = st.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"])
        desc = st.text_input("Descrição")
        
        if st.form_submit_button("Salvar Lançamento", use_container_width=True):
            vl_final = vl if tp == "Receita" else -vl
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao) VALUES (?,?,?,?,?)",
                       (dt.strftime('%Y-%m-%d'), tp, cat, vl_final, desc))
            conn.commit()
            conn.close()
            st.success("Lançamento salvo!")
            st.rerun()

# --- CARREGAMENTO E FILTRO ---
df_bruto = carregar_dados()
if not df_bruto.empty:
    df_filt = df_bruto[(df_bruto['data_dt'].dt.date >= data_inicio) & (df_bruto['data_dt'].dt.date <= data_fim)].copy()
    
    if not df_filt.empty:
        # --- 1. BALÕES DE RESUMO (METRICS) ---
        rec = df_filt[df_filt["valor"] > 0]["valor"].sum()
        desp = abs(df_filt[df_filt["valor"] < 0]["valor"].sum())
        saldo = rec - desp

        m1, m2, m3 = st.columns(3)
        m1.metric("Total de Entradas", f"R$ {rec:,.2f}")
        m2.metric("Total de Saídas", f"R$ {desp:,.2f}", delta_color="inverse")
        m3.metric("Saldo Geral", f"R$ {saldo:,.2f}", delta=f"{saldo:,.2f}")

        st.markdown("### 📈 Análise Visual")
        
        # --- 2. GRÁFICOS ---
        g1, g2 = st.columns(2)
        
        with g1:
            # Gráfico de Categorias (Pizza/Rosca)
            fig_cat = px.pie(df_filt, values=df_filt['valor'].abs(), names='categoria', 
                            title="Distribuição por Categoria", hole=0.4,
                            color_discrete_sequence=px.colors.qualitative.Safe)
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with g2:
            # Gráfico Entradas vs Saídas (Barras)
            resumo_tipo = df_filt.groupby('tipo')['valor'].abs().reset_index()
            fig_tipo = px.bar(resumo_tipo, x='tipo', y='valor', title="Entradas vs Saídas (R$)",
                             color='tipo', color_discrete_map={'Receita': '#2ecc71', 'Despesa': '#e74c3c'})
            st.plotly_chart(fig_tipo, use_container_width=True)

        # --- 3. TABELA COM AÇÕES ---
        st.markdown("### 📋 Histórico Detalhado")
        st.divider()
        
        # Cabeçalho manual
        h1, h2, h3, h4, h5, h6 = st.columns([1.2, 1, 1.2, 1, 2, 1])
        h1.write("**Data**")
        h2.write("**Tipo**")
        h3.write("**Categoria**")
        h4.write("**Valor**")
        h5.write("**Descrição**")
        h6.write("**Ações**")

        for _, row in df_filt.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([1.2, 1, 1.2, 1, 2, 1])
            r1.write(row['data_dt'].strftime('%d/%m/%Y'))
            r2.write(row['tipo'])
            r3.write(row['categoria'])
            r4.write(f"R$ {abs(row['valor']):,.2f}")
            r5.write(row['descricao'])
            
            # Botões de Ação
            btn_col1, btn_col2 = r6.columns(2)
            if btn_col1.button("✏️", key=f"ed_{row['id']}"):
                st.session_state.edit_id = row['id']
                st.rerun()
            if btn_col2.button("🗑️", key=f"dl_{row['id']}"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM movimentacoes WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.warning("Nenhum dado encontrado para as datas selecionadas.")
else:
    st.info("O banco de dados está vazio. Comece adicionando um novo lançamento!")
