import streamlit as st
from page_analytics_predict import dashboard_page
from page_call_to_action import call_to_action_page
# from page_metrics import metrics_page
from page_feedback import feedback_page
from streamlit_option_menu import option_menu

def main(df_compras, df_final, df_produtos, df_vendas_estoque, previsoes, sugestoes):
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # menu dentro do sidebar
    with st.sidebar:
        st.image("StockON.png")
        selected = option_menu('', ['Analytics & Predição', 'Call to Action', 'Feedback'], 
            icons=['file-earmark-bar-graph-fill', 'graph-up-arrow', 'check2-square', 'arrow-bar-up', 'check', 'send-check-fill'], menu_icon=" ", default_index=0,
            styles={
                "container": {"padding": "5!important", "background-color": "#fafafa"},
                "icon": {"color": "#009EE2", "font-size": "22px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee", "font-family": "Segoe UI, sans-serif"},
                "nav-link-selected": {"background-color": "#333333"},
            }
        )
        
    if selected == 'Analytics & Predição':
        dashboard_page(df_compras, df_final, df_produtos, df_vendas_estoque, previsoes, sugestoes)
    elif selected == "Call to Action":
        call_to_action_page(df_compras, df_final, df_produtos, df_vendas_estoque, previsoes, sugestoes)
    # elif selected == 'Métricas':
    #     metrics_page()
    elif selected == 'Feedback':
        feedback_page()

