import streamlit as st
import pandas as pd
import gspread
from gspread_pandas import Spread
from datetime import datetime

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Calendario de Mantenciones",
    page_icon="🗓️",
    layout="wide"
)

st.title("🗓️ Calendario de Mantenciones")
st.write("Aplicación para el seguimiento de tareas de mantención de Aldo Ramos y Nicolás Ruiz.")


# --- 2. CONEXIÓN A GOOGLE SHEETS ---
# Se usa cache_resource para que la conexión se haga una sola vez por sesión.
@st.cache_resource
def connect_to_sheet():
    """Conecta con Google Sheets usando las credenciales guardadas en st.secrets."""
    try:
        creds = st.secrets["gcp_service_account"]
        client = gspread.service_account_from_dict(creds)
        return client
    except Exception as e:
        st.error(f"Error de conexión con Google Sheets: {e}")
        st.info("Asegúrate de haber configurado correctamente tu archivo 'secrets.toml'.")
        return None


# --- 3. CARGA DE DATOS ---
# Se usa cache_data para recargar los datos periódicamente y no en cada interacción.
@st.cache_data(ttl=60)  # La caché de los datos expira cada 60 segundos
def load_data(_client, sheet_name="Calendario Mantenciones"):
    """Carga los datos de la hoja 'Calendario Mantenciones' y los devuelve como un DataFrame."""
    if _client is None:
        return pd.DataFrame()
    try:
        spread = Spread(sheet_name, client=_client)
        df = spread.sheet_to_df(index=False, header_rows=1)
        # Asegurarse que las columnas importantes tengan el tipo correcto
        df['id'] = pd.to_numeric(df['id'])
        df['estado'] = pd.to_numeric(df['estado'])
        df['fecha_dt'] = pd.to_datetime(df['fecha'], format='%d-%m-%y', errors='coerce')
        return df.sort_values(by='fecha_dt').reset_index(drop=True)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Error: No se encontró la hoja de cálculo con el nombre '{sheet_name}'.")
        st.info(f"Asegúrate de que el nombre sea exacto y que la hayas compartido con: {_client.auth.signer_email}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocurrió un error al cargar los datos: {e}")
        return pd.DataFrame()


# --- 4. LÓGICA PRINCIPAL DE LA APLICACIÓN ---

# Conectar y cargar los datos
client = connect_to_sheet()
df_tasks = load_data(client)

if not df_tasks.empty:
    # --- FILTROS EN LA BARRA LATERAL ---
    with st.sidebar:
        st.header("Filtros")
        ingeniero_filtro = st.selectbox(
            "Filtrar por Ingeniero:",
            options=["Todos"] + sorted(df_tasks["ingeniero"].unique().tolist())
        )
        # Convertir 0 y 1 a texto legible para el filtro
        estado_map = {0: "Pendiente", 1: "Completada"}
        estado_filtro_text = st.selectbox(
            "Filtrar por Estado:",
            options=["Todos", "Pendiente", "Completada"]
        )

    # --- APLICAR FILTROS ---
    df_filtered = df_tasks.copy()
    if ingeniero_filtro != "Todos":
        df_filtered = df_filtered[df_filtered["ingeniero"] == ingeniero_filtro]

    if estado_filtro_text != "Todos":
        estado_val = 0 if estado_filtro_text == "Pendiente" else 1
        df_filtered = df_filtered[df_filtered["estado"] == estado_val]

    # --- MOSTRAR LAS TAREAS ---
    st.write(f"#### Mostrando {len(df_filtered)} de {len(df_tasks)} tareas totales")

    if df_filtered.empty:
        st.info("No hay tareas que coincidan con los filtros seleccionados.")
    else:
        for index, row in df_filtered.iterrows():
            is_completed = (row['estado'] == 1)
            # Definir color del borde según el estado
            border_color = "border-green-500" if is_completed else "border-yellow-500"

            with st.container(border=True):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"**{row['tarea']}** (ID: {row['id']})")
                    st.caption(
                        f"Asignado a: {row['ingeniero']} | Fecha: {row['fecha']} | Frecuencia: {row['frecuencia']}")

                with col2:
                    if is_completed:
                        st.success("✅ Completada", icon="✅")
                    else:
                        if st.button("Marcar como completada", key=f"btn_{row['id']}", type="primary"):
                            try:
                                # Conectar a la hoja para actualizar
                                worksheet = client.open("Calendario Mantenciones").sheet1

                                # Encontrar la celda de la columna 'id' que coincide
                                cell = worksheet.find(str(row['id']), in_column=1)

                                if cell:
                                    # Actualizar la celda de la columna 'estado' (columna 6)
                                    worksheet.update_cell(cell.row, 6, 1)  # 1 = Completada
                                    st.toast(f"Tarea {row['id']} marcada como completada.")

                                    # Limpiar la caché y re-ejecutar para ver el cambio
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"No se encontró el ID {row['id']} en la hoja.")

                            except Exception as e:
                                st.error(f"No se pudo actualizar la hoja: {e}")

# --- 5. EJECUTAR LA APLICACIÓN ---
# Para correr tu aplicación, abre una terminal en la carpeta del proyecto y ejecuta:
# streamlit run app.py