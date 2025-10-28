#!/usr/bin/env python3
"""
Script de prueba para autenticación Streamlit
"""
import streamlit as st
import streamlit_authenticator as stauth
import os

# Configuración de la página
st.set_page_config(page_title="Test Auth", page_icon="🔐")

# Configuración de autenticación simple
credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            "password": "admin123"
        },
        "testuser": {
            "name": "Usuario de Prueba",
            "password": "test123"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "test_db",
    "test_key",
    cookie_expiry_days=1
)

# Autenticación
authenticator.login('main')

if st.session_state["authentication_status"] is False:
    st.error('Usuario/contraseña incorrectos')
elif st.session_state["authentication_status"] is None:
    st.warning('Por favor ingresa tus credenciales')
else:
    st.success(f'Bienvenido {st.session_state["name"]}!')
    st.write("✅ Autenticación exitosa!")

    if st.button("Logout"):
        authenticator.logout('Logout', 'main')
        st.rerun()