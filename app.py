from datetime import datetime, timedelta
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

st.sidebar.header("🔐 Seguridad")
password_ingresada = st.sidebar.text_input(
    "Contraseña", type="password", placeholder="••••"
)

if password_ingresada != CONTRASEÑA_MAESTRA:
  st.title("🔒 Acceso Restringido")
  st.warning("⚠️ Introduce la contraseña en la barra lateral para acceder.")
  st.stop()

# --- CONFIGURACIÓN ---
st.sidebar.markdown("---")
nombre_clinica = st.sidebar.text_input("Nombre de la Clínica", value="nuestra clínica")

# Configurar Gemini
api_key_google = os.environ.get("GOOGLE_API_KEY")
if api_key_google:
  genai.configure(api_key=api_key_google)

st.title("📅 Recordatorios de Citas")
modo_entrada = st.radio(
    "¿Cómo quieres introducir las citas?",
    ["📁 Subir archivo Excel", "📸 Hacer foto a la libreta"],
)

df_filtrado = pd.DataFrame()


def preparar_imagen(archivo):
  img = Image.open(archivo)
  if img.mode in ("RGBA", "P"):
    img = img.convert("RGB")
  return img


# ==========================================
# 1. SUBIR EXCEL
# ==========================================
if modo_entrada == "📁 Subir archivo Excel":
  archivo = st.file_uploader("Sube tu Excel (.xlsx)", type=["xlsx", "xls"])
  if archivo is not None:
    try:
      df = pd.read_excel(archivo)
      df.columns = df.columns.astype(str).str.strip()

      # Detección simple de columnas
      cols = [c.lower() for c in df.columns]
      col_p = next((df.columns[i] for i, c in enumerate(cols) if 'pac' in c or 'nom' in c), df.columns[0])
      col_t = next((df.columns[i] for i, c in enumerate(cols) if 'tel' in c or 'móv' in c or 'mov' in c), df.columns[1])
      col_f = next((df.columns[i] for i, c in enumerate(cols) if 'fec' in c or 'data' in c or 'dia' in c), df.columns[2] if len(df.columns) > 2 else None)
      col_h = next((df.columns[i] for i, c in enumerate(cols) if 'hora' in c), df.columns[3] if len(df.columns) > 3 else None)

      df = df.rename(columns={col_p: "Paciente", col_t: "Teléfono", col_f: "Fecha", col_h: "Hora"})
      df = df.dropna(subset=["Paciente"])

      if "Fecha" in df.columns:
        df["Fecha_limpia"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.strftime("%Y-%m-%d")
        mañana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        df_mañana = df[df["Fecha_limpia"] == mañana]
        if not df_mañana.empty:
          df_filtrado = df_mañana
          st.success(f"✅ ¡Citas para mañana ({mañana}) filtradas con éxito!")
        else:
          st.warning(f"⚠️ No hay citas para mañana ({mañana}).")
    except Exception as e:
      st.error(f"Error al leer el Excel: {e}")

# ==========================================
# 2. FOTO DE LA LIBRETA (GEMINI)
# ==========================================
elif modo_entrada == "📸 Hacer foto a la libreta":
  foto = st.file_uploader("Sube la foto", type=["jpg", "jpeg", "png"])
  if foto is not None:
    st.image(foto, caption="Foto subida", use_container_width=True)
    if st.button("✨ Procesar con Gemini"):
      with st.spinner("Analizando con Gemini..."):
        try:
          img_opt = preparar_imagen(foto)
          model = genai.GenerativeModel("gemini-1.5-flash")
          prompt = "Extrae las citas de esta imagen y devuélvelas estrictamente en JSON con claves 'Paciente', 'Hora', 'Telefono'."
          response = model.generate_content([prompt, img_opt])
          st.success("¡Procesado correctamente!")
        except Exception as e:
          st.error(f"Error en Gemini: {e}")

# ==========================================
# 3. MENSAJES DE WHATSAPP
# ==========================================
if not df_filtrado.empty:
  st.markdown("---")
  st.subheader("💬 Mensajes listos para enviar")

  for index, row in df_filtrado.iterrows():
    paciente = str(row.get("Paciente", "Paciente"))
    hora = str(row.get("Hora", "su hora"))
    telefono_raw = str(row.get("Teléfono", ""))
    telefono_limpio = "".join(filter(str.isdigit, telefono_raw))

    mensaje = f"Hola {paciente}, le escribimos de *{nombre_clinica}* para recordarle su cita para mañana a las {hora}. Responda OK para confirmar."

    st.text_area(f"Paciente: {paciente} ({telefono_raw})", value=mensaje, height=70, key=f"msg_{index}")

    if telefono_limpio:
      w_url = f"https://wa.me/{telefono_limpio}?text={urllib.parse.quote(mensaje)}"
      sms_url = f"sms:{telefono_limpio}?body={urllib.parse.quote(mensaje)}"
      
      st.markdown(f"""
        <div style="margin-bottom: 20px;">
            <a href="{w_url}" style="display:block; background-color:#25D366; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold; text-align:center; margin-bottom: 8px;">
                📲 Enviar a WhatsApp de {paciente}
            </a>
            <a href="{sms_url}" style="display:block; background-color:#007AFF; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold; text-align:center;">
                ✉️ Enviar por SMS a {paciente}
            </a>
        </div>
      """, unsafe_allow_html=True)
    else:
      st.warning(f"⚠️ {paciente} no tiene teléfono válido.")
