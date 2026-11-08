import urllib.parse
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recordatorios Clínicas", page_icon="🦷", layout="centered"
)

st.title("🦷 Recordatorios Automáticos para Clínicas")
st.write(
    "Sube el archivo Excel de la clínica para generar los mensajes de WhatsApp y"
    " SMS."
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

      st.success(
          "¡Archivo procesado con éxito! Citas detectadas correctamente."
      )

      # Generador de mensajes con botones de WhatsApp y SMS
      st.subheader("💬 Mensajes listos para enviar")

      for index, row in df.iterrows():
        paciente = str(row.get("Paciente", "Paciente"))
        hora = str(row.get("Hora", "su hora habitual"))
        telefono_raw = str(row.get("Teléfono", ""))

        # Limpiar teléfono para los enlaces (solo números)
        telefono_limpio = "".join(filter(str.isdigit, telefono_raw))

        mensaje = (
            f"Hola {paciente}, le escribimos de la clínica para recordarle su"
            f" cita programada para mañana a las {hora}. Por favor, responda"
            " OK para confirmar."
        )

        # Mostrar cuadro de texto con el mensaje
        st.text_area(
            f"Paciente: {paciente} ({telefono_raw})",
            value=mensaje,
            height=70,
            key=f"msg_{index}",
        )

        if telefono_limpio:
          mensaje_encoded = urllib.parse.quote(mensaje)
          whatsapp_url = f"https://wa.me/{telefono_limpio}?text={mensaje_encoded}"
          sms_url = f"sms:{telefono_limpio}?body={mensaje_encoded}"

          # Contenedor para poner los botones uno al lado del otro o apilados limpios
          st.markdown(
              f"""
                        <div style="margin-bottom: 20px;">
                            <a href="{whatsapp_url}" target="_blank" style="display:block; background-color:#25D366; color:white; padding:10px 15px; border-radius:8px; text-decoration:none; font-weight:bold; text-align:center; margin-bottom: 8px;">
                                📲 Enviar a WhatsApp de {paciente}
                            </a>
                            <a href="{sms_url}" style="display:block; background-color:#007AFF; color:white; padding:10px 15px; border-radius:8px; text-decoration:none; font-weight:bold; text-align:center;">
                                ✉️ Enviar por SMS a {paciente}
                            </a>
                        </div>
                        """,
              unsafe_allow_html=True,
          )
        else:
          st.warning(
              f"⚠️ El paciente {paciente} no tiene un teléfono válido."
          )

  except Exception as e:
    st.error(f"❌ Error al procesar el archivo: {e}")
