#!/usr/bin/env python3
"""
Aplicación web Streamlit para Marketing Script
Interfaz completa para búsqueda, verificación de duplicados y merge de datos.
CON AUTENTICACIÓN BÁSICA
"""
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Añadir src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.business_processor import BusinessDataProcessor
from src.output_writer import OutputWriter

# Configuración de la página
st.set_page_config(
    page_title="Marketing Script Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estados globales
if 'current_data' not in st.session_state:
    st.session_state.current_data = None
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'output_file' not in st.session_state:
    st.session_state.output_file = None
if 'merge_completed' not in st.session_state:
    st.session_state.merge_completed = False

# ===== CONFIGURACIÓN DE AUTENTICACIÓN =====
def get_auth_config():
    """Obtiene la configuración de autenticación desde variables de entorno o valores por defecto."""

    # Credenciales desde variables de entorno (recomendado para producción)
    auth_users = os.getenv('AUTH_USERS', 'admin')  # Lista separada por comas
    auth_passwords = os.getenv('AUTH_PASSWORDS', 'admin123')  # Lista separada por comas
    auth_names = os.getenv('AUTH_NAMES', 'Administrador')  # Lista separada por comas

    # Convertir a listas
    usernames = [u.strip() for u in auth_users.split(',')]
    passwords = [p.strip() for p in auth_passwords.split(',')]
    names = [n.strip() for n in auth_names.split(',')]

    # Asegurar que todas las listas tengan la misma longitud
    min_length = min(len(usernames), len(passwords), len(names))
    usernames = usernames[:min_length]
    passwords = passwords[:min_length]
    names = names[:min_length]

    # Crear diccionario de credenciales
    credentials = {
        "usernames": {}
    }

    for i, username in enumerate(usernames):
        credentials["usernames"][username] = {
            "name": names[i] if i < len(names) else username,
            "password": passwords[i] if i < len(passwords) else "password"
        }

    return credentials

# Inicializar autenticador
auth_config = get_auth_config()
authenticator = stauth.Authenticate(
    auth_config,
    "marketing_script_db",
    "auth_key_unique_12345",
    cookie_expiry_days=1
)

def load_css():
    """Cargar estilos CSS personalizados."""
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def check_environment():
    """Verificar que el entorno esté configurado correctamente."""
    issues = []

    # Verificar API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        issues.append("❌ GOOGLE_API_KEY no encontrada en variables de entorno")

    # Verificar directorios
    required_dirs = ['data/input', 'data/output', 'data/merged']
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    # Verificar archivos existentes
    input_files = list(Path('data/input').glob('*.xlsx')) + list(Path('data/input').glob('*.xls'))
    output_files = list(Path('data/output').glob('*.xlsx')) + list(Path('data/output').glob('*.xls'))

    return {
        'api_key_ok': bool(api_key),
        'input_files': len(input_files),
        'output_files': len(output_files),
        'issues': issues
    }

def run_search(city, business_type, target_count, scan_emails, progress_callback=None):
    """Ejecutar búsqueda de empresas en un hilo separado."""
    try:
        processor = BusinessDataProcessor(
            api_key=os.getenv('GOOGLE_API_KEY'),
            workers=1,
            humanize=False,
            rate_limit_per_minute=600
        )

        if progress_callback:
            progress_callback("🔍 Buscando empresas con información de contacto...")

        results = processor.load_businesses_with_contact_info(
            city=city,
            business_type=business_type,
            target_count=target_count
        )

        if not results:
            return {"error": "No se encontraron resultados con información de contacto"}

        if progress_callback:
            progress_callback(f"✅ Encontrados {len(results)} resultados. Procesando detalles...")

        processed_data = processor.process_batch(
            items=results,
            scan_emails=scan_emails,
            delay=0,
            city=city
        )

        # Generar archivo de salida
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        city_clean = city.replace(",", "").replace(" ", "_")
        type_clean = business_type.replace(" ", "_")
        output_filename = f"output_{city_clean}_{type_clean}_{timestamp}.xlsx"
        output_path = os.path.join("data", "output", output_filename)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        processor.output_writer.write_to_excel(
            data=processed_data,
            filepath=output_path,
            use_template_columns=True
        )

        return {
            "success": True,
            "results": results,
            "processed_data": processed_data,
            "output_file": output_path,
            "count": len(processed_data)
        }

    except Exception as e:
        return {"error": str(e)}

def run_pre_merge(output_file, progress_callback=None):
    """Ejecutar verificación de duplicados."""
    try:
        # Importar funciones de pre_merge
        sys.path.insert(0, os.path.dirname(__file__))
        from pre_merge import find_input_excel, compare_with_existing, save_filtered_output

        input_file = find_input_excel()
        if not input_file:
            return {"error": "No se encontró Excel maestro en data/input/"}

        if progress_callback:
            progress_callback("🔍 Comparando con datos existentes...")

        # Leer datos nuevos
        df_new = pd.read_excel(output_file)
        new_data = df_new.to_dict('records')

        # Comparar
        nuevos, duplicados, info_duplicados = compare_with_existing(new_data, input_file)

        result = {
            "total_analyzed": len(new_data),
            "new_records": len(nuevos),
            "duplicate_records": len(duplicados),
            "duplicates_info": info_duplicados,
            "new_data": nuevos,
            "duplicates": duplicados
        }

        # Si hay duplicados, crear archivo filtrado
        if duplicados:
            filtered_path = save_filtered_output(output_file, nuevos, "_sin_duplicados")
            result["filtered_file"] = filtered_path

        return result

    except Exception as e:
        return {"error": str(e)}

def run_merge(output_file, progress_callback=None):
    """Ejecutar merge final."""
    try:
        writer = OutputWriter(humanize=False)

        if progress_callback:
            progress_callback("🔄 Iniciando merge...")

        # Leer datos
        df_new = pd.read_excel(output_file)
        new_data = df_new.to_dict('records')

        # Encontrar archivo maestro
        input_dir = Path("data/input")
        excel_files = list(input_dir.glob("*.xlsx")) + list(input_dir.glob("*.xls"))
        if not excel_files:
            return {"error": "No se encontró Excel maestro en data/input/"}

        input_file = str(excel_files[0])

        # Hacer merge
        merged_path, renamed_original = writer.merge_into_existing_excel(
            existing_filepath=input_file,
            data=new_data,
            key_priority=['Pagina Web', 'Nombre']
        )

        if merged_path and renamed_original:
            return {
                "success": True,
                "merged_file": merged_path,
                "original_renamed": renamed_original
            }
        else:
            return {"error": "No se pudo completar el merge"}

    except Exception as e:
        return {"error": str(e)}

def main():
    # ===== AUTENTICACIÓN =====
    try:
        authenticator.login('main')
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return

    if st.session_state["authentication_status"] is False:
        st.error('Usuario/contraseña incorrectos')
        return

    if st.session_state["authentication_status"] is None:
        st.warning('Por favor ingresa tus credenciales')
        return

    # Usuario autenticado - mostrar aplicación
    load_css()

    # ===== HEADER CON LOGOUT =====
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        st.write(f"👤 **{st.session_state['name']}**")
    with col2:
        st.markdown('<h1 class="main-header" style="text-align: center; margin-bottom: 0;">📊 Marketing Script Dashboard</h1>', unsafe_allow_html=True)
    with col3:
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()

    # ===== SIDEBAR =====
    with st.sidebar:
        st.title("📊 Marketing Script")
        st.markdown("---")

        # Verificar entorno
        env_status = check_environment()

        if env_status['issues']:
            st.error("⚠️ Problemas de configuración:")
            for issue in env_status['issues']:
                st.error(issue)
        else:
            st.success("✅ Entorno configurado correctamente")

        st.markdown("---")

        # Navegación
        page = st.radio(
            "Navegación:",
            ["🏠 Inicio", "🔍 Buscar Empresas", "🔄 Verificar Duplicados", "📊 Merge Final", "📁 Archivos"]
        )

        st.markdown("---")
        st.markdown(f"**Archivos encontrados:**")
        st.markdown(f"📥 Input: {env_status['input_files']}")
        st.markdown(f"📤 Output: {env_status['output_files']}")

    # ===== CONTENIDO PRINCIPAL =====
    if page == "🏠 Inicio":
        show_home_page()
    elif page == "🔍 Buscar Empresas":
        show_search_page()
    elif page == "🔄 Verificar Duplicados":
        show_duplicates_page()
    elif page == "📊 Merge Final":
        show_merge_page()
    elif page == "📁 Archivos":
        show_files_page()

def show_home_page():
    st.markdown('<h1 class="main-header">🏠 Marketing Script Dashboard</h1>', unsafe_allow_html=True)

    st.markdown("""
    ## 📋 Bienvenido al Sistema de Gestión de Datos de Marketing

    Esta aplicación te permite gestionar de forma eficiente la búsqueda y organización de datos de empresas para tus campañas de marketing.

    ### 🚀 Funcionalidades Principales

    1. **🔍 Buscar Empresas**: Encuentra empresas con información de contacto verificada
    2. **🔄 Verificar Duplicados**: Evita duplicados antes del merge final
    3. **📊 Merge Final**: Integra nuevos datos con tu base de datos maestra
    4. **📁 Gestión de Archivos**: Administra y descarga tus archivos de datos

    ### 📊 Flujo de Trabajo Recomendado

    ```
    🔍 Buscar Empresas → 🔄 Verificar Duplicados → 📊 Merge Final
    ```

    ### ⚙️ Configuración Requerida

    - ✅ API Key de Google Places configurada
    - ✅ Directorios de datos creados automáticamente
    - ✅ Archivos Excel en `data/input/` para merge

    ---
    """)

    # Mostrar estado del sistema
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Archivos Input", check_environment()['input_files'])

    with col2:
        st.metric("Archivos Output", check_environment()['output_files'])

    with col3:
        api_status = "✅ OK" if check_environment()['api_key_ok'] else "❌ Faltante"
        st.metric("API Key", api_status)

def show_search_page():
    st.markdown('<h1 class="main-header">🔍 Buscar Empresas</h1>', unsafe_allow_html=True)

    st.markdown("""
    Busca empresas con información de contacto verificada usando Google Places API.
    Todos los resultados tendrán teléfono o WhatsApp.
    """)

    # Formulario de búsqueda
    with st.form("search_form"):
        col1, col2 = st.columns(2)

        with col1:
            city = st.text_input("🏙️ Ciudad y País", placeholder="Ej: Bogotá, Colombia", key="city")
            business_type = st.text_input("🏢 Tipo de Negocio", placeholder="Ej: restaurantes, hoteles", key="business_type")

        with col2:
            target_count = st.number_input("📊 Cantidad de Empresas", min_value=1, max_value=100, value=10, key="count")
            scan_emails = st.checkbox("📧 Escanear emails en páginas web", value=True, key="scan_emails")

        submitted = st.form_submit_button("🚀 Iniciar Búsqueda", use_container_width=True)

    if submitted:
        if not city or not business_type:
            st.error("❌ Por favor completa todos los campos")
            return

        # Barra de progreso
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Ejecutar búsqueda
        result = run_search(city, business_type, target_count, scan_emails,
                          lambda msg: status_text.text(msg))

        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
            return

        # Resultados exitosos
        st.success("✅ Búsqueda completada exitosamente!")

        # Guardar en session state
        st.session_state.search_results = result['results']
        st.session_state.processed_data = result['processed_data']
        st.session_state.output_file = result['output_file']

        # Mostrar resumen
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Empresas Encontradas", result['count'])
        with col2:
            st.metric("Ubicación", city)
        with col3:
            st.metric("Tipo", business_type)

        # Mostrar datos
        if result['processed_data']:
            st.markdown("### 📋 Resultados de la Búsqueda")
            df = pd.DataFrame(result['processed_data'])
            st.dataframe(df, use_container_width=True)

            # Botón de descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar CSV",
                data=csv,
                file_name=f"empresas_{city.replace(' ', '_')}_{business_type}.csv",
                mime='text/csv',
                use_container_width=True
            )

