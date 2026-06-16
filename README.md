MesaFlow es una plataforma SaaS multiempresa para restaurantes desarrollada por NautilusTech S.A.S. — automatiza la operación completa desde la toma de pedidos hasta la cocina, el cobro y el análisis del negocio.


🎯 Problema que resuelve

Los restaurantes en Latinoamérica gestionan pedidos con papel, WhatsApp o aplicaciones desconectadas. MesaFlow centraliza toda la operación en una sola plataforma: los meseros toman pedidos desde el teléfono, la cocina los recibe en pantalla en tiempo real, y el dueño ve las métricas del negocio desde cualquier lugar.


✨ Funcionalidades principales

MóduloDescripción📱 POS modernoToma de pedidos por mesa, búsqueda rápida de productos, carrito y cobro👨‍🍳 Kitchen Display System (KDS)Pantalla de cocina en tiempo real con WebSockets — sin papel🪑 Gestión de mesasMapa visual del restaurante, estado de mesas, asignación de meseros📊 Dashboard operacionalVentas del día, productos más vendidos, tiempo promedio de atención🤖 IA integradaPredicción de demanda y sugerencias de stock con OpenAI GPT💬 WhatsAppNotificaciones automáticas a clientes🏢 Multi-restauranteUn sistema para múltiples sucursales con datos completamente aislados🔐 Roles y permisosAdministrador, Cajero, Mesero, Cocinero


🛠️ Stack tecnológico

Backend:     Python 3.12 + Django 5.0 + Django REST Framework
Base datos:  PostgreSQL 16
Frontend:    React 18 + TailwindCSS + Vite
Tiempo real: WebSockets (Django Channels)
IA:          OpenAI GPT-3.5/4
Despliegue:  Azure VM + Docker + Nginx + Gunicorn
Auth:        JWT (SimpleJWT)


🏗️ Arquitectura

┌─────────────────────────────────────────────────┐
│                   CLIENTE                        │
│         React SPA (Mesero / Cajero / Admin)      │
└──────────────────────┬──────────────────────────┘
                       │ REST API + WebSockets
┌──────────────────────▼──────────────────────────┐
│              DJANGO BACKEND                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │   API    │  │ Channels │  │  Celery Tasks│  │
│  │  REST    │  │(WS/KDS)  │  │  (Reports)   │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│   PostgreSQL 16   │   Redis   │   Azure Blob     │
└─────────────────────────────────────────────────┘

Patrón multi-tenant: cada restaurante opera en su propio schema de base de datos — datos 100% aislados con una sola instancia del sistema.


📸 Capturas del sistema


Sistema funcionando en producción con clientes reales en Colombia



DashboardKitchen DisplayPOSVista ejecutiva de ventasÓrdenes en tiempo realToma de pedidos por mesa


📈 Métricas del proyecto


✅ En producción con clientes reales en Colombia
🏢 Arquitectura multi-tenant — soporta múltiples restaurantes
⚡ Tiempo de respuesta del KDS: < 500ms (WebSockets)
🤖 IA integrada para predicción de demanda



🚀 Instalación local (desarrollo)

bash# 1. Clonar el repositorio
git clone https://github.com/jdarangom2012/MesaFlow.git
cd MesaFlow

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PostgreSQL y Azure

# 5. Migrar base de datos
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Instalar dependencias frontend
cd frontend && npm install && npm run build

# 8. Correr servidor
python manage.py runserver


📁 Estructura del proyecto

MesaFlow/
├── apps/
│   ├── pedidos/        # Gestión de órdenes y mesas
│   ├── cocina/         # Kitchen Display System
│   ├── pos/            # Punto de venta
│   ├── inventario/     # Control de stock
│   ├── reportes/       # Dashboard y analytics
│   └── tenants/        # Multi-tenant management
├── config/             # Configuración Django
├── frontend/           # React + TailwindCSS
├── docker/             # Archivos Docker
└── requirements.txt


🌐 Producto comercial

MesaFlow es un producto SaaS comercial de NautilusTech S.A.S.

📧 Contacto: admin@nautilustech.app
🌐 Web: nautilustech.app


👨‍💻 Desarrollado por

Juan David Arango Morales
Co-Founder & CTO @ NautilusTech S.A.S.
Senior Software Engineer — Python | Django | PostgreSQL | SaaS
