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
nombre_clinica = st.sidebar.text_input(
    "Nombre de la Clínica", value="nuestra clínica"
)

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


# Función optimizada: reduce drásticamente el peso de la foto para que vuele
def preparar_imagen_rapida(archivo_subido, ancho_maximo=800, calidad_jpg=75):
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
# 1. SUBIR EXCEL
# ==========================================
if modo_entrada == "📁 Subir archivo Excel":
  archivo = st.file_uploader("Sube tu Excel (.xlsx)", type=["xlsx", "xls"])
  if archivo is not None:
    try:
      df = pd.read_excel(archivo)
      df.columns = df.columns.astype(str).str.strip()

      cols = [c.lower() for c in df.columns]
      col_p = next(
          (
              df.columns[i]
              for i, c in enumerate(cols)
              if "pac" in c or "nom" in c
          ),
          df.columns[0],
      )
      col_t = next(
          (
              df.columns[i]
              for i, c in enumerate(cols)
              if "tel" in c or "móv" in c or "mov" in c
          ),
          df.columns[1],
      )
      col_f = next(
          (
              df.columns[i]
              for i, c in enumerate(cols)
              if "fec" in c or "data" in c or "dia" in c
          ),
          df.columns[2] if len(df.columns) > 2 else None,
      )
      col_h = next(
          (df.columns[i] for i, c in enumerate(cols) if "hora" in c),
          df.columns[3] if len(df.columns) > 3 else None,
      )

      df = df.rename(
          columns={
              col_p: "Paciente",
              col_t: "Teléfono",
              col_f: "Fecha",
              col_h: "Hora",
          }
      )
      df = df.dropna(subset=["Paciente"])

      if "Fecha" in df.columns:
        df["Fecha_limpia"] = pd.to_datetime(
            df["Fecha"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
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
# 2. FOTO DE LA LIBRETA (ULTRA RÁPIDA)
# ==========================================
elif modo_entrada == "📸 Hacer foto a la libreta":
  foto = st.file_uploader("Sube la foto", type=["jpg", "jpeg", "png"])
  if foto is not None:
    st.image(foto, caption="Foto subida", use_container_width=True)

    if st.button("✨ Procesar con Gemini"):
      mañana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
      with st.spinner("Procesando imagen rápidamente..."):
        try:
          # Comprimimos la imagen al instante antes de enviarla
          img_opt = preparar_imagen_rapida(foto)
          model = genai.GenerativeModel("gemini-3.8-flash")

          prompt = (
              f"Hoy es {datetime.now().strftime('%Y-%m-%d')}. Analiza esta"
              f" imagen. Extrae ÚNICAMENTE las citas que correspondan al día de"
              f" mañana ({mañana}). Devuélvelas EXCLUSIVAMENTE en formato JSON"
              " con una clave llamada 'citas' que sea una lista de objetos."
              " Cada objeto debe tener exactamente las claves: 'Paciente',"
              " 'Hora', 'Telefono'. Si no hay citas para mañana, devuelve una"
              " lista vacía."
          )

          response = model.generate_content([prompt, img_opt])

          texto = response.text.strip()
          if texto.startswith("```json"):
            texto = texto[7:]
          if texto.endswith("```"):
            texto = texto[:-3]

          data = json.loads(texto.strip())
          lista = (
              data.get("citas") or data.get("data") or list(data.values())[0]
          )

          df_ia = pd.DataFrame(lista)
          if not df_ia.empty:
            st.session_state["df_ia"] = df_ia
            st.success(
                f"✅ ¡Citas para mañana ({mañana}) extraídas al instante!"
            )
            st.rerun()
          else:
            st.warning(
                f"⚠️ La IA no ha encontrado citas para mañana ({mañana}) en la"
                " foto."
            )
        except Exception as e:
          st.error(f"Error en Gemini: {e}")

    if "df_ia" in st.session_state:
      st.write("📋 **Revisa los datos extraídos:**")
      df_filtrado = st.data_editor(st.session_state["df_ia"], num_rows="dynamic")

# ==========================================
# 3. MENSAJES DE WHATSAPP
# ==========================================
if not df_filtrado.empty:
  st.markdown("---")
  st.subheader("💬 Mensajes listos para enviar")

  for index, row in df_filtrado.iterrows():
    paciente = str(row.get("Paciente", "Paciente"))
    hora = str(row.get("Hora", "su hora"))
    telefono_raw = str(
        row.get("Teléfono", row.get("Telefono", row.get("Tel", "")))
    )
    telefono_limpio = "".join(filter(str.isdigit, telefono_raw))

    mensaje = (
        f"Hola {paciente}, le escribimos de *{nombre_clinica}* para recordarle"
        f" su cita para mañana a las {hora}. Responda OK para confirmar."
    )

    st.text_area(
        f"Paciente: {paciente} ({telefono_raw})",
        value=mensaje,
        height=70,
        key=f"msg_{index}",
    )

    if telefono_limpio:
      w_url = (
          f"https://wa.me/{telefono_limpio}?text={urllib.parse.quote(mensaje)}"
      )
      sms_url = f"sms:{telefono_limpio}?body={urllib.parse.quote(mensaje)}"

      st.markdown(
          f"""
        <div style="margin-bottom: 20px;">
            <a href="{w_url}" style="display:block; background-color:#25D366; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold; text-align:center; margin-bottom: 8px;">
                📲 Enviar a WhatsApp de {paciente}
            </a>
            <a href="{sms_url}" style="display:block; background-color:#007AFF; color:white; padding:12px; border-radius:8px; text-decoration:none; font-weight:bold; text-align:center;">
                ✉️ Enviar por SMS a {paciente}
            </a>
        </div>
      """,
          unsafe_allow_html=True,
      )
    else:
      st.warning(f"⚠️ {paciente} no tiene teléfono válido.")
