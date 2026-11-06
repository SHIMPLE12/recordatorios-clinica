from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Gestor de Citas y Recordatorios",
    page_icon="🏥",
    layout="centered",
)

st.title("🏥 Gestor de Recordatorios de Citas")
st.write(
    "Sube el archivo Excel de la clínica. La app filtrará automáticamente"
    " solo las citas de mañana."
)

archivo_subido = st.file_uploader(
    "Selecciona el archivo Excel (.xlsx)", type=["xlsx"]
)

if archivo_subido is not None:
  df = pd.read_excel(archivo_subido)

  # Normalizar nombres de columnas por si acaso vienen con mayúsculas/minúsculas
  df.columns = df.columns.str.strip()
  if "Teléfono" in df.columns:
    df.rename(columns={"Teléfono": "Telefono"}, inplace=True)

  # Eliminar filas donde falte el paciente o el teléfono
  df = df.dropna(subset=["Paciente", "Telefono"])

  # --- FILTRO INTELIGENTE DE FECHAS ---
  # Si tu Excel tiene una columna llamada 'Fecha', filtramos automáticamente para mañana:
  if "Fecha" in df.columns:
    # Calculamos la fecha de mañana en formato YYYY-MM-DD (ajustable según tu formato de Excel)
    mañana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Filtramos el DataFrame para que solo salgan los de mañana
    # (Convertimos a string por seguridad)
    df["Fecha_str"] = pd.to_datetime(df["Fecha"]).dt.strftime("%Y-%m-%d")
    df_filtrado = df[df["Fecha_str"] == mañana]

    if df_filtrado.empty:
      st.warning(
          "⚠️ No se han encontrado citas para mañana en el Excel. Mostrando"
          " todas las citas disponibles de ejemplo:"
      )
      df_filtrado = df  # Si no coincide exactamente, mostramos todo para que no se quede vacío
    else:
      st.success(
          f"✅ Se han filtrado automáticamente las citas para mañana"
          f" ({mañana})."
      )
  else:
    df_filtrado = (
        df  # Si el Excel no tiene columna de fecha, usa todas las filas
    )

  # Pestañas para WhatsApp y SMS
  tab1, tab2 = st.tabs(["📱 WhatsApp", "💬 SMS Tradicional"])

  with tab1:
    st.subheader("Mensajes para WhatsApp")
    for _, row in df_filtrado.iterrows():
      mensaje_wa = (
          f"Hola {row['Paciente']}, le recordamos desde la clínica su cita"
          f" mañana a las {row['Hora']} con {row['Fisio / Dentista']}. Por"
          " favor, responda OK para confirmar. ¡Gracias!"
      )
      st.markdown(
          f"""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <p style="color: #000000; margin: 0 0 8px 0; font-size: 16px;"><b>Paciente:</b> {row['Paciente']} &nbsp;|&nbsp; <b>Tlf:</b> {row['Telefono']}</p>
                <hr style="margin: 6px 0; border-top: 1px solid #dcdcdc;">
                <p style="color: #000000; margin: 8px 0 0 0; font-size: 15px;">💬 {mensaje_wa}</p>
            </div>
            """,
          unsafe_allow_html=True,
      )

  with tab2:
    st.subheader("Mensajes cortos para SMS")
    for _, row in df_filtrado.iterrows():
      mensaje_sms = (
          f"Clinica: Le recordamos su cita manana a las {row['Hora']} con"
          f" {row['Fisio / Dentista']}. Responda OK para confirmar."
      )
      st.markdown(
          f"""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 12px; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <p style="color: #000000; margin: 0 0 8px 0; font-size: 16px;"><b>Paciente:</b> {row['Paciente']} &nbsp;|&nbsp; <b>Tlf:</b> {row['Telefono']}</p>
                <hr style="margin: 6px 0; border-top: 1px solid #dcdcdc;">
                <p style="color: #000000; margin: 8px 0 0 0; font-size: 15px;">✉️ {mensaje_sms}</p>
            </div>
            """,
          unsafe_allow_html=True,
      )
