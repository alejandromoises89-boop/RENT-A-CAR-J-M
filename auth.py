import streamlit as st

def login_screen():
    st.markdown('<div class="header-jm"><h1>🔒 ACCESO J&M</h1></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        mode = st.radio("", ["Iniciar Sesión", "Registrarse"], horizontal=True)
        
        if mode == "Iniciar Sesión":
            user = st.text_input("Correo o Teléfono", placeholder="Usuario Maestro o Cliente")
            pw = st.text_input("Contraseña", type="password")
            if st.button("ENTRAR"):
                if user == "admin@jymasociados.com" and pw == "JM2026_MASTER":
                    st.session_state.logged_in = True
                    st.session_state.role = "admin"
                    st.session_state.user_name = "Administrador J&M"
                    st.rerun()
                elif user != "" and pw != "":
                    st.session_state.logged_in = True
                    st.session_state.role = "user"
                    st.session_state.user_name = user
                    st.rerun()
        else:
            nombre = st.text_input("Nombre Completo *")
            tel = st.text_input("WhatsApp (Ej: 595991...) *")
            if st.button("Finalizar Registro"):
                st.session_state.temp_nombre = nombre
                st.session_state.temp_tel = tel
                st.success("✅ Datos guardados.")
        st.markdown('</div>', unsafe_allow_html=True)
