import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import smtplib
from email.message import EmailMessage

# --- CONFIGURACIÓN DE PÁGINA E INICIALIZACIÓN ---

st.set_page_config(
    page_title="Calendario de Revisiones",
    page_icon="📅",
    layout="wide",
)

# Inicializar el estado de la sesión para el historial y acciones
if "history" not in st.session_state:
    # El historial almacenará los registros de tareas completadas
    st.session_state.history = []
if "action_task" not in st.session_state:
    # Guardará la tarea que se está marcando como completa
    st.session_state.action_task = None

# --- CARGA DE ESTILOS CSS ---

def load_css():
    """Carga el CSS personalizado desde el archivo style.css."""
    st.markdown("""
    <style>
        /* Estilos para las tarjetas de tarea */
        .task-card {
            border-radius: 0.5rem;
            padding: 1rem;
            border-width: 1px;
            border-left-width: 4px;
            transition: all 0.3s ease;
        }
        .task-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        .completed {
            background-color: #f0fdf4; /* verde claro */
            border-left-color: #10b981;
        }
        .pending {
            background-color: #fffbeb; /* amarillo claro */
            border-left-color: #f59e0b;
        }
        /* Ajustes de botones y texto */
        .stButton > button {
            width: 100%;
        }
        .task-details p {
            margin-bottom: 0.25rem;
            color: #4b5563; /* text-gray-600 */
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- CONEXIÓN A GOOGLE SHEETS Y CARGA DE DATOS ---

@st.cache_data(ttl=300) # Cache de 5 minutos
def load_google_sheet_data():
    """Carga los datos desde Google Sheets y los procesa."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet_url = "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.worksheet("Hoja 1") # Asegúrate que el nombre de la hoja sea correcto
        
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # IMPORTANTE: Asegúrate que tu Google Sheet tenga estas columnas:
        # id, ingeniero, tarea, fecha, tipo (diaria, semanal, mensual, cada3meses)
        df['fecha_dt'] = pd.to_datetime(df['fecha'], format='%d-%m-%y')
        return df.sort_values(by="fecha_dt")

    except Exception as e:
        st.error(f"Error al cargar los datos desde Google Sheets: {e}")
        return pd.DataFrame()

tasks_df = load_google_sheet_data()

# --- LÓGICA DE TAREAS Y NOTIFICACIONES ---

def is_task_completed(task_id):
    """Verifica si una tarea está en el historial de completados."""
    return any(record['taskId'] == task_id for record in st.session_state.history)

def get_completion_info(task_id):
    """Obtiene la información de completado de una tarea."""
    record = next((r for r in st.session_state.history if r['taskId'] == task_id), None)
    if record:
        return {
            "time": datetime.fromisoformat(record['date']).strftime("%H:%M"),
            "comment": record.get('comment', '')
        }
    return None

def send_email_notification(record):
    """Envía un correo de notificación al completar una tarea."""
    try:
        user = st.secrets["email_credentials"]["user"]
        password = st.secrets["email_credentials"]["password"]

        msg = EmailMessage()
        msg['Subject'] = f"Tarea Completada: {record['taskName']}"
        msg['From'] = user
        msg['To'] = "nicolas.ruiz@interwins.cl" # Destinatario
        
        # Cuerpo del correo
        fecha_registro = datetime.fromisoformat(record['date']).strftime("%d-%m-%Y a las %H:%M")
        msg.set_content(f"""
        Se ha completado la siguiente tarea:

        - Tarea: {record['taskName']}
        - Responsable: {record['responsible']}
        - Fecha/Hora de Registro: {fecha_registro}
        - Observación: {record.get('comment', 'Sin observación.')}
        """)

        # Usar el servidor SMTP de Outlook
        with smtplib.SMTP('smtp.office365.com', 587) as s:
            s.starttls()
            s.login(user, password)
            s.send_message(msg)
        
        st.toast("Correo de notificación enviado.", icon="📧")

    except Exception as e:
        st.error(f"No se pudo enviar el correo de notificación. Error: {e}")

def mark_task_as_completed(task, observation=""):
    """Agrega una tarea al historial y envía notificación."""
    record = {
        "taskId": task['id'],
        "taskName": f"{task['tarea']} del {task['fecha']}",
        "responsible": task['ingeniero'],
        "date": datetime.now().isoformat(),
        "status": "Completado",
        "type": task['tipo'],
        "comment": observation
    }
    st.session_state.history.append(record)
    send_email_notification(record)
    st.session_state.action_task = None # Limpiar la acción

def unmark_task(task_id):
    """Elimina una tarea del historial."""
    st.session_state.history = [r for r in st.session_state.history if r['taskId'] != task_id]


# --- INTERFAZ DE USUARIO (UI) ---

# Encabezado
st.markdown(
    """
    <h1 style="display: flex; align-items: center; font-size: 2rem;">
        <i class="fas fa-calendar-alt" style="color: #10b981; margin-right: 0.75rem;"></i>
        Calendario de Revisiones
    </h1>
    """,
    unsafe_allow_html=True
)
st.write("Aldo Ramos y Hernan Inostroza – Ingenieros de Soporte Interwins")
st.write(f"**Hoy es:** {datetime.now().strftime('%A, %d de %B de %Y')}")

# Pestañas principales
tab_calendario, tab_registro = st.tabs(["🗓️ Calendario", "📊 Registro y Estadísticas"])

# Pestaña Calendario
with tab_calendario:
    # Sub-pestañas de frecuencia
    sub_tabs_types = ['diaria', 'semanal', 'mensual', 'cada3meses']
    sub_tabs = st.tabs([s.capitalize() for s in sub_tabs_types])

    for i, tab in enumerate(sub_tabs):
        with tab:
            task_type = sub_tabs_types[i]
            
            # Filtrar tareas por tipo
            type_tasks_df = tasks_df[tasks_df['tipo'] == task_type]

            # Filtros de la pestaña
            col1, col2 = st.columns(2)
            with col1:
                engineer_filter = st.selectbox(
                    "Filtrar por Ingeniero:",
                    options=["Todos"] + sorted(list(type_tasks_df['ingeniero'].unique())),
                    key=f"eng_{task_type}"
                )
            with col2:
                status_filter = st.selectbox(
                    "Filtrar por Estado:",
                    options=["Todos", "Pendiente", "Completado"],
                    key=f"status_{task_type}"
                )
            
            # Aplicar filtros
            filtered_df = type_tasks_df.copy()
            if engineer_filter != "Todos":
                filtered_df = filtered_df[filtered_df['ingeniero'] == engineer_filter]
            
            if status_filter != "Todos":
                filtered_df['completed'] = filtered_df['id'].apply(is_task_completed)
                if status_filter == "Pendiente":
                    filtered_df = filtered_df[~filtered_df['completed']]
                else: # Completado
                    filtered_df = filtered_df[filtered_df['completed']]
            
            if filtered_df.empty:
                st.info("No hay tareas que coincidan con los filtros seleccionados.")
            else:
                # Contenedor de tareas
                cols = st.columns(3) # 3 tarjetas por fila
                for index, task in enumerate(filtered_df.to_dict('records')):
                    col = cols[index % 3]
                    with col:
                        completed = is_task_completed(task['id'])
                        status_class = "completed" if completed else "pending"

                        st.markdown(f'<div class="task-card {status_class}">', unsafe_allow_html=True)
                        
                        st.markdown(f"**{task['tarea']}**")
                        st.markdown(f"""
                        <div class="task-details">
                            <p><i class="fas fa-user-circle"></i> {task['ingeniero']}</p>
                            <p><i class="far fa-calendar-alt"></i> {task['fecha']} | {task['tipo'].capitalize()}</p>
                        </div>
                        """, unsafe_allow_html=True)

                        if completed:
                            info = get_completion_info(task['id'])
                            st.success(f"Completado a las {info['time']}", icon="✅")
                            if info['comment']:
                                st.caption(f"Obs: {info['comment']}")
                            
                            if st.button("Anular Tarea", key=f"unmark_{task['id']}", type="secondary"):
                                unmark_task(task['id'])
                                st.rerun()
                        else:
                            if st.button("Marcar como Completada", key=f"mark_{task['id']}", type="primary"):
                                st.session_state.action_task = task
                                st.rerun()

                        st.markdown('</div>', unsafe_allow_html=True)
                        st.write("") # Espacio vertical

# Formulario para completar tarea (modal simulado)
if st.session_state.action_task:
    task_to_complete = st.session_state.action_task
    with st.form(key="completion_form"):
        st.info(f"Completando tarea: **{task_to_complete['tarea']}**")
        observation = st.text_area("Puedes agregar una observación (opcional):")
        
        submitted = st.form_submit_button("Confirmar Revisión")
        if submitted:
            mark_task_as_completed(task_to_complete, observation)
            st.success("Tarea registrada y notificación enviada.")
            st.rerun()

# Pestaña Registro y Estadísticas
with tab_registro:
    if not st.session_state.history:
        st.info("Aún no hay tareas completadas para mostrar en el registro.")
    else:
        # Filtro
        all_engineers = sorted(list(tasks_df['ingeniero'].unique()))
        user_filter_reg = st.selectbox("Filtrar por usuario:", ["Todos"] + all_engineers)

        # Aplicar filtro al historial
        display_history = st.session_state.history
        if user_filter_reg != "Todos":
            display_history = [r for r in display_history if r['responsible'] == user_filter_reg]
        
        # Ordenar de más reciente a más antiguo
        display_history.sort(key=lambda r: r['date'], reverse=True)

        # Métricas
        st.subheader("Métricas")
        total_asignado = len(tasks_df) if user_filter_reg == "Todos" else len(tasks_df[tasks_df['ingeniero'] == user_filter_reg])
        total_completado = len(display_history)
        porcentaje = (total_completado / total_asignado * 100) if total_asignado > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tareas Asignadas", total_asignado)
        col2.metric("Total Tareas Completadas", total_completado)
        col3.metric("Porcentaje Realizado", f"{porcentaje:.1f}%")

        # Tabla de historial
        st.subheader("Historial de Tareas Completadas")
        history_df = pd.DataFrame(display_history)
        history_df_display = history_df[['taskName', 'responsible', 'date', 'status', 'comment']].copy()
        history_df_display['date'] = pd.to_datetime(history_df_display['date']).dt.strftime('%d-%m-%Y %H:%M')
        
        st.dataframe(history_df_display, use_container_width=True)
