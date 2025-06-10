import streamlit as st

import gspread

import pandas as pd

import plotly.express as px

from google.oauth2.service_account import Credentials

from datetime import datetime



# --- 1. CONFIGURACIÓN DE PÁGINA ---

st.set_page_config(

    page_title="Sistema de Gestión de Mantenciones",

    page_icon="🔧",

    layout="wide",

    initial_sidebar_state="collapsed"

)



# --- 2. NUEVO SISTEMA DE DISEÑO (CSS MEJORADO) ---



def load_professional_css():

    """

    Carga un CSS profesional y adaptable a temas claro/oscuro.

    """

    st.markdown("""

    <style>

        /* --- Importar Fuente --- */

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');



        /* --- Variables de Color (Tema Claro por defecto) --- */

        :root {

            --primary-color: #0068C9;

            --primary-color-light: #E6F0FA;

            --success-color: #28a745;

            --success-color-light: #EAF6EC;

            --warning-color: #ffc107;

            --warning-color-light: #FFF8E7;

            --danger-color: #dc3545;

            --danger-color-light: #FBEBEB;

            

            --bg-color: #F0F2F6;

            --content-bg-color: #FFFFFF;

            --text-color: #262626;

            --subtle-text-color: #595959;

            --border-color: #E0E0E0;

            --border-radius: 12px;

            --box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);

            --box-shadow-hover: 0 6px 16px rgba(0, 0, 0, 0.12);

        }



        /* --- Variables de Color (Tema Oscuro) --- */

        [data-theme="dark"] {

            --primary-color: #1A8DFF;

            --primary-color-light: #1F2B3A;

            --success-color: #34D399;

            --success-color-light: #1F3A31;

            --warning-color: #FBBF24;

            --warning-color-light: #3A3221;

            --danger-color: #F87171;

            --danger-color-light: #3A2626;



            --bg-color: #0E1117;

            --content-bg-color: #161B22;

            --text-color: #E0E0E0;

            --subtle-text-color: #A0A0A0;

            --border-color: #30363D;

        }



        /* --- Estilos Generales --- */

        body {

            font-family: 'Inter', sans-serif;

            background-color: var(--bg-color);

            color: var(--text-color);

        }



        /* --- Header Principal --- */

        .main-header {

            background: var(--content-bg-color);

            border: 1px solid var(--border-color);

            color: var(--text-color);

            padding: 2rem;

            border-radius: var(--border-radius);

            margin-bottom: 2rem;

            text-align: center;

            box-shadow: var(--box-shadow);

        }

        .main-header h1 {

            font-size: 2.2rem;

            font-weight: 700;

            margin: 0;

        }

        .main-header p {

            font-size: 1.1rem;

            color: var(--subtle-text-color);

            margin: 0.5rem 0 0 0;

        }



        /* --- Estilo de Pestañas (Tabs) --- */

        button[data-baseweb="tab"] {

            font-size: 1rem;

            font-weight: 600;

            color: var(--subtle-text-color);

            border-radius: 8px 8px 0 0 !important;

        }

        button[data-baseweb="tab"][aria-selected="true"] {

            color: var(--primary-color);

            background-color: transparent;

            border-bottom: 3px solid var(--primary-color) !important;

        }



        /* --- Tarjetas de Tareas --- */

        .task-card {

            background-color: var(--content-bg-color);

            border: 1px solid var(--border-color);

            border-radius: var(--border-radius);

            padding: 1rem 1.5rem;

            margin-bottom: 1rem;

            transition: all 0.2s ease-in-out;

            box-shadow: var(--box-shadow);

        }

        .task-card:hover {

            border-color: var(--primary-color);

            transform: translateY(-2px);

            box-shadow: var(--box-shadow-hover);

        }

        

        /* --- Tarjetas de Métricas --- */

        .metric-card {

            background-color: var(--content-bg-color);

            padding: 1.5rem;

            border-radius: var(--border-radius);

            box-shadow: var(--box-shadow);

            border: 1px solid var(--border-color);

            text-align: center;

        }

        .metric-number {

            font-size: 2.5rem;

            font-weight: 700;

            margin: 0;

        }

        .metric-label {

            font-size: 0.9rem;

            color: var(--subtle-text-color);

            font-weight: 500;

        }



        /* --- Etiquetas de Estado --- */

        .status-badge {

            padding: 5px 12px;

            border-radius: 50px;

            font-size: 0.8rem;

            font-weight: 600;

            display: inline-flex;

            align-items: center;

            gap: 6px;

        }

        .status-completada {

            background-color: var(--success-color-light);

            color: var(--success-color);

        }

        .status-vencida {

            background-color: var(--danger-color-light);

            color: var(--danger-color);

        }

        .status-pendiente {

            background-color: var(--warning-color-light);

            color: var(--warning-color);

        }



        /* --- Alertas personalizadas --- */

        .custom-alert {

            padding: 1rem 1.5rem;

            border-radius: var(--border-radius);

            margin-bottom: 1rem;

            border: 1px solid transparent;

            font-weight: 500;

        }

        .alert-info {

            background-color: var(--primary-color-light);

            border-color: var(--primary-color);

            color: var(--primary-color);

        }

        .alert-warning {

            background-color: var(--warning-color-light);

            border-color: var(--warning-color);

            color: var(--warning-color);

        }

    </style>

    """, unsafe_allow_html=True)



