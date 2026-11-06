import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestor de Citas y Recordatorios",
    page_icon="🏥",
    layout="centered",
)

st.title("🏥 Recordatorios Automáticos de WhatsApp")
st.write(
    "Sube el archivo Excel de citas del día para generar los mensajes"
    " automáticamente."
)

archivo_subido = st.file_uploader(
    "Selecciona el archivo Excel (.xlsx)", type=["xlsx"]
)

if archivo_subido is not None:
  df = pd.read_excel(archivo_subido)

  if "Teléfono" in df.columns:
    df.rename(columns={"Teléfono": "Telefono"}, inplace=True)

  st.success("✅ Archivo cargado correctamente.")
  st.subheader("📱 Mensajes listos para enviar:")

  for _, row in df.iterrows():
    mensaje = (
        f"Hola {row['Paciente']}, le recordamos desde la clínica su cita"
        f" mañana a las {row['Hora']} con {row['Fisio / Dentista']}. Por favor,"
        " responda OK para confirmar. ¡Gracias!"
    )

    # Tarjeta limpia con letras en negro y fondo elegante
    st.markdown(
        f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <p style="color: #000000; margin: 0 0 8px 0; font-size: 16px;"><b>Paciente:</b> {row['Paciente']} &nbsp;|&nbsp; <b>Tlf:</b> {row['Telefono']}</p>
            <hr style="margin: 6px 0; border-top: 1px solid #dcdcdc;">
            <p style="color: #000000; margin: 8px 0 0 0; font-size: 15px;">💬 {mensaje}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
