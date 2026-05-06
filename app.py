import streamlit as st
import pandas as pd
import sqlite3
import io
import plotly.express as px
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Fluxo de Caixa", layout="wide", page_icon="💰")

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

# --- SIDEBAR (Filtros e Exportação) ---
with st.sidebar:
    # 📦 IMAGEM DA CAIXA ACIMA DO FILTRO
    st.image("https://via.placeholder.com/150x150.png?text=Relatórios", width=80) 
    st.title("Filtros de Relatório")
    
    data_inicio = st.date_input("Início", datetime(2026, 4, 1), format="DD/MM/YYYY")
    data_fim = st.date_input("Fim", datetime(2026, 5, 30), format="DD/MM/YYYY")
    
    st.divider()
    st.markdown("### 📥 Exportação")
    df_base = carregar_dados()
    if not df_base.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_export = df_base.copy()
            df_export['data'] = pd.to_datetime(df_export['data']).dt.strftime('%d/%m/%Y')
            df_export[['data', 'tipo', 'categoria', 'valor', 'descricao']].to_excel(writer, index=False, sheet_name='Relatório')
        st.download_button("📊 Baixar XLSX Completo", output.getvalue(), "fluxo_caixa.xlsx", 
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- CABEÇALHO ---
col_logo, col_titulo, col_boneco = st.columns([1, 4, 1])

with col_logo:
    # Substitua pelo caminho da sua imagem da BOIANI
    st.image("https://via.placeholder.com/150x150.png?text=BOIANI", width=100) 

with col_titulo:
    st.title("Gestão de Fluxo de Caixa")
    st.caption("Controle financeiro inteligente com armazenamento local")

with col_boneco:
    # 👤 IMAGEM DO BONECO NA RETA DO TÍTULO
    st.image("https://via.placeholder.com/150x150.png?text=Perfil", width=80) 

st.markdown("---")

# --- FORMULÁRIO DE LANÇAMENTO ---
with st.expander("➕ REALIZAR NOVO LANÇAMENTO", expanded=False):
    with st.form("form_novo", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dt = c1.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        tp = c2.selectbox("Tipo", ["Receita", "Despesa"])
        vl = c3.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        
        c4, c5 = st.columns([1, 2])
        cat = c4.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"])
        desc = c5.text_input("Descrição / Detalhes")
        
        if st.form_submit_button("✅ SALVAR", use_container_width=True):
            vl_final = vl if tp == "Receita" else -vl
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao) VALUES (?,?,?,?,?)",
                       (dt.strftime('%Y-%m-%d'), tp, cat, vl_final, desc))
            conn.commit()
            conn.close()
            st.success("Lançamento salvo com sucesso!")
            st.rerun()

# --- DASHBOARD DE RESUMO (BALÕES) ---
df_bruto = carregar_dados()

if not df_bruto.empty:
    df = df_bruto[(df_bruto['data_dt'].dt.date >= data_inicio) & (df_bruto['data_dt'].dt.date <= data_fim)].copy()
    
    if not df.empty:
        rec = df[df["valor"] > 0]["valor"].sum()
        desp = abs(df[df["valor"] < 0]["valor"].sum())
        saldo = rec - desp

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Total Entradas", f"R$ {rec:,.2f}")
        col_m2.metric("Total Saídas", f"R$ {desp:,.2f}", delta_color="inverse")
        col_m3.metric("Saldo do Período", f"R$ {saldo:,.2f}")

        st.divider()

        # --- GRÁFICOS ---
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown("#### 🍕 Gastos por Categoria")
            df_gastos = df[df['valor'] < 0].copy()
            df_gastos['valor_abs'] = df_gastos['valor'].abs()
            if not df_gastos.empty:
                fig_pie = px.pie(df_gastos, values='valor_abs', names='categoria', hole=0.4,
                                color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Sem despesas registradas no período.")

        with g2:
            st.markdown("#### 📈 Fluxo Líquido Diário")
            df_evolucao = df.groupby('data_dt')['valor'].sum().reset_index().sort_values('data_dt')
            fig_line = px.bar(df_evolucao, x='data_dt', y='valor', 
                             color='valor', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_line, use_container_width=True)

        # --- LISTA DE LANÇAMENTOS ---
        st.markdown("### 📋 Histórico Detalhado")
        st.divider()
        
        # Cabeçalho da Lista
        h1, h2, h3, h4, h5, h6 = st.columns([1.2, 1, 1.2, 1, 2, 0.8])
        h1.write("**Data**")
        h2.write("**Tipo**")
        h3.write("**Categoria**")
        h4.write("**Valor**")
        h5.write("**Descrição**")
        h6.write("**Excluir**")

        for _, row in df.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([1.2, 1, 1.2, 1, 2, 0.8])
            r1.write(row['data_dt'].strftime('%d/%m/%Y'))
            r2.write(row['tipo'])
            r3.write(row['categoria'])
            cor = "green" if row['valor'] > 0 else "red"
            r4.write(f":{cor}[R$ {abs(row['valor']):,.2f}]")
            r5.write(row['descricao'])
            
            # Botão de excluir simplificado
            if r6.button("🗑️", key=f"del_{row['id']}"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM movimentacoes WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.warning("Nenhum lançamento encontrado para o período filtrado.")
else:
    st.info("O banco de dados está vazio. Comece adicionando um novo lançamento!")
