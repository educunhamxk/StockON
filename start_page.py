import streamlit as st
from main import main
from dataframe import load_df_compras, load_df_final, load_df_produtos, load_df_vendas_estoque, load_previsoes, load_sugestoes

# Definindo o page_config no início do start_page.py
st.set_page_config(
    page_title="Stock ON Dashboard",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .reportview-container {
            background: #000000;  # Cinza claro
        }
    </style>
""", unsafe_allow_html=True)


def get_session_state():
    if 'session_state' not in st.session_state:
        st.session_state['session_state'] = {}
    return st.session_state['session_state']

session_state = get_session_state()

if 'page' not in session_state:
    session_state['page'] = 'start_page'

if session_state['page'] == 'start_page':
    st.title("Bem-vindo ao Aplicativo de IA: Stock ON!")
    st.write("Descomplicando a Análise de Dados e as Tomadas de decisões: Explore e Inteja com a Stock ON.")
    if st.button("Entrar"):
        session_state['page'] = 'main'
        st.experimental_rerun()
else:
    main(load_df_compras(), load_df_final(), load_df_produtos(), load_df_vendas_estoque(), load_previsoes(), load_sugestoes())


