import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_extras.metric_cards import style_metric_cards
import locale

def call_to_action_page(df_compras, df_final, df_produtos, df_vendas_estoque, previsoes, sugestoes):

    # Definir o locale para português brasileiro
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')

    def format_brazilian(value):
        """Formata um número no padrão brasileiro."""
        return locale.format_string('%g', value, True)
    
    # st.write('### Recomendações de Ações: Sua Escolha, Nossa Integração')
    st.title('Recomendação e Integração')

    # Dados
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro']
    acoes_recomendadas = [10, 12, 15, 14, 9, 8, 11, 13, 10]
    acoes_realizadas = [8, 11, 14, 10, 7, 6, 9, 11, 9]

    # Criando o DataFrame
    dfa = pd.DataFrame({
        'Mês': meses,
        'Qte Ações recomendadas': acoes_recomendadas,
        'Qtd Ações realizadas': acoes_realizadas
    })

    # Calculando os totais e o percentual
    total_recomendadas = sum(acoes_recomendadas)
    total_realizadas = sum(acoes_realizadas)
    percentual_realizado = (total_realizadas / total_recomendadas) * 100

    # Criando colunas para métricas
    metrics_column1, metrics_column2, metrics_column3 = st.columns([1,1,3])

    # Exibindo as métricas nas respectivas colunas
    with metrics_column1:
        st.metric("Ações realizadas", total_realizadas, "")

    with metrics_column2:
        st.metric("(%) Realizado", f"{percentual_realizado:.0f}%", "")

    style_metric_cards()  # Se existir, aplique o estilo nos cards de métricas
   
    # Criando o gráfico de barras
    fig = go.Figure()

    # Adicionando ações recomendadas ao gráfico
    fig.add_trace(go.Bar(
        x=dfa['Mês'],
        y=dfa['Qte Ações recomendadas'],
        name='Ações Recomendadas',
        marker=dict(color='#CDCDCD'),  # Define a cor da coluna
        text=dfa['Qte Ações recomendadas'],  # Adiciona rótulos de texto
        textposition='outside'  # Define a posição dos rótulos
    ))

    # Adicionando ações realizadas ao gráfico
    fig.add_trace(go.Bar(
        x=dfa['Mês'],
        y=dfa['Qtd Ações realizadas'],
        name='Ações Realizadas',
        marker=dict(color='#1087B2'),  # Define a cor da coluna
        text=dfa['Qtd Ações realizadas'],  # Adiciona rótulos de texto
        textposition='outside'  # Define a posição dos rótulos
    ))

    # Atualizando o layout do gráfico
    fig.update_layout(
        title='',
        xaxis=dict(title='', showgrid=False),  # Oculta o rótulo do eixo x
        yaxis=dict(title='', showgrid=True),  # Oculta o rótulo do eixo y
        barmode='group',
        height=400,  # Ajuste a altura conforme necessário
        legend=dict(
            x=0.5,
            y=1.4,  # Ajuste a distância da legenda em relação ao gráfico
            xanchor='center',
            orientation='h'
        )
    )

    # Mostrando o gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)


    # Inicializa a session_state
    if 'aprovacoes' not in st.session_state:
        st.session_state.aprovacoes = []

    st.write('### Etapa: Avaliação e Aprovação de Sugestão de Compra')

    st.write('### 1. Método de Aprovação')
    
    col1, col2, col3 = st.columns(3)

    with col1:
        
        approval_method = st.selectbox('Escolha:', ['Selecione...', 'por Produto', 'por Setor'])

    with col2:
        st.write()
        
    with col3:
        st.write()

        
    # Inicialização das variáveis de estado da sessão, se necessário
    if "aprovacoes" not in st.session_state:
        st.session_state.aprovacoes = []

    if "aprovacoes_setor" not in st.session_state:
        st.session_state.aprovacoes_setor = []

    if approval_method == 'por Produto':
            
        # Obtenha a quantidade de produtos únicos e o total de 'Sugestão_Compra'
        total_produtos = len(df_final["Nome_Produto2"].unique())
        total_sugestao = df_final["Sugestao_Compra"].sum()
        
        # Informe o usuário sobre a quantidade de produtos e o total de 'Sugestão_Compra'
        st.write(f'Há {total_produtos} produtos que serão enviados à avaliação com um total de {format_brazilian(total_sugestao)} na Sugestão de Compra.')
        st.write('Selecione os produtos que deseja aprovar.')
        
        # Inicializar o registro dos produtos já vistos e aprovações, se necessário
        if "produtos_vistos" not in st.session_state:
            st.session_state.produtos_vistos = []

        # Obter a lista de produtos únicos e filtrar os já vistos
        produtos = df_final["Nome_Produto2"].unique()
        produtos_restantes = [produto for produto in produtos if produto not in st.session_state.produtos_vistos]
        
        if produtos_restantes:
            # Se ainda houver produtos não revisados
            current_produto = produtos_restantes[0]
            sugestao_value = df_final[df_final["Nome_Produto2"] == current_produto]["Sugestao_Compra"].values[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                            
                with st.expander(" ", expanded=True):
                    st.markdown(f"<div style='font-weight: bold;'>{current_produto}</div>", unsafe_allow_html=True)
                    st.write(f'Sugestão de Compra: {format_brazilian(sugestao_value)}')
                    
                    col_sim, col_nao = st.columns(2)
                    
                    # Use flags para capturar a seleção do usuário
                    if col_sim.button('Sim'):
                        st.session_state.aprovacoes.append({
                            "Nome_Produto2": current_produto, 
                            "Sugestao_Compra": sugestao_value, 
                            "Status": "Aprovado e enviado ao ERP da SAP"
                        })
                        st.session_state.produtos_vistos.append(current_produto)
                        
                    if col_nao.button('Não'):
                        st.session_state.produtos_vistos.append(current_produto)
                        
                # As mensagens são mostradas fora do "expander", mas ainda na mesma coluna
                if "Nome_Produto2" in [item.get("Nome_Produto2", "") for item in st.session_state.aprovacoes] and current_produto == st.session_state.aprovacoes[-1]["Nome_Produto2"]:
                    st.success("Aprovado e enviado ao ERP da SAP")
                elif current_produto in st.session_state.produtos_vistos and current_produto != st.session_state.aprovacoes[-1]["Nome_Produto2"]:
                    st.error("Não aprovado.")
            
            with col2:
                st.write()
                
            with col3:
                st.write()
                
        else:
            # Se todos os produtos já foram revisados
            st.success("Etapa de Aprovação concluída.")

            
    # Inicialização das variáveis de estado da sessão, se necessário
    if "aprovacoes" not in st.session_state:
        st.session_state.aprovacoes = []

    if "aprovacoes_setor" not in st.session_state:
        st.session_state.aprovacoes_setor = []

    if approval_method == 'por Setor':
        
        # Obtenha a quantidade de setores únicos e o total de 'Sugestão_Compra'
        total_setores = len(df_final["Setor"].unique())
        total_sugestao = df_final["Sugestao_Compra"].sum()
        
        # Informe o usuário sobre a quantidade de setores e o total de 'Sugestão_Compra'
        st.write(f'Há {total_setores} setores que serão enviados à avaliação com um total de {format_brazilian(total_sugestao)} na Sugestão de Compra.')
        st.write('Selecione os setores que deseja aprovar.')
        
        # Inicializar o registro dos setores já vistos e aprovações, se necessário
        if "setores_vistos" not in st.session_state:
            st.session_state.setores_vistos = []

        # Obter a lista de setores únicos e filtrar os já vistos
        setores = df_final["Setor"].unique()
        setores_restantes = [setor for setor in setores if setor not in st.session_state.setores_vistos]
        
        if setores_restantes:
            # Se ainda houver setores não revisados
            current_setor = setores_restantes[0]
            sugestao_value = df_final[df_final["Setor"] == current_setor]["Sugestao_Compra"].sum()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                
                with st.expander("", expanded=True):
                    st.markdown(f"<div style='font-weight: bold;'>{current_setor}</div>", unsafe_allow_html=True)
                    st.write(f'Sugestão de Compra para o Setor: {format_brazilian(sugestao_value)}')
                    
                    col_sim, col_nao = st.columns(2)
                    
                    # Use flags para capturar a seleção do usuário
                    if col_sim.button('Sim'):
                        st.session_state.aprovacoes_setor.append({
                            "Setor": current_setor, 
                            "Sugestao_Compra": sugestao_value, 
                            "Status": "Aprovado e enviado ao ERP da SAP"
                        })
                        st.session_state.setores_vistos.append(current_setor)
                    
                    if col_nao.button('Não'):
                        st.session_state.setores_vistos.append(current_setor)
                        
                # As mensagens são mostradas fora do "expander", mas ainda na mesma coluna
                if "Setor" in [item.get("Setor", "") for item in st.session_state.aprovacoes_setor] and current_setor == st.session_state.aprovacoes_setor[-1]["Setor"]:
                    st.success("Aprovado e enviado ao ERP da SAP")
                elif current_setor in st.session_state.setores_vistos and current_setor != st.session_state.aprovacoes_setor[-1]["Setor"]:
                    st.error("Não aprovado.")
            
            with col2:
                st.write()
                
            with col3:
                st.write()
                
        else:
            # Se todos os setores já foram revisados
            st.success("Etapa de Aprovação concluída.")
            
            total_aprovados = len([item for item in st.session_state.aprovacoes_setor if item["Status"] == "Aprovado e enviado ao ERP da SAP"])
            total_nao_aprovados = len(st.session_state.setores_vistos) - total_aprovados

            st.write(f"Total de setores aprovados e enviados ao ERP da SAP: {total_aprovados}")
            st.write(f"Total de setores não aprovados: {total_nao_aprovados}")


    # Seção de "Resultado da Aprovação":
    st.write('---')
    st.write('### 2. Resultado da Aprovação')

    # Decidir qual lista usar com base no método de aprovação
    if approval_method == 'por Produto':
        aprovs_data = st.session_state.aprovacoes
        columns_to_display = ["Nome_Produto2", "Sugestao_Compra", "Status"]
    elif approval_method == 'por Setor':
        aprovs_data = st.session_state.aprovacoes_setor
        columns_to_display = ["Setor", "Sugestao_Compra", "Status"]
    else:
        aprovs_data = []

    if aprovs_data:
        df_aprovacoes = pd.DataFrame(aprovs_data)
        
        # Aplicar formatação brasileira na coluna 'Sugestao_Compra'
        df_aprovacoes["Sugestao_Compra"] = df_aprovacoes["Sugestao_Compra"].apply(format_brazilian)
        
        st.dataframe(df_aprovacoes[columns_to_display])