# --- 3. CARGA DE DATOS (Sin cambios) ---



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

            df['fecha_dt'] = pd.to_datetime(df['fecha'], format='%d-%m-%y', errors='coerce')

        else:

            st.error("Error: La columna 'fecha' no se encuentra en el Google Sheet.")

            return pd.DataFrame()

        return df

    except Exception as e:

        st.error(f"Error al cargar los datos: {e}")

        return pd.DataFrame()



# --- 4. FUNCIONES DE ANÁLISIS Y PERSISTENCIA (Sin cambios) ---



def update_task_status_in_sheets(task_id, status, completion_date=None):

    try:

        scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)

        client = gspread.authorize(creds)

        sheet_url = "https://docs.google.com/spreadsheets/d/1UGNaLGrqJ3KMCCEXnxzPfDhcLooDTIhAj-UFUI0UNRo"

        spreadsheet = client.open_by_url(sheet_url)

        sheet = spreadsheet.worksheet("Hoja 1")

        cell = sheet.find(str(task_id), in_column=1)

        if cell:

            sheet.update_cell(cell.row, 7, status)

            if completion_date:

                sheet.update_cell(cell.row, 8, completion_date.strftime('%d-%m-%y'))

            return True

        else:

            st.error(f"No se encontró una tarea con el ID {task_id} en la base de datos.")

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

    if df.empty:

        return None, None

    

    # Gráfico de tareas por ingeniero

    tasks_by_engineer = df['ingeniero'].value_counts()

    fig_engineer = px.bar(

        x=tasks_by_engineer.values, y=tasks_by_engineer.index,

        orientation='h', title="Tareas por Ingeniero"

    )

    fig_engineer.update_layout(height=350, xaxis_title=None, yaxis_title=None)

    

    # Gráfico circular de estados

    metrics = calculate_metrics(df)

    status_data = pd.DataFrame({

        'Estado': ['Completadas', 'Vencidas', 'Pendientes'],

        'Cantidad': [metrics['completadas'], metrics['vencidas'], metrics['pendientes']],

    })

    fig_status = px.pie(

        status_data, values='Cantidad', names='Estado',

        title="Distribución de Estados",

        color='Estado',

        color_discrete_map={

            'Completadas': '#28a745', 'Vencidas': '#dc3545', 'Pendientes': '#ffc107'

        }

    )

    fig_status.update_layout(height=350, legend_title=None)

    

    # Adaptar gráficos al tema de Streamlit

    fig_engineer.update_layout(template="streamlit")

    fig_status.update_layout(template="streamlit")

    

    return fig_engineer, fig_status



# --- 5. INTERFAZ PRINCIPAL (MODIFICADA CON NUEVO DISEÑO) ---



