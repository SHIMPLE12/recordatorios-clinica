from datetime import datetime, timedelta
import io
import json
import os
import urllib.parse
from PIL import Image
import google.generativeai as genai
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recordatorios de Citas", page_icon="📅", layout="centered"
)

# --- CONTRASEÑA DE ACCESO ---
CONTRASEÑA_MAESTRA = "prueba-2026"

st.sidebar.header("🔐 Acceso de Seguridad")
password_ingresada = st.sidebar.text_input(
    "Introduce la contraseña", type="password", placeholder="••••"
)

if password_ingresada != CONTRASEÑA_MAESTRA:
  st.title("🔒 Acceso Restringido")
  st.warning(
      "⚠️ Por favor, introduce la contraseña correcta en la barra lateral para"
      " acceder a la aplicación."
  )
  st.stop()

# --- CONFIGURACIÓN DE LA CLÍNICA ---
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuración")
nombre_clinica = st.sidebar.text_input(
    "Nombre de la Clínica",
    value="nuestra clínica",
    placeholder="Ej: Clínica Dental Sonrisa",
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 Sube un archivo Excel de gestión o haz una foto a tu libreta"
    " manuscrita."
)

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
api_key_google = os.environ.get("GOOGLE_API_KEY")
if api_key_google:
  genai.configure(api_key=api_key_google)

# --- CONTENIDO PRINCIPAL ---
st.title("📅 Recordatorios Automáticos de Citas")
st.write(
    "Elige cómo quieres introducir las citas para generar los recordatorios de"
    " mañana."
)

modo_entrada = st.radio(
    "¿Cómo gestionáis las citas en vuestra clínica?",
    ["📁 Subir archivo Excel", "📸 Hacer foto a la libreta de papel"],
)

df_filtrado = pd.DataFrame()


# Función para comprimir y redimensionar imágenes
def preparar_imagen_para_ia(
    archivo_subido, ancho_maximo=1000, calidad_jpg=80
):
  imagen = Image.open(archivo_subido)
  if imagen.mode in ("RGBA", "P"):
    imagen = imagen.convert("RGB")

  ancho_actual, alto_actual = imagen.size
  if ancho_actual > ancho_maximo:
    proporcion = ancho_maximo / ancho_actual
    nuevo_alto = int(alto_actual * proporcion)
    imagen = imagen.resize(
        (ancho_max
