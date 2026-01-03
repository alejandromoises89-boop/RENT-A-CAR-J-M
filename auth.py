import streamlit as st

def login_screen():
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h2 style='color:#D4AF37;'>ACCESO EJECUTIVO</h2>", unsafe_allow_html=True)
    
    user = st.text_input("Usuario (admin@jymasociados.com)")
    pw = st.text_input("Contraseña", type="password")
    
    if st.button("INGRESAR"):
        if user == "admin@jymasociados.com" and pw == "JM2026_MASTER":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.session_state.user_name = "ADMIN_MASTER"
            st.rerun()
        elif user != "":
            st.session_state.logged_in = True
            st.session_state.role = "user"
            st.session_state.user_name = user
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
