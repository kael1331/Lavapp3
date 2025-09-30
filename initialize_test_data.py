#!/usr/bin/env python3
"""
Script para inicializar datos de prueba del sistema LavApp
Basado en la información del problem statement
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pathlib import Path
import uuid

# Add backend to path
sys.path.append('/app/backend')

from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

async def clear_database():
    """Limpia la base de datos para empezar limpio"""
    print("🗑️  Limpiando base de datos...")
    collections = await db.list_collection_names()
    for collection_name in collections:
        await db[collection_name].drop()
    print("✅ Base de datos limpiada")

async def create_super_admin():
    """Crea el Super Admin"""
    print("👑 Creando Super Admin...")
    
    super_admin = {
        "id": str(uuid.uuid4()),
        "email": "kearcangel@gmail.com",
        "nombre": "Super Admin",
        "password_hash": await hash_password("K@#l1331"),
        "rol": "SUPER_ADMIN",
        "created_at": datetime.now(timezone.utc),
        "is_active": True
    }
    
    await db.users.insert_one(super_admin)
    
    # Configuración del Super Admin
    config_superadmin = {
        "id": str(uuid.uuid4()),
        "alias_bancario": "superadmin.sistema.mp",
        "precio_mensualidad": 10000.0,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.configuracion_superadmin.insert_one(config_superadmin)
    
    print(f"✅ Super Admin creado: {super_admin['email']}")
    return super_admin["id"]

async def create_admin_lavaderos():
    """Crea los administradores de lavaderos y sus lavaderos"""
    print("🚿 Creando administradores de lavaderos...")
    
    admins_data = [
        {
            "email": "carlos@lavaderosur.com",
            "password": "carlos123", 
            "lavadero": "Lavadero Sur",
            "direccion": "Av. Libertador 1234, San Miguel de Tucumán, Tucumán",
            "estado": "ACTIVO"
        },
        {
            "email": "maria@lavaderocentro.com", 
            "password": "maria123",
            "lavadero": "Lavadero Centro",
            "direccion": "25 de Mayo 567, San Miguel de Tucumán, Tucumán", 
            "estado": "ACTIVO"
        },
        {
            "email": "juan@lavaderonorte.com",
            "password": "juan123", 
            "lavadero": "Lavadero Norte",
            "direccion": "San Martín 890, San Miguel de Tucumán, Tucumán",
            "estado": "PENDIENTE"
        },
        {
            "email": "ana@lavaderoexpress.com",
            "password": "ana123",
            "lavadero": "Lavadero Express", 
            "direccion": "Las Heras 345, San Miguel de Tucumán, Tucumán",
            "estado": "ACTIVO"
        }
    ]
    
    lavaderos_ids = []
    
    for admin_data in admins_data:
        # Crear usuario admin
        admin_id = str(uuid.uuid4())
        admin_user = {
            "id": admin_id,
            "email": admin_data["email"],
            "nombre": admin_data["lavadero"] + " Admin",
            "password_hash": await hash_password(admin_data["password"]),
            "rol": "ADMIN",
            "created_at": datetime.now(timezone.utc),
            "is_active": admin_data["estado"] == "ACTIVO"
        }
        
        await db.users.insert_one(admin_user)
        
        # Crear lavadero
        lavadero_id = str(uuid.uuid4())
        lavadero = {
            "id": lavadero_id,
            "nombre": admin_data["lavadero"],
            "admin_id": admin_id,
            "direccion_registro": admin_data["direccion"],
            "telefono": "381-555-0123",
            "descripcion": f"El mejor servicio de lavado en {admin_data['lavadero'].lower()}",
            "estado_pago": admin_data["estado"],
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.lavaderos.insert_one(lavadero)
        
        # Crear configuración del lavadero
        configuracion = {
            "id": str(uuid.uuid4()),
            "lavadero_id": lavadero_id,
            "direccion": admin_data["direccion"],
            "latitud": -26.8241,  # San Miguel de Tucumán
            "longitud": -65.2226,
            "esta_abierto": admin_data["estado"] == "ACTIVO",
            "horario_apertura": "08:00",
            "horario_cierre": "20:00",
            "precio_lavado": 2500.0,
            "duracion_turno": 60,  # 60 minutos por turno
            "configurado": True,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db.configuracion_lavadero.insert_one(configuracion)
        
        print(f"✅ Lavadero creado: {lavadero['nombre']} - Admin: {admin_user['email']}")
        lavaderos_ids.append(lavadero_id)
    
    return lavaderos_ids

async def create_sample_clients():
    """Crea algunos clientes de ejemplo"""
    print("👥 Creando clientes de ejemplo...")
    
    clients = [
        {"email": "cliente1@gmail.com", "nombre": "Juan Cliente", "password": "cliente123"},
        {"email": "cliente2@gmail.com", "nombre": "María Cliente", "password": "cliente123"},
        {"email": "cliente3@gmail.com", "nombre": "Pedro Cliente", "password": "cliente123"}
    ]
    
    for client_data in clients:
        client = {
            "id": str(uuid.uuid4()),
            "email": client_data["email"],
            "nombre": client_data["nombre"],
            "password_hash": await hash_password(client_data["password"]),
            "rol": "CLIENTE",
            "created_at": datetime.now(timezone.utc),
            "is_active": True
        }
        
        await db.users.insert_one(client)
        print(f"✅ Cliente creado: {client['email']}")

async def main():
    """Función principal de inicialización"""
    print("🚀 Inicializando datos de prueba para LavApp...")
    
    try:
        # Limpiar base de datos
        await clear_database()
        
        # Crear Super Admin
        super_admin_id = await create_super_admin()
        
        # Crear admins y lavaderos
        lavaderos_ids = await create_admin_lavaderos()
        
        # Crear clientes de ejemplo
        await create_sample_clients()
        
        print("\n🎉 ¡Datos de prueba inicializados exitosamente!")
        print("\n📋 RESUMEN DE USUARIOS CREADOS:")
        print("="*50)
        print("👑 Super Admin:")
        print("   Email: kearcangel@gmail.com")
        print("   Password: K@#l1331")
        print("   URL: /superadmin-dashboard")
        
        print("\n🚿 Administradores de Lavaderos:")
        admins = [
            ("carlos@lavaderosur.com", "carlos123", "Lavadero Sur"),
            ("maria@lavaderocentro.com", "maria123", "Lavadero Centro"),
            ("juan@lavaderonorte.com", "juan123", "Lavadero Norte"),
            ("ana@lavaderoexpress.com", "ana123", "Lavadero Express")
        ]
        
        for email, password, lavadero in admins:
            print(f"   Email: {email}")
            print(f"   Password: {password}")
            print(f"   Lavadero: {lavadero}")
            print()
        
        print("👥 Clientes de ejemplo:")
        print("   cliente1@gmail.com - cliente123")
        print("   cliente2@gmail.com - cliente123")
        print("   cliente3@gmail.com - cliente123")
        
        print("\n🌐 URLs de acceso:")
        print("   Frontend: https://lavadero-system.preview.emergentagent.com/")
        print("   Admin Login: https://lavadero-system.preview.emergentagent.com/admin-login")
        print("   Super Admin: https://lavadero-system.preview.emergentagent.com/superadmin-dashboard")
        
    except Exception as e:
        print(f"❌ Error durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())