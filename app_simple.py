#!/usr/bin/env python3
"""
Aplicación web Streamlit para Marketing Script - VERSIÓN BÁSICA CON AUTENTICACIÓN
"""
import streamlit as st
import streamlit_authenticator as stauth
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="Marketing Script - Login",
    page_icon="🔐",
    layout="centered"
)

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

def main():
    # ===== AUTENTICACIÓN =====
    try:
        authenticator.login('main')
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return

    if st.session_state["authentication_status"] is False:
        st.error('❌ Usuario/contraseña incorrectos')
        return

    if st.session_state["authentication_status"] is None:
        st.info('🔐 Por favor ingresa tus credenciales para acceder al sistema')
        st.markdown("""
        ### Credenciales de prueba:
        - **Usuario:** `admin`
        - **Contraseña:** `admin123`

        - **Usuario:** `testuser`
        - **Contraseña:** `test123`
        """)
        return

    # Usuario autenticado - mostrar aplicación
    st.success(f'✅ ¡Bienvenido {st.session_state["name"]}!')

    st.markdown("""
    ## 🎉 Autenticación Exitosa

    Has accedido correctamente al **Marketing Script Dashboard**.

    ### 🚀 Funcionalidades Disponibles:
    - 🔍 **Buscar Empresas**: Encuentra contactos verificados
    - 🔄 **Verificar Duplicados**: Evita registros repetidos
    - 📊 **Merge Final**: Integra datos con tu base maestra
    - 📁 **Gestión de Archivos**: Administra tus datos

    ### 📋 Próximos Pasos:
    1. Configura tu API Key de Google Places
    2. Coloca tu Excel maestro en `data/input/`
    3. ¡Comienza a buscar empresas!

    ---
    """)

    # Información del sistema
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Usuario", st.session_state["name"])
    with col2:
        st.metric("Estado", "✅ Autenticado")

    # Botón de logout
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        authenticator.logout('Cerrar Sesión', 'main')
        st.rerun()

if __name__ == "__main__":
    main()