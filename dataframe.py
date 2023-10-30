import pandas as pd
import urllib.request
import streamlit as st

# @st.cache_data
def load_data_from_url(url):
    response = urllib.request.urlopen(url)
    return pd.read_csv(response)

def load_df_compras():
    url = 'https://raw.githubusercontent.com/TabathaLarissa/AppStockON/main/df_compras.csv'
    df_compras = load_data_from_url(url)
    df_compras['Data'] = pd.to_datetime(df_compras['Data'])
    return df_compras

def load_df_final():
    url = 'https://raw.githubusercontent.com/TabathaLarissa/AppStockON/main/df_final.csv'
    df_final = load_data_from_url(url)
    df_final['Valor_Total_Compra'] = df_final['Custo_Unitario'] * df_final['Sugestao_Compra']
    return df_final

def load_df_produtos():
    url = 'https://raw.githubusercontent.com/TabathaLarissa/AppStockON/main/df_produtos.csv'
    return load_data_from_url(url)

def load_df_vendas_estoque():
    url = 'https://raw.githubusercontent.com/TabathaLarissa/AppStockON/main/df_vendas_estoque.csv'
    df_vendas_estoque = load_data_from_url(url)
    df_vendas_estoque['Data'] = pd.to_datetime(df_vendas_estoque['Data'])
    return df_vendas_estoque

def load_previsoes():
    url = 'https://raw.githubusercontent.com/TabathaLarissa/AppStockON/main/previsoes.csv'
    return load_data_from_url(url)

def load_sugestoes():
    url = 'https://raw.githubusercontent.com/TabathaLarissa/AppStockON/main/sugestoes.csv'
    return load_data_from_url(url)

