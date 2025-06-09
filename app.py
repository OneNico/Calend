import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE PÁGINA E INICIALIZACIÓN ---

st.set_page_config(
    page_title="Calendario de Mantenciones",
    page_icon="📅",
    layout="wide",
)

# Inicializar el estado de la sesión para guardar las IDs de tareas completadas
if "completed_ids" not in st.session_state:
    st.session_state.completed_ids = set()

# --- 2. ESTILOS Y CARGA DE DATOS ---

def load_css():
    """ Inyecta el CSS personalizado para los estilos de la app. """
    st.markdown("""
    <style>
        /* Estilos para las etiquetas de estado */
        .status-tag {
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
            color: white;
            white-space: nowrap;
            display: inline-block;
        }
        .status-pendiente { background-color: #f59e0b; } /* Amber */
        .status-vencida { background-color: #ef4444; } /* Red */
        .status-completada { background-color: #22c55e; } /* Green */
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300) # Cache de 5 minutos
def load_data_from_google_sheet():
    """ Carga y procesa los datos desde la hoja de cálculo de Google. """
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet_url = "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.worksheet("Hoja 1")
        
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Convertir la columna de fecha a formato datetime
        df['fecha_dt'] = pd.to_datetime(df['fecha'], format='%d-%m-%y')
        return df

    except Exception as e:
        st.error(f"Error al cargar los datos desde Google Sheets: {e}")
        return pd.DataFrame()

# --- 3. LÓGICA DE LA APLICACIÓN ---

def get_task_status(task):
    """ Determina el estado de una tarea: Completada, Vencida o Pendiente. """
    today = datetime.now().date()
    task_date = task['fecha_dt'].date()
    
    if task['id'] in st.session_state.completed_ids:
        return "Completada"
    if task_date < today:
        return "Vencida"
    return "Pendiente"

def handle_complete_task(task_id):
    """ Agrega una ID de tarea al conjunto de tareas completadas. """
    st.session_state.completed_ids.add(task_id)

# --- 4. RENDERIZADO DE LA INTERFAZ ---

# Cargar CSS y datos
load_css()
tasks_df = load_data_from_google_sheet()

# Encabezado de la aplicación
st.markdown('<h1 class="text-3xl md:text-4xl font-bold text-gray-700" style="text-align: center;">Calendario de Mantenciones</h1>', unsafe_allow_html=True)
st.markdown('<p class="text-lg text-gray-500" style="text-align: center;">Año 2025</p>', unsafe_allow_html=True)
st.write("---")

# Crear pestañas de navegación
tab_semana_actual, tab_registro = st.tabs(["Semana Actual", "Registro de Tareas"])

# Pestaña 1: Semana Actual
with tab_semana_actual:
    st.header("Tareas Programadas y Vencidas")

    if tasks_df.empty:
        st.warning("No se pudieron cargar las tareas.")
    else:
        # Calcular fechas de la semana actual (Lunes a Domingo)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        # Filtrar tareas: Vencidas o de la semana actual, y que no estén completadas
        tasks_to_show = []
        for _, task in tasks_df.iterrows():
            status = get_task_status(task)
            if status != "Completada" and (status == "Vencida" or (start_of_week <= task['fecha_dt'].date() <= end_of_week)):
                task_with_status = task.to_dict()
                task_with_status['estado'] = status
                tasks_to_show.append(task_with_status)
        
        # Ordenar por fecha
        tasks_to_show.sort(key=lambda x: x['fecha_dt'])

        # Encabezado de la tabla
        cols = st.columns((2, 2, 2, 2, 2, 2))
        headers = ["Fecha", "Cliente", "Responsable", "Tipo", "Estado", "Acción"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("---")

        # Filas de la tabla
        if not tasks_to_show:
            st.info("No hay tareas pendientes o vencidas para esta semana.")
        else:
            for task in tasks_to_show:
                status_class = task['estado'].lower()
                cols = st.columns((2, 2, 2, 2, 2, 2))
                cols[0].write(task['fecha_dt'].strftime('%d-%m-%Y'))
                cols[1].write(task['cliente'])
                cols[2].write(task['ingeniero'])
                cols[3].write(task['tipo'])
                cols[4].markdown(f'<span class="status-tag status-{status_class}">{task["estado"]}</span>', unsafe_allow_html=True)
                
                # Botón de acción en la última columna
                button_pressed = cols[5].button("Completar", key=f"complete_{task['id']}")
                if button_pressed:
                    handle_complete_task(task['id'])
                    st.toast(f"Tarea '{task['tarea']}' marcada como completada.", icon="🎉")
                    st.rerun() # Recargar la página para reflejar el cambio


# Pestaña 2: Registro de Tareas
with tab_registro:
    st.header("Historial de Tareas Completadas")

    if not st.session_state.completed_ids:
        st.info("Aún no se ha completado ninguna tarea.")
    else:
        # Filtrar el DataFrame para obtener solo las tareas completadas
        completed_tasks_df = tasks_df[tasks_df['id'].isin(st.session_state.completed_ids)].copy()
        completed_tasks_df.sort_values(by='fecha_dt', ascending=False, inplace=True)

        # Encabezado de la tabla de registro
        cols = st.columns((2, 2, 2, 2, 2))
        headers = ["Fecha", "Cliente", "Responsable", "Tipo", "Estado"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("---")

        # Filas de la tabla de registro
        for _, task in completed_tasks_df.iterrows():
            cols = st.columns((2, 2, 2, 2, 2))
            cols[0].write(task['fecha_dt'].strftime('%d-%m-%Y'))
            cols[1].write(task['cliente'])
            cols[2].write(task['ingeniero'])
            cols[3].write(task['tipo'])
            cols[4].markdown('<span class="status-tag status-completada">Completada</span>', unsafe_allow_html=True)
