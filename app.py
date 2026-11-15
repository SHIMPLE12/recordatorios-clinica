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
        (ancho_maximo, nuevo_alto), Image.Resampling.LANCZOS
    )

  buffer_salida = io.BytesIO()
  imagen.save(buffer_salida, format="JPEG", quality=calidad_jpg)
  buffer_salida.seek(0)
  return Image.open(buffer_salida)


# ==========================================
# OPCIÓN 1: SUBIR EXCEL
# ==========================================
if modo_entrada == "📁 Subir archivo Excel":
  uploaded_file = st.file_uploader(
      "Selecciona el archivo Excel (.xlsx)", type=["xlsx", "xls"]
  )

  if uploaded_file is not None:
    try:
      df = pd.read_excel(uploaded_file)
      df.columns = df.columns.astype(str).str.strip()


      def encontrar_columna_inteligente(df_cols, palabras_clave):
        for col in df_cols:
          col_lower = str(col).lower()
          for palabra in palabras_clave:
            if palabra in col_lower:
              return col
        return None


      col_paciente = encontrar_columna_inteligente(
          df.columns,
          ["paciente", "nombre", "cliente", "nom", "pacient", "client"],
      )
      col_telefono = encontrar_columna_inteligente(
          df.columns,
          ["tel", "móvil", "movil", "tlf", "celular", "telèfon", "mòbil"],
      )
      col_fecha = encontrar_columna_inteligente(
          df.columns, ["fech", "data", "dia", "día"]
      )
      col_hora = encontrar_columna_inteligente(
          df.columns, ["hora", "horario", "horari", "hr"]
      )

      if not col_fecha and len(df.columns) >= 3:
        col_fecha = df.columns[2]

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

        if "Fecha" in df.columns:
          mañana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
          df["Fecha_str"] = pd.to_datetime(
              df["Fecha"], errors="coerce"
          ).dt.strftime("%Y-%m-%d")

          mask_nans = df["Fecha_str"].isna()
          if mask_nans.any():
            df.loc[mask_nans, "Fecha_str"] = (
                pd.to_datetime(
                    df.loc[mask_nans, "Fecha"], dayfirst=True, errors="coerce"
                )
                .dt.strftime("%Y-%m-%d")
                .fillna(df.loc[mask_nans, "Fecha"].astype(str))
            )

          df_mañana = df[df["Fecha_str"] == mañana]

          if df_mañana.empty:
            st.warning(
                f"⚠️ No hay citas para mañana ({mañana}) en este archivo."
            )
            df_filtrado = df.iloc[0:0]
          else:
            df_filtrado = df_mañana
            st.success(f"✅ ¡Citas para mañana ({mañana}) filtradas con éxito!")
        else:
          st.warning(
              "⚠️ No se ha encontrado ninguna columna de fecha en el archivo."
          )
          df_filtrado = df.iloc[0:0]

    except Exception as e:
      st.error(f"❌ Error al procesar el archivo Excel: {e}")

# ==========================================
# OPCIÓN 2: FOTO DE LA LIBRETA (CON GEMINI 3.8 FLASH)
# ==========================================
elif modo_entrada == "📸 Hacer foto a la libreta de papel":
  st.info(
      "💡 Sube una foto clara de la página de la libreta. Gemini extraerá los"
      " datos automáticamente."
  )
  foto_subida = st.file_uploader(
      "Sube la foto de la libreta", type=["jpg", "jpeg", "png"]
  )

  if foto_subida is not None:
    st.image(foto_subida, caption="Foto de la libreta", width="stretch")

    if st.button("✨ Procesar libreta con Gemini"):
      with st.spinner("Analizando la libreta con Google Gemini..."):
        try:
          # 1. Preparamos la imagen con PIL
          imagen_optimizada = preparar_imagen_para_ia(foto_subida)

          # 2. Usamos el modelo correcto pedido por Google
          model = genai.GenerativeModel("gemini-3.8-flash")

          prompt = (
              "Analiza esta imagen de una agenda o libreta médica manuscrita."
              " Extrae todas las citas que aparezcan y devuélvelas"
              " EXCLUSIVAMENTE en formato JSON válido que contenga una clave"
              " llamada 'citas' con una lista de objetos. Cada objeto debe"
              " tener exactamente estas tres claves: 'Paciente', 'Hora' y"
              " 'Telefono'. Si algún dato no aparece, escribe 'No"
              " especificado'. No incluyas explicaciones ni texto fuera del"
              " JSON."
          )

          response = model.generate_content([prompt, imagen_optimizada])

          texto_respuesta = response.text.strip()
          if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:]
          if texto_respuesta.endswith("```"):
            texto_respuesta = texto_respuesta[:-3]

          contenido_json = json.loads(texto_respuesta.strip())
          lista_citas = (
              contenido_json.get("citas")
              or contenido_json.get("data")
              or list(contenido_json.values())[0]
          )

          df_ia = pd.DataFrame(lista_citas)
          if not df_ia.empty:
            st.session_state["df_ia_procesado"] = df_ia
            st.success("¡Citas extraídas correctamente de la libreta!")
          else:
            st.warning("No se han encontrado citas claras en la imagen.")

        except Exception as e:
          st.error(f"Error al procesar la imagen con Gemini: {e}")

    if "df_ia_procesado" in st.session_state:
      st.write("📋 **Revisa y edita los datos si es necesario:**")
      df_filtrado = st.data_editor(
          st.session_state["df_ia_procesado"], num_rows="dynamic"
      )


# ==========================================
# 3. GENERADOR DE MENSAJES DE WHATSAPP
# ==========================================
if not df_filtrado.empty:
  st.markdown("---")
  st.subheader("💬 Mensajes listos para enviar")

  for index, row in df_filtrado.iterrows():
    paciente = str(row.get("Paciente", "Paciente"))
    hora = str(row.get("Hora", "su hora habitual"))
    telefono_raw = str(row.get("Teléfono", row.get("Telefono", "")))

    telefono_limpio = "".join(filter(str.isdigit, telefono_raw))

    mensaje = (
        f"Hola {paciente}, le escribimos de *{nombre_clinica}* para recordarle"
        f" su cita programada para mañana a las {hora}. Por favor, responda OK"
        " para confirmar."
    )

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

      st.markdown(
          f"""
                    <div style="margin-bottom: 20px;">
                        <a href="{whatsapp_url}" style="display:block; background-color:#25D366; color:white; padding:12px 15px; border-radius:8px; text-decoration:none; font-weight:bold; text-align:center; margin-bottom: 8px;">
                            📲 Enviar a WhatsApp de {paciente}
                        </a>
                        <a href="{sms_url}" style="display:block; background-color:#007AFF; color:white; padding:12px 15px; border-radius:8px; text-decoration:none; font-weight:bold; text-align:center;">
                            ✉️ Enviar por SMS a {paciente}
                        </a>
                    </div>
                    """,
          unsafe_allow_html=True,
      )
    else:
      st.warning(f"⚠️ El paciente {paciente} no tiene un teléfono válido.")
