import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recordatorios Clínicas", page_icon="🦷", layout="centered"
)

st.title("🦷 Recordatorios Automáticos para Clínicas")
st.write(
    "Sube el archivo Excel de la clínica. La app detectará automáticamente los"
    " datos sin importar el orden o los nombres de las columnas."
)

uploaded_file = st.file_uploader(
    "Selecciona el archivo Excel (.xlsx)", type=["xlsx", "xls"]
)

if uploaded_file is not None:
  try:
    # 1. Leer el archivo Excel
    df = pd.read_excel(uploaded_file)

    # 2. Normalizar nombres de columnas (quitar espacios y pasar a minúsculas)
    df.columns = df.columns.astype(str).str.strip()

    # 3. Diccionario de sinónimos para encontrar columnas clave
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

    # 4. Validar columnas obligatorias
    if not col_paciente or not col_telefono:
      st.error(
          "⚠️ No se han podido detectar automáticamente las columnas de"
          f" 'Paciente' y 'Teléfono'. Columnas encontradas: {list(df.columns)}"
      )
    else:
      # Renombrar para estandarizar
      renombrar_dict = {
          col_paciente: "Paciente",
          col_telefono: "Teléfono",
      }
      if col_fecha:
        renombrar_dict[col_fecha] = "Fecha"
      if col_hora:
        renombrar_dict[col_hora] = "Hora"

      df = df.rename(columns=renombrar_dict)

      # Limpiar filas vacías de pacientes
      df = df.dropna(subset=["Paciente"])

      st.success(
          "¡Archivo procesado con éxito! Se han detectado los pacientes"
          " correctamente."
      )

      # Mostrar vista previa de la tabla limpia
      st.dataframe(df)

      # Generador de mensajes de WhatsApp
      st.subheader("💬 Mensajes de WhatsApp listos para enviar")
      for index, row in df.iterrows():
        paciente = str(row.get("Paciente", "Paciente"))
        hora = str(row.get("Hora", "su hora habitual"))
        telefono = str(row.get("Teléfono", ""))

        mensaje = (
            f"Hola {paciente}, le escribimos de la clínica para recordarle su"
            f" cita programada para mañana a las {hora}. Por favor, responda"
            " OK para confirmar."
        )

        st.text_area(
            f"Mensaje para: {paciente} ({telefono})", value=mensaje, height=70
        )

  except Exception as e:
    st.error(f"❌ Error al leer el archivo Excel: {e}")
