import streamlit as st
import pandas as pd
import openai
from decouple import config
import urllib.request
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from streamlit_extras.metric_cards import style_metric_cards
from datetime import datetime
from streamlit_option_menu import option_menu
import base64
import time


def dashboard_page(df_compras, df_final, df_produtos, df_vendas_estoque, previsoes, sugestoes):
    
    st.title("Análise Simplificada com a Stock ON")
    # st.markdown("<h1 style='font-size: 32px;'>Análise Descritiva e Preditiva: Simplificada com a Stock ON</h1>", unsafe_allow_html=True)

    # st.markdown("<span style='color:#666666'> Do descritivo e preditivo ao prescritivo. </span>", unsafe_allow_html=True)

    # Fazendo o merge entre df_final e df_vendas_estoque usando a coluna 'Produto_ID'
    df_merged = pd.merge(df_final, df_vendas_estoque, on='Produto_ID', how='inner')
    df_merged.rename(columns={
        'Nome_Produto2_x': 'Nome_Produto2',
        'SKU_x': 'SKU',
        'Setor_x': 'Setor',
        'Classificação ABC_x': 'Classificação ABC'
    }, inplace=True)
        
    df_filtered = df_merged
    df_filtered['Data'] = pd.to_datetime(df_filtered['Data'])

    def abbreviated_format_decimal(num):
        if num < 1_000:
            return '{:,.1f}'.format(num).replace(",", "@").replace(".", ",").replace("@", ".")
        elif num < 1_000_000:
            return '{:,.1f}k'.format(num/1_000).replace(",", "@").replace(".", ",").replace("@", ".")
        else:
            return '{:,.1f}M'.format(num/1_000_000).replace(",", "@").replace(".", ",").replace("@", ".")

    def brazilian_format(num):
        return '{:,.0f}'.format(num).replace(",", "@").replace(".", ",").replace("@", ".")

    def brazilian_currency_format(num):
        return 'R$ ' + brazilian_format(num) 

    def get_statistical_summary(df_final):
        """ Retorna o sumário estatístico das colunas numéricas """
        return df_final.describe()

    def get_data_type(df_final):
        """ Retorna os tipos de dados do dataframe """
        dtypes_df = df_final.dtypes.reset_index()
        dtypes_df.columns = ["Coluna", "Tipo de Dado"]
        return dtypes_df

    def get_products_below_min_stock(df_final):
        """ Retorna os produtos com quantidade abaixo do estoque mínimo """
        filtered_df = df_final[df_final['Quantidade_Estoque_Atual'] < df_final['Estoque_Minimo']]

        # Filtrando apenas as colunas desejadas
        filtered_df = filtered_df[['Nome_Produto2', 'Setor', 'Classificacao ABC', 'Estoque_Minimo', 'Quantidade_Estoque_Atual']]
        
        # Aplicando a formatação brasileira nas colunas desejadas
        filtered_df['Estoque_Minimo'] = filtered_df['Estoque_Minimo'].apply(lambda x: f"{brazilian_format(x)}")
        filtered_df['Quantidade_Estoque_Atual'] = filtered_df['Quantidade_Estoque_Atual'].apply(lambda x: f"{brazilian_format(x)}")

        if filtered_df.empty:  # Verifica se o DataFrame filtrado está vazio
            return "Não há produtos com estoque abaixo do mínimo."
        else:
            st.write("Os produtos abaixo do estoque mínimo recomendado são:")
            return filtered_df


    def get_abc_distribution(df_final):
        """ Retorna a distribuição da Classificação ABC """
        return df_final['Classificacao ABC'].value_counts()

    def get_total_purchase_suggestion(df_final):
        """ Retorna a quantidade total sugerida para compra """
        return df_final['Sugestao_Compra'].sum()

    def get_products_with_highest_lead_time(df_final):
        """ Retorna os produtos com o maior lead time """
        return df_final[df_final['Lead_Time_Dias'] == df_final['Lead_Time_Dias'].max()]

    def get_most_expensive_product(df_final):
        """ Retorna o produto mais caro """
        most_expensive = df_final[df_final['Custo_Unitario'] == df_final['Custo_Unitario'].max()]
        
        # Lista para armazenar os nomes dos produtos e seus respectivos custos
        products_list = []

        # Iterando sobre as linhas do dataframe mais_expensive para construir a lista de produtos
        for _, row in most_expensive.iterrows():
            product_name = row['Nome_Produto2']
            product_cost = row['Custo_Unitario']
            products_list.append(f"'{product_name}' no Valor de R$ {product_cost:.2f}")

        # Construindo a resposta final
        if len(products_list) == 1:
            response = f"O produto com maior valor agregado é: {products_list[0]}"
        else:
            products_str = ", ".join(products_list[:-1]) + " e " + products_list[-1]
            response = f"O(s) produto(s) com maior valor agregado são: {products_str}"

        return response
        
    FUNCTIONS_DICT = {
        "Estatísticas básicas": get_statistical_summary,
        "Tipos de Dados": get_data_type,
        "Quantos produtos estão abaixo do estoque mínimo recomendado?": get_products_below_min_stock,
        "Como está a distribuição da curva ABC?": get_abc_distribution,
        "Qual é o Total de sugestões de compra?": get_total_purchase_suggestion,
        "Quais são os produtos com maior lead time do fornecedor?": get_products_with_highest_lead_time,
        "Quais são os produtos com maior valor agregado?": get_most_expensive_product
    }
    
    # Chamando a chave para API com chatgpt
    
    openai_api_key = config('OPENAI_API_KEY')
    if not openai_api_key:
        st.error("Chave API da OpenAI não configurada.")
        raise ValueError("Chave API da OpenAI não encontrada!")
    openai.api_key = openai_api_key

    def graficos(df_final):
        
        GRAPH_WIDTH = 700
        GRAPH_HEIGHT = 400
        
        # Agrupando por Nome_Produto2 e agregando as colunas necessárias
        df_grouped = df_final.groupby('Nome_Produto2').agg({
            'Quantidade_Estoque_Atual': 'sum',
            'Estoque_Minimo': 'mean'
        }).reset_index()
        
        # Criando um espaço reservado para o gráfico
        graph_placeholder = st.empty()
        
        formatted_labels = df_final['Sugestao_Compra'].apply(brazilian_format)

        # Gráfico 1
        fig1 = px.bar(df_final, 
                    x='Nome_Produto2', 
                    y='Sugestao_Compra',
                    color='Classificacao ABC',
                    labels={'Nome_Produto2': '', 'Sugestao_Compra': 'Sugestão de Compra'}, 
                    text=formatted_labels,
                    height=400)
        
        fig1.update_traces(texttemplate='%{text}', textposition='outside')

        fig1.update_layout(
            showlegend=True,
            title_text='Sugestão de Compra para reposição de estoque',  
            legend_title_text='',  
            legend=dict(
                orientation="h",  
                yanchor="bottom",
                y=1.02,  
                xanchor="right",
                x=1  
            ),
            xaxis_title="",
            yaxis_title="",  # Remove o título do eixo y
            width=GRAPH_WIDTH,
            height=GRAPH_HEIGHT
        )  
        
        graph_placeholder.plotly_chart(fig1)

        traces = [
            {
                'y_data': 'Quantidade_Estoque_Atual',
                'name': 'Estoque Atual',
                'color': 'gray'
            },
            {
                'y_data': 'Estoque_Minimo',
                'name': 'Estoque Mínimo',
                'color': '#39baff'
            }
        ]
        
        # Grafico 2
        fig2 = go.Figure()

        # Adicionando traços de forma automática
        for trace in traces:
            y_data = trace['y_data']
            
            fig2.add_trace(go.Bar(
                x=df_grouped['Nome_Produto2'],
                y=df_grouped[y_data],
                name=trace['name'],
                marker_color=trace['color'],
                width=0.5,
                hovertemplate=df_grouped[y_data].apply(lambda x: brazilian_format(x) + '<extra></extra>'),
                text=df_grouped[y_data].apply(brazilian_format),
                textposition='outside'
            ))

        # Configuração do layout
        fig2.update_layout(
            showlegend=True,
            title_text='Estoque Mínimo vs Atual',
            legend_title_text='',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis_title="",
            yaxis_title="",
            barmode='group',
            hovermode="x",
            width=GRAPH_WIDTH,
            height=GRAPH_HEIGHT
        )  
        
        # Gráfico 3
        def plot_graph(product_col):
            fig, ax = plt.subplots(figsize=(10, 6))  # Ajustar o tamanho do gráfico
            
            historico = previsoes[previsoes['Historico_Projecao'] == 'Historico']
            projecao = previsoes[previsoes['Historico_Projecao'] == 'Projecao']
            
            # Fazendo a projeção começar do último ponto do histórico
            projecao = pd.concat([historico.tail(1), projecao])

            ax.plot(historico['Data'], historico[product_col], label='Histórico', linestyle='-', color='blue')
            ax.plot(projecao['Data'], projecao[product_col], label='Projeção', linestyle='--', color='red')

            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m'))
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            fig.autofmt_xdate()

            ax.set_xlabel('Data', fontsize=10)  # Tamanho da fonte para o rótulo do eixo x
            ax.set_ylabel('Valor', fontsize=10)  # Tamanho da fonte para o rótulo do eixo y
            ax.set_title(f'Histórico e Projeção para {product_col}', fontsize=16)  # Tamanho da fonte para o título

            ax.legend()
            ax.grid(True, which='both', linestyle='--', linewidth=0.5)  # Adicionando linhas de grade

            plt.xticks(rotation=90, fontsize = 10)  # Rotacionar rótulos do eixo x

            plt.tight_layout()  # Ajusta o layout para garantir que tudo se ajuste corretamente

            return fig

        # Inicialização do st.session_state.show_graph
        if not hasattr(st.session_state, 'show_graph'):
            st.session_state.show_graph = 'graph1'

        # Botões para alternar gráficos

        col1, col2, col3, col4 = st.columns(4)
        if col1.button("Estoque Mínimo vs Atual", type="primary"):
            st.session_state.show_graph = 'graph1'  # Altere aqui para 'graph1'
        if col2.button("Sugestão de Compra", type="primary"):
            st.session_state.show_graph = 'graph2'  # Altere aqui para 'graph2'
        if col3.button("Venda vs Projeção", type="primary"):
            st.session_state.show_graph = 'graph3'

        col4.write("") 

        # Lógica para exibir o gráfico correto após pressionar um botão
        if st.session_state.show_graph == 'graph1':
            graph_placeholder.plotly_chart(fig2)  # Altere aqui para fig2
        elif st.session_state.show_graph == 'graph2':
            graph_placeholder.plotly_chart(fig1)  # Altere aqui para fig1
        elif st.session_state.show_graph == 'graph3':
            # Filtro de produtos
            products = previsoes.columns.drop(['Data', 'Historico_Projecao']).tolist()
            selected_product = st.selectbox("Escolha um produto:", products)
            fig3 = plot_graph(selected_product)
            graph_placeholder.pyplot(fig3)
        

    with st.container():
        chart = graficos(df_final)
        if chart:
            st.plotly_chart(chart)

        st.write("---")
        
        st.markdown("##### Perguntas e Análises frequentes:")
        options = st.multiselect(
            "",
            list(FUNCTIONS_DICT.keys())
        )

        for option in options:
            # Executando a função correspondente à opção selecionada
            result = FUNCTIONS_DICT[option](df_final)
            # st.markdown(f"**{option}**")

            if isinstance(result, pd.DataFrame):
                st.write(result)  # Mostra o dataframe em formato de tabela
            else:
                st.write(f"**{result}**")  # Mostra a resposta como texto
            
        st.write("---")

        # # MODELO 5 - FINE TUNING
        
        # st.markdown("##### Explore seus dados junto com ChatGPT! Me faça uma pergunta:")
        # user_input = st.text_input("")

        # # 1. Calcule os produtos de criticidade "Alta", "Média" e "Baixa"
        # produtos_alta_criticidade_df = df_final[df_final['Criticidade'] == 'Alta']
        # produtos_alta_criticidade_list = produtos_alta_criticidade_df['Nome_Produto2'].tolist()

        # produtos_media_criticidade_df = df_final[df_final['Criticidade'] == 'Media']
        # produtos_media_criticidade_list = produtos_media_criticidade_df['Nome_Produto2'].tolist()

        # produtos_baixa_criticidade_df = df_final[df_final['Criticidade'] == 'Baixa']
        # produtos_baixa_criticidade_list = produtos_baixa_criticidade_df['Nome_Produto2'].tolist()

        # # 2. Formate as listas como strings
        # produtos_alta_criticidade_str = ', '.join(produtos_alta_criticidade_list)
        # produtos_media_criticidade_str = ', '.join(produtos_media_criticidade_list)
        # produtos_baixa_criticidade_str = ', '.join(produtos_baixa_criticidade_list)


        # # Interagindo com o modelo do chatgpt
        # if user_input:
            
        #     # Parte 1: Descrição Geral do Dataframe
        #     dataframe_overview = f"""
        #     O dataframe carregado {df_final} contém um total de {len(df_final)} linhas e fornece informações detalhadas sobre produtos, suas vendas, estoques, fornecedores, e outros detalhes associados.
        #     """
            
        #     # Parte 2: Detalhes das Colunas
        #     column_details = f"""
        #     Aqui estão algumas colunas-chave e suas descrições:
        #     - 'Produto_ID': ID individual de cada produto.
        #     - 'SKU': Código individual de cada produto.
        #     - 'Nome_Produto2': Nome de cada produto.
        #     - 'Setor': Classifica o setor de cada produto, como Eletrônicos, Esporte e lazer, Saúde e bem-estar, etc.
        #     - 'Custo_Unitario': Valor de venda de cada produto.
        #     - 'Classificacao ABC': Classificação que prioriza os produtos de acordo com sua representatividade de faturamento. A classificação pode ser A, B ou C. Os produtos classificados são:
        #         - Alta Criticidade: {produtos_alta_criticidade_str}
        #         - Média Criticidade: {produtos_media_criticidade_str}
        #         - Baixa Criticidade: {produtos_baixa_criticidade_str}
        #     - 'Quantidade_Estoque_Atual': Quantidade que cada produto tem em estoque atualmente.
        #     - 'Estoque_Minimo': é uma recomendação que se baseia na ponderação entre venda histórica e projeção, lead time de recebimento da industria e fator de criticidade baseado na curva A, B, C e quantidade de fornecedores. O total de estoque mínimo seria {df_final['Estoque_Minimo'].sum()}
        #     - 'Criticidade_Num': Coluna numérica que indica a criticidade do produto. Um número maior indica maior criticidade.
        #     - 'Criticidade': é uma coluna que indica produtos de alta, média e baixa criticidade.
        #     - 'Venda_ult_30d', 'Venda_ult_60', 'Venda_ult_90d': Vendas do produto nos últimos 30, 60 e 90 dias, respectivamente.
        #     - 'Lead_Time_Dias': Tempo em dias que um produto leva para ser entregue pelo fornecedor.
        #     - 'Sugestao_Compra': Representa a quantidade de produtos sugeridos para compra. O total de sugestão de compra seria {df_final['Sugestao_Compra'].sum()}.
        #     """

        #     # Juntando tudo
        #     user_context = f"""
        #     {dataframe_overview}
        #     {column_details}
        #     Com base nas informações fornecidas, você perguntou: '{user_input}'. Vamos analisar e fornecer uma resposta.
        #     """

        #     # Se não for uma das operações predefinidas, consulte o modelo
        #     response = openai.ChatCompletion.create(
        #         model="gpt-3.5-turbo",
        #         messages=[
        #             {"role": "system", "content": "Você é um analista de dados sênior. Seu interlocutor é uma pessoa de negócios que espera respostas claras, concisas e prontas para ação. Não forneça códigos ou fórmulas. Analise os dados e comunique suas descobertas de forma direta, oferecendo insights práticos baseados em dados."},
        #             {"role": "user", "content": user_context}  # Uso do contexto criado
        #         ]
        #     )

        #     # Exibindo a resposta
        #     st.write("Resposta:", response.choices[0].message['content'].strip())
        
        # MODELO 6 - FINE TUNING INCORPORANDO MÉTRICAS
        
        st.markdown("##### Explore seus dados junto com ChatGPT! Me faça uma pergunta:")
        user_input = st.text_input("")

        # 1. Calcule os produtos de criticidade "Alta", "Média" e "Baixa"
        produtos_alta_criticidade_df = df_final[df_final['Criticidade'] == 'Alta']
        produtos_alta_criticidade_list = produtos_alta_criticidade_df['Nome_Produto2'].tolist()

        produtos_media_criticidade_df = df_final[df_final['Criticidade'] == 'Media']
        produtos_media_criticidade_list = produtos_media_criticidade_df['Nome_Produto2'].tolist()

        produtos_baixa_criticidade_df = df_final[df_final['Criticidade'] == 'Baixa']
        produtos_baixa_criticidade_list = produtos_baixa_criticidade_df['Nome_Produto2'].tolist()

        # 2. Formate as listas como strings
        produtos_alta_criticidade_str = ', '.join(produtos_alta_criticidade_list)
        produtos_media_criticidade_str = ', '.join(produtos_media_criticidade_list)
        produtos_baixa_criticidade_str = ', '.join(produtos_baixa_criticidade_list)
        
        # Criando um dicionário que mapeia o 'Nome_Produto2' ao 'Estoque_Minimo'
        estoque_minimo_dict = dict(zip(df_final['Nome_Produto2'], df_final['Estoque_Minimo']))
        # Convertendo o dicionário para uma string formatada
        estoque_minimo_str = ', '.join([f"{produto}: {quantidade}" for produto, quantidade in estoque_minimo_dict.items()])
        # Calculando o 'Estoque_Minimo' total
        estoque_minimo_total = df_final['Estoque_Minimo'].sum()
        estoque_minimo_total_str = f"Estoque Mínimo Total: {estoque_minimo_total}"

        # Calculando o 'Sugestao_Compra' total
        sugestao_compra_total = df_final['Sugestao_Compra'].sum()
        sugestao_compra_total_str = f"Sugestão de Compra Total: {sugestao_compra_total}"

        # 'Sugestao_Compra' por produto
        produtos_sugestao_compra_df = df_final[['Nome_Produto2', 'Sugestao_Compra']]
        produtos_sugestao_compra_list = [f"{row['Nome_Produto2']}: {row['Sugestao_Compra']}" for _, row in produtos_sugestao_compra_df.iterrows()]
        produtos_sugestao_compra_str = ', '.join(produtos_sugestao_compra_list)
        
        # Calculando o 'Sugestao_Compra' para cada categoria da 'Classificacao ABC'
        sugestao_compra_A = df_final[df_final['Classificacao ABC'] == 'A']['Sugestao_Compra'].sum()
        sugestao_compra_B = df_final[df_final['Classificacao ABC'] == 'B']['Sugestao_Compra'].sum()
        sugestao_compra_C = df_final[df_final['Classificacao ABC'] == 'C']['Sugestao_Compra'].sum()

        # Formatando as sugestões para as categorias
        sugestao_compra_A_str = f"Sugestão de Compra para produtos de classificação A: {sugestao_compra_A}"
        sugestao_compra_B_str = f"Sugestão de Compra para produtos de classificação B: {sugestao_compra_B}"
        sugestao_compra_C_str = f"Sugestão de Compra para produtos de classificação C: {sugestao_compra_C}"


    ###########################

        # Cálculo das variáveis RUPTURA PREDITIVA
        # Filtrando o dataframe 'previsoes' para obter apenas as linhas com 'Projecao' em 'Historico_Projecao'
        df_projecao = previsoes[previsoes['Historico_Projecao'] == 'Projecao']

        # Removendo a coluna 'Historico_Projecao' e 'Data' para ficar apenas com as colunas de produtos
        df_projecao = df_projecao.drop(columns=['Historico_Projecao', 'Data'])

        # Somando todos os valores de 'Projecao' para obter a Venda projetada para 30 dias
        Venda_proj_30d = df_projecao.sum().sum()
        Estoque_Atual = float(df_final['Quantidade_Estoque_Atual'].sum())

        # Calculando as métricas de disponibilidade e ruptura
        Disponibilidade_estoque = (Estoque_Atual / Venda_proj_30d) * 100
        Nivel_rup_perc = ((Estoque_Atual / Venda_proj_30d - 1) * 100)*-1
        Nivel_rup_itens = Venda_proj_30d - Estoque_Atual

        # Calculando as novas variáveis DURAÇÃO ESTOQUE (em dias) - baseado venda projetada
        Venda_proj_dia = Venda_proj_30d / 30
        Duracao_estoque = Estoque_Atual / Venda_proj_dia
        Dias_sem_cobertura = 30 - Duracao_estoque

        # Calculando as novas variáveis RUPTURA BASEADA VENDA PASSAD
        Venda_ult_30d = df_final['Venda_ult_30d'].sum()
        Disp_etq_rup_pass = (Estoque_Atual / Venda_ult_30d) * 100
        Nivel_rup_perc_pass = ((Estoque_Atual / Venda_ult_30d - 1) * 100)*-1
        Nivel_rup_itens_pass = Venda_ult_30d - Estoque_Atual

        # Calculando as novas variáveis CALCULO DE OPORTUNIDADE
        Vlr_med_produto = df_final['Custo_Unitario'].mean()
        Vlr_venda_ult_30d = Venda_ult_30d * Vlr_med_produto
        Vlr_venda_proj_30d = Venda_proj_30d * Vlr_med_produto
        perda_venda_etq_proj = Vlr_med_produto * Nivel_rup_itens
        perda_venda_etq_passado = Vlr_med_produto * Nivel_rup_itens_pass
        
    ############################
    
        # Criação das métricas
        Venda_proj_30d_str = f"Venda Projetada para 30 dias: {brazilian_format(Venda_proj_30d)}"
        Estoque_Atual_str = f"Estoque Atual: {brazilian_format(Estoque_Atual)}"
        Disponibilidade_estoque_str = f"Disponibilidade de Estoque (%): {Disponibilidade_estoque:.2f}%"
        Nivel_rup_perc_str = f"Nível de Ruptura (%): {Nivel_rup_perc:.2f}%"
        Nivel_rup_itens_str = f"Nível de Ruptura (Itens): {brazilian_format(Nivel_rup_itens)}"

        Venda_proj_dia_str = f"Venda Projetada por Dia: {brazilian_format(Venda_proj_dia)}"
        Duracao_estoque_str = f"Duração Estoque (em dias): {Duracao_estoque:.1f}"
        Dias_sem_cobertura_str = f"Dias Sem Cobertura: {Dias_sem_cobertura:.1f}"

        Venda_ult_30d_str = f"Venda Últimos 30 dias: {brazilian_format(Venda_ult_30d)}"
        Disp_etq_rup_pass_str = f"Disponibilidade de Estoque com base em Ruptura Passada: {Disp_etq_rup_pass:.2f}%"
        Nivel_rup_perc_pass_str = f"Nível de Ruptura Passada (%): {Nivel_rup_perc_pass:.1f}%"
        Nivel_rup_itens_pass_str = f"Nível de Ruptura (Itens) Passada: {brazilian_format(Nivel_rup_itens_pass)}"

        Vlr_med_produto_str = f"Valor Médio Produto: {brazilian_currency_format(Vlr_med_produto)}"
        Vlr_venda_ult_30d_str = f"Valor Venda Últimos 30 dias: {brazilian_currency_format(Vlr_venda_ult_30d)}"
        Vlr_venda_proj_30d_str = f"Valor Venda Projetada para 30 dias: {brazilian_currency_format(Vlr_venda_proj_30d)}"
        perda_venda_etq_proj_str = f"Perda em Venda Estoque Atual vs Projeção Venda: {brazilian_currency_format(perda_venda_etq_proj)}"
        perda_venda_etq_passado_str = f"Perda em Venda Estoque Atual vs Venda passada: {brazilian_currency_format(perda_venda_etq_passado)}"

        # Interagindo com o modelo do chatgpt
        if user_input:
            
            # Parte 1: Descrição Geral do Dataframe
            dataframe_overview = f"""
            O dataframe carregado {df_final} contém um total de {len(df_final)} linhas e fornece informações detalhadas sobre produtos, suas vendas, estoques, fornecedores, e outros detalhes associados.
            """
            
            # Parte 2: Detalhes das Colunas
            column_details = f"""
            Aqui estão algumas colunas-chave e suas descrições:
            - 'Produto_ID': ID individual de cada produto.
            - 'SKU': Código individual de cada produto.
            - 'Nome_Produto2': Nome de cada produto.
            - 'Setor': Classifica o setor de cada produto, como Eletrônicos, Esporte e lazer, Saúde e bem-estar, etc.
            - 'Custo_Unitario': Valor de venda de cada produto.
            - 'Classificacao ABC': Classificação que prioriza os produtos de acordo com sua representatividade de faturamento. A classificação pode ser A, B ou C. Os produtos classificados são:
                - Alta Criticidade: {produtos_alta_criticidade_str}
                - Média Criticidade: {produtos_media_criticidade_str}
                - Baixa Criticidade: {produtos_baixa_criticidade_str}
            - 'Quantidade_Estoque_Atual': Quantidade que cada produto tem em estoque atualmente.
            - 'Estoque_Minimo': é uma recomendação que se baseia na ponderação entre venda histórica e projeção, lead time de recebimento da indústria e fator de criticidade baseado na curva A, B, C e quantidade de fornecedores. O estoque mínimo por produto é: {estoque_minimo_str}. e o total de estoque mínimo é {estoque_minimo_total_str}. 
            - 'Criticidade_Num': Coluna numérica que indica a criticidade do produto. Um número maior indica maior criticidade.
            - 'Criticidade': é uma coluna que indica produtos de alta, média e baixa criticidade.
            - 'Venda_ult_30d', 'Venda_ult_60', 'Venda_ult_90d': Vendas do produto nos últimos 30, 60 e 90 dias, respectivamente.
            - 'Lead_Time_Dias': Tempo em dias que um produto leva para ser entregue pelo fornecedor.
            - 'Sugestao_Compra': Representa a quantidade de produtos sugeridos para compra.
                - Sugestões de compra por produto são: {produtos_sugestao_compra_str} e o total é {sugestao_compra_total_str}.
                - Sugestões de compra segmentadas pela 'Classificacao ABC' são:
                    {sugestao_compra_A_str}
                    {sugestao_compra_B_str}
                    {sugestao_compra_C_str}
            
            Aqui estão métricas relacionadas ao contexto de Ruptura Preditiva, Duração de Estoque, Ruptura Baseada na Venda Passada e Cálculo de Oportunidade:
            - Venda Projetada para 30 dias: Representa o total de vendas projetadas para os próximos 30 dias. 
                - {Venda_proj_30d_str}
            - Estoque Atual: Quantidade total de produtos em estoque no momento.
                - {Estoque_Atual_str}
            - Disponibilidade de Estoque (%): Percentual do estoque atual em relação à venda projetada para 30 dias.
                - {Disponibilidade_estoque_str}
            - Nível de Ruptura (%): Percentual de produtos que estão em falta com base na venda projetada para 30 dias.
                - {Nivel_rup_perc_str}
                - {Nivel_rup_itens_str}
            - Venda Projetada por Dia: Representa a venda projetada dividida por 30 dias.
                - {Venda_proj_dia_str}
            - Duração Estoque (em dias): Quantos dias o estoque atual durará, considerando a venda projetada diária.
                - {Duracao_estoque_str}
                - {Dias_sem_cobertura_str}
            - Venda Últimos 30 dias: Total de vendas nos últimos 30 dias.
                - {Venda_ult_30d_str}
            - Disponibilidade de Estoque com base em Ruptura Passada: Percentual do estoque atual em relação à venda dos últimos 30 dias.
                - {Disp_etq_rup_pass_str}
            - Nível de Ruptura Passada (%): Percentual de produtos em falta com base na venda dos últimos 30 dias.
                - {Nivel_rup_perc_pass_str}
                - {Nivel_rup_itens_pass_str}
            - Valor Médio Produto: Valor médio de venda dos produtos.
                - {Vlr_med_produto_str}
            - Valor Venda Últimos 30 dias: Valor total das vendas nos últimos 30 dias.
                - {Vlr_venda_ult_30d_str}
            - Valor Venda Projetada para 30 dias: Valor total das vendas projetadas para os próximos 30 dias.
                - {Vlr_venda_proj_30d_str}
            - Perda em Venda Estoque Atual vs Projeção Venda: Valor que será perdido se o estoque atual for insuficiente para atender à venda projetada.
                - {perda_venda_etq_proj_str}
            - Perda em Venda Estoque Atual vs Venda passada: Valor que foi perdido devido à insuficiência de estoque em relação à venda dos últimos 30 dias.
                - {perda_venda_etq_passado_str}            
            """

            # Juntando tudo
            user_context = f"""
            {dataframe_overview}
            {column_details}
            Com base nas informações fornecidas, você perguntou: '{user_input}'. Vamos analisar e fornecer uma resposta.
            """

            # Se não for uma das operações predefinidas, consulte o modelo
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um analista de dados sênior. Seu interlocutor é uma pessoa de negócios que espera respostas claras, concisas e prontas para ação. Não forneça códigos ou fórmulas. Analise os dados e comunique suas descobertas de forma direta, oferecendo insights práticos baseados em dados."},
                    {"role": "user", "content": user_context}  # Uso do contexto criado
                ]
            )

            # Exibindo a resposta
            st.write("Resposta:", response.choices[0].message['content'].strip())

    def download_board_ia(bin_file, file_label='File'):
        with open(bin_file, 'rb') as f:
            data = f.read()
        bin_str = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{bin_str}" download="{bin_file}">{file_label}</a>'
        return href

    st.write("---")
    st.subheader("Gerar board com IA?")

    col1, col2, col3 = st.columns(3)

    button1 = col1.button("Report de Resultados", type="primary")
    button2 = col2.button("Report + Sugestão PDCA", type="primary")

    if button1:
        with st.spinner('Gerando Board Report de Resultados...'):
            time.sleep(5)
        st.write('⭐ Board Report de Resultados gerado com sucesso!')
        # Aqui você oferece o arquivo para download após o botão ser clicado
        st.markdown(download_board_ia('AI_generated_Board_Presentation.pdf', 'Download Report de Resultados'), unsafe_allow_html=True)
        
    if button2:
        with st.spinner('Gerando Board Report + Sugestão PDCA...'):
            time.sleep(5)
        st.success('⭐ Board Report + Sugestão PDCA gerado com sucesso!') #write
        # Aqui você oferece o arquivo para download após o botão ser clicado
        st.markdown(download_board_ia('AI_generated_Board_Presentation.pdf', 'Download Report + Sugestão PDCA'), unsafe_allow_html=True)
        
    # # MÉTRICAS DO CONTEXTO DA NOSSA PLATAFORMA
    # st.write("---")
    # st.subheader("RUPTURA PREDITIVA")

    # # Cálculo das variáveis 
    # # Filtrando o dataframe 'previsoes' para obter apenas as linhas com 'Projecao' em 'Historico_Projecao'
    # df_projecao = previsoes[previsoes['Historico_Projecao'] == 'Projecao']

    # # Removendo a coluna 'Historico_Projecao' e 'Data' para ficar apenas com as colunas de produtos
    # df_projecao = df_projecao.drop(columns=['Historico_Projecao', 'Data'])

    # # Somando todos os valores de 'Projecao' para obter a Venda projetada para 30 dias
    # Venda_proj_30d = df_projecao.sum().sum()
    # Estoque_Atual = float(df_final['Quantidade_Estoque_Atual'].sum())

    # # Calculando as métricas de disponibilidade e ruptura
    # Disponibilidade_estoque = (Estoque_Atual / Venda_proj_30d) * 100
    # Nivel_rup_perc = ((Estoque_Atual / Venda_proj_30d - 1) * 100)*-1
    # Nivel_rup_itens = Venda_proj_30d - Estoque_Atual

    # # Apresentando as variáveis e métricas no Streamlit com formatação brasileira
    # st.write(f"Venda Projetada para 30 dias: {brazilian_format(Venda_proj_30d)}")
    # st.write(f"Estoque Atual: {brazilian_format(Estoque_Atual)}")
    # st.write(f"Disponibilidade de Estoque (%): {Disponibilidade_estoque:.2f}%")
    # st.write(f"Nível de Ruptura (%): {Nivel_rup_perc:.2f}%")
    # st.write(f"Nível de Ruptura (Itens): {brazilian_format(Nivel_rup_itens)}")
    
    # # Novo bloco: Duração estoque (em dias)
    # st.write("---")
    # st.subheader("DURAÇÃO ESTOQUE (em dias) - baseado venda projetada")

    # # Calculando as novas variáveis
    # Venda_proj_dia = Venda_proj_30d / 30
    # Duracao_estoque = Estoque_Atual / Venda_proj_dia
    # Dias_sem_cobertura = 30 - Duracao_estoque

    # # Apresentando as variáveis e métricas no Streamlit
    # st.write(f"Venda Projetada por Dia: {brazilian_format(Venda_proj_dia)}")
    # st.write(f"Duração Estoque (em dias): {Duracao_estoque:.1f}")
    # st.write(f"Dias Sem Cobertura: {Dias_sem_cobertura:.1f}")
    
    # # Novo bloco: Ruptura passada
    # st.write("---")
    # st.subheader("RUPTURA BASEADA VENDA PASSADA")

    # # Calculando as novas variáveis
    # Venda_ult_30d = df_final['Venda_ult_30d'].sum()
    # Disp_etq_rup_pass = (Estoque_Atual / Venda_ult_30d) * 100
    # Nivel_rup_perc_pass = ((Estoque_Atual / Venda_ult_30d - 1) * 100)*-1
    # Nivel_rup_itens_pass = Venda_ult_30d - Estoque_Atual

    # # Apresentando as variáveis e métricas no Streamlit
    # st.write(f"Venda Últimos 30 dias: {brazilian_format(Venda_ult_30d)}")
    # st.write(f"Disponibilidade de Estoque com base em Ruptura Passada: {Disp_etq_rup_pass:.2f}%")
    # st.write(f"Nível de Ruptura Passada (%): {Nivel_rup_perc_pass:.1f}%")
    # st.write(f"Nível de Ruptura (Itens) Passada: {brazilian_format(Nivel_rup_itens_pass)}")
    
    # # Novo bloco: CÁLCULO DE OPORTUNIDADE
    # st.write("---")
    # st.subheader("CALCULO DE OPORTUNIDADE")

    # # Calculando as novas variáveis
    # Vlr_med_produto = df_final['Custo_Unitario'].mean()
    # Vlr_venda_ult_30d = Venda_ult_30d * Vlr_med_produto
    # Vlr_venda_proj_30d = Venda_proj_30d * Vlr_med_produto
    # perda_venda_etq_proj = Vlr_med_produto * Nivel_rup_itens
    # perda_venda_etq_passado = Vlr_med_produto * Nivel_rup_itens_pass

    # # Apresentando as variáveis e métricas no Streamlit
    # st.write(f"Valor Médio Produto: {brazilian_currency_format(Vlr_med_produto)}")
    # st.write(f"Valor Venda Últimos 30 dias: {brazilian_currency_format(Vlr_venda_ult_30d)}")
    # st.write(f"Valor Venda Projetada para 30 dias: {brazilian_currency_format(Vlr_venda_proj_30d)}")
    # st.write(f"Perda em Venda Estoque Atual vs Projeção Venda: {brazilian_currency_format(perda_venda_etq_proj)}")
    # st.write(f"Perda em Venda Estoque Atual vs Venda passada: {brazilian_currency_format(perda_venda_etq_passado)}")
    
