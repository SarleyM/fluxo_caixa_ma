# --- TELA: RELATÓRIO DE FECHAMENTO ---
st.subheader("📑 Relatório de Fechamento de Prestador")

# 1. Filtros Superiores
col_f1, col_f2, col_f3 = st.columns([1, 1, 1])
with col_f1:
    data_ini = st.date_input("De:", value=datetime(2026, 4, 1))
with col_f2:
    data_fim = st.date_input("Até:", value=datetime(2026, 4, 28))
with col_f3:
    # Aqui buscaremos os nomes da sua tabela de prestadores futuramente
    lista_prestadores = ["Selecione...", "Prestador A", "Prestador B"] 
    prestador_sel = st.selectbox("Selecione o Prestador", lista_prestadores)

if prestador_sel != "Selecione...":
    # 2. Lógica de Filtragem (Exemplo baseada no seu DF atual)
    # No projeto final, aqui filtrará a tabela de PRODUÇÃO pelo nome do prestador
    df_fechamento = df_total[(df_total['data_dt'].dt.date >= data_ini) & 
                             (df_total['data_dt'].dt.date <= data_ini)]
    
    # Simulação de Cálculo de Produção
    subtotal_producao = abs(df_fechamento['valor'].sum()) 
    
    st.markdown(f"### Resumo: {prestador_sel}")
    
    # 3. Bloco de Fechamento Financeiro
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        st.metric("Subtotal Produção", f"R$ {subtotal_producao:,.2f}")
    
    with col_res2:
        # CAMPO DE DESCONTO solicitado
        valor_desconto = st.number_input("Valor de Desconto (R$)", min_value=0.0, step=10.0, format="%.2f")
    
    with col_res3:
        valor_liquido = subtotal_producao - valor_desconto
        st.metric("Total Líquido a Pagar", f"R$ {valor_liquido:,.2f}", delta=f"-R$ {valor_desconto:,.2f}", delta_color="inverse")

    # Botão para finalizar o acerto
    if st.button("Finalizar Fechamento e Gerar Recibo"):
        st.success(f"Fechamento de {prestador_sel} realizado com sucesso!")
        # Aqui podemos salvar em uma tabela 'historico_pagamentos'
