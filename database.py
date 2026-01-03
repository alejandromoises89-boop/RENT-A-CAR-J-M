import sqlite3
import pandas as pd

def init_db():
    conn = sqlite3.connect('jm_asociados.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservas 
                 (id INTEGER PRIMARY KEY, cliente TEXT, auto TEXT, inicio TEXT, fin TEXT, monto REAL, doc TEXT)''')
    conn.commit()
    conn.close()

def obtener_flota():
    return [
        {"id": "TUCSON", "nombre": "Hyundai Tucson", "color": "Blanco", "precio": 260000, "img": "https://www.iihs.org/cdn-cgi/image/width=636/api/ratings/model-year-images/2098/"},
        {"id": "VITZ_W", "nombre": "Toyota Vitz", "color": "Blanco", "precio": 195000, "img": "https://raw.githubusercontent.com/MarcosB-dev/images/main/vitz_blanco.png"},
        {"id": "VITZ_N", "nombre": "Toyota Vitz", "color": "Negro", "precio": 195000, "img": "https://i.ibb.co/yFNrttM2/BG160258-2427f0-Photoroom.png"},
        {"id": "VOXY", "nombre": "Toyota Voxy", "color": "Gris", "precio": 240000, "img": "https://i.ibb.co/Y7ZHY8kX/pngegg.png"}
    ]
