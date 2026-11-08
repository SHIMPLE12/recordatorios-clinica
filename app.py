from datetime import datetime, timedelta
import urllib.parse
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recordatorios Clínicas", page_icon="🦷", layout="centered"
)

st.title("🦷 Recordatorios Automáticos para Clínicas")
st.write(
    "Sube el archivo Excel. La app filtrará automáticamente solo las citas de"
    " mañana."
)

uploaded_file = st.file_uploader(
    "Selecciona el archivo Excel (.xlsx)", type=["xlsx", "xls"]
)

if uploaded_file is not None:
  try:
    # 1. Leer el archivo Excel
    df = pd.read_excel(uploaded_file)

    # 2. Normalizar nombres de columnas
    df.columns = df.columns.astype(str).str.strip()

    column_mapping = {
        "paciente": [
            "paciente",
            "nombre",
            "cliente",
            "nombre paciente",
            "nombre y apellidos",
        ],
        "telefono": ["telefono", "móvil", "movil", "tlf", "celular", "teléfono"],
        "fecha": ["fecha", "dia", "día", "fecha cita"],
        "hora": ["hora", "horario", "hora cita"],
    }


    def encontrar_columna(df_cols, posibles_nombres):
      for col in df_cols:
        if col.lower() in posibles_nombres:
          return col
      return None


    col_paciente = encontrar_columna(df.columns, column_mapping["paciente"])
    col_telefono = encontrar_columna(df.columns, column_mapping["telefono"])
    col_fecha = encontrar_columna(df.columns, column_mapping["fecha"])
    col_hora = encontrar_columna(df.columns, column_mapping["hora"])

    if not col_paciente or not col_telefono:
      st.error(
          "⚠️ No se han podido detectar las columnas de 'Paciente' y"
          f" 'Teléfono'. Columnas: {list(df.columns)}"
      )
    else:
      renombrar_dict = {
          col_paciente: "Paciente",
          col_telefono: "Teléfono",
      }
      if col_fecha:
        renombrar_dict[col_fecha] = "Fecha"
      if col_hora:
        renombrar_dict[col_hora] = "Hora"

      df = df.rename(columns=renombrar_dict)
      df = df.dropna(subset=["Paciente"])

      # 3. Filtrar estrictamente por la fecha de mañana
      if "Fecha" in df.columns:
        mañana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        df["Fecha_str"] = (
            pd.to_datetime(df["Fecha"], errors="coerce")
            .dt.strftime("%Y-%m-%d")
            .fillna(df["Fecha"].astype(str))
        )

        df_mañana = df[df["Fecha_str"] == mañana]

        if df_
