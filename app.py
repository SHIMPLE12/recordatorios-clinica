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

    with st.container():
      st.markdown(
          f"**Paciente:** {row['Paciente']} | **Tlf:** {row['Telefono']}"
      )
      st.code(mensaje, language="text")
      st.divider()
