import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema de Gestión de Mantenciones",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SISTEMA DE DISEÑO (CSS) ---
def load_professional_css():
    css_styles = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        :root {
            --primary-color: #0068C9; --primary-color-light: #E6F0FA;
            --success-color: #28a745; --success-color-light: #EAF6EC;
            --warning-color: #ffc107; --warning-color-light: #FFF8E7;
            --danger-color: #dc3545; --danger-color-light: #FBEBEB;
            --bg-color: #F0F2F6; --content-bg-color: #FFFFFF;
            --text-color: #262626; --subtle-text-color: #595959;
            --border-color: #E0E0E0; --border-radius: 12px;
            --box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            --box-shadow-hover: 0 6px 16px rgba(0, 0, 0, 0.12);
        }
        [data-theme="dark"] {
            --primary-color: #1A8DFF; --primary-color-light: #1F2B3A;
            --success-color: #34D399; --success-color-light: #1F3A31;
            --warning-color: #FBBF24; --warning-color-light: #3A3221;
            --danger-color: #F87171; --danger-color-light: #3A2626;
            --bg-color: #0E1117; --content-bg-color: #161B22;
            --text-color: #E0E0E0; --subtle-text-color: #A0A0A0;
            --border-color: #30363D;
        }
        body { font-family: 'Inter', sans-serif; background-color: var(--bg-color); color: var(--text-color); }
        .main-header { background: linear-gradient(135deg, #4F46E5, #818CF8); color: white; padding: 2.5rem; border-radius: var(--border-radius); margin-bottom: 2rem; text-align: center; }
        .main-header h1 { font-size: 2.5rem; font-weight: 700; margin: 0; }
        .main-header p { font-size: 1.2rem; opacity: 0.9; margin: 0.5rem 0 0 0; }
        .day-header { font-size: 1.1rem; font-weight: 600; padding-bottom: 0.8rem; border-bottom: 2px solid var(--border-color); margin-bottom: 1rem; text-align: center; }
        .day-header .date-num { font-size: 0.9rem; font-weight: 500; color: var(--subtle-text-color); }
        .task-card-calendar { background-color: var(--bg-color); border-left: 5px solid var(--primary-color); border-radius: 8px; padding: 0.8rem; margin-bottom: 0.8rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .task-card-calendar .task-title { font-weight: 600; font-size: 0.95rem; }
        .task-card-calendar .task-details { font-size: 0.8rem; color: var(--subtle-text-color); }
        .task-card-calendar .task-status { font-size: 0.8rem; font-weight: 600; text-align: right; }
        .task-status-Pendiente { color: var(--warning-color); }
        .task-status-Vencida { color: var(--danger-color); }
        button[data-baseweb="tab"] { font-size: 1rem; font-weight: 600; color: var(--subtle-text-color); border-radius: 8px 8px 0 0 !important; }
        button[data-baseweb="tab"][aria-selected="true"] { color: var(--primary-color); background-color: transparent; border-bottom: 3px solid var(--primary-color) !important; }
        .metric-card { background-color: var(--content-bg-color); padding: 1.5rem; border-radius: var(--border-radius); box-shadow: var(--box-shadow); border: 1px solid var(--border-color); text-align: center; }
        .metric-number { font-size: 2.5rem; font-weight: 700; margin: 0; }
        .metric-label { font-size: 0.9rem; color: var(--subtle-text-color); font-weight: 500; }
        .custom-alert { padding: 1rem 1.5rem; border-radius: var(--border-radius); margin-bottom: 1rem; border: 1px solid transparent; font-weight: 500; }
        .alert-info { background-color: var(--primary-color-light); border-color: var(--primary-color); color: var(--primary-color); }
        .alert-warning { background-color: var(--warning-color-light); border-color: var(--warning-color); color: var(--warning-color); }
    </style>
    """
    st.markdown(css_styles, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
@st.cache_data(ttl=300)
def load_data_from_google_sheet():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet_url = "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.worksheet("Hoja 1")
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if 'fecha' in df.columns:
            df['fecha_dt'] = pd.to_datetime(df['fecha'], format='%d-%m-%Y', errors='coerce')
        else:
            st.error("Error: La columna 'fecha' no se encuentra en el Google Sheet.")
            return pd.DataFrame()
        return df
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

# --- 4. FUNCIONES DE ANÁLISIS Y PERSISTENCIA ---
def update_task_status_in_sheets(task_id, status, completion_date=None):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet_url = "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.worksheet("Hoja 1")
        cell = sheet.find(str(task_id)) 
        if cell:
            sheet.update_cell(cell.row, 7, status) 
            if completion_date:
                # Actualiza la columna 8 (H), asumiendo que es la de fecha de completado
                sheet.update_cell(cell.row, 8, completion_date.strftime('%d-%m-%Y'))
            return True
        else:
            st.error(f"No se encontró una tarea con el ID {task_id}.")
            return False
    except Exception as e:
        st.error(f"Error al actualizar Google Sheets: {e}")
        return False

def get_task_status(task):
    today = datetime.now().date()
    task_date = task['fecha_dt'].date() if pd.notna(task['fecha_dt']) else None
    if task.get('estado') == 'Completada':
        return "Completada"
    if task_date and task_date < today:
        return "Vencida"
    return "Pendiente"

def calculate_metrics(df):
    if df.empty:
        return {'total': 0, 'completadas': 0, 'vencidas': 0, 'pendientes': 0}
    total_tasks = len(df)
    today = datetime.now().date()
    completadas = df[df['estado'] == 'Completada'].shape[0]
    not_completed_df = df[df['estado'] != 'Completada'].copy()
    valid_dates_df = not_completed_df.dropna(subset=['fecha_dt'])
    vencidas = valid_dates_df[valid_dates_df['fecha_dt'].dt.date < today].shape[0]
    pendientes = valid_dates_df[valid_dates_df['fecha_dt'].dt.date >= today].shape[0]
    return {'total': total_tasks, 'completadas': completadas, 'vencidas': vencidas, 'pendientes': pendientes}

def create_charts(df):
    if df.empty: return None, None
    tasks_by_engineer = df['ingeniero'].value_counts()
    fig_engineer = px.bar(x=tasks_by_engineer.values, y=tasks_by_engineer.index, orientation='h', title="Tareas por Ingeniero")
    fig_engineer.update_layout(height=350, xaxis_title=None, yaxis_title=None, template="streamlit")
    metrics = calculate_metrics(df)
    status_data = pd.DataFrame({'Estado': ['Completadas', 'Vencidas', 'Pendientes'], 'Cantidad': [metrics['completadas'], metrics['vencidas'], metrics['pendientes']]})
    fig_status = px.pie(status_data, values='Cantidad', names='Estado', title="Distribución de Estados", color='Estado', color_discrete_map={'Completadas': '#28a745', 'Vencidas': '#dc3545', 'Pendientes': '#ffc107'})
    fig_status.update_layout(height=350, legend_title=None, template="streamlit")
    return fig_engineer, fig_status

# --- 5. INTERFAZ PRINCIPAL ---
def main():
    load_professional_css()
    
    st.markdown("""
    <div class="main-header">
        <h1><span style="font-size: 2.8rem;">📅</span> Sistema de Gestión de Mantenciones</h1>
        <p>Monitoreo y control de tareas de mantenimiento - 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    tasks_df = load_data_from_google_sheet()
    
    if tasks_df.empty:
        st.error("No se pudieron cargar los datos. Verifica la conexión con Google Sheets.")
        return
        
    tab1, tab2, tab3 = st.tabs([
        "🗓️ Vista Semanal", "📊 Dashboard", "✅ Registro"
    ])
    
    with tab1:
        st.header("Calendario de Tareas")
        st.write("") 
        
        col1, col2 = st.columns([3, 1])
        with col2:
            st.subheader("Resumen del Mes")
            calendar_events = []
            tasks_with_date = tasks_df.dropna(subset=['fecha_dt'])
            for _, task in tasks_with_date.iterrows():
                status = get_task_status(task)
                color_map = {"Pendiente": "#FBBF24", "Vencida": "#F87171", "Completada": "#34D399"}
                calendar_events.append({
                    "title": task.get('cliente', 'N/A'),
                    "color": color_map.get(status, "#A0A0A0"),
                    "start": task['fecha_dt'].strftime("%Y-%m-%d"),
                    "end": task['fecha_dt'].strftime("%Y-%m-%d"),
                })
            
            calendar(events=calendar_events, options={"headerToolbar": {"left": "prev,next", "center": "title", "right": ""}, "initialView": "dayGridMonth"})
            st.markdown("""
            <small>
            <span style='color:#34D399'>●</span> Completada &nbsp; 
            <span style='color:#FBBF24'>●</span> Pendiente &nbsp; 
            <span style='color:#F87171'>●</span> Vencida
            </small>
            """, unsafe_allow_html=True)

        with col1:
            st.subheader("Tareas de la Semana Actual")
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            week_days = [start_of_week + timedelta(days=i) for i in range(7)]
            
            week_cols = st.columns(7)
            dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

            for i, day in enumerate(week_days):
                with week_cols[i]:
                    st.markdown(f"<div class='day-header'>{dias_semana[i]}<br><span class='date-num'>{day.strftime('%d/%m')}</span></div>", unsafe_allow_html=True)
                    tasks_for_day = tasks_df[tasks_df['fecha_dt'].dt.date == day.date()]
                    if tasks_for_day.empty:
                        st.markdown("<div style='text-align:center; padding-top:50px; color: var(--subtle-text-color); font-size: 0.9rem;'>No hay tareas.</div>", unsafe_allow_html=True)
                    else:
                        for _, task in tasks_for_day.iterrows():
                            status = get_task_status(task)
                            if status == "Completada": continue
                            border_color = {"Pendiente": "var(--warning-color)", "Vencida": "var(--danger-color)"}.get(status, "var(--primary-color)")
                            st.markdown(f"""
                            <div class="task-card-calendar" style="border-left-color: {border_color};">
                                <div class="task-title">{task.get('cliente', 'N/A')}</div>
                                <div class="task-details">👨‍🔧 {task.get('ingeniero', 'N/A')}</div>
                                <div class="task-details">🔧 {task.get('tipo', 'N/A')}</div>
                                <div class="task-status task-status-{status}">{status}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            task_id = task.get('id')
                            if st.button("Completar", key=f"complete_{task_id}", use_container_width=True):
                                success = update_task_status_in_sheets(task_id, "Completada", datetime.now())
                                if success:
                                    st.success(f"Tarea {task_id} marcada.")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Error al actualizar.")
    with tab2:
        st.header("Resumen Ejecutivo")
        st.write("")
        metrics = calculate_metrics(tasks_df)
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="metric-card"><p class="metric-number" style="color: var(--text-color);">{metrics["total"]}</p><p class="metric-label">Total Tareas</p></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><p class="metric-number" style="color: var(--success-color);">{metrics["completadas"]}</p><p class="metric-label">Completadas</p></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><p class="metric-number" style="color: var(--warning-color);">{metrics["pendientes"]}</p><p class="metric-label">Pendientes</p></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card"><p class="metric-number" style="color: var(--danger-color);">{metrics["vencidas"]}</p><p class="metric-label">Vencidas</p></div>', unsafe_allow_html=True)
        st.write(""); st.write("")
        if metrics['vencidas'] > 0:
            st.markdown(f'<div class="custom-alert alert-warning">⚠️ <strong>Atención:</strong> Hay {metrics["vencidas"]} tareas vencidas que requieren acción inmediata.</div>', unsafe_allow_html=True)
        if not tasks_df.empty:
            st.header("Visualizaciones")
            col1, col2 = st.columns(2)
            fig_eng, fig_status = create_charts(tasks_df)
            if fig_status: col1.plotly_chart(fig_status, use_container_width=True)
            if fig_eng: col2.plotly_chart(fig_eng, use_container_width=True)

    # --- TAB 3: REGISTRO (CON LÓGICA CORREGIDA) ---
    with tab3:
        st.header("Registro de Tareas Completadas")
        st.write("")
        completed_tasks_df = tasks_df[tasks_df['estado'] == 'Completada'].copy()
        if completed_tasks_df.empty:
            st.markdown('<div class="custom-alert alert-info">ℹ️ Aún no hay tareas completadas en el registro.</div>', unsafe_allow_html=True)
        else:
            # --- INICIO DE LA CORRECCIÓN ---
            # 1. Verificar si la columna 'fecha_completado' existe
            if 'fecha_completado' in completed_tasks_df.columns:
                completed_tasks_df['fecha_completado_dt'] = pd.to_datetime(completed_tasks_df['fecha_completado'], format='%d-%m-%Y', errors='coerce')
                # Ordenar por fecha de completado (si existe), luego por fecha de tarea
                completed_tasks_df = completed_tasks_df.sort_values(by=['fecha_completado_dt', 'fecha_dt'], ascending=[False, False])
            else:
                # Si no existe, solo ordenar por la fecha de la tarea y crear una columna vacía para no generar error
                completed_tasks_df['fecha_completado_dt'] = pd.NaT # NaT = Not a Time (valor nulo para fechas)
                completed_tasks_df = completed_tasks_df.sort_values(by='fecha_dt', ascending=False)
            # --- FIN DE LA CORRECCIÓN ---

            for _, task in completed_tasks_df.iterrows():
                st.markdown('<div class="task-card-calendar" style="border-left-color: var(--success-color);">', unsafe_allow_html=True)
                col1, col2 = st.columns([4, 1.5])
                with col1:
                    fecha_str = task.get('fecha_dt').strftime('%d/%m/%Y') if pd.notna(task.get('fecha_dt')) else "N/A"
                    st.markdown(f"""
                        <span style="font-weight: 600;">{task.get('cliente', 'N/A')}</span><br>
                        <small style="color: var(--subtle-text-color);">
                            📅 Programada: {fecha_str} &nbsp; • &nbsp; 👨‍🔧 {task.get('ingeniero', 'N/A')}
                        </small>
                    """, unsafe_allow_html=True)
                with col2:
                    # Esta línea ahora maneja de forma segura si la fecha de completado existe o no
                    fecha_comp_str = task.get('fecha_completado_dt').strftime('%d/%m/%Y') if pd.notna(task.get('fecha_completado_dt')) else "N/A"
                    st.markdown(f"<div style='text-align:right;'><span style='color: var(--success-color); font-weight:600;'>✅ Completada</span><br><small style='color: var(--subtle-text-color)'>Finalizada: {fecha_comp_str}</small></div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
