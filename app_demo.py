"""
Aplicación de prueba sin dependencias de API externas.
Muestra datos de ejemplo para verificar que la interfaz funciona.
"""
import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Configuración de la página
st.set_page_config(
    page_title="Marketing Script - Demo",
    page_icon="📊",
    layout="wide"
)

st.title("🎯 Marketing Script - Versión Demo")
st.markdown("---")

# Datos de ejemplo
sample_data = [
    {
        "name": "Restaurante El Buen Sabor",
        "address": "Calle 123 #45-67, Montería",
        "phone": "+57 300 123 4567",
        "email": "info@elbuensabor.com",
        "website": "https://elbuensabor.com"
    },
    {
        "name": "Hotel Plaza Central",
        "address": "Carrera 50 #30-15, Montería",
        "phone": "+57 301 234 5678",
        "email": "reservas@plazacentral.com",
        "website": "https://plazacentral.com"
    },
    {
        "name": "Café Paradiso",
        "address": "Centro Comercial Los Ejecutivos, Montería",
        "phone": "+57 302 345 6789",
        "email": "contacto@cafeparadiso.com",
        "website": "https://cafeparadiso.com"
    }
]

st.header("📋 Datos de Ejemplo")
st.markdown("Estos son datos de muestra para probar la funcionalidad de la aplicación:")

df = pd.DataFrame(sample_data)
st.dataframe(df, use_container_width=True)

st.markdown("---")

# Simulación de búsqueda
st.header("🔍 Simulación de Búsqueda")

col1, col2, col3 = st.columns(3)

with col1:
    city = st.selectbox("Ciudad", ["Montería", "Medellín", "Bogotá", "Cali"])

with col2:
    business_type = st.selectbox("Tipo de Negocio", ["restaurante", "hotel", "café", "tienda"])

with col3:
    target_count = st.slider("Cantidad objetivo", 5, 50, 10)

if st.button("🚀 Buscar Negocios", type="primary"):
    with st.spinner("Buscando negocios..."):
        import time
        time.sleep(2)  # Simular búsqueda

        # Mostrar resultados simulados
        st.success(f"✅ Encontrados {len(sample_data)} negocios en {city}")

        # Mostrar resultados
        for i, business in enumerate(sample_data, 1):
            with st.expander(f"{i}. {business['name']}"):
                st.write(f"📍 **Dirección:** {business['address']}")
                st.write(f"📞 **Teléfono:** {business['phone']}")
                st.write(f"📧 **Email:** {business['email']}")
                st.write(f"🌐 **Website:** {business['website']}")

st.markdown("---")

# Información del sistema
st.header("ℹ️ Información del Sistema")

st.info("""
**Estado:** ✅ Aplicación funcionando correctamente

**Problema identificado:** La API key de Google Places necesita ser configurada correctamente.

**Solución:** Obtén una API key válida desde [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
""")

# Mostrar configuración actual
st.subheader("🔧 Configuración Actual")
st.code(f"""
GOOGLE_API_KEY={'*' * 20} (necesita configuración)
AUTH_USERS=admin,testuser
AUTH_PASSWORDS=admin123,test123
""")

st.markdown("---")

st.markdown("""
### 📝 Próximos Pasos:

1. **Obtener API Key de Google Places:**
   - Ve a [Google Cloud Console](https://console.cloud.google.com/)
   - Crea un proyecto o selecciona uno existente
   - Habilita la API de Places
   - Crea credenciales (API Key)
   - Copia la API key al archivo `.env`

2. **Actualizar configuración:**
   ```bash
   # Edita el archivo .env
   GOOGLE_API_KEY=tu_api_key_real_aqui
   ```

3. **Ejecutar aplicación completa:**
   ```bash
   streamlit run app.py
   ```

### 🆘 ¿Necesitas ayuda?

Si tienes problemas para obtener la API key, puedes usar esta versión demo para familiarizarte con la interfaz.
""")