def show_duplicates_page():
    st.markdown('<h1 class="main-header">🔄 Verificar Duplicados</h1>', unsafe_allow_html=True)

    if not st.session_state.output_file:
        st.warning("⚠️ Primero debes realizar una búsqueda de empresas")
        return

    st.markdown(f"**Archivo a verificar:** {st.session_state.output_file}")

    if st.button("🔍 Verificar Duplicados", use_container_width=True):
        with st.spinner("Verificando duplicados..."):
            result = run_pre_merge(st.session_state.output_file)

        if "error" in result:
            st.error(f"❌ Error: {result['error']}")
            return

        # Mostrar resultados
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Analizados", result['total_analyzed'])
        with col2:
            st.metric("Registros Nuevos", result['new_records'])
        with col3:
            st.metric("Duplicados", result['duplicate_records'])

        if result['duplicate_records'] > 0:
            st.warning(f"⚠️ Se encontraron {result['duplicate_records']} duplicados")

            # Mostrar detalles de duplicados
            st.markdown("### 📋 Detalles de Duplicados")
            for nombre, info in result['duplicates_info'].items():
                with st.expander(f"🔴 {nombre}"):
                    st.write(f"**Motivo:** {info['reason']}")
                    st.write(f"**Teléfono:** {info['telefono']}")
                    st.write(f"**WhatsApp:** {info['whatsapp']}")
                    st.write(f"**Web:** {info['website']}")

            # Opciones
            st.markdown("### 🤔 ¿Qué deseas hacer?")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Continuar con Merge (solo nuevos)", use_container_width=True):
                    st.success("✅ Procede al Merge Final con los registros filtrados")
                    st.session_state.current_data = result['new_data']

            with col2:
                if st.button("🔄 Buscar Más Empresas", use_container_width=True):
                    st.info(f"📝 Buscar {result['duplicate_records']} empresas adicionales")
                    # Aquí se podría implementar búsqueda adicional

        else:
            st.success("🎉 ¡No hay duplicados! Todos los registros son nuevos.")
            st.session_state.current_data = result['new_data']

