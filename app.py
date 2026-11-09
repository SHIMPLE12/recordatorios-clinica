from datetime import datetime, timedelta
import urllib.parse
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Recordatorios Clínicas", page_icon="🦷", layout="centered"
)

# --- BARRA LATERAL: Configuración de la Clínica ---
st.sidebar.header("⚙️ Configuración")
nombre_clinica = st.sidebar.text_input(
    "Nombre de la Clínica",
    value="nuestra clínica",
    placeholder="Ej: Clínica Dental Sonrisa",
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 Sube tu Excel. La app filtrará automáticamente solo las citas de"
    " mañana y adaptará el mensaje con el nombre de tu centro."
)

# --- CONTENIDO PRINCIPAL ---
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

    # 2. Normalizar nombres de columnas (quitar espacios a los lados y pasar a minúsculas)
    df.columns = df.columns.astype(str).str.strip()


    # BÚSQUEDA SÚPER FLEXIBLE Y DIRECTA
    def encontrar_columna_inteligente(df_cols, palabras_clave):
      for col in df_cols:
        col_lower = str(col).lower()
        for palabra in palabras_clave:
          if palabra in col_lower:
            return col
      return None


    # Definimos qué buscar
    col_paciente = encontrar_columna_inteligente(
        df.columns, ["paciente", "nombre", "cliente"]
    )
    col_telefono = encontrar_columna_inteligente(
        df.columns, ["tel", "móvil", "movil", "tlf", "celular"]
    )
    col_fecha = encontrar_columna_inteligente(
        df.columns, ["fecha", "dia", "día", "cita"]
    )
    col_hora = encontrar_columna_inteligente(df.columns, ["hora", "horario"])

    if not col_paciente or not col_telefono:
      st.error(
          "⚠️ No se han podido detectar las columnas de 'Paciente' y"
          f" 'Teléfono'. Columnas encontradas: {list(df.columns)}"
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

      # 3. Filtrar estrictamente por la fecha de mañana (con dayfirst=True para formato europeo)
      if "Fecha" in df.columns:
        mañana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        df["Fecha_str"] = (
            pd.to_datetime(df["Fecha"], dayfirst=True, errors="coerce")
            .dt.strftime("%Y-%m-%d")
            .fillna(df["Fecha"].astype(str))
        )

        df_mañana = df[df["Fecha_str"] == mañana]

        if df_mañana.empty:
          st.warning(
              f"⚠️ No hay ninguna cita programada para mañana ({mañana}). El"
              " archivo no contiene citas para esa fecha."
          )
          df_filtrado = df.iloc[0:0]
        else:
          df_filtrado = df_mañana
          st.success(
              f"✅ ¡Se han encontrado y filtrado las citas para mañana"
              f" ({mañana})!"
          )
      else:
        st.warning(
            "⚠️ No se ha encontrado ninguna columna de fecha en el archivo."
        )
        df_filtrado = df.iloc[0:0]

      # 4. Generador de mensajes (solo si hay citas para mañana)
      if not df_filtrado.empty:
        st.subheader("💬 Mensajes listos para enviar")

        for index, row in df_filtrado.iterrows():
          paciente = str(row.get("Paciente", "Paciente"))
          hora = str(row.get("Hora", "su hora habitual"))
          telefono_raw = str(row.get("Teléfono", ""))

          telefono_limpio = "".join(filter(str.isdigit, telefono_raw))

          # Mensaje personalizado incluyendo el nombre de la clínica dinámico
          mensaje = (
              f"Hola {paciente}, le escribimos de *{nombre_clinica}* para"
              f" recordarle su cita programada para mañana a las {hora}. Por"
              " favor, responda OK para confirmar."
          )

          st.text_area(
              f"Paciente: {paciente} ({telefono_raw})",
              value=mensaje,
              height=70,
              key=f"msg_{index}",
          )

          if telefono_limpio:
            mensaje_encoded = urllib.parse.quote(mensaje)
            whatsapp_url = (
                f"https://wa.me/{telefono_limpio}?text={mensaje_encoded}"
            )
            sms_url = f"sms:{telefono_limpio}?body={mensaje_encoded}"

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
