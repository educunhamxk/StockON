import streamlit as st

def feedback_page():
    st.markdown(""" 
    <style> 
        .font {
            font-size:35px; 
            font-family: 'Segoe UI'; 
            color: #696969;
            text-align: center;  # Adicionado para centralizar o texto
        } 
    </style> 
    """, unsafe_allow_html=True)

    st.markdown('<p class="font">Nos dê seu feedback e nos ajude a melhorar!</p>', unsafe_allow_html=True)

    with st.form(key='columns_in_form2',clear_on_submit=True):
        Name = st.text_input(label='Digite seu nome:')
        Email = st.text_input(label='Digite seu melhor e-mail:')
        Message = st.text_input(label='Espaço para sua mensagem:')
        
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Obrigado por nos contatar. Responderemos você em instantes!')


