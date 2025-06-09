import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
# Usar st.set_page_config() como el primer comando de Streamlit
st.set_page_config(
    page_title="Calendario de Tareas",
    page_icon="📅",
    layout="wide",
)

# --- CONEXIÓN CON GOOGLE SHEETS ---
# Esta función se conecta a Google Sheets usando los "Secrets" de Streamlit
# y devuelve el DataFrame con los datos.
@st.cache_data(ttl=60) # Cache para no recargar los datos en cada interacción por 60s
def load_data():
    try:
        # Define los alcances (scopes) necesarios para la API
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        
        # Carga las credenciales desde los Secrets de Streamlit
        # st.secrets["gcp_service_account"] es donde guardaste el contenido del JSON
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes,
        )
        client = gspread.authorize(creds)
        
        # Abre la hoja de cálculo por su URL
        sheet_url = "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
        spreadsheet = client.open_by_url(sheet_url)
        
        # Selecciona la hoja por su nombre (asegúrate que se llame 'Hoja 1')
        sheet = spreadsheet.worksheet("Hoja 1")
        
        # Obtiene todos los datos y los convierte a un DataFrame de Pandas
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Convierte la columna 'fecha' a formato de fecha para poder ordenarla
        df['fecha'] = pd.to_datetime(df['fecha'], format='%d-%m-%y')
        
        return df
    except Exception as e:
        # Si hay un error (ej. Secrets no configurados), muestra un mensaje amigable
        st.error(f"Error al cargar los datos desde Google Sheets: {e}")
        st.info("Asegúrate de haber configurado correctamente los 'Secrets' en Streamlit Cloud y de haber compartido la hoja de cálculo con el email de servicio.")
        return pd.DataFrame() # Devuelve un DataFrame vacío en caso de error

# Carga los datos al iniciar la app
df = load_data()

# --- INTERFAZ DE LA APLICACIÓN ---

st.title("📅 Calendario de Tareas de Ingeniería")
st.markdown("Aplicación para visualizar y registrar las tareas del equipo.")

if not df.empty:
    # --- FILTROS ---
    st.sidebar.header("Filtros")
    
    # Filtro por ingeniero
    ingenieros = df['ingeniero'].unique()
    selected_ingeniero = st.sidebar.multiselect('Filtrar por Ingeniero:', ingenieros, default=ingenieros)
    
    # Filtro por rango de fechas
    min_date = df['fecha'].min().date()
    max_date = df['fecha'].max().date()
    selected_date_range = st.sidebar.date_input(
        'Filtrar por Fecha:',
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Aplicar filtros al DataFrame
    # Asegurarse que el rango de fechas tenga dos valores
    if len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        # Convertir fechas a datetime para comparar
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        df_filtered = df[
            (df['ingeniero'].isin(selected_ingeniero)) &
            (df['fecha'] >= start_datetime) &
            (df['fecha'] <= end_datetime)
        ]
    else:
        df_filtered = df[df['ingeniero'].isin(selected_ingeniero)]


    # --- VISUALIZACIÓN DE DATOS ---
    st.markdown("### Vista de Tareas Programadas")
    
    # Formatear la columna de fecha para mostrarla sin la hora
    df_display = df_filtered.copy()
    df_display['fecha'] = df_display['fecha'].dt.strftime('%d-%m-%Y')
    
    # Mostrar el DataFrame filtrado
    st.dataframe(df_display.sort_values(by="fecha", ascending=False), use_container_width=True)

    # --- AGREGAR NUEVO REGISTRO ---
    st.markdown("---")
    with st.expander("📝 Agregar Nueva Tarea"):
        with st.form("new_task_form", clear_on_submit=True):
            # Obtiene el último ID y suma 1 para el nuevo registro
            next_id = df['id'].max() + 1
            
            # Columnas para el formulario
            col1, col2 = st.columns(2)
            with col1:
                ingeniero = st.selectbox("Ingeniero", options=ingenieros)
                fecha = st.date_input("Fecha de la Tarea")
            with col2:
                tarea = st.text_area("Descripción de la Tarea")
            
            submitted = st.form_submit_button("Guardar Tarea")

            if submitted:
                # Formatea la fecha al formato de la hoja de cálculo (dd-mm-yy)
                formatted_date = fecha.strftime("%d-%m-%y")
                # Crea la nueva fila
                new_row = [next_id, ingeniero, tarea, formatted_date]
                
                # Agrega la fila a la hoja de cálculo
                try:
                    # Conexión dentro del formulario para asegurar que esté fresca
                    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
                    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
                    client = gspread.authorize(creds)
                    sheet_url = "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
                    spreadsheet = client.open_by_url(sheet_url)
                    sheet = spreadsheet.worksheet("Hoja 1")
                    sheet.append_row(new_row)
                    
                    st.success("¡Tarea agregada exitosamente!")
                    # Invalida el caché para que los datos se recarguen
                    st.cache_data.clear()
                    # st.experimental_rerun() # Descomentar si la tabla no se actualiza sola
                except Exception as e:
                    st.error(f"Error al guardar la tarea: {e}")

else:
    st.warning("No se pudieron cargar los datos. Verifica la conexión y la configuración.")
