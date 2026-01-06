# styles.py
def aplicar_estilo_premium():
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
        
        /* Fondo Premium de la Imagen */
        .stApp {
            background: radial-gradient(circle at top, #4A0404 0%, #121212 100%);
            color: #ffffff;
            font-family: 'Montserrat', sans-serif;
        }

        /* Tarjetas estilo "Glass" de la imagen */
        .card-auto {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(212, 175, 55, 0.3);
            border-radius: 20px;
            padding: 20px;
            backdrop-filter: blur(10px);
            transition: 0.4s;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
            margin-bottom: 20px;
        }
        .card-auto:hover {
            transform: translateY(-5px);
            border-color: #D4AF37;
            background: rgba(212, 175, 55, 0.05);
        }

        /* Botones Dorados */
        div.stButton > button {
            background: linear-gradient(90deg, #D4AF37 0%, #B8860B 100%) !important;
            color: black !important;
            font-weight: bold !important;
            border-radius: 12px !important;
            border: none !important;
            height: 45px;
        }

        /* Títulos */
        h1, h2, h3 { color: #D4AF37 !important; text-align: center; }
        
        /* Caja de Pago Pix */
        .pix-box {
            background: rgba(212, 175, 55, 0.1);
            border: 2px dashed #D4AF37;
            padding: 15px;
            border-radius: 15px;
            margin: 15px 0;
        }
    </style>
    """
