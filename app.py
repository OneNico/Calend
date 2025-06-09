import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import calendar

# --- 1. CONFIGURACIÓN DE PÁGINA ---

st.set_page_config(
    page_title="Sistema de Gestión de Mantenciones",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# NOTA: Se ha eliminado st.session_state.completed_ids para usar Google Sheets como única fuente de verdad.

# --- 2. ESTILOS MEJORADOS (Sin cambios) ---

def load_enhanced_css():
    """Estilos CSS mejorados para una interfaz más moderna"""
    st.markdown("""
    <style>
        /* Importar fuente moderna */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        /* Variables CSS */
        :root {
            --primary-blue: #0066cc;
            --success-green: #00b894;
            --warning-orange: #fdcb6e;
            --danger-red: #e17055;
            --light-gray: #f8f9fa;
            --medium-gray: #6c757d;
            --dark-gray: #343a40;
            --border-radius: 12px;
            --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Estilos generales */
        .main > div {
            font-family: 'Inter', sans-serif;
        }
        
        /* Header principal */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: var(--border-radius);
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: var(--box-shadow);
        }
        
        .main-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
        }
        
        .main-header p {
            font-size: 1.2rem;
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        
        /* Cards estilizados */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            border-left: 4px solid var(--primary-blue);
            margin-bottom: 1rem;
        }
        
        .metric-number {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-blue);
            margin: 0;
        }
        
        .metric-label {
            font-size: 0.9rem;
            color: var(--medium-gray);
            margin: 0;
            font-weight: 500;
        }
        
        /* Etiquetas de estado mejoradas */
        .status-badge {
            padding: 6px 16px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            color: white;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        
        .status-pendiente { 
            background: linear-gradient(45deg, #f39c12, #e67e22);
        }
        .status-vencida { 
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }
        .status-completada { 
            background: linear-gradient(45deg, #27ae60, #229954);
        }
        
        /* Botones mejorados */
        .custom-button {
            background: linear-gradient(45deg, var(--primary-blue), #0052a3);
            color: white;
            padding: 8px 20px;
            border: none;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .custom-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 102, 204, 0.3);
        }
        
        /* Tabla estilizada */
        .task-table {
            background: white;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            overflow: hidden;
            margin-bottom: 2rem;
        }
        
        .table-header {
            background: var(--light-gray);
            padding: 1rem;
            font-weight: 600;
            color: var(--dark-gray);
            border-bottom: 2px solid #dee2e6;
        }
        
        .table-row {
            padding: 1rem;
            border-bottom: 1px solid #eee;
            transition: background-color 0.2s ease;
        }
        
        .table-row:hover {
            background-color: #f8f9fa;
        }
        
        /* Sidebar personalizado */
        .sidebar-content {
            background: white;
            border-radius: var(--border-radius);
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: var(--box-shadow);
        }
        
        /* Alertas personalizadas */
        .custom-alert {
            padding: 1rem 1.5rem;
            border-radius: var(--border-radius);
            margin-bottom: 1rem;
            border-left: 4px solid;
        }
        
        .alert-info {
            background-color: #e3f2fd;
            border-color: var(--primary-blue);
            color: #0d47a1;
        }
        
        .alert-warning {
            background-color: #fff3e0;
            border-color: var(--warning-orange);
            color: #e65100;
        }
        
        .alert-success {
            background-color: #e8f5e8;
            border-color: var(--success-green);
            color: #2e7d32;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---

@st.cache_data(ttl=300)
def load_data_from_google_sheet():
    """Carga y procesa los datos desde Google Sheets"""
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
            df['fecha_dt'] = pd.to_datetime(df['fecha'], format='%d-%m-%y', errors='coerce')
        else:
            st.error("Error: La columna 'fecha' no se encuentra en el Google Sheet.")
            return pd.DataFrame()

        return df

    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

# --- 4. FUNCIONES DE ANÁLISIS Y PERSISTENCIA (MODIFICADAS) ---

# REEMPLAZA LA FUNCIÓN ORIGINAL CON ESTA VERSIÓN MEJORADA
def update_task_status_in_sheets(task_id, status, completion_date=None):
    """
    Actualiza el estado de una tarea directamente en Google Sheets de forma robusta.
    """
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        client = gspread.authorize(creds)
        sheet_url = "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.worksheet("Hoja 1")

        # Usar sheet.find() para localizar la celda con el ID de la tarea. Es más robusto.
        # Se busca en la primera columna (columna 'id').
        cell = sheet.find(str(task_id), in_column=1)

        if cell:
            # Actualizar la columna de estado (G) y fecha (H) en la misma fila encontrada.
            # La columna G es la 7ma, la H es la 8va.
            # IMPORTANTE: El valor se envuelve en una lista de listas: [[valor]]
            sheet.update_cell(cell.row, 7, status)
            if completion_date:
                sheet.update_cell(cell.row, 8, completion_date.strftime('%d-%m-%y'))
            return True
        else:
            # Si no se encuentra el ID, se informa el error.
            st.error(f"No se encontró una tarea con el ID {task_id} en la base de datos.")
            return False

    except Exception as e:
        st.error(f"Error al actualizar Google Sheets: {e}")
        return False

def get_task_status(task):
    """Determina el estado de una tarea basándose únicamente en los datos de la BDD."""
    today = datetime.now().date()
    # La columna 'fecha_dt' ya es un objeto datetime
    task_date = task['fecha_dt'].date() if pd.notna(task['fecha_dt']) else None
    
    # El estado en la BDD es la única fuente de verdad para 'Completada'
    if task.get('estado') == 'Completada':
        return "Completada"
    
    # Si no está completada, se calcula si está Vencida o Pendiente
    if task_date and task_date < today:
        return "Vencida"
    
    return "Pendiente"

def calculate_metrics(df):
    """Calcula métricas del dashboard directamente desde el dataframe."""
    if df.empty:
        return {'total': 0, 'completadas': 0, 'vencidas': 0, 'pendientes': 0}
    
    total_tasks = len(df)
    today = datetime.now().date()
    
    # Contar completadas directamente desde la columna 'estado'
    completadas = df[df['estado'] == 'Completada'].shape[0]
    
    # Filtrar las no completadas para calcular pendientes y vencidas
    not_completed_df = df[df['estado'] != 'Completada'].copy()
    
    # Asegurarse de que la fecha no sea NaT antes de comparar
    valid_dates_df = not_completed_df.dropna(subset=['fecha_dt'])
    
    vencidas = valid_dates_df[valid_dates_df['fecha_dt'].dt.date < today].shape[0]
    pendientes = valid_dates_df[valid_dates_df['fecha_dt'].dt.date >= today].shape[0]
    
    return {
        'total': total_tasks,
        'completadas': completadas,
        'vencidas': vencidas,
        'pendientes': pendientes
    }


def create_charts(df):
    """Crea gráficos para el dashboard"""
    if df.empty:
        return None, None, None
    
    # Gráfico de tareas por ingeniero
    tasks_by_engineer = df['ingeniero'].value_counts()
    fig_engineer = px.bar(
        x=tasks_by_engineer.values,
        y=tasks_by_engineer.index,
        orientation='h',
        title="Tareas por Ingeniero",
        color=tasks_by_engineer.values,
        color_continuous_scale="Blues"
    )
    fig_engineer.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Número de Tareas",
        yaxis_title="Ingeniero"
    )
    
    # Gráfico de tendencia mensual
    df_copy = df.copy()
    df_copy['mes'] = df_copy['fecha_dt'].dt.strftime('%Y-%m')
    monthly_tasks = df_copy.groupby('mes').size().reset_index(name='cantidad')
    
    fig_trend = px.line(
        monthly_tasks,
        x='mes',
        y='cantidad',
        title="Tendencia de Tareas por Mes",
        markers=True
    )
    fig_trend.update_layout(height=400)
    
    # Gráfico circular de estados (ahora usa las métricas correctas)
    metrics = calculate_metrics(df)
    status_data = pd.DataFrame({
        'Estado': ['Completadas', 'Vencidas', 'Pendientes'],
        'Cantidad': [metrics['completadas'], metrics['vencidas'], metrics['pendientes']],
        'Color': ['#27ae60', '#e74c3c', '#f39c12']
    })
    
    fig_status = px.pie(
        status_data,
        values='Cantidad',
        names='Estado',
        title="Distribución de Estados",
        color='Estado',
        color_discrete_map={
            'Completadas': '#27ae60',
            'Vencidas': '#e74c3c',
            'Pendientes': '#f39c12'
        }
    )
    fig_status.update_layout(height=400)
    
    return fig_engineer, fig_trend, fig_status

# --- 5. INTERFAZ PRINCIPAL (MODIFICADA) ---

def main():
    load_enhanced_css()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🔧 Sistema de Gestión de Mantenciones</h1>
        <p>Monitoreo y control de tareas de mantenimiento - 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Cargar datos
    tasks_df = load_data_from_google_sheet()
    
    if tasks_df.empty:
        st.error("No se pudieron cargar los datos. Verifica la conexión con Google Sheets.")
        return
    
    # Sidebar con filtros
    with st.sidebar:
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
        st.markdown("### 🎛️ Filtros y Configuración")
        
        # Filtro por ingeniero
        engineers = ['Todos'] + list(tasks_df['ingeniero'].unique())
        selected_engineer = st.selectbox("👨‍🔧 Filtrar por Ingeniero:", engineers)
        
        # Filtro por cliente
        clients = ['Todos'] + list(tasks_df['cliente'].unique())
        selected_client = st.selectbox("🏢 Filtrar por Cliente:", clients)
        
        # Filtro por tipo
        types = ['Todos'] + list(tasks_df['tipo'].unique())
        selected_type = st.selectbox("🔧 Filtrar por Tipo:", types)
        
        # Rango de fechas
        st.markdown("### 📅 Rango de Fechas")
        min_date = tasks_df['fecha_dt'].min().date()
        max_date = tasks_df['fecha_dt'].max().date()
        date_from = st.date_input("Desde:", min_date)
        date_to = st.date_input("Hasta:", max_date)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Aplicar filtros
    filtered_df = tasks_df.copy()
    
    if selected_engineer != 'Todos':
        filtered_df = filtered_df[filtered_df['ingeniero'] == selected_engineer]
    if selected_client != 'Todos':
        filtered_df = filtered_df[filtered_df['cliente'] == selected_client]
    if selected_type != 'Todos':
        filtered_df = filtered_df[filtered_df['tipo'] == selected_type]
    
    # Filtrar por fecha solo si la columna fecha_dt no tiene nulos
    if filtered_df['fecha_dt'].notna().all():
        filtered_df = filtered_df[
            (filtered_df['fecha_dt'].dt.date >= date_from) & 
            (filtered_df['fecha_dt'].dt.date <= date_to)
        ]
    
    # Tabs principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard", 
        "📋 Tareas Actuales", 
        "✅ Completadas", 
        "📈 Análisis", 
        "📅 Calendario"
    ])
    
    # TAB 1: DASHBOARD
    with tab1:
        st.markdown("### 📊 Resumen Ejecutivo")
        
        metrics = calculate_metrics(filtered_df)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-number">{metrics['total']}</p>
                <p class="metric-label">Total de Tareas</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-number" style="color: var(--success-green);">{metrics['completadas']}</p>
                <p class="metric-label">Completadas</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-number" style="color: var(--warning-orange);">{metrics['pendientes']}</p>
                <p class="metric-label">Pendientes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-number" style="color: var(--danger-red);">{metrics['vencidas']}</p>
                <p class="metric-label">Vencidas</p>
            </div>
            """, unsafe_allow_html=True)
        
        if metrics['vencidas'] > 0:
            st.markdown(f"""
            <div class="custom-alert alert-warning">
                ⚠️ <strong>Atención:</strong> Hay {metrics['vencidas']} tareas vencidas que requieren atención inmediata.
            </div>
            """, unsafe_allow_html=True)
        
        if not filtered_df.empty:
            col1, col2 = st.columns(2)
            fig_eng, _, fig_status = create_charts(filtered_df)
            with col1:
                if fig_status:
                    st.plotly_chart(fig_status, use_container_width=True, key="dashboard_status")
            with col2:
                if fig_eng:
                    st.plotly_chart(fig_eng, use_container_width=True, key="dashboard_engineer")

    # TAB 2: TAREAS ACTUALES (Lógica de botón modificada)
    with tab2:
        st.markdown("### 📋 Tareas Pendientes y Vencidas")
        
        tasks_to_show = []
        for _, task_row in filtered_df.iterrows():
            task = task_row.to_dict()
            status = get_task_status(task)
            
            if status != "Completada":
                task['status_calculado'] = status
                tasks_to_show.append(task)
        
        tasks_to_show.sort(key=lambda x: x.get('fecha_dt', datetime.now()))
        
        if not tasks_to_show:
            st.markdown("""
            <div class="custom-alert alert-info">
                ℹ️ No hay tareas pendientes o vencidas para mostrar con los filtros seleccionados.
            </div>
            """, unsafe_allow_html=True)
        else:
            for i, task in enumerate(tasks_to_show):
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 2, 2, 1.5, 1.5, 1])
                    
                    fecha_str = task.get('fecha_dt').strftime('%d/%m/%Y') if pd.notna(task.get('fecha_dt')) else "Sin fecha"
                    
                    col1.write(f"📅 **{fecha_str}**")
                    col2.write(f"🏢 {task.get('cliente', 'N/A')}")
                    col3.write(f"👨‍🔧 {task.get('ingeniero', 'N/A')}")
                    col4.write(f"🔧 {task.get('tipo', 'N/A')}")
                    
                    status = task.get('status_calculado', 'Pendiente')
                    status_class = status.lower()
                    icon = "⏰" if status == "Pendiente" else "🚨"
                    
                    col5.markdown(f"""
                    <span class="status-badge status-{status_class}">
                        {icon} {status}
                    </span>
                    """, unsafe_allow_html=True)
                    
                    task_id = task.get('id', None)
                    if task_id:
                        if col6.button("✅ Completar", key=f"complete_{task_id}", type="primary"):
                            with st.spinner("Guardando en base de datos..."):
                                success = update_task_status_in_sheets(
                                    task_id, 
                                    "Completada", 
                                    datetime.now().date()
                                )
                            
                            if success:
                                st.success(f"✅ Tarea ID {task_id} guardada en la base de datos.")
                                # Limpiar cache y refrescar la app para ver el cambio
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("⚠️ No se pudo guardar el cambio en la base de datos.")
                                
                    if i < len(tasks_to_show) - 1:
                        st.divider()

    # TAB 3: COMPLETADAS (Lógica modificada)
    with tab3:
        st.markdown("### ✅ Historial de Tareas Completadas")
        
        # Filtrar tareas que tienen el estado "Completada" en la BDD
        completed_tasks_df = filtered_df[filtered_df['estado'] == 'Completada'].copy()
        
        if completed_tasks_df.empty:
            st.markdown("""
            <div class="custom-alert alert-info">
                ℹ️ No hay tareas completadas para mostrar según los filtros seleccionados.
            </div>
            """, unsafe_allow_html=True)
        else:
            completed_tasks_df = completed_tasks_df.sort_values(by='fecha_dt', ascending=False)
            
            for _, task_row in completed_tasks_df.iterrows():
                task = task_row.to_dict()
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([1.5, 2, 2, 1.5, 1.5])
                    
                    fecha_str = task.get('fecha_dt').strftime('%d/%m/%Y') if pd.notna(task.get('fecha_dt')) else "Sin fecha"
                    
                    col1.write(f"📅 **{fecha_str}**")
                    col2.write(f"🏢 {task.get('cliente', 'N/A')}")
                    col3.write(f"👨‍🔧 {task.get('ingeniero', 'N/A')}")
                    col4.write(f"🔧 {task.get('tipo', 'N/A')}")
                    col5.markdown('<span class="status-badge status-completada">✅ Completada</span>', unsafe_allow_html=True)
                    
                    st.divider()

    # TAB 4: ANÁLISIS
    with tab4:
        st.markdown("### 📈 Análisis y Reportes")
        
        if not filtered_df.empty:
            fig_eng, fig_trend, fig_status = create_charts(filtered_df)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if fig_eng:
                    st.plotly_chart(fig_eng, use_container_width=True, key="analysis_engineer")
                if fig_status:
                    st.plotly_chart(fig_status, use_container_width=True, key="analysis_status")
            
            with col2:
                if fig_trend:
                    st.plotly_chart(fig_trend, use_container_width=True, key="analysis_trend")
                
                st.markdown("#### 👨‍🔧 Resumen por Ingeniero")
                engineer_summary = filtered_df.groupby('ingeniero').agg(
                    Total_Tareas=('id', 'count'),
                    Clientes_Unicos=('cliente', 'nunique')
                ).reset_index()
                st.dataframe(engineer_summary, use_container_width=True)

    # TAB 5: CALENDARIO
    with tab5:
        st.markdown("### 📅 Vista de Calendario")
        
        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox("Año:", sorted(filtered_df['fecha_dt'].dt.year.unique()), index=0)
        with col2:
            selected_month = st.selectbox("Mes:", range(1, 13), 
                                          index=datetime.now().month-1,
                                          format_func=lambda x: calendar.month_name[x])
        
        month_tasks = filtered_df[
            (filtered_df['fecha_dt'].dt.year == selected_year) & 
            (filtered_df['fecha_dt'].dt.month == selected_month)
        ]
        
        if not month_tasks.empty:
            cal = calendar.monthcalendar(selected_year, selected_month)
            st.markdown(f"#### {calendar.month_name[selected_month]} {selected_year}")
            
            daily_tasks = month_tasks.groupby(month_tasks['fecha_dt'].dt.day).size()
            
            days_of_week = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            cols = st.columns(7)
            for i, day in enumerate(days_of_week):
                cols[i].markdown(f"**{day}**")
            
            for week in cal:
                cols = st.columns(7)
                for i, day in enumerate(week):
                    if day == 0:
                        cols[i].write("")
                    else:
                        task_count = daily_tasks.get(day, 0)
                        if task_count > 0:
                            cols[i].markdown(f"""
                            <div style="background-color: #e3f2fd; padding: 8px; border-radius: 8px; text-align: center;">
                                <strong>{day}</strong><br>
                                <small>📋 {task_count}</small>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            cols[i].markdown(f"""
                            <div style="padding: 8px; text-align: center;">
                                {day}
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.info(f"No hay tareas programadas para {calendar.month_name[selected_month]} {selected_year} con los filtros actuales.")

if __name__ == "__main__":
    main()
