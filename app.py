import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px
from datetime import date
import os
import io

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="Fluxo de Caixa Pro", layout="wide")

# --- CONEXÃO COM GOOGLE SHEETS ---
# No Streamlit Cloud, a URL deve estar em Settings > Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Tenta ler a planilha. ttl=0 evita cache para os dados virem sempre atualizados
        df = conn.read(ttl="0s")
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    except Exception:
        # Retorna estrutura vazia se a planilha estiver inacessível ou vazia
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Descrição'])

def salvar_dados(df_novo):
    # Atualiza a planilha inteira com o novo DataFrame
    conn.update(data=df_novo)

df = carregar_dados()
categorias = ["Vendas", "Fornecedores", "Aluguel", "Impostos", "Salários", "Marketing", "Outros"]

# --- CABEÇALHO HARMÔNICO ---
col_logo, col_titulo = st.columns([1, 10], gap="small") 

with col_logo:
    if os.path.exists("logo_ma.png"):
        st.image("logo_ma.png", width=80)
    else:
        st.write("📊") 

with col_titulo:
    st.markdown(
        """
        <h1 style='font-size: 42px; margin-top: 0px; margin-bottom: 0px; line-height: 80px; color: white;'>
            Gestão de Fluxo de Caixa
        </h1>
        """, 
        unsafe_allow_html=True
    )

st.divider()

# --- NOVO LANÇAMENTO (SEM FORM PARA BLOQUEAR O ENTER) ---
with st.expander("➕ Realizar Novo Lançamento", expanded=False):
    col1, col2, col3 = st.columns(3)
    data_mov = col1.date_input("Data", date.today(), format="DD/MM/YYYY", key="new_date")
    tipo = col2.selectbox("Tipo", ["Receita", "Despesa"], key="new_type")
    valor = col3.number_input("Valor (R$)", min_value=0.0, step=0.01, key="new_val")
    
    col4, col5 = st.columns(2)
    categoria = col4.selectbox("Categoria", categorias, key="new_cat")
    descricao = col5.text_input("Descrição / Detalhes", key="new_desc")
    
    if st.button("✅ Salvar na Nuvem", use_container_width=True):
        if valor > 0:
            novo_item = pd.DataFrame([{
                'Data': data_mov, 'Tipo': tipo, 'Categoria': categoria,
                'Valor': valor, 'Descrição': descricao
            }])
            df_final = pd.concat([df, novo_item], ignore_index=True)
            salvar_dados(df_final)
            st.success("Lançamento salvo com sucesso no Google Sheets!")
            st.rerun()
        else:
            st.error("Por favor, insira um valor válido.")

# --- SIDEBAR (FILTROS E EXPORTAÇÃO) ---
st.sidebar.header("📅 Filtros de Relatório")
data_inicio = st.sidebar.date_input("Início", date.today().replace(day=1), format="DD/MM/YYYY")
data_fim = st.sidebar.date_input("Fim", date.today(), format="DD/MM/YYYY")

# Filtragem
df_filtrado = df[(df['Data'] >= data_inicio) & (df['Data'] <= data_fim)]

st.sidebar.markdown("---")
st.sidebar.header("📥 Exportar")

if not df_filtrado.empty:
    # Excel
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='xlsxwriter') as writer:
        df_filtrado.to_excel(writer, index=False, sheet_name='Financeiro')
    st.sidebar.download_button("📊 Baixar em Excel", buf.getvalue(), f"fluxo_{date.today()}.xlsx", use_container_width=True)

    # PDF/HTML
    html_data = f"<h2>Relatório Financeiro</h2><p>Período: {data_inicio} a {data_fim}</p>{df_filtrado.to_html(index=False)}"
    st.sidebar.download_button("📄 Baixar em PDF (HTML)", html_data, f"relatorio_{date.today()}.html", use_container_width=True)
else:
    st.sidebar.warning("Sem dados para exportar.")

# --- DASHBOARD VISUAL ---
if not df_filtrado.empty:
    total_rec = df_filtrado[df_filtrado['Tipo'] == 'Receita']['Valor'].sum()
    total_des = df_filtrado[df_filtrado['Tipo'] == 'Despesa']['Valor'].sum()
    saldo = total_rec - total_des

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Entradas", f"R$ {total_rec:,.2f}")
    m2.metric("Total Saídas", f"R$ {total_des:,.2f}", delta=f"-{total_des:,.2f}", delta_color="inverse")
    m3.metric("Saldo Atual", f"R$ {saldo:,.2f}")

    c_esq, c_dir = st.columns([2, 1])
    with c_esq:
        fig_barra = px.bar(df_filtrado, x='Data', y='Valor', color='Tipo', barmode='group',
                          title="Movimentação Diária", color_discrete_map={'Receita': '#2ECC71', 'Despesa': '#E74C3C'})
        fig_barra.update_layout(template="plotly_dark")
        st.plotly_chart(fig_barra, use_container_width=True)
    with c_dir:
        fig_rosca = px.pie(df_filtrado[df_filtrado['Tipo'] == 'Despesa'], values='Valor', names='Categoria', hole=0.5, title="Gastos")
        fig_rosca.update_layout(template="plotly_dark")
        st.plotly_chart(fig_rosca, use_container_width=True)

# --- GERENCIAMENTO ---
st.divider()
st.subheader("📋 Gerenciar Movimentações")

col_h = st.columns([1.5, 1.5, 1.5, 1.5, 2.5, 1.5])
col_h[0].markdown("**Data**"); col_h[1].markdown("**Tipo**"); col_h[2].markdown("**Categoria**")
col_h[3].markdown("**Valor**"); col_h[4].markdown("**Descrição**"); col_h[5].markdown("**Ações**")

for idx, row in df.sort_index(ascending=False).iterrows():
    r = st.columns([1.5, 1.5, 1.5, 1.5, 2.5, 1.5])
    r[0].text(row['Data'].strftime('%d/%m/%Y'))
    r[1].text(f"{'🟢' if row['Tipo'] == 'Receita' else '🔴'} {row['Tipo']}")
    r[2].text(row['Categoria'])
    r[3].text(f"R$ {row['Valor']:,.2f}")
    r[4].text(str(row['Descrição'])[:30])
    
    b_edit, b_del = r[5].columns(2)
    if b_edit.button("✏️", key=f"e_{idx}"):
        st.session_state['editing'] = idx
        st.rerun()
    if b_del.button("🗑️", key=f"d_{idx}"):
        st.session_state['deleting'] = idx
        st.rerun()

# Modais (Edição e Exclusão)
if 'editing' in st.session_state:
    idx_e = st.session_state['editing']
    with st.expander("📝 Editar Lançamento", expanded=True):
        with st.form("edit_form"):
            ed_dat = st.date_input("Data", df.loc[idx_e, 'Data'])
            ed_val = st.number_input("Valor", value=float(df.loc[idx_e, 'Valor']))
            ed_des = st.text_input("Descrição", value=df.loc[idx_e, 'Descrição'])
            if st.form_submit_button("Atualizar na Planilha"):
                df.at[idx_e, 'Data'], df.at[idx_e, 'Valor'], df.at[idx_e, 'Descrição'] = ed_dat, ed_val, ed_des
                salvar_dados(df); del st.session_state['editing']; st.rerun()

if 'deleting' in st.session_state:
    idx_d = st.session_state['deleting']
    st.error(f"Deseja excluir permanentemente: {df.loc[idx_d, 'Descrição']}?")
    if st.button("Confirmar Exclusão"):
        df_novo = df.drop(idx_d)
        salvar_dados(df_novo); del st.session_state['deleting']; st.rerun()