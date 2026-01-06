# styles.py

def aplicar_estilo_premium():
    return """
    <style>
        /* Fuente y Fondo Principal */
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
        
        .stApp {
            background: radial-gradient(circle at top, #3d0a0a 0%, #121212 100%);
            color: #ffffff;
            font-family: 'Montserrat', sans-serif;
        }

        /* Banner de Encabezado J&M */
        .header-jm {
            text-align: center;
            padding: 25px;
            background: rgba(0,0,0,0.4);
            border-bottom: 3px solid #D4AF37;
            border-radius: 0 0 20px 20px;
            margin-bottom: 40px;
        }
        .header-jm h1 { color: #D4AF37; font-weight: 700; letter-spacing: 3px; margin:0; }

        /* Tarjetas de Autos (Efecto Cristal de la Imagen) */
        .car-card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(212, 175, 55, 0.2);
            border-radius: 20px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(15px);
            transition: all 0.4s ease;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .car-card:hover {
            border-color: #D4AF37;
            transform: translateY(-10px);
            background: rgba(212, 175, 55, 0.08);
            box-shadow: 0 15px 40px rgba(212, 175, 55, 0.2);
        }

        /* Botones Dorados */
        div.stButton > button {
            background: linear-gradient(90deg, #D4AF37 0%, #B8860B 100%) !important;
            color: #000 !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            border: none !important;
            transition: 0.3s;
            text-transform: uppercase;
        }
        div.stButton > button:hover {
            box-shadow: 0px 0px 20px rgba(212, 175, 55, 0.7);
            transform: scale(1.03);
        }

        /* Tabs / Pestañas Personalizadas */
        .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255,255,255,0.05);
            border: 1px solid rgba(212, 175, 55, 0.1);
            border-radius: 10px 10px 0 0;
            color: #D4AF37;
            padding: 10px 30px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #D4AF37 !important;
            color: #000 !important;
        }
    </style>
    
    <div class="header-jm">
        <h1>J&M ASOCIADOS</h1>
        <p style="color: #D4AF37; font-weight: 400; letter-spacing: 1px;">ALQUILER DE VEHÍCULOS DE LUJO</p>
    </div>
    """