import streamlit as st

def aplicar_estilos():
    st.markdown("""
    <style>
    /* Fondo General Bordo Degradado */
    .stApp {
        background: linear-gradient(180deg, #4e0b0b 0%, #2b0606 100%);
        color: white;
    }
    /* Encabezado Dorado */
    .header-jm { text-align: center; color: #D4AF37; padding: 20px; }
    .header-jm h1 { font-size: 50px; font-weight: bold; margin-bottom: 0; text-transform: uppercase; }
    .header-jm h2 { font-size: 20px; margin-top: 0; }

    /* Login Box */
    .login-box {
        border: 1px solid #D4AF37;
        padding: 40px;
        border-radius: 15px;
        background: rgba(0,0,0,0.4);
        text-align: center;
    }
    .stTextInput>div>div>input {
        border: 1px solid #D4AF37 !important;
        background-color: transparent !important;
        color: #D4AF37 !important;
        text-align: center;
    }
    /* Botón Entrar Bordo Destacado */
    div.stButton > button {
        background-color: #800000 !important;
        color: #D4AF37 !important;
        font-weight: bold !important;
        border: 1px solid #D4AF37 !important;
        width: 100%;
        font-size: 18px;
    }

    /* Pestañas Blancas con Hover Bordo */
    .stTabs [data-baseweb="tab-list"] {
        background-color: white;
        border-radius: 10px 10px 0 0;
        padding: 5px;
    }
    .stTabs [data-baseweb="tab"] {
        color: black !important;
        font-weight: normal;
        border-bottom: 2px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        border-bottom: 3px solid #800000 !important;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #800000 !important;
        text-decoration: underline;
    }
    /* Contenido de pestañas Blanco */
    [data-testid="stExpander"], .stTabs [data-baseweb="tab-panel"] {
        background-color: white;
        color: black;
        border-radius: 0 0 10px 10px;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