def show_merge_page():
    st.markdown('<h1 class="main-header">📊 Merge Final</h1>', unsafe_allow_html=True)

    if not st.session_state.current_data and not st.session_state.output_file:
        st.warning("⚠️ Primero debes realizar una búsqueda y verificar duplicados")
        return

    # Verificar archivos
    input_files = list(Path('data/input').glob('*.xlsx')) + list(Path('data/input').glob('*.xls'))
    if not input_files:
        st.error("❌ No se encontró archivo Excel maestro en data/input/")
        st.info("💡 Coloca tu archivo Excel maestro en la carpeta data/input/")
        return

    master_file = str(input_files[0])
    st.markdown(f"**Archivo maestro:** {master_file}")

    # Mostrar datos a mergear
    if st.session_state.current_data:
        data_to_merge = st.session_state.current_data
        source = "datos filtrados (sin duplicados)"
    else:
        # Leer del archivo de output
        df = pd.read_excel(st.session_state.output_file)
        data_to_merge = df.to_dict('records')
        source = "archivo de búsqueda completo"

    st.markdown(f"**Datos a mergear:** {len(data_to_merge)} registros ({source})")

    # Vista previa
    with st.expander("👀 Vista Previa de Datos a Mergear"):
        df_preview = pd.DataFrame(data_to_merge)
        st.dataframe(df_preview.head(10), use_container_width=True)

    if st.button("🔄 Ejecutar Merge Final", use_container_width=True):
        with st.spinner("Ejecutando merge..."):
            result = run_merge(st.session_state.output_file or "temp.xlsx")

        if "error" in result:
            st.error(f"❌ Error en merge: {result['error']}")
            return

        st.success("✅ Merge completado exitosamente!")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Archivo Merged", os.path.basename(result['merged_file']))
        with col2:
            st.metric("Original Renombrado", os.path.basename(result['original_renamed']))

        st.markdown("### 📂 Estructura Final")
        st.markdown(f"📁 **Original preservado:** `data/input/{os.path.basename(result['original_renamed'])}`")
        st.markdown(f"📊 **Resultado merged:** `data/merged/{os.path.basename(result['merged_file'])}`")

        st.session_state.merge_completed = True

        # Botón para descargar
        if os.path.exists(result['merged_file']):
            with open(result['merged_file'], 'rb') as f:
                st.download_button(
                    label="📥 Descargar Archivo Merged",
                    data=f,
                    file_name=os.path.basename(result['merged_file']),
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True
                )