def main():

    load_professional_css()

    

    st.markdown("""

    <div class="main-header">

        <h1><span style="font-size: 2.5rem;">🔧</span> Sistema de Gestión de Mantenciones</h1>

        <p>Monitoreo y control de tareas de mantenimiento - 2025</p>

    </div>

    """, unsafe_allow_html=True)

    

    tasks_df = load_data_from_google_sheet()

    

    if tasks_df.empty:

        st.error("No se pudieron cargar los datos. Verifica la conexión con Google Sheets.")

        return

    

    filtered_df = tasks_df.copy()

    

    tab1, tab2, tab3 = st.tabs([

        "📋 Tareas Actuales", "📊 Dashboard", "✅ Registro"

    ])

    

    # TAB 1: TAREAS ACTUALES

    with tab1:

        st.header("Tareas Pendientes y Vencidas")

        st.write("") # Espacio

        

        tasks_to_show = [row.to_dict() for _, row in filtered_df.iterrows() if get_task_status(row.to_dict()) != "Completada"]

        tasks_to_show.sort(key=lambda x: x.get('fecha_dt', datetime.now()))

        

        if not tasks_to_show:

            st.markdown('<div class="custom-alert alert-info">ℹ️ ¡Excelente! No hay tareas pendientes o vencidas.</div>', unsafe_allow_html=True)

        else:

            for task in tasks_to_show:

                st.markdown('<div class="task-card">', unsafe_allow_html=True)

                col1, col2, col3 = st.columns([4, 2, 1.5])

                

                with col1:

                    fecha_str = task.get('fecha_dt').strftime('%d/%m/%Y') if pd.notna(task.get('fecha_dt')) else "N/A"

                    st.markdown(f"""

                        <span style="font-weight: 600; font-size: 1.1rem;">{task.get('cliente', 'N/A')}</span><br>

                        <small style="color: var(--subtle-text-color);">

                            📅 {fecha_str} &nbsp; • &nbsp; 👨‍🔧 {task.get('ingeniero', 'N/A')} &nbsp; • &nbsp; 🔧 {task.get('tipo', 'N/A')}

                        </small>

                    """, unsafe_allow_html=True)

                

                status = get_task_status(task)

                status_class = status.lower()

                icon = {"Pendiente": "⏰", "Vencida": "🚨"}.get(status, "")

                with col2:

                    st.markdown(f'<div style="text-align: right; padding-top: 10px;"><span class="status-badge status-{status_class}">{icon} {status}</span></div>', unsafe_allow_html=True)

                

                task_id = task.get('id', None)

                if task_id:

                    with col3:

                         # Botón centrado verticalmente

                        st.write("") # Placeholder

                        if st.button("Marcar Completada", key=f"complete_{task_id}", type="primary", use_container_width=True):

                            with st.spinner("Actualizando..."):

                                success = update_task_status_in_sheets(task_id, "Completada", datetime.now().date())

                            if success:

                                st.success(f"Tarea ID {task_id} completada.")

                                st.cache_data.clear()

                                st.rerun()

                            else:

                                st.error("No se pudo actualizar.")

                

                st.markdown('</div>', unsafe_allow_html=True)



    # TAB 2: DASHBOARD

    with tab2:

        st.header("Resumen Ejecutivo")

        st.write("") # Espacio

        

        metrics = calculate_metrics(filtered_df)

        

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.markdown(f"""

            <div class="metric-card">

                <p class="metric-number" style="color: var(--text-color);">{metrics['total']}</p>

                <p class="metric-label">Total Tareas</p>

            </div>""", unsafe_allow_html=True)

        with col2:

            st.markdown(f"""

            <div class="metric-card">

                <p class="metric-number" style="color: var(--success-color);">{metrics['completadas']}</p>

                <p class="metric-label">Completadas</p>

            </div>""", unsafe_allow_html=True)

        with col3:

            st.markdown(f"""

            <div class="metric-card">

                <p class="metric-number" style="color: var(--warning-color);">{metrics['pendientes']}</p>

                <p class="metric-label">Pendientes</p>

            </div>""", unsafe_allow_html=True)

        with col4:

            st.markdown(f"""

            <div class="metric-card">

                <p class="metric-number" style="color: var(--danger-color);">{metrics['vencidas']}</p>

                <p class="metric-label">Vencidas</p>

            </div>""", unsafe_allow_html=True)

            

        st.write(""); st.write("") # Espacio



        if metrics['vencidas'] > 0:

            st.markdown(f'<div class="custom-alert alert-warning">⚠️ <strong>Atención:</strong> Hay {metrics["vencidas"]} tareas vencidas que requieren acción inmediata.</div>', unsafe_allow_html=True)

        

        if not filtered_df.empty:

            st.header("Visualizaciones")

            col1, col2 = st.columns(2)

            fig_eng, fig_status = create_charts(filtered_df)

            with col1:

                if fig_status:

                    st.plotly_chart(fig_status, use_container_width=True)

            with col2:

                if fig_eng:

                    st.plotly_chart(fig_eng, use_container_width=True)



    # TAB 3: REGISTRO

    with tab3:

        st.header("Registro de Tareas Completadas")

        st.write("") # Espacio

        

        completed_tasks_df = filtered_df[filtered_df['estado'] == 'Completada'].copy()

        

        if completed_tasks_df.empty:

            st.markdown('<div class="custom-alert alert-info">ℹ️ Aún no hay tareas completadas en el registro.</div>', unsafe_allow_html=True)

        else:

            completed_tasks_df = completed_tasks_df.sort_values(by='fecha_dt', ascending=False)

            for _, task in completed_tasks_df.iterrows():

                st.markdown('<div class="task-card">', unsafe_allow_html=True)

                col1, col2 = st.columns([4, 2])

                

                with col1:

                    fecha_str = task.get('fecha_dt').strftime('%d/%m/%Y') if pd.notna(task.get('fecha_dt')) else "N/A"

                    st.markdown(f"""

                        <span style="font-weight: 600; font-size: 1.1rem;">{task.get('cliente', 'N/A')}</span><br>

                        <small style="color: var(--subtle-text-color);">

                            📅 {fecha_str} &nbsp; • &nbsp; 👨‍🔧 {task.get('ingeniero', 'N/A')} &nbsp; • &nbsp; 🔧 {task.get('tipo', 'N/A')}

                        </small>

                    """, unsafe_allow_html=True)

                

                with col2:

                    st.markdown('<div style="text-align: right; padding-top: 10px;"><span class="status-badge status-completada">✅ Completada</span></div>', unsafe_allow_html=True)



                st.markdown('</div>', unsafe_allow_html=True)



if __name__ == "__main__":

    main() quiero que en vez de verse asi, se vea un calendario de la semana en cuestion en grande y las tareas que hay por cada dia y su estado y responzable en tarjetasd dentro. En la aprte superior derecha quiero un calendario del ems mas chico que muestre las tareas mas chiquitas que hay por dia.
