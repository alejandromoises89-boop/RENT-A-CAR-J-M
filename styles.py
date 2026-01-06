def aplicar_estilo_premium():
    return """
    <style>
    /* ... otros estilos ... */

    .card-auto {
        background: transparent !important; /* Esto hace que se funda con el fondo */
        border: none !important;
        box-shadow: none !important;
        text-align: center;
        padding: 10px;
        margin-bottom: 20px;
    }
    
    .card-auto img {
        border-radius: 15px;
        /* Si las fotos tienen fondo blanco, este mix-blend-mode intenta fundirlas */
        mix-blend-mode: multiply; 
    }
    
    .card-auto h3 {
        color: #D4AF37; /* Dorado para que resalte sobre el fondo oscuro */
        margin-bottom: 5px;
    }
    </style>
    """
