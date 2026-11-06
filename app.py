import os
import pandas as pd


def generar_recordatorios():
  archivo_excel = "citas_clinica.xlsx"

  if not os.path.exists(archivo_excel):
    print(
        f"⚠️ No se encuentra el archivo '{archivo_excel}'. Asegúrate de que está"
        " en la misma carpeta."
    )
    return

  # Cargar la tabla de Excel
  df = pd.read_excel(archivo_excel)

  # Normalizar el nombre de la columna por si lleva tilde
  if "Teléfono" in df.columns:
    df.rename(columns={"Teléfono": "Telefono"}, inplace=True)

  fecha_objetivo = "2026-11-07"

  print(
      f"🏥 [SISTEMA DE CITAS] Buscando citas para la fecha: {fecha_objetivo}...\n"
  )

  citas_filtradas = df[df["Fecha_Cita"] == fecha_objetivo]

  if citas_filtradas.empty:
    print(
        "📭 No hay citas para esa fecha. Revisa que la fecha en el Excel"
        " coincida."
    )
    return

  # Generar los mensajes listos para WhatsApp
  for _, row in citas_filtradas.iterrows():
    mensaje = (
        f"Hola {row['Paciente']}, le recordamos desde la clínica su cita"
        f" mañana a las {row['Hora']} con {row['Fisio / Dentista']}. Por favor,"
        " responda OK para confirmar. ¡Gracias!"
    )
    print(f"📱 [MENSAJE PARA: {row['Paciente']} - Tlf: {row['Telefono']}]")
    print(f'"{mensaje}"\n')
    print("-" * 50)


if __name__ == "__main__":
  generar_recordatorios()
