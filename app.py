import pandas as pd
import urllib.parse
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Recordatorio de Citas - WhatsApp", page_icon="📅", layout="centered"
)

# Estilo visual limpio y directo
st.title("📅 Recordatorios de Citas por WhatsApp")
st.markdown(
    "Sube el Excel con las citas del día para generar los enlaces de WhatsApp de"
    " forma automática."
)

# --- BARRA LATERAL: Configuración de la Clínica ---
st.sidebar.header("⚙️ Configuración")
nombre_clinica = st.sidebar.text_input(
    "Nombre de la Clínica",
    value="Clínica Médica",
    placeholder="Ej: Clínica Dental Sonrisa",
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Consejo:** El sistema detecta automáticamente las columnas de"
    " Nombre, Teléfono y Hora si tus cabeceras tienen nombres lógicos."
)

# --- CONTENIDO PRINCIPAL ---
uploaded_file = st.file_uploader(
    "Sube tu archivo Excel (.xlsx o .xls) o CSV", type=["xlsx", "xls", "csv"]
)

if uploaded_file is not None:
  try:
    # Leer el archivo según su formato
    if uploaded_file.name.endswith(".csv"):
      df = pd.read_csv(uploaded_file)
    else:
      df = pd.read_excel(uploaded_file)

    st.success(
        f"¡Archivo cargado con éxito! Se han encontrado {len(df)} registros."
    )

    # Mostrar una vista previa de los datos
    with st.expander("🔍 Ver vista previa de los datos"):
      st.dataframe(df.head())

    # --- DETECCIÓN INTELIGENTE DE COLUMNAS ---
    columnas = list(df.columns)


    def buscar_columna_sugerida(opciones, palabras_clave):
      for col in opciones:
        col_lower = str(col).lower()
        for palabra in palabras_clave:
          if palabra in col_lower:
            return col
      return opciones[0] if len(opciones) > 0 else None


    sugerencia_nombre = buscar_columna_sugerida(
        columnas, ["nombre", "paciente", "cliente", "name"]
    )
    sugerencia_tel = buscar_columna_sugerida(
        columnas, ["telefono", "tel", "movil", "celular", "phone"]
    )
    sugerencia_hora = buscar_columna_sugerida(
        columnas, ["hora", "fecha", "cita", "time", "date"]
    )

    idx_nombre = (
        columnas.index(sugerencia_nombre) if sugerencia_nombre in columnas else 0
    )
    idx_tel = (
        columnas.index(sugerencia_tel) if sugerencia_tel in columnas else 0
    )
    idx_hora = (
        columnas.index(sugerencia_hora) if sugerencia_hora in columnas else 0
    )

    st.subheader("1. Columnas detectadas")
    col1, col2, col3 = st.columns(3)
    with col1:
      col_nombre = st.selectbox(
          "Columna de Nombre", columnas, index=idx_nombre
      )
    with col2:
      col_telefono = st.selectbox(
          "Columna de Teléfono", columnas, index=idx_tel
      )
    with col3:
      col_hora = st.selectbox("Columna de Hora/Fecha", columnas, index=idx_hora)

    # Personalización de la plantilla del mensaje
    st.subheader("2. Plantilla del mensaje")
    plantilla_defecto = (
        f"Hola [Nombre], le recordamos su cita en *{nombre_clinica}* para mañana"
        " a las [Hora]. Por favor, responda OK para confirmar su asistencia."
        " ¡Gracias!"
    )
    mensaje_personalizado = st.text_area(
        "Edita el mensaje si lo deseas (usa [Nombre] y [Hora] como"
        " comodines):",
        value=plantilla_defecto,
        height=100,
    )

    # Botón para generar los enlaces
    if st.button("🚀 Generar Enlaces de WhatsApp"):
      st.markdown("---")
      st.subheader(f"3. Enlaces listos para enviar ({nombre_clinica})")

      for index, row in df.iterrows():
        paciente = str(row[col_nombre])
        telefono = str(row[col_telefono]).strip()
        hora = str(row[col_hora])

        # Limpiar el teléfono dejando solo dígitos y el signo +
        telefono_limpio = "".join(filter(lambda x: x.isdigit() or x == "+", telefono))

        # Reemplazar comodines en el mensaje
        texto_final = (
            mensaje_personalizado.replace("[Nombre]", paciente)
            .replace("[Hora]", hora)
            .replace("[Clinica]", nombre_clinica)
        )

        # Codificar el texto para URL de WhatsApp
        texto_codificado = urllib.parse.quote(texto_final)
        link_whatsapp = (
            f"https://api.whatsapp.com/send?phone={telefono_limpio}&text={texto_codificado}"
        )

        # Mostrar tarjeta limpia por cada paciente
        col_info, col_btn = st.columns([3, 1])
        with col_info:
          st.markdown(
              f"**{paciente}** — 🕒 {hora} — 📱 `+{telefono_limpio}`"
          )
        with col_btn:
          st.markdown(
              f"[Enviar WhatsApp]({link_whatsapp})", unsafe_allow_html=True
          )

      st.success(
          "¡Todos los enlaces generados correctamente! Haz clic en cada botón"
          " para abrir WhatsApp Web con el mensaje listo."
      )

  except Exception as e:
    st.error(
        f"Hubo un error al leer el archivo. Comprueba que el formato sea"
        f" correcto. Detalle: {e}"
    )

else:
  st.info(
      "👆 Sube un archivo Excel arriba para comenzar a generar los"
      " recordatorios personalizados."
  )
