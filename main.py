import streamlit as st
import sqlite3
import pandas as pd
import base64
import urllib.parse
from datetime import datetime, date, time
from fpdf import FPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io

# --- 1. IDENTIDAD VISUAL ---
st.set_page_config(page_title="JM ASOCIADOS | SISTEMA V7", layout="wide")

def aplicar_estilos_premium():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(180deg, #4b0000 0%, #1a0000 100%); color: white; }
        .header-jm { text-align: center; padding: 15px; }
        .header-jm h1 { color: #D4AF37; font-family: 'Times New Roman', serif; font-size: 50px; margin-bottom: 0; }
        .stTextInput>div>div>input { border: 1px solid #D4AF37 !important; background-color: transparent !important; color: white !important; }
        div.stButton > button { background-color: #800000 !important; color: #D4AF37 !important; border: 1px solid #D4AF37 !important; font-weight: bold; width: 100%; border-radius: 10px; }
        .stTabs [data-baseweb="tab-list"] { background-color: white; border-radius: 10px; padding: 5px; }
        .stTabs [data-baseweb="tab"] { color: black !important; font-weight: bold; }
        .card-auto { background: white; color: black; padding: 1
