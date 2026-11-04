import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np

# Lista de activos que quieres vigilar en marco diario
ACTIVOS = ["BBVA.MC", "SAN.MC", "ITX.MC", "REP.MC", "AENA.MC", "TEF.MC", "IAG.MC"]

def detectar_doble_suelo(df):
    """
    Algoritmo simplificado para detectar un patrón de doble suelo en datos diarios:
    - Busca dos mínimos locales (valles) con una diferencia de precio menor al 2-3%.
    - Comprueba que el precio actual esté rebotando desde el segundo suelo.
    """
    if len(df) < 60:
        return False, 0
    
    # Usamos los precios mínimos (Low) de los últimos 60 días
    lows = df['Low'].values[-60:]
    closes = df['Close'].values[-60:]
    
    # Encontrar el mínimo global del periodo
    min1_idx = np.argmin(lows[:35])  
    min1_val = lows[min1_idx]
    
    # Buscar un segundo mínimo en la segunda mitad del periodo
    min2_candidates = lows[min1_idx + 10:]
    if len(min2_candidates) < 5:
        return False, 0
        
    min2_local_idx = np.argmin(min2_candidates)
    min2_idx = min1_idx + 10 + min2_local_idx
    min2_val = lows[min2_idx]
    
    # Condición 1: Los dos mínimos deben estar cerca en precio (margen del 2.5%)
    diferencia_porcentual = abs(min1_val - min2_val) / min1_val
    if diferencia_porcentual > 0.025:
        return False, 0
        
    # Condición 2: Debe haber transcurrido una distancia razonable entre ambos suelos (al menos 10 días)
    if (min2_idx - min1_idx) < 10:
        return False, 0
        
    # Condición 3: El precio actual (último cierre) debe estar rebotando al alza desde el segundo suelo
    precio_actual = closes[-1]
    if precio_actual > min2_val * 1.015:  # Al menos un 1.5% por encima del segundo suelo
        return True, min2_val
        
    return False, 0

def analizar_mercado():
    alertas = []
    
    for ticker in ACTIVOS:
        try:
            # Descargar 6 meses de datos en velas de 1 día (1d)
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty:
                continue
                
            # Limpiar formato multindex si lo hubiera en yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df = df.droplevel(1, axis=1)
                
            es_doble_suelo, precio_suelo = detectar_doble_suelo(df)
            
            if es_doble_suelo:
                precio_actual = df['Close'].iloc[-1]
                alertas.append(
                    f"🟢 *¡Posible Doble Suelo Detectado!*\n"
                    f"• *Activo:* `{ticker}`\n"
                    f"• *Precio Actual:* €{precio_actual:.2f}\n"
                    f"• *Zona de Suelo:* ~€{precio_suelo:.2f}\n"
                    f"• *Temporalidad:* Gráfico Diario (1D)\n"
                )
        except Exception as e:
            print(f"Error analizando {ticker}: {e}")
            
    return alertas

def enviar_telegram(mensaje):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    hallazgos = analizar_mercado()
    if hallazgos:
        texto_final = "🤖 *Radar Diario de Patrones (Doble Suelo)*\n\n" + "\n\n".join(hallazgos)
        enviar_telegram(texto_final)
    else:
        print("No se detectaron patrones de doble suelo hoy en el gráfico diario.")