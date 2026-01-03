import streamlit as st

def login_screen():
    st.markdown('<div class="header-jm"><h1>J&M ASOCIADOS</h1><p>Alquiler de Vehículos</p></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("<h2 style='color:#D4AF37;'>🔒</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='color:#D4AF37;'>ACCESO J&M</h3>", unsafe_allow_html=True)
        
        mode = st.radio("", ["Iniciar Sesión", "Registrarse"], horizontal=True)
        
        if mode == "Iniciar Sesión":
            user = st.text_input("Correo o número de teléfono", placeholder="Inicio de Sesión")
            pw = st.text_input("Contraseña", type="password")
            if st.button("ENTRAR"):
                if user == "admin" and pw == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.role = "admin"
                else:
                    st.session_state.logged_in = True
                    st.session_state.role = "user"
                st.session_state.user_name = user
                st.rerun()
        else:
            st.text_input("Nombre y Apellido *")
            st.text_input("C.I. / DNI / Pasaporte / CPF / RG *")
            st.text_input("Teléfono / Dirección *")
            st.button("Registrarse con Google 🟢")
        st.markdown('</div>', unsafe_allow_html=True)
