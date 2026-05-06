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

# --- CONTROLE DE ESTADO (EDIÇÃO) ---
if 'edit_id' not in st.session_state:
    st.session_state.edit_id = None

# --- SIDEBAR (Filtros e Ícone de Caixa) ---
with st.sidebar:
    # 📦 ÍCONE DA CAIXA (Relatórios)
    st.image("https://cdn-icons-png.flaticon.com/512/2850/2850343.png", width=70) 
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
            df_export[['data', 'tipo', 'categoria', 'valor', 'descricao']].to_excel(writer, index=False)
        st.download_button("📊 Baixar XLSX", output.getvalue(), "fluxo_caixa.xlsx", 
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- CABEÇALHO (Logo + Título + Boneco) ---
col_logo, col_titulo, col_boneco = st.columns([1, 4, 1])

with col_logo:
    # Use sua logo oficial aqui
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=90) 

with col_titulo:
    st.title("Fluxo de Caixa")
    st.caption("Controle Boiani - Produção e Finanças")

with col_boneco:
    # 👤 ÍCONE DO BONECO (Usuário)
    st.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=70) 

st.markdown("---")

# --- FORMULÁRIO DINÂMICO (NOVO / EDITAR) ---
# Se houver um ID no estado de edição, buscamos os dados dele
dados_preenchidos = {"data": datetime.now(), "tipo": "Receita", "valor": 0.0, "cat": "Outros", "desc": ""}
if st.session_state.edit_id:
    conn = sqlite3.connect(DB_NAME)
    res = conn.execute("SELECT * FROM movimentacoes WHERE id=?", (st.session_state.edit_id,)).fetchone()
    conn.close()
    if res:
        dados_preenchidos = {
            "data": datetime.strptime(res[1], '%Y-%m-%d'),
            "tipo": res[2],
            "cat": res[3],
            "valor": abs(res[4]),
            "desc": res[5]
        }

titulo_expander = "📝 EDITAR LANÇAMENTO" if st.session_state.edit_id else "➕ REALIZAR NOVO LANÇAMENTO"
with st.expander(titulo_expander, expanded=st.session_state.edit_id is not None):
    with st.form("form_registro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        dt_reg = c1.date_input("Data", dados_preenchidos["data"], format="DD/MM/YYYY")
        tp_reg = c2.selectbox("Tipo", ["Receita", "Despesa"], index=0 if dados_preenchidos["tipo"]=="Receita" else 1)
        vl_reg = c3.number_input("Valor (R$)", value=dados_preenchidos["valor"], min_value=0.0, step=0.01, format="%.2f")
        
        c4, c5 = st.columns([1, 2])
        cat_reg = c4.selectbox("Categoria", ["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"],
                              index=["Vendas", "Suprimentos", "Aluguel", "Pessoal", "Marketing", "Outros"].index(dados_preenchidos["cat"]))
        desc_reg = c5.text_input("Descrição / Detalhes", value=dados_preenchidos["desc"])
        
        col_btn_salvar, col_btn_canc = st.columns([1, 0.3])
        if col_btn_salvar.form_submit_button("✅ SALVAR DADOS", use_container_width=True):
            vl_final = vl_reg if tp_reg == "Receita" else -vl_reg
            conn = sqlite3.connect(DB_NAME)
            if st.session_state.edit_id:
                conn.execute("UPDATE movimentacoes SET data=?, tipo=?, categoria=?, valor=?, descricao=? WHERE id=?",
                           (dt_reg.strftime('%Y-%m-%d'), tp_reg, cat_reg, vl_final, desc_reg, st.session_state.edit_id))
                st.session_state.edit_id = None
            else:
                conn.execute("INSERT INTO movimentacoes (data, tipo, categoria, valor, descricao) VALUES (?,?,?,?,?)",
                           (dt_reg.strftime('%Y-%m-%d'), tp_reg, cat_reg, vl_final, desc_reg))
            conn.commit()
            conn.close()
            st.rerun()
            
        if st.session_state.edit_id:
            if col_btn_canc.form_submit_button("CANCELAR"):
                st.session_state.edit_id = None
                st.rerun()

# --- DASHBOARD (BALÕES E GRÁFICOS) ---
df_bruto = carregar_dados()
if not df_bruto.empty:
    df = df_bruto[(df_bruto['data_dt'].dt.date >= data_inicio) & (df_bruto['data_dt'].dt.date <= data_fim)].copy()
    
    if not df.empty:
        # Métricas (Balões)
        rec = df[df["valor"] > 0]["valor"].sum()
        desp = abs(df[df["valor"] < 0]["valor"].sum())
        saldo = rec - desp

        st.markdown("### 💰 Resumo Financeiro")
        m1, m2, m3 = st.columns(3)
        m1.metric("Entradas", f"R$ {rec:,.2f}")
        m2.metric("Saídas", f"R$ {desp:,.2f}", delta_color="inverse")
        m3.metric("Saldo Líquido", f"R$ {saldo:,.2f}")

        # Gráficos
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_gastos = df[df['valor'] < 0].copy()
            if not df_gastos.empty:
                df_gastos['valor_abs'] = df_gastos['valor'].abs()
                fig_pie = px.pie(df_gastos, values='valor_abs', names='categoria', hole=0.4, title="Despesas por Categoria")
                st.plotly_chart(fig_pie, use_container_width=True)
        with g2:
            df_diario = df.groupby('data_dt')['valor'].sum().reset_index()
            fig_bar = px.bar(df_diario, x='data_dt', y='valor', title="Saldo Diário (R$)", color='valor', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- LISTA COM BOTÕES DE EDITAR E EXCLUIR ---
        st.markdown("### 📋 Movimentações Detalhadas")
        st.divider()
        
        # Cabeçalho da tabela
        h1, h2, h3, h4, h5, h6 = st.columns([1.2, 0.8, 1.2, 1, 2, 1])
        h1.write("**Data**")
        h2.write("**Tipo**")
        h3.write("**Categoria**")
        h4.write("**Valor**")
        h5.write("**Descrição**")
        h6.write("**Ações**")

        for _, row in df.iterrows():
            r1, r2, r3, r4, r5, r6 = st.columns([1.2, 0.8, 1.2, 1, 2, 1])
            r1.write(row['data_dt'].strftime('%d/%m/%Y'))
            r2.write(row['tipo'])
            r3.write(row['categoria'])
            cor = "green" if row['valor'] > 0 else "red"
            r4.write(f":{cor}[R$ {abs(row['valor']):,.2f}]")
            r5.write(row['descricao'])
            
            # Botões de Ação lado a lado
            btn_edit, btn_del = r6.columns(2)
            if btn_edit.button("✏️", key=f"edit_{row['id']}"):
                st.session_state.edit_id = row['id']
                st.rerun()
            if btn_del.button("🗑️", key=f"del_{row['id']}"):
                conn = sqlite3.connect(DB_NAME)
                conn.execute("DELETE FROM movimentacoes WHERE id=?", (row['id'],))
                conn.commit()
                conn.close()
                st.rerun()
    else:
        st.warning("Sem dados para este período.")
else:
    st.info("Inicie um lançamento para ver o dashboard.")