def show_files_page():
    st.markdown('<h1 class="main-header">📁 Gestión de Archivos</h1>', unsafe_allow_html=True)

    st.markdown("Administra y descarga tus archivos de datos de marketing.")

    # Tabs para diferentes directorios
    tab1, tab2, tab3, tab4 = st.tabs(["📥 Input", "📤 Output", "🔄 Merged", "📊 Todos"])

    # Función helper para mostrar archivos
    def show_files_in_directory(directory, tab):
        path = Path(f"data/{directory}")
        if not path.exists():
            tab.warning(f"Directorio data/{directory}/ no existe")
            return

        files = list(path.glob("*.xlsx")) + list(path.glob("*.xls"))
        if not files:
            tab.info(f"No hay archivos Excel en data/{directory}/")
            return

        for file in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
            with tab.expander(f"📄 {file.name}"):
                # Información del archivo
                stat = file.stat()
                modified_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                size_mb = stat.st_size / (1024 * 1024)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Tamaño", f"{size_mb:.2f} MB")
                with col2:
                    st.metric("Modificado", modified_time)
                with col3:
                    # Leer primeras filas para preview
                    try:
                        df = pd.read_excel(file)
                        st.metric("Registros", len(df))
                    except:
                        st.metric("Registros", "N/A")

                # Botón de descarga
                with open(file, 'rb') as f:
                    tab.download_button(
                        label="📥 Descargar",
                        data=f,
                        file_name=file.name,
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )

    with tab1:
        show_files_in_directory("input", tab1)

    with tab2:
        show_files_in_directory("output", tab2)

    with tab3:
        show_files_in_directory("merged", tab3)

    with tab4:
        st.markdown("### 📊 Resumen General")
        env = check_environment()
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Input", env['input_files'])
        with col2:
            st.metric("Total Output", env['output_files'])
        with col3:
            merged_count = len(list(Path('data/merged').glob('*.xlsx')) + list(Path('data/merged').glob('*.xls')))
            st.metric("Total Merged", merged_count)

if __name__ == "__main__":
    main()