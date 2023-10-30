
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp

from dataframe import load_df_compras, load_df_final, load_df_vendas_estoque, load_previsoes

df_compras = load_df_compras()
df_final = load_df_final()
df_vendas_estoque = load_df_vendas_estoque()
previsoes = load_previsoes()

import pandas as pd
# Primeiro, precisamos converter a coluna 'Data' para um objeto datetime se ainda n�o estiver em um.
df_vendas_estoque['Data'] = pd.to_datetime(df_vendas_estoque['Data'])
# Em seguida, vamos obter o �ltimo m�s no dataframe.
ultimo_mes = df_vendas_estoque['Data'].dt.to_period('M').max()
# Agora, vamos filtrar o dataframe para incluir apenas as entradas do �ltimo m�s.
df_ultimo_mes = df_vendas_estoque[df_vendas_estoque['Data'].dt.to_period('M') == ultimo_mes]
# Finalmente, a venda do �ltimo m�s ser� a soma da coluna 'Quantidade Vendida' para o �ltimo m�s.
venda_ultimo_mes = df_ultimo_mes['Quantidade Vendida'].sum()
venda_ultimo_mes
result = venda_ultimo_mes

if isinstance(result, pd.DataFrame):
    st.write(result)
elif isinstance(result, (go.Figure, plt.Figure)):
    st.plotly_chart(result)
elif isinstance(result, dict):
    st.write(pd.DataFrame([result]))
else:
    st.write(result)
