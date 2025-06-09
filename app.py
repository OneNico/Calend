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
        if 'fecha' in df.columns:
            df['fecha_dt'] = pd.to_datetime(df['fecha'], format='%d-%m-%y')
        else:
            st.error("Error crítico: La columna 'fecha' no se encuentra en el Google Sheet.")
            df['fecha_dt'] = pd.to_datetime(datetime.now())

        return df

    except Exception as e:
        st.error(f"Error al cargar los datos desde Google Sheets: {e}")
        return pd.DataFrame()

# --- 3. LÓGICA DE LA APLICACIÓN ---

def get_task_status(task):
    """ Determina el estado de una tarea: Completada, Vencida o Pendiente. """
    today = datetime.now().date()
    task_date = task.get('fecha_dt').date() if pd.notna(task.get('fecha_dt')) else today
    
    if task.get('id') in st.session_state.completed_ids:
        return "Completada"
    if task_date < today:
        return "Vencida"
    return "Pendiente"

def handle_complete_task(task_id):
    """ Agrega una ID de tarea al conjunto de tareas completadas. """
    st.session_state.completed_ids.add(task_id)

# --- 4. RENDERIZADO DE LA INTERFAZ ---

load_css()
tasks_df = load_data_from_google_sheet()

st.markdown('<h1 class="text-3xl md:text-4xl font-bold text-gray-700" style="text-align: center;">Calendario de Mantenciones</h1>', unsafe_allow_html=True)
st.markdown('<p class="text-lg text-gray-500" style="text-align: center;">Año 2025</p>', unsafe_allow_html=True)
st.write("---")

tab_semana_actual, tab_registro = st.tabs(["Semana Actual", "Registro de Tareas"])

with tab_semana_actual:
    st.header("Tareas Programadas y Vencidas")

    if tasks_df.empty:
        st.warning("No se pudieron cargar las tareas o la hoja está vacía.")
    else:
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        tasks_to_show = []
        for _, task_row in tasks_df.iterrows():
            task = task_row.to_dict()
            status = get_task_status(task)
            task_date = task.get('fecha_dt').date() if pd.notna(task.get('fecha_dt')) else today
            if status != "Completada" and (status == "Vencida" or (start_of_week <= task_date <= end_of_week)):
                task['estado'] = status
                tasks_to_show.append(task)
        
        tasks_to_show.sort(key=lambda x: x.get('fecha_dt', datetime.now()))

        cols = st.columns((2, 2, 2, 2, 2, 2))
        headers = ["Fecha", "Cliente", "Responsable", "Tipo", "Estado", "Acción"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("---")

        if not tasks_to_show:
            st.info("No hay tareas pendientes o vencidas para esta semana.")
        else:
            for task in tasks_to_show:
                status_class = task.get('estado', 'pendiente').lower()
                cols = st.columns((2, 2, 2, 2, 2, 2))
                cols[0].write(task.get('fecha_dt').strftime('%d-%m-%Y') if pd.notna(task.get('fecha_dt')) else "Sin fecha")
                
                # ===== LÍNEAS CORREGIDAS =====
                cols[1].write(task.get('cliente', 'N/A'))  # No fallará si 'cliente' no existe
                cols[2].write(task.get('ingeniero', 'N/A'))# No fallará si 'ingeniero' no existe
                cols[3].write(task.get('tipo', 'N/A'))     # No fallará si 'tipo' no existe
                # =============================
                
                cols[4].markdown(f'<span class="status-tag status-{status_class}">{task.get("estado", "Pendiente")}</span>', unsafe_allow_html=True)
                
                task_id = task.get('id', None)
                if task_id:
                    button_pressed = cols[5].button("Completar", key=f"complete_{task_id}")
                    if button_pressed:
                        handle_complete_task(task_id)
                        st.toast(f"Tarea '{task.get('tarea', task_id)}' marcada como completada.", icon="🎉")
                        st.rerun()

with tab_registro:
    st.header("Historial de Tareas Completadas")

    if not st.session_state.completed_ids:
        st.info("Aún no se ha completado ninguna tarea.")
    else:
        completed_tasks_df = tasks_df[tasks_df['id'].isin(st.session_state.completed_ids)].copy()
        completed_tasks_df.sort_values(by='fecha_dt', ascending=False, inplace=True)

        cols = st.columns((2, 2, 2, 2, 2))
        headers = ["Fecha", "Cliente", "Responsable", "Tipo", "Estado"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("---")

        for _, task_row in completed_tasks_df.iterrows():
            task = task_row.to_dict()
            cols = st.columns((2, 2, 2, 2, 2))
            cols[0].write(task.get('fecha_dt').strftime('%d-%m-%Y') if pd.notna(task.get('fecha_dt')) else "Sin fecha")
            
            # ===== LÍNEAS CORREGIDAS =====
            cols[1].write(task.get('cliente', 'N/A'))
            cols[2].write(task.get('ingeniero', 'N/A'))
            cols[3].write(task.get('tipo', 'N/A'))
            # =============================
            
            cols[4].markdown('<span class="status-tag status-completada">Completada</span>', unsafe_allow_html=True)
