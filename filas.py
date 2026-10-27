from flask import Flask, render_template_string, redirect, url_for, request, session, jsonify, make_response, send_file
import os
import json
import sqlite3
import csv
import io
import secrets
import re
import time
import hashlib
import hmac
import math
from contextlib import contextmanager
from functools import wraps
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Clave secreta para manejo seguro de sesiones
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
# Configuración adicional de sesión y cookies. En producción se recomienda HTTPS y
# definir SECRET_KEY como variable de entorno para conservar las sesiones entre reinicios.
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)

# Credenciales demo. En producción usa DISABLE_DEMO_ACCOUNTS=1 y define
# ADMIN_EMAIL, ADMIN_PASSWORD y SECRET_KEY como variables de entorno.
DESHABILITAR_DEMO = os.getenv("DISABLE_DEMO_ACCOUNTS", "0") == "1"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL") or ("" if DESHABILITAR_DEMO else "admin@keepinventory.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD") or ("" if DESHABILITAR_DEMO else "admin123password")

# ZONA HORARIA LOCAL (UTC-5)
def obtener_tiempo_local():
    zona_horaria_local = timezone(timedelta(hours=-5))
    return datetime.now(zona_horaria_local).strftime("%Y-%m-%d %H:%M:%S")

# Lista global en memoria para simular la base de datos y nuevas entidades jerárquicas
PEDIDOS_REGISTRADOS = []
EMPRESAS_REGISTRADAS = [
    {
        "id": 1,
        "nombre_empresa": "Supermercados El Ahorro",
        "email_dueno": "dueno@elahorro.com",
        "password_dueno": "dueno123",
        "sedes": [
            {"nombre": "Sede Central", "direccion": "Calle 10 # 5-20"}
        ],
        "usuarios_staff": [
            {"nombre": "Carlos Manager", "email": "manager@elahorro.com", "password": "mgr123", "rol": "manager", "sede": "Sede Central"},
            {"nombre": "Ana Cajera", "email": "empleado@elahorro.com", "password": "emp123", "rol": "empleado", "sede": "Sede Central"}
        ]
    }
]

# INVENTARIO SUPERMERCADO - CÓDIGOS RÁPIDOS, GRAN VARIEDAD E IMÁGENES VERIFICADAS Y CORREGIDAS
INVENTARIO_SUPER = [
    # Lácteos y Huevos (Imagen corregida de huevos)
    {"codigo": "001", "nombre": "Huevos AA x30 unidades", "precio": 18500, "stock": 120, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTi22raN8VU750R9OTZCMsTwxZtVe1ayRM6AIYibBG6lQ&s=10"},
    {"codigo": "002", "nombre": "Leche Entera 1L Colanta", "precio": 4300, "stock": 200, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "003", "nombre": "Queso Campesino 500g", "precio": 12800, "stock": 65, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1452195100486-9cc805987862?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "004", "nombre": "Mantequilla con Sal 250g", "precio": 9200, "stock": 80, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "005", "nombre": "Yogurt Melocotón 1L", "precio": 8500, "stock": 90, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400&auto=format&fit=crop&q=80"},
    
    # Despensa y Granos
    {"codigo": "006", "nombre": "Arroz Roa Blanco 1Kg", "precio": 4800, "stock": 350, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "007", "nombre": "Aceite Vegetal Premier 900ml", "precio": 14500, "stock": 110, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "008", "nombre": "Frijol Cargamanto 500g", "precio": 6200, "stock": 140, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTk6vhtQPQVX1A2qF2Srnqysx7BX-RBXNu2Y4wTbt6qNY4cCs7ecRRVLjJ4&s=10"},
    {"codigo": "009", "nombre": "Lenteja Seleccionada 500g", "precio": 4500, "stock": 160, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTpzPTsxyM_o88E7e6CKS1vooqPUId3RHFSggtbyTj-oQ&s=10"},
    {"codigo": "010", "nombre": "Azúcar Blanca Incauca 1Kg", "precio": 4900, "stock": 220, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSZ9lR7W_EE8pgYO3jvoNsfLAd9pxKMf75KVAoFZAAuvQ_ukgKi9BD5Oeg-&s=10"},
    {"codigo": "011", "nombre": "Sal Marina Refinada 1Kg", "precio": 2100, "stock": 180, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQsfKf19KXUfOj9XuJEX2dtkuD07lJWQE9wvdxv0dR4hpRkAP5cUbU912o&s=10"},
    {"codigo": "012", "nombre": "Pasta Espagueti Doria 500g", "precio": 3800, "stock": 210, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "013", "nombre": "Harina de Maíz PAN 1Kg", "precio": 4200, "stock": 300, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "014", "nombre": "Atún en Agua Zenú 170g", "precio": 7800, "stock": 175, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT9Og7uR6HCIl53aH0dAbIDLvAbLNOs3TvKe7kr0fdAMA&s"},
    {"codigo": "015", "nombre": "Maíz Tierno Lata 300g", "precio": 4100, "stock": 130, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ59FS67lCOsnsIzU2awGPSiBA1HF3pGWRIUDDQUB4Td2xEPZmqbVp-QLrJ&s=10"},

    # Carnes y Charcutería
    {"codigo": "016", "nombre": "Pechuga de Pollo 1Kg", "precio": 16900, "stock": 85, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "017", "nombre": "Carne Molida Especial 1Kg", "precio": 24500, "stock": 70, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTrUaaRLrpYQr_l8EltllB-cEoXnaY42gK-Fk2WdwVoSw&s"},
    {"codigo": "018", "nombre": "Lomo de Cerdo 1Kg", "precio": 22000, "stock": 60, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQtVCBiSp6xhaomH2xrJdzsTC66BTa27VwUlZou4K8dnxSrHtUj1GaqxTqh&s=10"},
    {"codigo": "019", "nombre": "Salchicha Ranchera Premium 14 unidades", "precio": 9800, "stock": 115, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSClyw6bmnKTclvMHUexOnA-Dfc9XKZGlYzZn831DDHmg&s=10"},
    {"codigo": "020", "nombre": "Jamón Pietrán de Pavo 230g", "precio": 11500, "stock": 95, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTR5SWq9-vYmzlkGuSYC2kzNTjhUDfXsxL2tbYZYKM0PQ&s=10"},

    # Frutas y Verduras
    {"codigo": "021", "nombre": "Aguacate Hass 1Kg", "precio": 8900, "stock": 90, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "022", "nombre": "Tomate Chonto 1Kg", "precio": 4200, "stock": 150, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "023", "nombre": "Cebolla Cabezona Roja 1Kg", "precio": 3800, "stock": 140, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTKg_Pm9rjrPVnYHHE3_glaGej8pnE3Ax-ZdzoUnj-LSw&s=10"},
    {"codigo": "024", "nombre": "Papa Sabanera 1Kg", "precio": 3200, "stock": 280, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "025", "nombre": "Manzana Roja Importada 1Kg", "precio": 9500, "stock": 110, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&auto=format&fit=crop&q=80"},

    # Bebidas
    {"codigo": "026", "nombre": "Café Sello Rojo 500g", "precio": 18900, "stock": 130, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "027", "nombre": "Coca-Cola Original 1.5L", "precio": 6200, "stock": 190, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "028", "nombre": "Agua Manantial Sin Gas 5L", "precio": 8900, "stock": 80, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400&auto=format&fit=crop&q=80"},
    {"codigo": "029", "nombre": "Jugo Hit Mora 1L", "precio": 4500, "stock": 140, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=400&auto=format&fit=crop&q=80"},

    # Aseo y Cuidado Personal
    {"codigo": "030", "nombre": "Detergente en Polvo Ariel 2Kg", "precio": 26900, "stock": 75, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8HKgqc_aKcS0OrABlzjz2xiHqQiQwOPnfDJXzPRFabQ&s=10"},
    {"codigo": "031", "nombre": "Jabón de Baño Palmolive x3", "precio": 11200, "stock": 105, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSjeDittM5iqnNji-aYFguLuYoWDMz8uQDJMQhHWMfVf7cTfgGfnZ_pUYsy&s=10"},
    {"codigo": "032", "nombre": "Papel Higiénico Familia 12 Rollos", "precio": 22500, "stock": 90, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTGn9vkHKlrIoX7X0EztD05bNpNtrsgCtlKu3I09C4ewQ&s=10"}
]

REPORTES_EMPLEADOS = []

# Módulos añadidos: trazabilidad, proveedores, compras, devoluciones, promociones y auditoría.
MOVIMIENTOS_INVENTARIO = []
PROVEEDORES_REGISTRADOS = []
ORDENES_COMPRA = []
DEVOLUCIONES_REGISTRADAS = []
PROMOCIONES_REGISTRADAS = []
REGISTRO_AUDITORIA = []
NOTIFICACIONES_SISTEMA = []
FAVORITOS_CLIENTES = {}
LOTES_PRODUCTOS = []
TRASLADOS_INVENTARIO = []
PRODUCTOS_ARCHIVADOS = []
CLIENTES_REGISTRADOS = []
LOGIN_INTENTOS = {}

# Persistencia local SQLite: conserva los datos existentes sin cambiar la organización
# principal del programa ni sus nombres de listas y rutas.
DB_PATH = os.getenv("KEEPINVENTORY_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "keepinventory_data.sqlite3"))
ESTADO_LISTAS = {
    "pedidos": "PEDIDOS_REGISTRADOS",
    "empresas": "EMPRESAS_REGISTRADAS",
    "inventario": "INVENTARIO_SUPER",
    "reportes": "REPORTES_EMPLEADOS",
    "movimientos": "MOVIMIENTOS_INVENTARIO",
    "proveedores": "PROVEEDORES_REGISTRADOS",
    "ordenes_compra": "ORDENES_COMPRA",
    "devoluciones": "DEVOLUCIONES_REGISTRADAS",
    "promociones": "PROMOCIONES_REGISTRADAS",
    "auditoria": "REGISTRO_AUDITORIA",
    "notificaciones": "NOTIFICACIONES_SISTEMA",
    "favoritos": "FAVORITOS_CLIENTES",
    "lotes": "LOTES_PRODUCTOS",
    "traslados": "TRASLADOS_INVENTARIO",
    "archivados": "PRODUCTOS_ARCHIVADOS",
    "clientes": "CLIENTES_REGISTRADOS",
}

@contextmanager
def _conexion_db():
    carpeta = os.path.dirname(os.path.abspath(DB_PATH))
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    conexion = sqlite3.connect(DB_PATH, timeout=20)
    try:
        conexion.execute("PRAGMA journal_mode=WAL")
        conexion.execute("PRAGMA foreign_keys=ON")
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

def guardar_estado():
    """Guarda una copia coherente de las listas del sistema en SQLite."""
    try:
        with _conexion_db() as conexion:
            conexion.execute("CREATE TABLE IF NOT EXISTS estado_aplicacion (clave TEXT PRIMARY KEY, valor TEXT NOT NULL, actualizado TEXT NOT NULL)")
            for clave, nombre_global in ESTADO_LISTAS.items():
                valor = globals().get(nombre_global, [])
                conexion.execute(
                    "INSERT INTO estado_aplicacion(clave, valor, actualizado) VALUES(?, ?, ?) "
                    "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor, actualizado=excluded.actualizado",
                    (clave, json.dumps(valor, ensure_ascii=False), obtener_tiempo_local())
                )
    except (sqlite3.Error, TypeError, ValueError) as error:
        app.logger.exception("No se pudo guardar el estado del sistema: %s", error)

def cargar_estado():
    """Restaura datos guardados; si no existe una base, conserva los datos demo iniciales."""
    try:
        with _conexion_db() as conexion:
            conexion.execute("CREATE TABLE IF NOT EXISTS estado_aplicacion (clave TEXT PRIMARY KEY, valor TEXT NOT NULL, actualizado TEXT NOT NULL)")
            filas = conexion.execute("SELECT clave, valor FROM estado_aplicacion").fetchall()
        if not filas:
            # Convertir las contraseñas iniciales a hashes antes de persistirlas.
            for empresa in EMPRESAS_REGISTRADAS:
                if not str(empresa.get("password_dueno", "")).startswith("pbkdf2:") and not str(empresa.get("password_dueno", "")).startswith("scrypt:"):
                    empresa["password_dueno"] = generate_password_hash(empresa.get("password_dueno", ""))
                for usuario in empresa.get("usuarios_staff", []):
                    if not str(usuario.get("password", "")).startswith(("pbkdf2:", "scrypt:")):
                        usuario["password"] = generate_password_hash(usuario.get("password", ""))
            guardar_estado()
            return
        for clave, valor in filas:
            nombre_global = ESTADO_LISTAS.get(clave)
            if nombre_global:
                globals()[nombre_global] = json.loads(valor)
        # Migración de contraseñas antiguas guardadas en texto plano.
        cambios = False
        for empresa in EMPRESAS_REGISTRADAS:
            pw = str(empresa.get("password_dueno", ""))
            if pw and not pw.startswith(("pbkdf2:", "scrypt:")):
                empresa["password_dueno"] = generate_password_hash(pw); cambios = True
            for usuario in empresa.get("usuarios_staff", []):
                pw = str(usuario.get("password", ""))
                if pw and not pw.startswith(("pbkdf2:", "scrypt:")):
                    usuario["password"] = generate_password_hash(pw); cambios = True
        if cambios:
            guardar_estado()
    except (sqlite3.Error, json.JSONDecodeError, TypeError) as error:
        app.logger.exception("No se pudo cargar el estado guardado: %s", error)

def _verificar_password(almacenada, ingresada):
    """Acepta temporalmente credenciales heredadas y hashes modernos."""
    if not isinstance(almacenada, str) or not isinstance(ingresada, str):
        return False
    if almacenada.startswith(("pbkdf2:", "scrypt:")):
        try:
            return check_password_hash(almacenada, ingresada)
        except (ValueError, TypeError):
            return False
    if almacenada.startswith("pbkdf2_sha256$"):
        try:
            _, iteraciones, sal_hex, hash_hex = almacenada.split("$", 3)
            calculado = hashlib.pbkdf2_hmac("sha256", ingresada.encode("utf-8"), bytes.fromhex(sal_hex), int(iteraciones)).hex()
            return hmac.compare_digest(calculado, hash_hex)
        except (ValueError, TypeError):
            return False
    return secrets.compare_digest(almacenada, ingresada)

def _hash_password(password):
    return generate_password_hash(password)

def _auditar(accion, detalle="", empresa=None, sede=None):
    REGISTRO_AUDITORIA.insert(0, {
        "fecha": obtener_tiempo_local(),
        "usuario": session.get("user_nombre") or session.get("cliente_nombre") or session.get("user_type", "anonimo"),
        "rol": session.get("user_type", "anonimo"),
        "accion": str(accion)[:100],
        "detalle": str(detalle)[:500],
        "empresa": empresa or session.get("empresa_nombre", "Supermercados El Ahorro"),
        "sede": sede or session.get("user_sede") or session.get("sede", "")
    })
    del REGISTRO_AUDITORIA[5000:]

def _notificar(tipo, mensaje, empresa=None, sede=None, destinatario=None):
    NOTIFICACIONES_SISTEMA.insert(0, {
        "id": secrets.token_hex(6), "fecha": obtener_tiempo_local(), "tipo": str(tipo)[:40],
        "mensaje": str(mensaje)[:300], "empresa": empresa or session.get("empresa_nombre", "Supermercados El Ahorro"),
        "sede": sede or session.get("user_sede") or session.get("sede", ""),
        "destinatario": destinatario, "leida": False
    })
    del NOTIFICACIONES_SISTEMA[1000:]

def _usuario_autorizado(*roles):
    return session.get("user_type") in roles

def _producto_empresa_sede(producto, empresa=None, sede=None):
    if empresa and producto.get("empresa") != empresa:
        return False
    if sede and producto.get("sede") != sede:
        return False
    return True

def validar_codigo_producto(codigo):
    return bool(re.fullmatch(r"\d{3}", str(codigo or "").strip()))

def buscar_producto(codigo, sede=None, empresa=None):
    codigo = str(codigo or "").strip()
    return next((p for p in INVENTARIO_SUPER if p.get("codigo") == codigo and (sede is None or p.get("sede") == sede) and (empresa is None or p.get("empresa") == empresa)), None)

def _normalizar_items(items):
    """Valida y agrupa las líneas del carrito que llegan desde el navegador."""
    if not isinstance(items, list) or not items:
        raise ValueError("El carrito está vacío o tiene un formato inválido.")
    normalizados = {}
    if len(items) > 100:
        raise ValueError("El carrito supera el límite de 100 líneas de producto.")
    for linea in items:
        if not isinstance(linea, dict):
            raise ValueError("Hay un producto con formato inválido.")
        codigo = str(linea.get("codigo", "")).strip()
        cantidad = linea.get("cantidad", 1)
        if not validar_codigo_producto(codigo):
            raise ValueError("Todos los productos deben tener un código válido de tres dígitos.")
        if isinstance(cantidad, bool) or not str(cantidad).isdigit():
            raise ValueError("La cantidad de un producto no es válida.")
        cantidad = int(cantidad)
        if cantidad < 1 or cantidad > 500:
            raise ValueError("La cantidad debe estar entre 1 y 500 unidades.")
        normalizados[codigo] = normalizados.get(codigo, 0) + cantidad
        if normalizados[codigo] > 1000:
            raise ValueError("La cantidad acumulada por producto supera el límite permitido.")
    return normalizados

def procesar_items_inventario(items, sede, empresa, descontar=True):
    lineas = _normalizar_items(items)
    detalle = []
    total = 0.0
    for codigo, cantidad in lineas.items():
        producto = buscar_producto(codigo, sede, empresa)
        if not producto:
            raise ValueError(f"El producto #{codigo} no existe en el inventario de esta sede.")
        stock = int(producto.get("stock", 0))
        if descontar and stock < cantidad:
            raise ValueError(f"Stock insuficiente para {producto.get('nombre', codigo)}.")
        precio = float(producto.get("precio", 0))
        if not math.isfinite(precio) or precio < 0:
            raise ValueError("Se encontró un precio inválido en el inventario.")
        detalle.append({"codigo": codigo, "nombre": producto.get("nombre", ""), "cantidad": cantidad, "precio_unitario": precio, "subtotal": round(precio * cantidad, 2)})
        total += precio * cantidad
    if descontar:
        for linea in detalle:
            producto = buscar_producto(linea["codigo"], sede, empresa)
            anterior = int(producto.get("stock", 0))
            producto["stock"] = anterior - linea["cantidad"]
            MOVIMIENTOS_INVENTARIO.insert(0, {"fecha": obtener_tiempo_local(), "codigo": linea["codigo"], "producto": linea["nombre"], "cantidad": -linea["cantidad"], "stock_anterior": anterior, "stock_nuevo": producto["stock"], "tipo": "venta", "sede": sede, "empresa": empresa, "responsable": session.get("user_nombre") or session.get("cliente_nombre", "Cliente")})
            if producto["stock"] <= 10:
                _notificar("stock_bajo", f"{producto.get('nombre')} tiene {producto['stock']} unidades.", empresa=empresa, sede=sede)
    return detalle, round(total, 2)

def es_venta_cerrada(pedido):
    return pedido.get("tipo") == "venta" or (pedido.get("tipo") == "pedido_recoger" and pedido.get("estado") == "entregado")

def _importe_seguro(valor):
    try:
        importe = float(valor)
    except (TypeError, ValueError):
        raise ValueError("El importe no es válido.")
    if not math.isfinite(importe) or importe < 0 or importe > 1_000_000_000:
        raise ValueError("El importe está fuera del rango permitido.")
    return round(importe, 2)

# Cargar el estado después de declarar las listas originales y las nuevas.
cargar_estado()

def inicializar_sedes_demo():
    """Alinea las tres sedes que muestra el portal con el inventario de demostración."""
    empresa = next((e for e in EMPRESAS_REGISTRADAS if e.get('nombre_empresa') == 'Supermercados El Ahorro'), None)
    if not empresa:
        return
    sedes_demo = [
        {'nombre': 'Sede Norte', 'direccion': 'Av. Principal #102-15, Plaza Norte'},
        {'nombre': 'Sede Sur Express', 'direccion': 'Carrera 45 #12-30, Portal Sur'},
    ]
    cambio = False
    for sede_info in sedes_demo:
        if not any(x.get('nombre') == sede_info['nombre'] for x in empresa.get('sedes', [])):
            empresa.setdefault('sedes', []).append(dict(sede_info))
            cambio = True
        if not any(p.get('empresa') == empresa['nombre_empresa'] and p.get('sede') == sede_info['nombre'] for p in INVENTARIO_SUPER):
            base = [dict(p) for p in INVENTARIO_SUPER if p.get('empresa') == empresa['nombre_empresa'] and p.get('sede') == 'Sede Central']
            for producto in base:
                producto['sede'] = sede_info['nombre']
                INVENTARIO_SUPER.append(producto)
            if base:
                cambio = True
    if cambio:
        guardar_estado()

inicializar_sedes_demo()

if DESHABILITAR_DEMO:
    # Mantiene el catálogo, pero retira las credenciales de prueba del sistema.
    for _empresa in EMPRESAS_REGISTRADAS:
        if _empresa.get('email_dueno', '').lower() == 'dueno@elahorro.com':
            _empresa['email_dueno'] = ''
            _empresa['password_dueno'] = ''
        _empresa['usuarios_staff'] = [u for u in _empresa.get('usuarios_staff', []) if u.get('email', '').lower() not in ('manager@elahorro.com', 'empleado@elahorro.com')]
    guardar_estado()

@app.after_request
def aplicar_cabeceras_seguridad(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

@app.errorhandler(413)
def solicitud_demasiado_grande(_error):
    return jsonify({"status": "error", "mensaje": "La solicitud supera el tamaño permitido."}), 413

# CSS COMPLETO CON ESTABILIZADOR DE LAYOUT Y ANIMACIONES
CSS_ESTILOS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

:root{
  --primary:#0f8a5f;
  --primary-dark:#064e3b;
  --primary-light:#e6f4ea;
  --primary-gradient: linear-gradient(135deg, #0f8a5f 0%, #064e3b 100%);
  --accent-gradient: linear-gradient(135deg, #10b981 0%, #059669 100%);
  --bg-gradient: linear-gradient(135deg, #0f172a 0%, #0f8a5f 50%, #064e3b 100%);
  --dark:#0f172a;
  --light:#f8fafc;
  --gray:#e2e8f0;
  --gray-text:#64748b;
  --red:#ef4444;
  --blue:#3b82f6;
  --accent:#f59e0b;
  --card-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
  --glass-bg: rgba(255, 255, 255, 0.85);
  --glass-border: rgba(255, 255, 255, 0.18);
}

*{margin:0;padding:0;box-sizing:border-box;font-family:'Plus Jakarta Sans', 'Segoe UI', system-ui, -apple-system, sans-serif;}
body{background:#f1f5f9; color:var(--dark); line-height:1.6; overflow-x:hidden;}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
  100% { transform: translateY(0px); }
}

@keyframes pulseGlow {
  0% { box-shadow: 0 0 0 0 rgba(15, 138, 95, 0.5); }
  70% { box-shadow: 0 0 0 15px rgba(15, 138, 95, 0); }
  100% { box-shadow: 0 0 0 0 rgba(15, 138, 95, 0); }
}

.fade-in { animation: fadeIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.float-anim { animation: float 4s ease-in-out infinite; }

.brand{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.logo{width:44px;height:44px;background:var(--primary-gradient);color:white;display:flex;align-items:center;justify-content:center;border-radius:14px;font-weight:800;font-size:20px;flex-shrink:0;box-shadow:0 8px 16px rgba(15,138,95,0.3); transition: transform 0.3s ease;}
.logo:hover{transform: rotate(5deg) scale(1.05);}
.brand-large{color:white;margin-bottom:35px; text-align:center;}
.logo-large{width:90px;height:90px;background:white;color:var(--primary);font-size:40px;font-weight:900;border-radius:24px;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;box-shadow:0 20px 40px rgba(0,0,0,0.3); animation: float 4s ease-in-out infinite;}
.brand-large h1{font-size:42px; margin-bottom:8px; font-weight:800; letter-spacing:-1px;}
.brand-large p{opacity:0.9; font-size:16px; font-weight:300;}

.landing-body{display:flex;justify-content:center;align-items:center;min-height:100vh;background:var(--bg-gradient);padding:20px; position:relative;}
.landing-container{max-width:900px;width:100%;text-align:center; z-index:1;}
.selector-grid{display:grid;grid-template-columns:1fr 1fr;gap:28px;}
.selector-card{background:var(--glass-bg); backdrop-filter:blur(12px); border:1px solid rgba(255,255,255,0.4); padding:40px 30px;border-radius:24px;cursor:pointer;transition:all .4s cubic-bezier(0.16, 1, 0.3, 1);box-shadow:0 20px 40px rgba(0,0,0,.15);text-align:center;text-decoration:none;color:inherit;display:block;position:relative;overflow:hidden;}
.selector-card:hover{transform:translateY(-10px) scale(1.02); box-shadow:0 30px 60px rgba(0,0,0,.3); background:white;}
.selector-card .icon{font-size:56px;margin-bottom:20px; transition:transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); display:inline-block;}
.selector-card:hover .icon{transform:scale(1.25) rotate(8deg);}
.selector-card h2{margin-bottom:10px; font-size:24px; font-weight:700;}
.selector-card p{color:var(--gray-text);margin-bottom:22px; font-size:15px; line-height:1.5;}
.selector-card span{color:var(--primary);font-weight:700;font-size:14px;letter-spacing:0.5px; display:inline-block; transition:transform 0.2s;}
.selector-card:hover span{transform:translateX(5px);}
.selector-card.staff{border-top:6px solid var(--dark);}
.selector-card.client{border-top:6px solid var(--primary);}

.login-body{display:flex;justify-content:center;align-items:center;min-height:100vh;background:var(--bg-gradient);padding:20px;}
.login-container{background:white;padding:42px 35px;border-radius:24px;width:100%;max-width:440px;box-shadow:0 25px 50px -12px rgba(0,0,0,0.35);text-align:center; transition: transform 0.3s ease;}
.login-container input, .login-container select, .login-container textarea{width:100%;padding:14px 16px;margin:10px 0;border:2px solid var(--gray);border-radius:12px;outline:none; font-size:15px; transition:all 0.3s ease; background:#f8fafc;}
.login-container input:focus{border-color:var(--primary); background:white; box-shadow:0 0 0 4px rgba(15,138,95,.15);}
.btn{width:100%;padding:14px 20px;background:var(--primary-gradient);color:white;border:none;border-radius:12px;cursor:pointer;font-weight:700;margin-top:14px; font-size:15px; transition:all .3s ease; display:inline-flex; align-items:center; justify-content:center; gap:8px; box-shadow:0 4px 12px rgba(15,138,95,0.25);}
.btn:hover{transform:translateY(-2px); box-shadow:0 8px 20px rgba(15,138,95,0.4); opacity:0.95;}
.btn:active{transform:translateY(0);}
.btn-outline{background:transparent; color:var(--primary); border:2px solid var(--primary); box-shadow:none;}
.btn-outline:hover{background:var(--primary-light); transform:translateY(-2px); box-shadow:none;}
.btn-danger{background:linear-gradient(135deg, #ef4444 0%, #dc2626 100%); box-shadow:0 4px 12px rgba(239,68,68,0.25);}
.btn-danger:hover{box-shadow:0 8px 20px rgba(239,68,68,0.4);}
.demo-creds{margin-top:20px; font-size:13px; background:#f8fafc; padding:14px; border-radius:12px; text-align:left; border-left:4px solid var(--primary); border:1px solid #e2e8f0; border-left-width:4px;}

.dashboard{display:flex;min-height:100vh;}
.sidebar{width:280px;background:var(--dark);color:white;padding:28px 20px;flex-shrink:0;display:flex;flex-direction:column;justify-content:space-between; box-shadow:4px 0 25px rgba(0,0,0,0.1);}
.sidebar .brand{margin-bottom:30px;}
.sidebar a{display:flex;align-items:center;gap:12px;color:#94a3b8;padding:14px 16px;text-decoration:none;border-radius:12px;margin:6px 0; font-size:15px; font-weight:500; transition:all .3s cubic-bezier(0.16, 1, 0.3, 1); cursor:pointer;}
.sidebar a:hover,.sidebar a.active{background:var(--primary-gradient);color:white; transform:translateX(6px); box-shadow:0 4px 15px rgba(15,138,95,0.3);}
.main{flex:1;padding:35px; overflow-y:auto; background:#f8fafc;}
.card{background:white;padding:28px;border-radius:20px;box-shadow:var(--card-shadow);margin-bottom:24px; border:1px solid #f1f5f9; transition:all 0.3s ease;}
.card:hover{box-shadow:0 20px 30px -10px rgba(0,0,0,0.07); transform:translateY(-2px);}
.grid{display:grid;grid-template-columns:repeat(auto-fill, minmax(250px, 1fr));gap:24px;}
table{width:100%;border-collapse:separate;border-spacing:0;margin-top:18px; font-size:14px;}
th,td{padding:14px 18px;text-align:left;}
th{background:#f8fafc; font-weight:700; color:var(--gray-text); font-size:12px; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid var(--gray);}
td{border-bottom:1px solid #f1f5f9; transition:background 0.2s;}
tr:hover td{background:#f8fafc;}
.tag{padding:6px 12px;border-radius:30px;font-size:12px;color:white; font-weight:700; display:inline-block; letter-spacing:0.3px;}
.tag-admin{background:linear-gradient(135deg, #ef4444, #b91c1c);} 
.tag-empleado{background:linear-gradient(135deg, #10b981, #047857);}

.header-cliente{display:flex; justify-content:space-between; align-items:center; background:white; padding:20px 32px; border-radius:20px; margin-bottom:30px; box-shadow:var(--card-shadow); border:1px solid #f1f5f9;}
.sede-selector-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;margin:25px 0;}
.sede-card-interactive{background:white;border:2px solid var(--gray);border-radius:20px;padding:28px 22px;text-align:center;cursor:pointer;transition:all .3s ease; position:relative;}
.sede-card-interactive:hover{border-color:var(--primary);transform:translateY(-6px); box-shadow:0 15px 35px rgba(15,138,95,0.12);}
.sede-card-interactive.active{border-color:var(--primary);background:var(--primary-light); animation:pulseGlow 2s infinite;}

/* ESTABILIZACIÓN DE TARJETAS PARA EVITAR SALTOS DE LAYOUT */
.product-card{background:white; border-radius:20px; border:1px solid #e2e8f0; padding:22px; display:flex; flex-direction:column; justify-content:space-between; transition:all 0.3s cubic-bezier(0.16, 1, 0.3, 1); position:relative; overflow:hidden; box-shadow:var(--card-shadow); min-height:360px;}
.product-card:hover{transform:translateY(-8px); box-shadow:0 20px 35px rgba(0,0,0,0.08); border-color:var(--primary);}
.product-badge{position:absolute; top:15px; right:15px; background:var(--accent); color:white; font-size:11px; font-weight:800; padding:4px 10px; border-radius:30px; letter-spacing:0.5px; box-shadow:0 4px 10px rgba(245,158,11,0.3); z-index:2;}
.product-img-container{width:100%; height:160px; min-height:160px; border-radius:12px; overflow:hidden; margin-bottom:12px; background:#f1f5f9; display:flex; align-items:center; justify-content:center; flex-shrink:0;}
.product-img-container img{width:100%; height:100%; object-fit:cover; transition:transform 0.4s ease;}
.product-card:hover .product-img-container img{transform:scale(1.08);}

.cart-floating-btn{position:fixed; bottom:30px; right:30px; background:var(--primary-gradient); color:white; padding:16px 26px; border-radius:50px; cursor:pointer; font-weight:700; box-shadow:0 10px 30px rgba(15,138,95,0.4); display:flex; align-items:center; gap:12px; z-index:99; transition:all 0.3s ease;}
.cart-floating-btn:hover{transform:scale(1.08) translateY(-3px); box-shadow:0 15px 35px rgba(15,138,95,0.5);}
.modal{display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.6); backdrop-filter:blur(6px); z-index:1000; justify-content:center; align-items:center;}
.modal-content{background:white; padding:35px; border-radius:24px; width:90%; max-width:520px; position:relative; animation:fadeIn 0.3s ease; box-shadow:0 25px 50px rgba(0,0,0,0.25); max-height:90vh; overflow-y:auto;}
.btn-remove{background:#fee2e2; color:#dc2626; border:none; border-radius:8px; padding:6px 10px; cursor:pointer; font-size:12px; font-weight:700; transition:all 0.2s;}
.btn-remove:hover{background:#fca5a5; transform:scale(1.05);}
.payment-method-box{border:2px solid var(--gray); border-radius:12px; padding:12px 16px; margin:10px 0; cursor:pointer; transition:all 0.2s;}
.payment-method-box:hover{border-color:var(--primary); background:var(--primary-light);}

@media(max-width:800px){
  .selector-grid{grid-template-columns:1fr;}
  .dashboard{flex-direction:column;}
  .sidebar{width:100%;}
  .header-cliente{flex-direction:column; gap:15px; align-items:flex-start;}
}
"""

HTML_LANDING = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KeepInventoryLite - Inicio</title>
    <style>{{ css | safe }}</style>
</head>
<body>
    <div class="landing-body">
        <div class="landing-container fade-in">
            <div class="brand-large">
                <div class="logo-large">KI</div>
                <h1>KeepInventoryLite</h1>
                <p>Gestión inteligente de inventarios y cadenas de supermercados (Zona Horaria Local Activa)</p>
            </div>
            <div class="selector-grid">
                <a href="/login-staff" class="selector-card staff">
                    <div class="icon">💼</div>
                    <h2>Personal / Dueños / Staff</h2>
                    <p>Acceso para Superadmin, Dueños de Supermercado (diferenciación por marca), Managers y Empleados.</p>
                    <span>INGRESAR COMO STAFF →</span>
                </a>
                <a href="/cliente-ubicacion" class="selector-card client">
                    <div class="icon">🛒</div>
                    <h2>Portal de Compras</h2>
                    <p>Encuentra tu sede y realiza tus compras de mercado online fácilmente con fotos de productos.</p>
                    <span>SELECCIONAR MI SEDE →</span>
                </a>
            </div>
        </div>
    </div>
</body>
</html>
"""

HTML_LOGIN_STAFF = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login Staff - KeepInventoryLite</title>
    <style>{{ css | safe }}</style>
</head>
<body>
    <div class="login-body">
        <div class="login-container fade-in">
            <div class="brand" style="justify-content:center;">
                <div class="logo">KI</div>
                <h2>Acceso Operativo</h2>
            </div>
            <p style="color:var(--gray-text); margin-bottom:15px; font-size:14px;">Ingresa tus credenciales de Superadmin, Dueño, Manager o Empleado</p>
            
            {% if error %}
            <div style="color:#dc2626; background:#fee2e2; padding:10px; border-radius:8px; font-size:13px; margin-bottom:12px;">
                {{ error }}
            </div>
            {% endif %}

            <form action="/login-staff" method="POST">
                <input type="email" name="usuario" placeholder="Correo electrónico" required>
                <input type="password" name="password" placeholder="Contraseña" required>
                <button type="submit" class="btn">🔑 Iniciar Sesión</button>
            </form>

            {% if mostrar_demo %}
            <div class="demo-creds">
                <b>Credenciales Demo (solo desarrollo):</b><br>
                • Dueño Empresa: dueno@elahorro.com / dueno123<br>
                • Manager: manager@elahorro.com / mgr123<br>
                • Empleado (Cajero): empleado@elahorro.com / emp123
            </div>
            {% endif %}

            <a href="/" style="display:block; margin-top:20px; color:var(--gray-text); text-decoration:none; font-size:13px;">← Volver al inicio</a>
        </div>
    </div>
</body>
</html>
"""

HTML_DASHBOARD_SUPERADMIN = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Superadministrador</title>
    <style>{{ css | safe }}</style>
</head>
<body>
    <div class="dashboard">
        <div class="sidebar">
            <div>
                <div class="brand">
                    <div class="logo">KI</div>
                    <h3>Superadmin</h3>
                </div>
                <a class="active">🏢 Cadenas y Dueños</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión</a>
        </div>
        <div class="main">
            <div class="card">
                <h2>Crear Nueva Cadena de Supermercados (Diferenciación de marcas)</h2>
                <p style="color:var(--gray-text); font-size:13px; margin-bottom:15px;">Escribe el nombre único de la cadena para diferenciar las cuentas entre distintos dueños.</p>
                <form action="/superadmin/crear-empresa" method="POST" style="margin-top:15px; display:grid; gap:12px;">
                    <input type="text" name="nombre_empresa" placeholder="Nombre de la línea o marca de supermercados" required style="padding:12px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="email" name="email_dueno" placeholder="Correo electrónico del Dueño" required style="padding:12px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="password" name="password_dueno" placeholder="Contraseña asignada al Dueño" required style="padding:12px; border:1px solid var(--gray); border-radius:8px;">
                    <button type="submit" class="btn">✨ Crear Empresa y Cuenta de Dueño</button>
                </form>
            </div>
            <div class="card">
                <h2>Empresas Registradas en el Sistema</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Nombre de la Cadena</th>
                            <th>Correo del Dueño</th>
                            <th>Sedes Creadas</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for emp in empresas %}
                        <tr>
                            <td><b>#{{ emp.id }}</b></td>
                            <td><span class="tag" style="background:var(--primary);">{{ emp.nombre_empresa }}</span></td>
                            <td>{{ emp.email_dueno }}</td>
                            <td>{{ emp.sedes|length }} sede(s)</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

HTML_DASHBOARD_DUENO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel del Dueño - {{ empresa.nombre_empresa }}</title>
    <style>{{ css | safe }}</style>
    <script>
        function cambiarSeccion(idSec, el) {
            document.querySelectorAll('.tab-sec').forEach(s => s.style.display = 'none');
            document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
            document.getElementById(idSec).style.display = 'block';
            el.classList.add('active');
        }
    </script>
</head>
<body>
    <div class="dashboard">
        <div class="sidebar">
            <div>
                <div class="brand">
                    <div class="logo">KI</div>
                    <h3>Dueño</h3>
                </div>
                <a onclick="cambiarSeccion('sec-sedes', this)" class="active">🏪 Sedes y Sucursales</a>
                <a onclick="cambiarSeccion('sec-personal', this)">👥 Personal (Managers / Empleados)</a>
                <a onclick="cambiarSeccion('sec-reportes', this)">📊 Reportes Mensuales de Ventas</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión</a>
        </div>
        <div class="main">
            <div id="sec-sedes" class="tab-sec fade-in">
                <div class="card">
                    <h2>Gestión de Sedes de {{ empresa.nombre_empresa }}</h2>
                    <form action="/dueno/crear-sede" method="POST" style="margin-top:15px; display:grid; grid-template-columns:1fr 1fr auto; gap:10px;">
                        <input type="text" name="nombre_sede" placeholder="Nombre de la Sede (Ej: Sede Norte)" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <input type="text" name="direccion_sede" placeholder="Ubicación / Dirección" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <button type="submit" class="btn" style="margin:0;">+ Añadir Sede</button>
                    </form>
                </div>
                <div class="card">
                    <h2>Sedes Actuales de la Empresa</h2>
                    <div class="grid" style="margin-top:15px;">
                        {% for sede in empresa.sedes %}
                        <div class="card">
                            <h3>🏢 {{ sede.nombre }}</h3>
                            <p style="color:var(--gray-text); font-size:13px; margin-top:5px;">📍 {{ sede.direccion }}</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <div id="sec-personal" class="tab-sec fade-in" style="display:none;">
                <div class="card">
                    <h2>Crear Cuenta de Manager o Empleado (Cajero)</h2>
                    <form action="/dueno/crear-personal" method="POST" style="margin-top:15px; display:grid; grid-template-columns:1fr 1fr 1fr 1fr auto; gap:10px;">
                        <input type="text" name="nombre" placeholder="Nombre completo" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <input type="email" name="email" placeholder="Correo corporativo" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <input type="password" name="password" placeholder="Contraseña" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <select name="rol" style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                            <option value="manager">Manager / Supervisor</option>
                            <option value="empleado">Empleado / Cajero</option>
                        </select>
                        <select name="sede" style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                            {% for sede in empresa.sedes %}
                            <option value="{{ sede.nombre }}">{{ sede.nombre }}</option>
                            {% endfor %}
                        </select>
                        <button type="submit" class="btn" style="grid-column: span 5; margin-top:5px;">+ Registrar Colaborador</button>
                    </form>
                </div>

                <div class="card">
                    <h2>Plantilla de Colaboradores Actuales</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Nombre</th>
                                <th>Rol</th>
                                <th>Correo</th>
                                <th>Sede Asignada</th>
                                <th>Acción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for staff in empresa.usuarios_staff %}
                            <tr>
                                <td><b>{{ staff.nombre }}</b></td>
                                <td>
                                    {% if staff.rol == 'manager' %}
                                    <span class="tag" style="background:var(--blue);">Manager</span>
                                    {% else %}
                                    <span class="tag tag-empleado">Empleado</span>
                                    {% endif %}
                                </td>
                                <td>{{ staff.email }}</td>
                                <td>{{ staff.sede }}</td>
                                <td>
                                    <form action="/dueno/eliminar-personal" method="POST" style="display:inline;">
                                        <input type="hidden" name="email" value="{{ staff.email }}">
                                        <button type="submit" class="btn-remove">Despedir / Eliminar</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div id="sec-reportes" class="tab-sec fade-in" style="display:none;">
                <div class="card">
                    <h2>📊 Reportes Mensuales y Desempeño (Zona Horaria Local)</h2>
                    <p style="color:var(--gray-text); margin-bottom:15px;">Registro acumulado de ventas por empleado, entradas de productos y auditoría mensual.</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Fecha / Hora Local</th>
                                <th>Empleado / Cajero</th>
                                <th>Sede</th>
                                <th>Productos Vendidos</th>
                                <th>Total Ingresado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in pedidos_empresa %}
                            <tr>
                                <td>{{ p.hora }}</td>
                                <td>{{ p.cliente }}</td>
                                <td>{{ p.sede }}</td>
                                <td>{{ p.productos }}</td>
                                <td><b style="color:var(--primary);">${{ "{:,.0f}".format(p.total) }}</b></td>
                            </tr>
                            {% else %}
                            <tr><td colspan="5" style="text-align:center; color:var(--gray-text);">No hay registros de ventas este mes todavía.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

HTML_DASHBOARD_MANAGER = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Manager - {{ user.sede }}</title>
    <style>{{ css | safe }}</style>
</head>
<body>
    <div class="dashboard">
        <div class="sidebar">
            <div>
                <div class="brand">
                    <div class="logo">KI</div>
                    <h3>Manager</h3>
                </div>
                <a class="active">📦 Control Rápido de Inventario e Imágenes</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión</a>
        </div>
        <div class="main">
            <div class="card">
                <h2>Registrar Producto con Código Rápido (3 Dígitos) e Imagen</h2>
                <p style="color:var(--gray-text); font-size:13px; margin-bottom:15px;">Usa códigos como 033, 034, 035 para facilitar el cobro y búsqueda. Agrega URL de la imagen del producto.</p>
                
                {% if error %}
                <div style="color:#dc2626; background:#fee2e2; padding:10px; border-radius:8px; font-size:13px; margin-bottom:12px;">
                    {{ error }}
                </div>
                {% endif %}

                <form action="/manager/agregar-producto" method="POST" style="display:grid; grid-template-columns:100px 1fr 120px 100px 1fr auto; gap:10px;">
                    <input type="text" name="codigo" placeholder="Código (033)" maxlength="3" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="text" name="nombre" placeholder="Nombre del producto" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="number" name="precio" placeholder="Precio ($)" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="number" name="stock" placeholder="Stock" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="text" name="imagen" placeholder="URL Imagen (https://...)" style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <button type="submit" class="btn" style="margin:0;">+ Añadir</button>
                </form>
            </div>

            <div class="card">
                <h2>Inventario Activo en {{ user.sede }}</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Imagen</th>
                            <th>Código Rápido</th>
                            <th>Producto</th>
                            <th>Precio Unitario</th>
                            <th>Stock Disponible</th>
                            <th>Sede</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for prod in inventario %}
                        <tr>
                            <td>
                                <div style="width:40px; height:40px; border-radius:8px; overflow:hidden; background:#e2e8f0;">
                                    <img src="{{ prod.imagen or 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&auto=format&fit=crop&q=80' }}" alt="prod" style="width:100%; height:100%; object-fit:cover;">
                                </div>
                            </td>
                            <td><span class="tag" style="background:var(--dark);">#{{ prod.codigo }}</span></td>
                            <td><b>{{ prod.nombre }}</b></td>
                            <td>${{ "{:,.0f}".format(prod.precio) }}</td>
                            <td>{{ prod.stock }} unidades</td>
                            <td>{{ prod.sede }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <h2>Reportes o Incidencias Recibidas de Empleados</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Fecha Local</th>
                            <th>Empleado</th>
                            <th>Descripción del Problema / Reporte</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for rep in reportes %}
                        <tr>
                            <td>{{ rep.fecha }}</td>
                            <td><b>{{ rep.empleado }}</b></td>
                            <td>{{ rep.mensaje }}</td>
                        </tr>
                        {% else %}
                        <tr><td colspan="3" style="text-align:center; color:var(--gray-text);">No hay reportes de empleados pendientes.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            <div class="card" style="margin-top:20px;">
                <h2>🧠 Herramientas de Inventario y Reportes</h2>
                <p style="color:var(--gray-text); margin-bottom:12px;">Consulta alertas de existencias, indicadores de tu sede y movimientos registrados.</p>
                <div class="grid">
                    <div class="card"><h3>📉 Resumen de la sede</h3><p id="manager-resumen" style="margin-top:8px;">Cargando indicadores...</p><button class="btn" type="button" onclick="cargarResumenManager()">Actualizar resumen</button></div>
                    <div class="card"><h3>⚠️ Stock bajo</h3><div id="manager-alertas" style="margin-top:8px;">Cargando alertas...</div><button class="btn" type="button" onclick="cargarAlertasManager()">Revisar alertas</button></div>
                    <div class="card"><h3>📦 Ajuste de existencias</h3><p>Registra entradas o salidas con un motivo para dejar trazabilidad.</p><button class="btn" type="button" onclick="ajustarStockManager()">Registrar movimiento</button></div>
                    <div class="card"><h3>🚚 Traslados</h3><p>Envía existencias a otra sede de tu empresa.</p><button class="btn" type="button" onclick="crearTrasladoManager()">Crear traslado</button></div>
                    <div class="card"><h3>🏭 Proveedores y compras</h3><p>Registra proveedores y recepciones de mercancía.</p><button class="btn" type="button" onclick="crearProveedorManager()">Nuevo proveedor</button><button class="btn btn-outline" type="button" onclick="registrarCompraManager()">Registrar compra</button></div>
                    <div class="card"><h3>📅 Lotes y vencimiento</h3><p>Controla fechas de vencimiento y consulta productos que requieren reposición.</p><button class="btn" type="button" onclick="registrarLoteManager()">Registrar lote</button><button class="btn btn-outline" type="button" onclick="verPronosticoManager()">Pronóstico de stock</button></div>
                </div>
                <div class="card"><h3>🛍️ Pedidos de la sede</h3><p>Actualiza el estado de los pedidos desde recepción hasta entrega.</p><div id="manager-pedidos" style="margin-top:10px;">Cargando pedidos...</div><button class="btn btn-outline" type="button" onclick="cargarPedidosManager()">Actualizar pedidos</button></div>
                <a class="btn" style="width:auto; padding:10px 16px;" href="/reportes/exportar.csv">⬇️ Exportar ventas a CSV</a>
            </div>
            <script>
                function escapeManagerHtml(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
                function cargarResumenManager(){fetch('/api/reportes/resumen').then(r=>r.json()).then(d=>{if(d.status==='error')throw Error(d.mensaje);document.getElementById('manager-resumen').innerHTML='Ventas registradas: <b>'+d.pedidos+'</b><br>Ingresos: <b>$'+Number(d.ventas_totales||0).toLocaleString()+'</b><br>Unidades en stock: <b>'+d.unidades_en_stock+'</b><br>Productos con stock bajo: <b>'+d.productos_bajo_stock+'</b>';}).catch(()=>document.getElementById('manager-resumen').innerText='No se pudo cargar el resumen.');}
                function cargarAlertasManager(){fetch('/api/inventario/alertas').then(r=>r.json()).then(d=>{if(d.status==='error')throw Error(d.mensaje);let el=document.getElementById('manager-alertas');el.innerHTML=(d.alertas||[]).map(p=>'<div style="padding:6px 0;border-bottom:1px solid #e2e8f0"><b>'+escapeManagerHtml(p.nombre)+'</b>: '+p.stock+' unidades ('+escapeManagerHtml(p.nivel)+')</div>').join('')||'No hay alertas de stock bajo.';}).catch(()=>document.getElementById('manager-alertas').innerText='No se pudieron cargar las alertas.');}
                function ajustarStockManager(){let codigo=prompt('Código del producto:');if(!codigo)return;let cantidad=parseInt(prompt('Cantidad positiva que vas a mover:'),10);if(!Number.isInteger(cantidad)||cantidad<=0){alert('Ingresa una cantidad entera mayor que cero.');return;}let tipo=prompt('Escribe entrada, salida o ajuste:', 'entrada');if(!['entrada','salida','ajuste','danado'].includes(tipo)){alert('Tipo de movimiento no válido.');return;}let motivo=prompt('Motivo del movimiento:');if(!motivo)return;fetch('/api/inventario/ajustar-stock',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({codigo,cantidad,tipo,motivo})}).then(r=>r.json()).then(d=>{alert(d.mensaje||('Stock actualizado: '+d.stock_nuevo));cargarResumenManager();cargarAlertasManager();}).catch(()=>alert('No se pudo guardar el movimiento.'));}
                function crearProveedorManager(){let nombre=prompt('Nombre del proveedor:');if(!nombre)return;let contacto=prompt('Contacto o teléfono (opcional):')||'';fetch('/api/proveedores',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({nombre,contacto})}).then(r=>r.json()).then(d=>alert(d.mensaje||d.error||('Proveedor registrado: '+d.proveedor.nombre))).catch(()=>alert('No se pudo registrar el proveedor.'));}
                function registrarCompraManager(){let codigo=prompt('Código del producto recibido:');if(!codigo)return;let cantidad=parseInt(prompt('Cantidad recibida:'),10);let costo=parseFloat(prompt('Costo unitario de compra (COP):'));if(!Number.isInteger(cantidad)||cantidad<=0||!Number.isFinite(costo)||costo<0){alert('Cantidad o costo inválido.');return;}fetch('/api/compras',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({codigo,cantidad,costo})}).then(r=>r.json()).then(d=>{alert(d.mensaje||d.error||'Compra registrada y stock actualizado.');cargarResumenManager();cargarAlertasManager();}).catch(()=>alert('No se pudo registrar la compra.'));}
                function crearTrasladoManager(){let codigo=prompt('Código del producto:');if(!codigo)return;let destino=prompt('Nombre exacto de la sede destino (por ejemplo, Sede Norte):');if(!destino)return;let cantidad=parseInt(prompt('Cantidad a trasladar:'),10);if(!Number.isInteger(cantidad)||cantidad<=0){alert('Cantidad inválida.');return;}fetch('/api/inventario/traslados',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({codigo,origen:'{{ user.sede }}',destino,cantidad})}).then(r=>r.json()).then(d=>{alert(d.mensaje||d.error||(d.traslado?'Traslado creado. La sede destino debe recibirlo.':'No se pudo crear el traslado.'));cargarResumenManager();cargarAlertasManager();}).catch(()=>alert('No se pudo crear el traslado.'));}
                function registrarLoteManager(){let codigo=prompt('Código del producto:');if(!codigo)return;let lote=prompt('Número o identificador del lote:');if(!lote)return;let cantidad=parseInt(prompt('Cantidad del lote:'),10);let fecha_vencimiento=prompt('Fecha de vencimiento (AAAA-MM-DD):');if(!Number.isInteger(cantidad)||cantidad<=0||!fecha_vencimiento){alert('Datos de lote no válidos.');return;}fetch('/api/lotes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({codigo,lote,cantidad,fecha_vencimiento})}).then(r=>r.json()).then(d=>alert(d.mensaje||d.error||'Lote registrado.')).catch(()=>alert('No se pudo registrar el lote.'));}
                function verPronosticoManager(){fetch('/api/reportes/pronostico').then(r=>r.json()).then(d=>{if(!Array.isArray(d)){alert(d.mensaje||d.error||'No se pudo calcular el pronóstico.');return;}alert(d.slice(0,15).map(p=>p.producto+': '+p.stock_actual+' en stock; '+p.recomendacion).join('\\n')||'No hay productos para analizar.');}).catch(()=>alert('No se pudo consultar el pronóstico.'));}
                function cargarPedidosManager(){fetch('/api/pedidos').then(r=>r.json()).then(d=>{if(!Array.isArray(d))throw Error(d.mensaje);let activos=d.filter(p=>!['entregado','cancelado'].includes(String(p.estado||'').toLowerCase()));let el=document.getElementById('manager-pedidos');el.innerHTML=activos.map(p=>{let estado=String(p.estado||'recibido').toLowerCase();let siguiente=estado==='recibido'?'preparando':estado==='preparando'?'listo_para_recoger':estado==='listo_para_recoger'?'entregado':'';let etiqueta=siguiente==='preparando'?'Preparar':siguiente==='listo_para_recoger'?'Marcar listo':'Entregar';let botones=siguiente?'<button class="btn" style="width:auto;padding:6px 10px;margin-left:8px" data-pedido="'+encodeURIComponent(p.id)+'" data-estado="'+siguiente+'" onclick="cambiarEstadoDesdeBoton(this)">'+etiqueta+'</button>':'';botones+='<button class="btn btn-danger" style="width:auto;padding:6px 10px;margin-left:8px" data-pedido="'+encodeURIComponent(p.id)+'" data-estado="cancelado" onclick="cambiarEstadoDesdeBoton(this)">Cancelar</button>';return '<div style="padding:10px 0;border-bottom:1px solid #e2e8f0"><b>Pedido #'+escapeManagerHtml(p.id)+'</b> — '+escapeManagerHtml(p.cliente)+'<br>'+escapeManagerHtml(p.productos)+'<br>Estado: <b>'+escapeManagerHtml(estado)+'</b> · $'+Number(p.total||0).toLocaleString()+botones+'</div>';}).join('')||'No hay pedidos pendientes.';}).catch(()=>document.getElementById('manager-pedidos').innerText='No se pudieron cargar los pedidos.');}
                function cambiarEstadoDesdeBoton(el){cambiarEstadoPedido(decodeURIComponent(el.dataset.pedido),el.dataset.estado);}
                function cambiarEstadoPedido(id,estado){fetch('/api/pedidos/'+encodeURIComponent(id)+'/estado',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({estado})}).then(r=>r.json()).then(d=>{if(d.status!=='ok'){alert(d.error||d.mensaje||'No se pudo actualizar el pedido.');return;}cargarPedidosManager();cargarResumenManager();}).catch(()=>alert('No se pudo actualizar el pedido.'));}
                document.addEventListener('DOMContentLoaded',()=>{cargarResumenManager();cargarAlertasManager();cargarPedidosManager();});
            </script>
        </div>
    </div>
</body>
</html>
"""

# DASHBOARD EMPLEADO ROBUSTO Y AMPLIADO CON CONTROL DE ERRORES Y ESTABILIDAD
HTML_DASHBOARD_EMPLEADO = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Caja / Empleado - {{ user.sede }}</title>
    <style>{{ css | safe }}</style>
    <script>
        let carritoCaja = [];

        // Función ampliada y optimizada con manejo avanzado de excepciones y feedback visual
        function buscarPorCodigoRapido(event) {
            if(event) event.preventDefault();
            let inputEl = document.getElementById('input-codigo-rapido');
            let codigo = inputEl.value.trim();
            
            if(!codigo) {
                console.warn('Código vacío ingresado');
                return;
            }

            // Petición AJAX robusta con control de red
            fetch('/api/buscar-codigo?codigo=' + encodeURIComponent(codigo))
                .then(res => {
                    if (!res.ok) throw new Error('Respuesta de red fallida');
                    return res.json();
                })
                .then(data => {
                    if(data && data.encontrado && data.producto) {
                        carritoCaja.push(data.producto);
                        actualizarCajaUI();
                        inputEl.value = '';
                        inputEl.focus();
                    } else {
                        alert('❌ Producto con código #' + codigo + ' no encontrado en esta sede.');
                        inputEl.value = '';
                        inputEl.focus();
                    }
                })
                .catch(err => {
                    console.error('Error detallado al buscar código rápido:', err);
                    alert('⚠️ Error al conectar con el servidor de inventario. Verifique su conexión.');
                    inputEl.focus();
                });
        }

        function quitarItemCaja(index) {
            if(index > -1 && index < carritoCaja.length) {
                carritoCaja.splice(index, 1);
                actualizarCajaUI();
            }
        }

        function actualizarCajaUI() {
            let total = carritoCaja.reduce((sum, p) => sum + (p.precio || 0), 0);
            let totalEl = document.getElementById('caja-total');
            if(totalEl) {
                totalEl.innerText = '$' + total.toLocaleString();
            }

            let html = '';
            carritoCaja.forEach((p, idx) => {
                html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #e2e8f0;">
                    <span>[#${p.codigo}] ${p.nombre}</span>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <b>$${(p.precio || 0).toLocaleString()}</b>
                        <button type="button" class="btn-remove" onclick="quitarItemCaja(${idx})">❌</button>
                    </div>
                </div>`;
            });
            
            let listaEl = document.getElementById('lista-caja-items');
            if(listaEl) {
                listaEl.innerHTML = html || '<p style="color:var(--gray-text);">Ningún producto agregado a la venta actual</p>';
            }
        }

        function cobrarVenta() {
            if(carritoCaja.length === 0) { 
                alert('Agregue productos usando el código rápido primero'); 
                return; 
            }
            let total = carritoCaja.reduce((sum, p) => sum + (p.precio || 0), 0);
            let nombres = carritoCaja.map(p => p.nombre).join(', ');

            fetch('/api/registrar-venta-cajero', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    productos: nombres,
                    items: carritoCaja.map(p => ({codigo: p.codigo, cantidad: 1})),
                    total: total,
                    sede: '{{ user.sede }}',
                    empleado: '{{ user.nombre }}'
                })
            })
            .then(res => res.json())
            .then(data => {
                if (!data || data.status !== 'ok') {
                    alert((data && data.mensaje) || 'No se pudo registrar la venta.');
                    return;
                }
                alert('✅ Venta registrada por $' + Number(data.total || 0).toLocaleString() + '!');
                carritoCaja = [];
                actualizarCajaUI();
            })
            .catch(err => {
                console.error('Error al registrar venta:', err);
                alert('Error al registrar la venta en el sistema.');
            });
        }
    </script>
</head>
<body>
    <div class="dashboard">
        <div class="sidebar">
            <div>
                <div class="brand">
                    <div class="logo">KI</div>
                    <h3>Caja Rápida</h3>
                </div>
                <a class="active">💻 Sistema de Caja</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión</a>
        </div>
        <div class="main">
            <div style="display:grid; grid-template-columns:2fr 1fr; gap:20px;">
                <div class="card">
                    <h2>Módulo de Caja - Búsqueda por Código Rápido</h2>
                    <p style="color:var(--gray-text); font-size:13px; margin-bottom:15px;">Introduce el código de 3 dígitos (Ej: 001, 006, 016, 026) para agregar el producto a la venta.</p>
                    
                    <form onsubmit="buscarPorCodigoRapido(event)" style="display:flex; gap:10px; margin-bottom:20px;">
                        <input type="text" id="input-codigo-rapido" placeholder="Ej: 001" maxlength="3" required autocomplete="off" style="padding:12px; font-size:18px; font-weight:bold; border:2px solid var(--primary); border-radius:8px; width:150px;">
                        <button type="submit" class="btn" style="margin:0; width:auto; padding:12px 25px;">🔍 Buscar y Agregar</button>
                    </form>

                    <h3>Productos Disponibles en Referencia Rápida:</h3>
                    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; margin-top:10px; max-height:300px; overflow-y:auto;">
                        {% for prod in inventario %}
                        <div style="background:#f8fafc; padding:10px; border-radius:8px; border:1px solid var(--gray); font-size:13px;">
                            <b>#{{ prod.codigo }}</b> - {{ prod.nombre }}<br>
                            <span style="color:var(--primary); font-weight:bold;">${{ "{:,.0f}".format(prod.precio) }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="card">
                    <h3>Ticket de Venta Actual</h3>
                    <div id="lista-caja-items" style="margin:15px 0; max-height:250px; overflow-y:auto;">
                        <p style="color:var(--gray-text);">Ningún producto agregado</p>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; font-size:18px; border-top:2px solid var(--gray); padding-top:10px;">
                        <span>Total:</span>
                        <b id="caja-total" style="color:var(--primary);">$0</b>
                    </div>
                    <button type="button" class="btn" onclick="cobrarVenta()" style="margin-top:15px;">💵 Cobrar Venta</button>
                </div>
            </div>

            <div class="card" style="margin-top:20px;">
                <h2>Reportar Problema o Incidencia al Manager</h2>
                <form action="/empleado/enviar-reporte" method="POST" style="margin-top:10px;">
                    <textarea name="mensaje" placeholder="Describe aquí si hay un problema en caja, falta de cambio, producto averiado..." required style="padding:12px; border:1px solid var(--gray); border-radius:8px; width:100%; height:80px;"></textarea>
                    <button type="submit" class="btn" style="width:auto; padding:10px 20px;">📤 Enviar Reporte al Supervisor</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

HTML_CLIENTE_UBICACION = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Selección de Ubicación - Cliente</title>
    <style>{{ css | safe }}</style>
    <script>
        function guardarSedeYContinuar(nombreSede, direccion) {
            fetch('/api/set-sede', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({sede: nombreSede, direccion: direccion})
            }).then(() => {
                window.location.href = '/cliente-auth';
            });
        }
    </script>
</head>
<body style="background:#f1f5f9; padding:40px 20px;">
    <div style="max-width:900px; margin:0 auto;" class="fade-in">
        <div class="brand" style="margin-bottom:20px;">
            <div class="logo">KI</div>
            <h2>Paso 1: Selecciona tu Sede de Supermercado Cercana</h2>
        </div>
        <p style="color:var(--gray-text); margin-bottom:25px;">Elige tu tienda habitual para gestionar tu mercado a domicilio o recoger en punto.</p>

        <div class="sede-selector-grid">
            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Principal (Centro)', 'Calle 10 # 5-20, Centro Comercial Central')">
                <div style="font-size:40px; margin-bottom:10px;">🏢</div>
                <h3>Sede Central</h3>
                <p style="color:var(--gray-text); font-size:13px;">Calle 10 # 5-20, Centro Comercial Central</p>
                <span style="color:var(--primary); font-weight:bold; font-size:13px; margin-top:10px; display:inline-block;">SELECCIONAR ESTA SEDE →</span>
            </div>

            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Norte (Plaza)', 'Av. Principal #102-15, Plaza Norte')">
                <div style="font-size:40px; margin-bottom:10px;">🏬</div>
                <h3>Sede Norte Plaza</h3>
                <p style="color:var(--gray-text); font-size:13px;">Av. Principal #102-15, Plaza Norte</p>
                <span style="color:var(--primary); font-weight:bold; font-size:13px; margin-top:10px; display:inline-block;">SELECCIONAR ESTA SEDE →</span>
            </div>

            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Sur (Express)', 'Carrera 45 #12-30, Portal Sur')">
                <div style="font-size:40px; margin-bottom:10px;">🏪</div>
                <h3>Sede Sur Express</h3>
                <p style="color:var(--gray-text); font-size:13px;">Carrera 45 #12-30, Portal Sur</p>
                <span style="color:var(--primary); font-weight:bold; font-size:13px; margin-top:10px; display:inline-block;">SELECCIONAR ESTA SEDE →</span>
            </div>
        </div>

        <a href="/" style="display:inline-block; margin-top:15px; color:var(--gray-text); text-decoration:none; font-size:14px;">← Cancelar y Volver</a>
    </div>
</body>
</html>
"""

HTML_CLIENTE_AUTH = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso Cliente - KeepInventoryLite</title>
    <style>{{ css | safe }}</style>
    <script>
        function alternarModo(modo) {
            if(modo === 'registro') {
                document.getElementById('form-login').style.display = 'none';
                document.getElementById('form-registro').style.display = 'block';
                document.getElementById('tab-login').classList.remove('btn');
                document.getElementById('tab-login').classList.add('btn-outline');
                document.getElementById('tab-registro').classList.add('btn');
                document.getElementById('tab-registro').classList.remove('btn-outline');
            } else {
                document.getElementById('form-registro').style.display = 'none';
                document.getElementById('form-login').style.display = 'block';
                document.getElementById('tab-registro').classList.remove('btn');
                document.getElementById('tab-registro').classList.add('btn-outline');
                document.getElementById('tab-login').classList.add('btn');
                document.getElementById('tab-login').classList.remove('btn-outline');
            }
        }
    </script>
</head>
<body>
    <div class="login-body">
        <div class="login-container fade-in">
            <div class="brand" style="justify-content:center;">
                <div class="logo">KI</div>
                <h2>Acceso Cliente</h2>
            </div>
            
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:8px 12px; border-radius:10px; margin-bottom:15px; font-size:12px; color:var(--primary-dark);">
                📍 Sede seleccionada: <b>{{ sede_seleccionada }}</b>
            </div>

            {% if error %}<div style="background:#fee2e2;color:#991b1b;padding:10px;border-radius:8px;margin-bottom:12px;">{{ error }}</div>{% endif %}
            <div style="display:flex; gap:10px; margin-bottom:15px;">
                <button id="tab-login" type="button" class="btn" onclick="alternarModo('login')" style="flex:1;">Ingresar</button>
                <button id="tab-registro" type="button" class="btn btn-outline" onclick="alternarModo('registro')" style="flex:1;">Registrarse</button>
            </div>

            <form id="form-login" action="/login-cliente" method="POST">
                <input type="email" name="email" placeholder="Tu correo electrónico" required>
                <input type="password" name="password" placeholder="Tu contraseña" required>
                <button type="submit" class="btn">🛒 Entrar a Hacer Mercado</button>
            </form>

            <form id="form-registro" action="/registro-cliente" method="POST" style="display:none;">
                <input type="text" name="nombre" placeholder="Nombre Completo" required>
                <input type="email" name="email" placeholder="Correo electrónico" required>
                <input type="password" name="password" placeholder="Crea una Contraseña" required>
                <button type="submit" class="btn">✨ Crear Cuenta y Comprar</button>
            </form>

            <a href="/cliente-ubicacion" style="display:block; margin-top:20px; color:var(--gray-text); text-decoration:none; font-size:13px;">← Cambiar de Sede</a>
        </div>
    </div>
</body>
</html>
"""

HTML_TIENDA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo de Supermercado - Cliente</title>
    <style>{{ css | safe }}</style>
    <script>
        let carrito = [];

        function agregarProducto(nombre, precio, codigo) {
            carrito.push({nombre, precio, codigo});
            actualizarCarritoUI();
        }

        function quitarProducto(index) {
            carrito.splice(index, 1);
            actualizarCarritoUI();
        }

        function actualizarCarritoUI() {
            document.getElementById('cart-count').innerText = carrito.length;
            let total = carrito.reduce((sum, p) => sum + p.precio, 0);
            document.getElementById('cart-total').innerText = '$' + total.toLocaleString();

            let listaHtml = '';
            carrito.forEach((p, index) => {
                listaHtml += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #e2e8f0;">
                    <span>${p.nombre}</span>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <b>$${p.precio.toLocaleString()}</b>
                        <button type="button" class="btn-remove" onclick="quitarProducto(${index})">❌</button>
                    </div>
                </div>`;
            });
            document.getElementById('cart-items').innerHTML = listaHtml || '<p style="color:var(--gray-text);">El carrito está vacío</p>';
        }

        function abrirCarrito() { 
            document.getElementById('modal-carrito').style.display = 'flex'; 
            document.getElementById('paso-carrito').style.display = 'block';
            document.getElementById('paso-pago').style.display = 'none';
        }

        function cerrarCarrito() { document.getElementById('modal-carrito').style.display = 'none'; }
        
        function irAPago() {
            if(carrito.length === 0) { alert('Añade productos de supermercado primero'); return; }
            let total = carrito.reduce((sum, p) => sum + p.precio, 0);
            document.getElementById('monto-pagar').innerText = '$' + total.toLocaleString();
            document.getElementById('paso-carrito').style.display = 'none';
            document.getElementById('paso-pago').style.display = 'block';
        }

        function seleccionarMetodoPago(metodo) {
            document.querySelectorAll('.payment-sec').forEach(el => el.style.display = 'none');
            if(metodo === 'tarjeta') {
                document.getElementById('pago-tarjeta').style.display = 'block';
            } else if(metodo === 'pse') {
                document.getElementById('pago-pse').style.display = 'block';
            } else if(metodo === 'nequi') {
                document.getElementById('pago-nequi').style.display = 'block';
            } else if(metodo === 'efectivo') {
                document.getElementById('pago-efectivo').style.display = 'block';
            }
        }

        function confirmarPagoFinal(metodoNombre) {
            let total = carrito.reduce((sum, p) => sum + p.precio, 0);
            let detallesItems = carrito.map(p => p.nombre).join(', ');

            fetch('/api/crear-pedido', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    cliente: '{{ cliente_nombre }}',
                    items: carrito.map(p => ({codigo: p.codigo, cantidad: 1})),
                    metodo_pago: metodoNombre
                })
            }).then(res => res.json()).then(data => {
                if (!data || data.status !== 'ok') { alert((data && data.mensaje) || 'No se pudo registrar el pedido.'); return; }
                alert((data.mensaje || ('Pedido registrado vía ' + metodoNombre + '.')) + '\\n\\nEste sitio registra el método seleccionado, pero no procesa cobros electrónicos hasta conectar una pasarela de pagos.');
                carrito = [];
                actualizarCarritoUI();
                cerrarCarrito();
            });
        }

        function filtrarCategoria(cat, btn) {
            document.querySelectorAll('.cat-btn').forEach(b => {
                b.classList.remove('btn');
                b.classList.add('btn-outline');
            });
            btn.classList.add('btn');
            btn.classList.remove('btn-outline');

            let productos = document.querySelectorAll('.product-card');
            productos.forEach(p => {
                if(cat === 'todos' || p.dataset.cat === cat) {
                    p.style.display = 'flex';
                } else {
                    p.style.display = 'none';
                }
            });
        }
    </script>
</head>
<body style="background:#f8fafc;">
    <div style="padding:25px; max-width:1200px; margin:0 auto;" class="fade-in">
        
        <div class="header-cliente">
            <div class="brand">
                <div class="logo">KI</div>
                <div>
                    <h2 style="font-size:20px;">Supermercados El Ahorro - Catálogo</h2>
                    <p style="font-size:12px; color:var(--gray-text);">Sede activa: <b>📍 {{ sede_actual }}</b></p>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:15px;">
                <span style="font-size:14px;">Hola, <b>{{ cliente_nombre }}</b></span>
                <a href="/mis-pedidos" class="btn btn-outline" style="padding:8px 12px; font-size:12px;">📦 Mis pedidos</a>
                <a href="/cliente-ubicacion" class="btn btn-outline" style="padding:8px 12px; font-size:12px;">📍 Cambiar Sede</a>
                <a href="/logout" class="btn btn-danger" style="padding:8px 12px; font-size:12px;">Cerrar Sesión</a>
            </div>
        </div>

        <div style="display:flex; gap:10px; margin-bottom:25px; overflow-x:auto; padding-bottom:5px;">
            <button type="button" class="btn cat-btn" onclick="filtrarCategoria('todos', this)">🏪 Todo el Mercado</button>
            <button type="button" class="btn btn-outline cat-btn" onclick="filtrarCategoria('lacteos', this)">🥛 Lácteos y Huevos</button>
            <button type="button" class="btn btn-outline cat-btn" onclick="filtrarCategoria('despensa', this)">🌾 Despensa y Granos</button>
            <button type="button" class="btn btn-outline cat-btn" onclick="filtrarCategoria('carnes', this)">🥩 Carnes y Embutidos</button>
            <button type="button" class="btn btn-outline cat-btn" onclick="filtrarCategoria('frutas', this)">🍎 Frutas y Verduras</button>
            <button type="button" class="btn btn-outline cat-btn" onclick="filtrarCategoria('bebidas', this)">🥤 Bebidas</button>
            <button type="button" class="btn btn-outline cat-btn" onclick="filtrarCategoria('aseo', this)">🧹 Aseo y Limpieza</button>
        </div>

        <div class="grid">
            <div class="product-card" data-cat="lacteos">
                <span class="product-badge">OFERTA</span>
                <div class="product-img-container"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVO8fktZ9PsqGMtJtLrIpxWMrEry8Zt100S55llzxX3Q&s=10" alt="Huevos AA x30 unidades"></div>
                <h3 style="font-size:16px;">Huevos Frescos AA x30 Unidades</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Cubeta de 30 huevos rojos categoría AA de granja.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$18.500</b>
                    <button type="button" class="btn" onclick="agregarProducto('Huevos Frescos AA x30', 18500, '001')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="lacteos">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&auto=format&fit=crop&q=80" alt="Leche Entera 1L Colanta"></div>
                <h3 style="font-size:16px;">Leche Entera Colanta 1L</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Leche pasteurizada enriquecida con vitaminas A y D.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$4.300</b>
                    <button type="button" class="btn" onclick="agregarProducto('Leche Entera Colanta 1L', 4300, '002')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="lacteos">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1452195100486-9cc805987862?w=400&auto=format&fit=crop&q=80" alt="Queso Campesino 500g"></div>
                <h3 style="font-size:16px;">Queso Campesino Fresco 500g</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Queso blanco tajado, ideal para desayunos y arepas.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$12.800</b>
                    <button type="button" class="btn" onclick="agregarProducto('Queso Campesino 500g', 12800, '003')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="despensa">
                <span class="product-badge">MAS VENDIDO</span>
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&auto=format&fit=crop&q=80" alt="Arroz Roa 1Kg"></div>
                <h3 style="font-size:16px;">Arroz Roa Superior 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Arroz blanco de grano entero de la más alta calidad.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$4.800</b>
                    <button type="button" class="btn" onclick="agregarProducto('Arroz Roa Superior 1Kg', 4800, '006')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="despensa">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&auto=format&fit=crop&q=80" alt="Aceite Premier 900ml"></div>
                <h3 style="font-size:16px;">Aceite Vegetal Premier 900ml</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Aceite puro libre de grasas trans para cocinar diariamente.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$14.500</b>
                    <button type="button" class="btn" onclick="agregarProducto('Aceite Vegetal Premier 900ml', 14500)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="despensa">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=400&auto=format&fit=crop&q=80" alt="Pasta Espagueti Doria 500g"></div>
                <h3 style="font-size:16px;">Pasta Espagueti Doria 500g</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Pasta tradicional fortificada con hierro y nutrición.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$3.800</b>
                    <button type="button" class="btn" onclick="agregarProducto('Pasta Espagueti Doria 500g', 3800, '012')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="carnes">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=400&auto=format&fit=crop&q=80" alt="Pechuga de Pollo 1Kg"></div>
                <h3 style="font-size:16px;">Pechuga de Pollo Entera 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Pechuga limpia, fresca y refrigerada de primera opción.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$16.900</b>
                    <button type="button" class="btn" onclick="agregarProducto('Pechuga de Pollo 1Kg', 16900, '016')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="carnes">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1588168333986-5078d3ae3976?w=400&auto=format&fit=crop&q=80" alt="Carne Molida 1Kg"></div>
                <h3 style="font-size:16px;">Carne Molida de Res 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Corte de res magro molido al día sin conservantes.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$24.500</b>
                    <button type="button" class="btn" onclick="agregarProducto('Carne Molida de Res 1Kg', 24500, '017')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="frutas">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=400&auto=format&fit=crop&q=80" alt="Aguacate Hass 1Kg"></div>
                <h3 style="font-size:16px;">Aguacate Hass Selección 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Aguacates cremosos y perfectos para madurar.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$8.900</b>
                    <button type="button" class="btn" onclick="agregarProducto('Aguacate Hass 1Kg', 8900, '021')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="frutas">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&auto=format&fit=crop&q=80" alt="Manzana Roja 1Kg"></div>
                <h3 style="font-size:16px;">Manzana Roja Importada 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Manzanas crujientes y dulces seleccionadas.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$9.500</b>
                    <button type="button" class="btn" onclick="agregarProducto('Manzana Roja 1Kg', 9500, '025')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="bebidas">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&auto=format&fit=crop&q=80" alt="Café Sello Rojo 500g"></div>
                <h3 style="font-size:16px;">Café Sello Rojo Molido 500g</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Café 100% colombiano de tueste medio y gran aroma.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$18.900</b>
                    <button type="button" class="btn" onclick="agregarProducto('Café Sello Rojo 500g', 18900, '026')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="bebidas">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400&auto=format&fit=crop&q=80" alt="Coca-Cola 1.5L"></div>
                <h3 style="font-size:16px;">Coca-Cola Sabor Original 1.5L</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Gaseosa refrescante ideal para acompañar tus comidas.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$6.200</b>
                    <button type="button" class="btn" onclick="agregarProducto('Coca-Cola 1.5L', 6200, '027')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="aseo">
                <div class="product-img-container"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQxsUE3LQsQMoxScMRP2K-RuDYFVLafI9H-mJXnETKUKTCTBl0bkF_vPIlh&s=10" alt="Detergente Ariel 2Kg"></div>
                <h3 style="font-size:16px;">Detergente en Polvo Ariel 2Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Limpieza profunda y remoce de manchas difíciles en la ropa.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$26.900</b>
                    <button type="button" class="btn" onclick="agregarProducto('Detergente Ariel 2Kg', 26900, '030')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="aseo">
                <div class="product-img-container"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTEvjy-zrI9DcLCFmEKgE1NFuS60y0_AE8FFKuY6ybZFg&s" alt="Papel Higiénico Familia 12 Rollos"></div>
                <h3 style="font-size:16px;">Papel Higiénico Familia 12 Rollos</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Rendidor, doble hoja acolchada y suavidad superior.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$22.500</b>
                    <button type="button" class="btn" onclick="agregarProducto('Papel Higiénico Familia x12', 22500, '032')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            {% for prod in productos_dinamicos %}
            <div class="product-card" data-cat="todos">
                <span class="product-badge">NUEVO (#{{ prod.codigo }})</span>
                <div class="product-img-container">
                    <img src="{{ prod.imagen or 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400&auto=format&fit=crop&q=80' }}" alt="{{ prod.nombre }}">
                </div>
                <h3 style="font-size:16px;">{{ prod.nombre }}</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Producto añadido recientemente a esta sede.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">${{ "{:,.0f}".format(prod.precio) }}</b>
                    <button type="button" class="btn" onclick="agregarProducto('{{ prod.nombre }}', {{ prod.precio }}, '{{ prod.codigo }}')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>
            {% endfor %}

        </div>
    </div>

    <div class="cart-floating-btn" onclick="abrirCarrito()">
        🛒 Carrito de Mercado (<span id="cart-count">0</span>)
    </div>

    <div id="modal-carrito" class="modal">
        <div class="modal-content">
            
            <div id="paso-carrito">
                <h3>Tu Pedido - <span style="color:var(--primary);">{{ sede_actual }}</span></h3>
                <div id="cart-items" style="margin:20px 0; max-height:220px; overflow-y:auto;">
                    <p style="color:var(--gray-text);">El carrito está vacío</p>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:18px; border-top:2px solid var(--gray); padding-top:10px;">
                    <span>Total a Pagar:</span>
                    <b id="cart-total" style="color:var(--primary);">$0</b>
                </div>
                <button type="button" class="btn" onclick="irAPago()" style="margin-top:20px;">💳 Proceder al Pago Seguro</button>
                <button type="button" class="btn btn-outline" onclick="cerrarCarrito()" style="margin-top:8px;">Seguir Mercando</button>
            </div>

            <div id="paso-pago" style="display:none;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <h3>Selecciona Método de Pago</h3>
                    <b id="monto-pagar" style="color:var(--primary); font-size:18px;">$0</b>
                </div>
                <p style="font-size:13px; color:var(--gray-text); margin-bottom:15px;">Pasarela integrada simulada (Rellena con datos ficticios)</p>

                <div class="payment-method-box" onclick="seleccionarMetodoPago('tarjeta')">
                    <b>💳 Tarjeta de Crédito / Débito</b>
                    <p style="font-size:12px; color:var(--gray-text);">Visa, Mastercard, American Express</p>
                </div>
                <div class="payment-method-box" onclick="seleccionarMetodoPago('pse')">
                    <b>🏦 PSE (Pagos Seguros en Línea)</b>
                    <p style="font-size:12px; color:var(--gray-text);">Debita directo de tu cuenta bancaria</p>
                </div>
                <div class="payment-method-box" onclick="seleccionarMetodoPago('nequi')">
                    <b>📱 Nequi / Daviplata</b>
                    <p style="font-size:12px; color:var(--gray-text);">Billetera digital rápida</p>
                </div>
                <div class="payment-method-box" onclick="seleccionarMetodoPago('efectivo')">
                    <b>💵 Pago contra entrega (Efectivo)</b>
                    <p style="font-size:12px; color:var(--gray-text);">Paga al recibir en la puerta</p>
                </div>

                <div id="pago-tarjeta" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Datos de la Tarjeta (Inventados)</p>
                    <input type="text" placeholder="Número de Tarjeta" value="4532 8821 9012 3456" style="padding:10px; font-size:13px;">
                    <div style="display:flex; gap:10px;">
                        <input type="text" placeholder="MM/AA" value="12/28" style="padding:10px; font-size:13px;">
                        <input type="text" placeholder="CVV" value="482" style="padding:10px; font-size:13px;">
                    </div>
                    <button type="button" class="btn" onclick="confirmarPagoFinal('Tarjeta de Crédito')">Pagar Mercado</button>
                </div>

                <div id="pago-pse" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Conexión Bancaria PSE (Inventado)</p>
                    <select style="padding:10px; font-size:13px; width:100%; border:1px solid var(--gray); border-radius:8px; margin-bottom:10px;">
                        <option>Bancolombia (Demo)</option>
                        <option>Banco de Bogotá (Demo)</option>
                        <option>Davivienda (Demo)</option>
                        <option>BBVA Colombia (Demo)</option>
                    </select>
                    <input type="text" placeholder="Correo electrónico asociado" value="cliente.demo@correo.com" style="padding:10px; font-size:13px;">
                    <button type="button" class="btn" onclick="confirmarPagoFinal('PSE Bancario')">Autorizar Pago en Banco</button>
                </div>

                <div id="pago-nequi" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Billetera Móvil (Inventado)</p>
                    <input type="text" placeholder="Número Celular" value="312 456 7890" style="padding:10px; font-size:13px;">
                    <button type="button" class="btn" onclick="confirmarPagoFinal('Nequi/Daviplata')">Generar Notificación Push</button>
                </div>

                <div id="pago-efectivo" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Pago contra entrega</p>
                    <input type="text" placeholder="¿Con cuánto dinero vas a pagar?" value="$100.000" style="padding:10px; font-size:13px;">
                    <button type="button" class="btn" onclick="confirmarPagoFinal('Efectivo contra entrega')">Confirmar Mercado</button>
                </div>

                <button type="button" class="btn btn-outline" onclick="abrirCarrito()" style="margin-top:15px;">← Volver al Carrito</button>
            </div>

        </div>
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Panel - Staff</title>
    <style>{{ css | safe }}</style>
    <script>
        function cambiarSeccion(idSeccion, elemento) {
            document.querySelectorAll('.seccion-tab').forEach(sec => sec.style.display = 'none');
            document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove('active'));
            document.getElementById(idSeccion).style.display = 'block';
            elemento.classList.add('active');
        }

        function agregarNuevoProducto(event) {
            event.preventDefault();
            let nombre = document.getElementById('prod-nombre').value;
            let sede = document.getElementById('prod-sede').value;
            let stock = document.getElementById('prod-stock').value;

            let tabla = document.getElementById('tabla-inventario');
            let nuevaFila = `<tr>
                <td><b>${nombre}</b></td>
                <td>${sede}</td>
                <td>${stock} unidades</td>
                <td><span class="tag tag-empleado">Disponible</span></td>
            </tr>`;
            tabla.innerHTML += nuevaFila;
            alert('¡Producto agregado al stock!');
            document.getElementById('form-prod').reset();
        }

        function cargarPedidosEnTiempoReal() {
            fetch('/api/pedidos')
                .then(res => res.json())
                .then(pedidos => {
                    let tabla = document.getElementById('tabla-pedidos-realtime');
                    document.getElementById('total-pedidos-count').innerText = pedidos.length;
                    
                    if(pedidos.length === 0) {
                        tabla.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--gray-text);">No hay pedidos recientes</td></tr>';
                        return;
                    }

                    let html = '';
                    pedidos.forEach(p => {
                        html += `<tr>
                            <td><b>${p.hora}</b></td>
                            <td>${p.cliente}</td>
                            <td>${p.sede}</td>
                            <td>${p.productos}</td>
                            <td><span class="tag" style="background:#3b82f6;">${p.metodo_pago || 'Tarjeta'}</span></td>
                            <td><b style="color:var(--primary);">$${p.total.toLocaleString()}</b></td>
                        </tr>`;
                    });
                    tabla.innerHTML = html;
                });
        }

        setInterval(cargarPedidosEnTiempoReal, 10000);
        window.onload = cargarPedidosEnTiempoReal;
    </script>
</head>
<body>
    <div class="dashboard">
        <div class="sidebar">
            <div>
                <div class="brand">
                    <div class="logo">KI</div>
                    <h3>KeepInventory</h3>
                </div>
                <a onclick="cambiarSeccion('panel', this)" class="active">📊 Panel Principal</a>
                <a onclick="cambiarSeccion('pedidos-live', this)">🔴 Pedidos (<span id="total-pedidos-count">0</span>)</a>
                <a onclick="cambiarSeccion('inventario', this)">📦 Control de Stock</a>
                <a onclick="cambiarSeccion('sedes', this)">🏪 Puntos de Venta</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión</a>
        </div>

        <div class="main">
            <div id="panel" class="seccion-tab fade-in">
                <div class="card">
                    <h2>Panel Administrativo General</h2>
                    <p style="color:var(--gray-text);">Monitoreo general del sistema KeepInventoryLite.</p>
                </div>
            </div>
            <div id="pedidos-live" class="seccion-tab fade-in" style="display:none;">
                <div class="card">
                    <h2>🔴 Órdenes en Tiempo Real</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Hora Local</th><th>Cliente</th><th>Sede</th><th>Productos</th><th>Pago</th><th>Total</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-pedidos-realtime">
                            <tr><td colspan="6" style="text-align:center;">Cargando...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div id="inventario" class="seccion-tab fade-in" style="display:none;">
                <div class="card">
                    <h2>Inventario de Almacén</h2>
                    <form id="form-prod" onsubmit="agregarNuevoProducto(event)" style="display:grid; grid-template-columns:1fr 1fr 1fr auto; gap:10px; margin-top:15px;">
                        <input type="text" id="prod-nombre" placeholder="Nombre" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <select id="prod-sede" style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                            <option>Sede Central</option><option>Sede Norte</option><option>Sede Sur Express</option>
                        </select>
                        <input type="number" id="prod-stock" placeholder="Stock" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <button type="submit" class="btn" style="margin:0;">+ Guardar</button>
                    </form>
                    <table style="margin-top:15px;">
                        <thead><tr><th>Producto</th><th>Sede</th><th>Disponibilidad</th><th>Estado</th></tr></thead>
                        <tbody id="tabla-inventario">
                            <tr><td>Arroz Roa Blanco 1Kg</td><td>Sede Central</td><td>350 unidades</td><td><span class="tag tag-empleado">Disponible</span></td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            <div id="sedes" class="seccion-tab fade-in" style="display:none;">
                <div class="card"><h2>Puntos de Distribución</h2></div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Protección CSRF para formularios y solicitudes JSON del mismo sitio.
@app.context_processor
def inyectar_token_csrf():
    if not session.get('_csrf_token'):
        session['_csrf_token'] = secrets.token_urlsafe(32)
    return {'csrf_token': session.get('_csrf_token')}

@app.before_request
def proteger_solicitudes_modificadoras():
    if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
        return None
    token_sesion = session.get('_csrf_token')
    token_recibido = request.headers.get('X-CSRF-Token')
    if not token_recibido:
        token_recibido = request.form.get('_csrf_token')
    if not token_sesion or not token_recibido or not hmac.compare_digest(str(token_sesion), str(token_recibido)):
        return jsonify({'status': 'error', 'mensaje': 'Solicitud rechazada por protección de seguridad. Recarga la página e inténtalo de nuevo.'}), 400
    return None

# Se agrega el campo oculto a los formularios POST sin cambiar su diseño y un
# envoltorio fetch que envía el token automáticamente en las peticiones AJAX.
for _nombre_template in [n for n in globals() if n.startswith('HTML_') and isinstance(globals().get(n), str)]:
    _html_template = globals()[_nombre_template]
    _html_template = re.sub(
        r'(<form\b(?=[^>]*\bmethod\s*=\s*[\"\']POST[\"\'])[^>]*>)',
        r'\1\n<input type="hidden" name="_csrf_token" value="{{ csrf_token }}">',
        _html_template, flags=re.IGNORECASE
    )
    _script_csrf = """<script>(function(){const token='{{ csrf_token }}';const originalFetch=window.fetch.bind(window);window.fetch=function(input,init){init=init||{};const method=String(init.method||'GET').toUpperCase();if(['POST','PUT','PATCH','DELETE'].includes(method)){const headers=new Headers(init.headers||{});headers.set('X-CSRF-Token',token);init=Object.assign({},init,{headers:headers});}return originalFetch(input,init);};})();</script>"""
    _html_template = _html_template.replace('</head>', _script_csrf + '\n</head>', 1)
    globals()[_nombre_template] = _html_template
del _nombre_template, _html_template, _script_csrf

@app.route('/')
def inicio():
    return render_template_string(HTML_LANDING, css=CSS_ESTILOS)

@app.route('/login-staff', methods=['GET', 'POST'])
def login_staff():
    error = None
    if request.method == 'POST':
        usuario = request.form.get('usuario', '').strip().lower()[:254]
        password = request.form.get('password', '')
        ahora = time.time()
        intentos = LOGIN_INTENTOS.get(usuario, {"cantidad": 0, "hasta": 0})
        if intentos.get("hasta", 0) > ahora:
            error = "Demasiados intentos. Espera unos minutos e inténtalo de nuevo."
        else:
            autenticado = False
            if ADMIN_EMAIL and ADMIN_PASSWORD and usuario == ADMIN_EMAIL.lower() and secrets.compare_digest(str(password), str(ADMIN_PASSWORD)):
                session.clear()
                session.permanent = True
                session['user_type'] = 'superadmin'
                LOGIN_INTENTOS.pop(usuario, None)
                _auditar("Inicio de sesión", "Acceso de superadministrador")
                guardar_estado()
                return redirect(url_for('superadmin_dashboard'))
            for emp in EMPRESAS_REGISTRADAS:
                if emp['email_dueno'].lower() == usuario and _verificar_password(emp['password_dueno'], password):
                    if not str(emp['password_dueno']).startswith(("pbkdf2:", "scrypt:")):
                        emp['password_dueno'] = _hash_password(password)
                    session.clear()
                    session.permanent = True
                    session['user_type'] = 'dueno'
                    session['empresa_id'] = emp['id']
                    session['empresa_nombre'] = emp['nombre_empresa']
                    autenticado = True
                    destino = 'dueno_dashboard'
                    break
                staff = next((st for st in emp['usuarios_staff'] if st['email'].lower() == usuario and _verificar_password(st['password'], password)), None)
                if staff:
                    if not str(staff['password']).startswith(("pbkdf2:", "scrypt:")):
                        staff['password'] = _hash_password(password)
                    session.clear()
                    session.permanent = True
                    session['user_type'] = staff['rol']
                    session['user_nombre'] = staff['nombre']
                    session['user_sede'] = staff['sede']
                    session['empresa_nombre'] = emp['nombre_empresa']
                    session['empresa_id'] = emp['id']
                    autenticado = True
                    destino = 'manager_dashboard' if staff['rol'] == 'manager' else 'empleado_dashboard'
                    break
            if autenticado:
                LOGIN_INTENTOS.pop(usuario, None)
                _auditar("Inicio de sesión", "Acceso correcto")
                guardar_estado()
                return redirect(url_for(destino))
            intentos['cantidad'] = intentos.get('cantidad', 0) + 1
            intentos['hasta'] = ahora + (300 if intentos['cantidad'] >= 5 else 0)
            LOGIN_INTENTOS[usuario] = intentos
            error = "Credenciales incorrectas o usuario no encontrado"
    return render_template_string(HTML_LOGIN_STAFF, css=CSS_ESTILOS, error=error, mostrar_demo=(not DESHABILITAR_DEMO and os.getenv('SHOW_DEMO_CREDENTIALS', '0') == '1'))

@app.route('/superadmin/dashboard')
def superadmin_dashboard():
    if session.get('user_type') != 'superadmin':
        return redirect(url_for('login_staff'))
    return render_template_string(HTML_DASHBOARD_SUPERADMIN, css=CSS_ESTILOS, empresas=EMPRESAS_REGISTRADAS)

@app.route('/superadmin/crear-empresa', methods=['POST'])
def superadmin_crear_empresa():
    if session.get('user_type') != 'superadmin':
        return redirect(url_for('login_staff'))
    nombre = request.form.get('nombre_empresa', '').strip()[:150]
    email = request.form.get('email_dueno', '').strip().lower()
    password = request.form.get('password_dueno', '')
    if not nombre or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(password) < 8:
        return redirect(url_for('superadmin_dashboard'))
    correos = [e.get('email_dueno', '').lower() for e in EMPRESAS_REGISTRADAS]
    correos += [u.get('email', '').lower() for e in EMPRESAS_REGISTRADAS for u in e.get('usuarios_staff', [])]
    if email in correos:
        return redirect(url_for('superadmin_dashboard'))
    nueva_empresa = {
        "id": max([int(e.get('id', 0)) for e in EMPRESAS_REGISTRADAS] + [0]) + 1,
        "nombre_empresa": nombre,
        "email_dueno": email,
        "password_dueno": _hash_password(password),
        "sedes": [],
        "usuarios_staff": []
    }
    EMPRESAS_REGISTRADAS.append(nueva_empresa)
    _auditar("Crear empresa", nueva_empresa["nombre_empresa"], empresa=nueva_empresa["nombre_empresa"])
    guardar_estado()
    return redirect(url_for('superadmin_dashboard'))

@app.route('/dueno/dashboard')
def dueno_dashboard():
    if session.get('user_type') != 'dueno':
        return redirect(url_for('login_staff'))
    emp_id = session.get('empresa_id')
    empresa = next((e for e in EMPRESAS_REGISTRADAS if e['id'] == emp_id), EMPRESAS_REGISTRADAS[0])
    pedidos_empresa = [p for p in PEDIDOS_REGISTRADOS if p.get('empresa') == empresa['nombre_empresa']]
    return render_template_string(HTML_DASHBOARD_DUENO, css=CSS_ESTILOS, empresa=empresa, pedidos_empresa=pedidos_empresa)

@app.route('/dueno/crear-sede', methods=['POST'])
def dueno_crear_sede():
    if session.get('user_type') != 'dueno':
        return redirect(url_for('login_staff'))
    emp_id = session.get('empresa_id')
    empresa = next((e for e in EMPRESAS_REGISTRADAS if e['id'] == emp_id), EMPRESAS_REGISTRADAS[0])
    nombre_sede = request.form.get('nombre_sede', '').strip()[:120]
    direccion_sede = request.form.get('direccion_sede', '').strip()[:250]
    if not nombre_sede or not direccion_sede or any(s.get('nombre', '').lower() == nombre_sede.lower() for e in EMPRESAS_REGISTRADAS if e.get('id') == emp_id for s in e.get('sedes', [])):
        return redirect(url_for('dueno_dashboard'))
    empresa['sedes'].append({"nombre": nombre_sede, "direccion": direccion_sede})
    _auditar("Crear sede", nombre_sede)
    guardar_estado()
    return redirect(url_for('dueno_dashboard'))

@app.route('/dueno/crear-personal', methods=['POST'])
def dueno_crear_personal():
    if session.get('user_type') != 'dueno':
        return redirect(url_for('login_staff'))
    emp_id = session.get('empresa_id')
    empresa = next((e for e in EMPRESAS_REGISTRADAS if e['id'] == emp_id), EMPRESAS_REGISTRADAS[0])
    if not request.form.get('nombre', '').strip() or not request.form.get('email', '').strip() or len(request.form.get('password', '')) < 8:
        return redirect(url_for('dueno_dashboard'))
    if any(u.get('email', '').lower() == request.form.get('email', '').strip().lower() for e in EMPRESAS_REGISTRADAS for u in e.get('usuarios_staff', [])) or any(e.get('email_dueno', '').lower() == request.form.get('email', '').strip().lower() for e in EMPRESAS_REGISTRADAS):
        return redirect(url_for('dueno_dashboard'))
    if request.form.get('sede') not in [s.get('nombre') for s in empresa.get('sedes', [])]:
        return redirect(url_for('dueno_dashboard'))
    empresa['usuarios_staff'].append({
        "nombre": request.form.get('nombre', '').strip()[:120],
        "email": request.form.get('email'),
        "password": _hash_password(request.form.get('password', '')),
        "rol": request.form.get('rol') if request.form.get('rol') in ('manager', 'empleado') else 'empleado',
        "sede": request.form.get('sede')
    })
    _auditar("Crear personal", request.form.get('email', ''))
    guardar_estado()
    return redirect(url_for('dueno_dashboard'))

@app.route('/dueno/eliminar-personal', methods=['POST'])
def dueno_eliminar_personal():
    if session.get('user_type') != 'dueno':
        return redirect(url_for('login_staff'))
    email_eliminar = request.form.get('email')
    emp_id = session.get('empresa_id')
    empresa = next((e for e in EMPRESAS_REGISTRADAS if e['id'] == emp_id), EMPRESAS_REGISTRADAS[0])
    empresa['usuarios_staff'] = [s for s in empresa['usuarios_staff'] if s['email'] != email_eliminar]
    _auditar("Eliminar personal", email_eliminar or '')
    guardar_estado()
    return redirect(url_for('dueno_dashboard'))

@app.route('/manager/dashboard')
def manager_dashboard():
    if session.get('user_type') != 'manager':
        return redirect(url_for('login_staff'))
    user_sede = session.get('user_sede')
    inv_sede = [i for i in INVENTARIO_SUPER if i.get('sede') == user_sede and i.get('empresa') == session.get('empresa_nombre')]
    rep_sede = [r for r in REPORTES_EMPLEADOS if r.get('sede') == user_sede and r.get('empresa', session.get('empresa_nombre')) == session.get('empresa_nombre')]
    error = request.args.get('error')
    return render_template_string(HTML_DASHBOARD_MANAGER, css=CSS_ESTILOS, user={'sede': user_sede}, inventario=inv_sede, reportes=rep_sede, error=error)

@app.route('/manager/agregar-producto', methods=['POST'])
def manager_agregar_producto():
    if session.get('user_type') != 'manager':
        return redirect(url_for('login_staff'))
    
    codigo = request.form.get('codigo', '').strip()
    user_sede = session.get('user_sede')
    nombre = request.form.get('nombre', '').strip()
    imagen = request.form.get('imagen', '').strip()
    try:
        precio = float(request.form.get('precio', 0))
        stock = int(request.form.get('stock', 0))
    except (ValueError, TypeError):
        return redirect(url_for('manager_dashboard', error='El precio y el stock deben ser valores numéricos válidos.'))
    if not re.fullmatch(r'\d{3}', codigo) or not nombre or precio <= 0 or stock < 0:
        return redirect(url_for('manager_dashboard', error='Verifica el código, nombre, precio y stock del producto.'))
    if imagen and not re.match(r'^https://', imagen, re.IGNORECASE):
        return redirect(url_for('manager_dashboard', error='La imagen debe usar una dirección HTTPS válida.'))
    codigo_repetido = any(i['codigo'] == codigo and i['sede'] == user_sede and i.get('empresa') == session.get('empresa_nombre') for i in INVENTARIO_SUPER)
    if codigo_repetido:
        return redirect(url_for('manager_dashboard', error=f"El código rápido #{codigo} ya está registrado en esta sede. Usa uno diferente."))

    INVENTARIO_SUPER.append({
        "codigo": codigo,
        "nombre": nombre[:160],
        "precio": precio,
        "stock": stock,
        "sede": user_sede,
        "empresa": session.get('empresa_nombre'),
        "imagen": imagen
    })
    MOVIMIENTOS_INVENTARIO.insert(0, {"fecha": obtener_tiempo_local(), "codigo": codigo, "producto": nombre, "sede": user_sede, "empresa": session.get('empresa_nombre'), "tipo": "alta", "cantidad": stock, "motivo": "Registro de producto", "usuario": session.get('user_nombre', 'Manager')})
    _auditar("Crear producto", f"{codigo} - {nombre}")
    if stock <= 5:
        _notificar("stock_bajo", f"El producto {nombre} tiene solo {stock} unidades.")
    guardar_estado()
    return redirect(url_for('manager_dashboard'))

@app.route('/empleado/dashboard')
def empleado_dashboard():
    if session.get('user_type') != 'empleado':
        return redirect(url_for('login_staff'))
    user_sede = session.get('user_sede')
    inv_sede = [i for i in INVENTARIO_SUPER if i.get('sede') == user_sede and i.get('empresa') == session.get('empresa_nombre')]
    return render_template_string(HTML_DASHBOARD_EMPLEADO, css=CSS_ESTILOS, user={'nombre': session.get('user_nombre'), 'sede': user_sede}, inventario=inv_sede)

@app.route('/api/buscar-codigo', methods=['GET'])
def buscar_codigo():
    if session.get('user_type') != 'empleado':
        return jsonify({'encontrado': False, 'mensaje': 'No autorizado.'}), 403
    codigo = request.args.get('codigo', '').strip()
    user_sede = session.get('user_sede', 'Sede Central')
    producto = next((i for i in INVENTARIO_SUPER if i['codigo'] == codigo and i['sede'] == user_sede and i.get('empresa') == session.get('empresa_nombre')), None)
    if producto:
        return jsonify({'encontrado': True, 'producto': producto})
    return jsonify({'encontrado': False})

@app.route('/api/registrar-venta-cajero', methods=['POST'])
def registrar_venta_cajero():
    if session.get('user_type') != 'empleado':
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    data = request.get_json(silent=True) or {}
    try:
        detalle, total = procesar_items_inventario(data.get('items'), session.get('user_sede'), session.get('empresa_nombre'), descontar=True)
    except ValueError as exc:
        return jsonify({'status': 'error', 'mensaje': str(exc)}), 400
    nuevo_pedido = {
        'id': secrets.token_hex(8), 'hora': obtener_tiempo_local(),
        'cliente': session.get('user_nombre', 'Cajero'), 'empleado': session.get('user_nombre'),
        'sede': session.get('user_sede'), 'productos': ', '.join(f"{x['nombre']} x{x['cantidad']}" for x in detalle),
        'items': detalle, 'total': total, 'metodo_pago': 'Caja Registradora',
        'empresa': session.get('empresa_nombre'), 'tipo': 'venta', 'estado': 'entregado',
        'inventario_descontado': True, 'actualizado_en': obtener_tiempo_local()
    }
    PEDIDOS_REGISTRADOS.insert(0, nuevo_pedido)
    _auditar('Venta registrada', f"{nuevo_pedido['id']} / ${total}")
    guardar_estado()
    return jsonify({'status': 'ok', 'pedido_id': nuevo_pedido['id'], 'total': total, 'productos': nuevo_pedido['productos']})

@app.route('/empleado/enviar-reporte', methods=['POST'])
def empleado_enviar_reporte():
    if session.get('user_type') != 'empleado':
        return redirect(url_for('login_staff'))
    mensaje = request.form.get('mensaje', '').strip()[:1000]
    if not mensaje:
        return redirect(url_for('empleado_dashboard'))
    REPORTES_EMPLEADOS.insert(0, {
        'id': secrets.token_hex(8), 'fecha': obtener_tiempo_local(), 'empleado': session.get('user_nombre'),
        'sede': session.get('user_sede'), 'empresa': session.get('empresa_nombre'), 'mensaje': mensaje,
        'estado': 'pendiente', 'respuesta_manager': '', 'resuelto': False
    })
    _notificar("reporte_empleado", f"Nuevo reporte de {session.get('user_nombre')}: {mensaje}")
    _auditar("Enviar reporte", mensaje)
    guardar_estado()
    return redirect(url_for('empleado_dashboard'))

@app.route('/cliente-ubicacion')
def cliente_ubicacion():
    return render_template_string(HTML_CLIENTE_UBICACION, css=CSS_ESTILOS)

@app.route('/api/set-sede', methods=['POST'])
def set_sede():
    data = request.get_json(silent=True) or {}
    sede_solicitada = str(data.get('sede', '')).strip()
    direccion = str(data.get('direccion', '')).strip()[:250]
    equivalencias = {'Sede Principal (Centro)': 'Sede Central', 'Sede Norte (Plaza)': 'Sede Norte', 'Sede Sur (Express)': 'Sede Sur Express', 'Sede Norte Plaza': 'Sede Norte', 'Sede Central': 'Sede Central', 'Sede Norte': 'Sede Norte', 'Sede Sur Express': 'Sede Sur Express'}
    sedes_empresa = [s.get('nombre') for e in EMPRESAS_REGISTRADAS for s in e.get('sedes', [])]
    if sede_solicitada not in equivalencias and sede_solicitada not in sedes_empresa:
        return jsonify({'status': 'error', 'mensaje': 'Sede no válida.'}), 400
    sede = equivalencias.get(sede_solicitada, sede_solicitada)
    session['sede_cliente'] = sede_solicitada
    session['sede'] = sede
    session['direccion_sede'] = direccion
    return {'status': 'ok'}

@app.route('/cliente-auth')
def cliente_auth():
    sede = session.get('sede', 'No seleccionada')
    return render_template_string(HTML_CLIENTE_AUTH, css=CSS_ESTILOS, sede_seleccionada=sede)

@app.route('/login-cliente', methods=['POST'])
def login_cliente():
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        return redirect(url_for('cliente_auth'))
    cliente = next((c for c in CLIENTES_REGISTRADOS if c.get('email') == email), None)
    if not cliente or not _verificar_password(cliente.get('password', ''), password):
        return render_template_string(HTML_CLIENTE_AUTH, css=CSS_ESTILOS, sede_seleccionada=session.get('sede', 'No seleccionada'), error='Correo o contraseña incorrectos. Si no tienes cuenta, regístrate.')
    sede = session.get('sede', 'Sede Central')
    sede_cliente = session.get('sede_cliente', sede)
    direccion = session.get('direccion_sede', '')
    session.clear()
    session.permanent = True
    session['user_type'] = 'cliente'
    session['cliente_email'] = email
    session['cliente_nombre'] = cliente.get('nombre', email.split('@')[0].title())
    session['sede'] = sede
    session['sede_cliente'] = sede_cliente
    session['direccion_sede'] = direccion
    return redirect(url_for('tienda'))

@app.route('/registro-cliente', methods=['POST'])
def registro_cliente():
    nombre = (request.form.get('nombre') or '').strip()[:100]
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    if not nombre or not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email) or len(password) < 8:
        return render_template_string(HTML_CLIENTE_AUTH, css=CSS_ESTILOS, sede_seleccionada=session.get('sede', 'No seleccionada'), error='Verifica tus datos. La contraseña debe tener al menos 8 caracteres.')
    if any(c.get('email') == email for c in CLIENTES_REGISTRADOS):
        return render_template_string(HTML_CLIENTE_AUTH, css=CSS_ESTILOS, sede_seleccionada=session.get('sede', 'No seleccionada'), error='Ya existe una cuenta con ese correo.')
    CLIENTES_REGISTRADOS.append({'id': secrets.token_hex(8), 'nombre': nombre, 'email': email, 'password': _hash_password(password), 'creado_en': obtener_tiempo_local()})
    sede = session.get('sede', 'Sede Central')
    sede_cliente = session.get('sede_cliente', sede)
    direccion = session.get('direccion_sede', '')
    session.clear()
    session.permanent = True
    session['user_type'] = 'cliente'
    session['cliente_nombre'] = nombre
    session['cliente_email'] = email
    session['sede'] = sede
    session['sede_cliente'] = sede_cliente
    session['direccion_sede'] = direccion
    _auditar('Registro de cliente', email)
    guardar_estado()
    return redirect(url_for('tienda'))

@app.route('/tienda')
def tienda():
    if session.get('user_type') != 'cliente':
        return redirect(url_for('cliente_ubicacion'))
    sede_actual = session.get('sede', 'Sede Principal (Centro)')
    cliente_nombre = session.get('cliente_nombre', 'Cliente')
    
    codigos_base = [f"{i:03d}" for i in range(1, 33)]
    productos_dinamicos = [i for i in INVENTARIO_SUPER if i['codigo'] not in codigos_base and (i['sede'] == sede_actual or sede_actual in i['sede'])]
    
    return render_template_string(HTML_TIENDA, css=CSS_ESTILOS, sede_actual=sede_actual, cliente_nombre=cliente_nombre, productos_dinamicos=productos_dinamicos)

@app.route('/api/crear-pedido', methods=['POST'])
def crear_pedido():
    if session.get('user_type') != 'cliente':
        return jsonify({'status': 'error', 'mensaje': 'Inicia sesión para realizar un pedido.'}), 401
    data = request.get_json(silent=True) or {}
    sede = session.get('sede')
    empresa = EMPRESAS_REGISTRADAS[0].get('nombre_empresa') if EMPRESAS_REGISTRADAS else 'Supermercados El Ahorro'
    metodo = str(data.get('metodo_pago', 'Por confirmar')).strip()[:40]
    try:
        detalle, total = procesar_items_inventario(data.get('items'), sede, empresa, descontar=True)
    except ValueError as exc:
        return jsonify({'status': 'error', 'mensaje': str(exc)}), 400
    pedido_id = secrets.token_hex(8)
    nuevo_pedido = {
        'id': pedido_id, 'hora': obtener_tiempo_local(), 'cliente': session.get('cliente_nombre', 'Cliente'),
        'cliente_email': session.get('cliente_email', ''), 'sede': sede,
        'productos': ', '.join(f"{x['nombre']} x{x['cantidad']}" for x in detalle), 'items': detalle,
        'total': total, 'metodo_pago': metodo, 'empresa': empresa, 'tipo': 'pedido_recoger',
        'estado': 'recibido', 'inventario_descontado': True, 'actualizado_en': obtener_tiempo_local()
    }
    PEDIDOS_REGISTRADOS.insert(0, nuevo_pedido)
    _notificar('pedido_nuevo', f"Nuevo pedido de {nuevo_pedido['cliente']} por ${total:,.0f}.", empresa=empresa, sede=sede, destinatario=session.get('cliente_email'))
    _auditar('Crear pedido', f"Pedido {pedido_id} - ${total:,.0f}", empresa=empresa, sede=sede)
    guardar_estado()
    return jsonify({'status': 'ok', 'pedido': nuevo_pedido, 'mensaje': 'Pedido registrado. El método de pago queda registrado, pero el cobro electrónico requiere integrar una pasarela de pagos real.'})

@app.route('/api/pedidos', methods=['GET'])
def obtener_pedidos():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager', 'empleado'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    pedidos = PEDIDOS_REGISTRADOS
    if session.get('user_type') != 'superadmin':
        pedidos = [p for p in pedidos if p.get('empresa') == session.get('empresa_nombre') and (session.get('user_type') == 'dueno' or p.get('sede') == session.get('user_sede'))]
    return jsonify(pedidos)

# -----------------------------------------------------------------------------
# MÓDULOS NUEVOS: movimientos, alertas, compras, proveedores, devoluciones,
# promociones, favoritos, reportes, exportación y copia de seguridad.
# -----------------------------------------------------------------------------
@app.route('/api/inventario/alertas', methods=['GET'])
def api_alertas_inventario():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    empresa = None if session.get('user_type') == 'superadmin' else session.get('empresa_nombre')
    sede = session.get('user_sede') if session.get('user_type') == 'manager' else None
    alertas = []
    for producto in INVENTARIO_SUPER:
        if _producto_empresa_sede(producto, empresa, sede) and int(producto.get('stock', 0)) <= 10:
            alertas.append({'codigo': producto.get('codigo'), 'nombre': producto.get('nombre'), 'stock': int(producto.get('stock', 0)), 'sede': producto.get('sede'), 'nivel': 'agotado' if int(producto.get('stock', 0)) <= 0 else 'critico' if int(producto.get('stock', 0)) <= 3 else 'bajo'})
    return jsonify({'cantidad': len(alertas), 'alertas': alertas})

@app.route('/api/inventario/movimientos', methods=['GET'])
def api_movimientos_inventario():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    movimientos = MOVIMIENTOS_INVENTARIO
    if session.get('user_type') != 'superadmin':
        movimientos = [m for m in movimientos if m.get('empresa') == session.get('empresa_nombre') and (session.get('user_type') == 'dueno' or m.get('sede') == session.get('user_sede'))]
    return jsonify(movimientos[:500])

@app.route('/api/inventario/ajustar-stock', methods=['POST'])
@app.route('/api/inventario/ajustar', methods=['POST'])
def api_ajustar_stock():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    data = request.get_json(silent=True) or {}
    codigo = str(data.get('codigo', '')).strip()
    try:
        cantidad = int(data.get('cantidad'))
    except (ValueError, TypeError):
        return jsonify({'status': 'error', 'mensaje': 'La cantidad debe ser un número entero.'}), 400
    motivo = str(data.get('motivo', '')).strip()[:250]
    tipo = str(data.get('tipo', 'entrada')).lower()
    if cantidad <= 0 or tipo not in ('entrada', 'salida', 'ajuste', 'danado') or not motivo:
        return jsonify({'status': 'error', 'mensaje': 'Cantidad, tipo o motivo no válido.'}), 400
    producto = next((p for p in INVENTARIO_SUPER if p.get('codigo') == codigo and (session.get('user_type') == 'superadmin' or p.get('empresa') == session.get('empresa_nombre')) and (session.get('user_type') != 'manager' or p.get('sede') == session.get('user_sede'))), None)
    if not producto:
        return jsonify({'status': 'error', 'mensaje': 'Producto no encontrado o fuera de tu sede.'}), 404
    anterior = int(producto.get('stock', 0))
    nuevo = anterior + cantidad if tipo == 'entrada' else anterior - cantidad if tipo in ('salida', 'danado') else cantidad
    if nuevo < 0:
        return jsonify({'status': 'error', 'mensaje': 'No hay existencias suficientes para esa salida.'}), 409
    producto['stock'] = nuevo
    MOVIMIENTOS_INVENTARIO.insert(0, {'fecha': obtener_tiempo_local(), 'codigo': codigo, 'producto': producto.get('nombre'), 'empresa': producto.get('empresa'), 'sede': producto.get('sede'), 'tipo': tipo, 'cantidad': cantidad, 'stock_anterior': anterior, 'stock_nuevo': nuevo, 'motivo': motivo, 'usuario': session.get('user_nombre', session.get('user_type'))})
    if nuevo <= 10:
        _notificar('stock_bajo', f"{producto.get('nombre')} tiene {nuevo} unidades.", empresa=producto.get('empresa'), sede=producto.get('sede'))
    _auditar('Ajustar inventario', f"{codigo}: {anterior} -> {nuevo}. Motivo: {motivo}", empresa=producto.get('empresa'), sede=producto.get('sede'))
    guardar_estado()
    return jsonify({'status': 'ok', 'stock_anterior': anterior, 'stock_nuevo': nuevo})

@app.route('/api/proveedores', methods=['GET', 'POST'])
def api_proveedores():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    empresa = session.get('empresa_nombre', 'Supermercados El Ahorro')
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        nombre = str(data.get('nombre', '')).strip()[:150]
        contacto = str(data.get('contacto', '')).strip()[:150]
        email = str(data.get('email', '')).strip()[:254]
        telefono = str(data.get('telefono', '')).strip()[:40]
        if not nombre or (email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email)):
            return jsonify({'status': 'error', 'mensaje': 'Nombre o correo no válido.'}), 400
        proveedor = {'id': secrets.token_hex(6), 'nombre': nombre, 'contacto': contacto, 'email': email, 'telefono': telefono, 'empresa': empresa, 'fecha': obtener_tiempo_local()}
        PROVEEDORES_REGISTRADOS.append(proveedor)
        _auditar('Crear proveedor', nombre)
        guardar_estado()
        return jsonify({'status': 'ok', 'proveedor': proveedor}), 201
    lista = PROVEEDORES_REGISTRADOS if session.get('user_type') == 'superadmin' else [p for p in PROVEEDORES_REGISTRADOS if p.get('empresa') == empresa]
    return jsonify(lista)

@app.route('/api/compras', methods=['GET', 'POST'])
def api_compras():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    empresa = session.get('empresa_nombre', 'Supermercados El Ahorro')
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        codigo = str(data.get('codigo', '')).strip()
        try:
            cantidad = int(data.get('cantidad'))
            costo = float(data.get('costo', 0))
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'mensaje': 'Cantidad y costo deben ser numéricos.'}), 400
        sede = session.get('user_sede') if session.get('user_type') == 'manager' else str(data.get('sede', '')).strip()
        producto = next((p for p in INVENTARIO_SUPER if p.get('codigo') == codigo and p.get('empresa') == empresa and (not sede or p.get('sede') == sede)), None)
        proveedor_id = str(data.get('proveedor_id', '')).strip()
        proveedor = next((p for p in PROVEEDORES_REGISTRADOS if p.get('id') == proveedor_id and (p.get('empresa') == empresa or session.get('user_type') == 'superadmin')), None)
        if not producto or cantidad <= 0 or costo < 0:
            return jsonify({'status': 'error', 'mensaje': 'Producto, cantidad o costo no válido.'}), 400
        if proveedor_id and not proveedor:
            return jsonify({'status': 'error', 'mensaje': 'Proveedor no encontrado.'}), 404
        orden = {'id': secrets.token_hex(6), 'fecha': obtener_tiempo_local(), 'codigo': codigo, 'producto': producto.get('nombre'), 'cantidad': cantidad, 'costo_unitario': costo, 'costo_total': round(costo*cantidad, 2), 'proveedor_id': proveedor_id, 'proveedor': proveedor.get('nombre') if proveedor else 'Sin proveedor asignado', 'empresa': empresa, 'sede': producto.get('sede'), 'estado': 'recibida', 'usuario': session.get('user_nombre', session.get('user_type'))}
        producto['stock'] = int(producto.get('stock', 0)) + cantidad
        ORDENES_COMPRA.insert(0, orden)
        MOVIMIENTOS_INVENTARIO.insert(0, {'fecha': obtener_tiempo_local(), 'codigo': codigo, 'producto': producto.get('nombre'), 'empresa': empresa, 'sede': producto.get('sede'), 'tipo': 'entrada_compra', 'cantidad': cantidad, 'stock_nuevo': producto['stock'], 'motivo': f"Recepción de compra {orden['id']}", 'usuario': orden['usuario']})
        _auditar('Registrar compra', f"Orden {orden['id']} - {producto.get('nombre')} x{cantidad}", empresa=empresa, sede=producto.get('sede'))
        guardar_estado()
        return jsonify({'status': 'ok', 'orden': orden}), 201
    lista = ORDENES_COMPRA if session.get('user_type') == 'superadmin' else [o for o in ORDENES_COMPRA if o.get('empresa') == empresa and (session.get('user_type') == 'dueno' or o.get('sede') == session.get('user_sede'))]
    return jsonify(lista[:500])

@app.route('/api/devoluciones', methods=['GET', 'POST'])
def api_devoluciones():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager', 'empleado'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    empresa = session.get('empresa_nombre', 'Supermercados El Ahorro')
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        codigo = str(data.get('codigo', '')).strip()
        motivo = str(data.get('motivo', '')).strip()[:250]
        try:
            cantidad = int(data.get('cantidad', 1))
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'mensaje': 'Cantidad no válida.'}), 400
        producto = next((p for p in INVENTARIO_SUPER if p.get('codigo') == codigo and (session.get('user_type') == 'superadmin' or p.get('empresa') == empresa) and (session.get('user_type') != 'manager' or p.get('sede') == session.get('user_sede')) and (session.get('user_type') != 'empleado' or p.get('sede') == session.get('user_sede'))), None)
        if not producto or cantidad <= 0 or not motivo:
            return jsonify({'status': 'error', 'mensaje': 'Producto, cantidad o motivo no válido.'}), 400
        devolucion = {'id': secrets.token_hex(6), 'fecha': obtener_tiempo_local(), 'codigo': codigo, 'producto': producto.get('nombre'), 'cantidad': cantidad, 'motivo': motivo, 'empresa': producto.get('empresa'), 'sede': producto.get('sede'), 'usuario': session.get('user_nombre', session.get('user_type')), 'estado': 'pendiente_revision'}
        DEVOLUCIONES_REGISTRADAS.insert(0, devolucion)
        _notificar('devolucion', f"Devolución pendiente: {producto.get('nombre')} x{cantidad}.", empresa=producto.get('empresa'), sede=producto.get('sede'))
        _auditar('Registrar devolución', f"{producto.get('nombre')} x{cantidad}: {motivo}", empresa=producto.get('empresa'), sede=producto.get('sede'))
        guardar_estado()
        return jsonify({'status': 'ok', 'devolucion': devolucion}), 201
    lista = DEVOLUCIONES_REGISTRADAS if session.get('user_type') == 'superadmin' else [d for d in DEVOLUCIONES_REGISTRADAS if d.get('empresa') == empresa and (session.get('user_type') == 'dueno' or d.get('sede') == session.get('user_sede'))]
    return jsonify(lista[:500])

@app.route('/api/promociones', methods=['GET', 'POST'])
def api_promociones():
    if request.method == 'POST' and session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        codigo = str(data.get('codigo', '')).strip()
        nombre = str(data.get('nombre', '')).strip()[:150]
        try:
            descuento = float(data.get('descuento', 0))
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'mensaje': 'Descuento no válido.'}), 400
        if not nombre or not 0 < descuento <= 80:
            return jsonify({'status': 'error', 'mensaje': 'La promoción requiere nombre y descuento entre 0 y 80%.'}), 400
        producto = next((p for p in INVENTARIO_SUPER if p.get('codigo') == codigo and (session.get('user_type') == 'superadmin' or p.get('empresa') == session.get('empresa_nombre')) and (session.get('user_type') != 'manager' or p.get('sede') == session.get('user_sede'))), None)
        if not producto:
            return jsonify({'status': 'error', 'mensaje': 'Producto no encontrado.'}), 404
        promocion = {'id': secrets.token_hex(6), 'nombre': nombre, 'codigo': codigo, 'producto': producto.get('nombre'), 'descuento': descuento, 'precio_original': producto.get('precio'), 'precio_promocional': round(float(producto.get('precio', 0))*(1-descuento/100), 2), 'empresa': producto.get('empresa'), 'sede': producto.get('sede'), 'activa': True, 'fecha': obtener_tiempo_local()}
        PROMOCIONES_REGISTRADAS.append(promocion)
        _auditar('Crear promoción', f"{nombre} - {descuento}%")
        guardar_estado()
        return jsonify({'status': 'ok', 'promocion': promocion}), 201
    activas = [p for p in PROMOCIONES_REGISTRADAS if p.get('activa') and (session.get('user_type') == 'superadmin' or p.get('empresa') == session.get('empresa_nombre') or session.get('user_type') == 'cliente')]
    return jsonify(activas)

@app.route('/api/favoritos', methods=['GET', 'POST', 'DELETE'])
def api_favoritos():
    if session.get('user_type') != 'cliente':
        return jsonify({'status': 'error', 'mensaje': 'Inicia sesión como cliente.'}), 401
    clave = str(session.get('cliente_nombre', 'Cliente')) + '|' + str(session.get('sede', ''))
    if request.method == 'GET':
        return jsonify(FAVORITOS_CLIENTES.get(clave, []))
    data = request.get_json(silent=True) or {}
    codigo = str(data.get('codigo', '')).strip()
    producto = next((p for p in INVENTARIO_SUPER if p.get('codigo') == codigo and (p.get('sede') == session.get('sede') or session.get('sede') in p.get('sede', ''))), None)
    if not producto:
        return jsonify({'status': 'error', 'mensaje': 'Producto no disponible en esta sede.'}), 404
    favoritos = FAVORITOS_CLIENTES.setdefault(clave, [])
    if request.method == 'DELETE':
        FAVORITOS_CLIENTES[clave] = [f for f in favoritos if f.get('codigo') != codigo]
    elif not any(f.get('codigo') == codigo for f in favoritos):
        favoritos.append({'codigo': codigo, 'nombre': producto.get('nombre'), 'precio': producto.get('precio'), 'imagen': producto.get('imagen')})
    guardar_estado()
    return jsonify({'status': 'ok', 'favoritos': FAVORITOS_CLIENTES.get(clave, [])})

@app.route('/api/reportes/resumen', methods=['GET'])
def api_resumen_reportes():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    pedidos = PEDIDOS_REGISTRADOS
    inventario = INVENTARIO_SUPER
    if session.get('user_type') != 'superadmin':
        pedidos = [p for p in pedidos if p.get('empresa') == session.get('empresa_nombre')]
        inventario = [p for p in inventario if p.get('empresa') == session.get('empresa_nombre')]
    if session.get('user_type') == 'manager':
        pedidos = [p for p in pedidos if p.get('sede') == session.get('user_sede')]
        inventario = [p for p in inventario if p.get('sede') == session.get('user_sede')]
    ventas = sum(float(p.get('total', 0) or 0) for p in pedidos)
    return jsonify({'pedidos': len(pedidos), 'ventas_totales': round(ventas, 2), 'ticket_promedio': round(ventas/len(pedidos), 2) if pedidos else 0, 'productos_registrados': len(inventario), 'unidades_en_stock': sum(int(p.get('stock', 0) or 0) for p in inventario), 'productos_bajo_stock': sum(1 for p in inventario if int(p.get('stock', 0) or 0) <= 10)})

@app.route('/api/lotes', methods=['GET', 'POST'])
def api_lotes():
    """Registra lotes con fecha de vencimiento y permite detectar productos próximos a vencer."""
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        codigo = str(data.get('codigo', '')).strip()
        lote = str(data.get('lote', '')).strip()[:80]
        vencimiento = str(data.get('fecha_vencimiento', '')).strip()
        try:
            cantidad = int(data.get('cantidad'))
            fecha_venc = datetime.strptime(vencimiento, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'mensaje': 'Cantidad o fecha de vencimiento no válida. Usa AAAA-MM-DD.'}), 400
        empresa = session.get('empresa_nombre', 'Supermercados El Ahorro')
        producto = next((p for p in INVENTARIO_SUPER if p.get('codigo') == codigo and (session.get('user_type') == 'superadmin' or p.get('empresa') == empresa) and (session.get('user_type') != 'manager' or p.get('sede') == session.get('user_sede'))), None)
        if not producto or cantidad <= 0 or not lote:
            return jsonify({'status': 'error', 'mensaje': 'Producto, lote o cantidad no válida.'}), 400
        registro = {'id': secrets.token_hex(6), 'codigo': codigo, 'producto': producto.get('nombre'), 'lote': lote, 'cantidad': cantidad, 'fecha_vencimiento': vencimiento, 'empresa': producto.get('empresa'), 'sede': producto.get('sede'), 'fecha_registro': obtener_tiempo_local()}
        LOTES_PRODUCTOS.insert(0, registro)
        _auditar('Registrar lote', f"{producto.get('nombre')} - lote {lote}", empresa=producto.get('empresa'), sede=producto.get('sede'))
        if (fecha_venc - datetime.now().date()).days <= 30:
            _notificar('vencimiento', f"El lote {lote} de {producto.get('nombre')} vence el {vencimiento}.", empresa=producto.get('empresa'), sede=producto.get('sede'))
        guardar_estado()
        return jsonify({'status': 'ok', 'lote': registro}), 201
    hoy = datetime.now().date()
    empresa = session.get('empresa_nombre')
    sede = session.get('user_sede') if session.get('user_type') == 'manager' else None
    lotes = [l for l in LOTES_PRODUCTOS if (session.get('user_type') == 'superadmin' or l.get('empresa') == empresa) and (not sede or l.get('sede') == sede)]
    for lote in lotes:
        try:
            dias = (datetime.strptime(lote['fecha_vencimiento'], '%Y-%m-%d').date() - hoy).days
            lote['dias_para_vencer'] = dias
            lote['estado_vencimiento'] = 'vencido' if dias < 0 else 'proximo' if dias <= 30 else 'vigente'
        except (KeyError, ValueError):
            lote['dias_para_vencer'] = None
            lote['estado_vencimiento'] = 'fecha_no_valida'
    return jsonify(lotes[:500])

@app.route('/api/inventario/traslados', methods=['GET', 'POST'])
def api_traslados():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        codigo = str(data.get('codigo', '')).strip()
        destino = str(data.get('destino', '')).strip()
        try: cantidad = int(data.get('cantidad', 0))
        except (ValueError, TypeError): return jsonify({'error': 'Cantidad inválida'}), 400
        empresa = next((e for e in EMPRESAS_REGISTRADAS if e.get('nombre_empresa') == session.get('empresa_nombre')), None)
        origen = session.get('user_sede') if session.get('user_type') == 'manager' else str(data.get('origen', '')).strip()
        sedes = [s.get('nombre') for s in empresa.get('sedes', [])] if empresa else []
        if not empresa or destino not in sedes or origen not in sedes or origen == destino or cantidad <= 0:
            return jsonify({'error': 'Origen, destino o cantidad no válidos'}), 400
        producto = buscar_producto(codigo, origen, empresa.get('nombre_empresa'))
        if not producto or int(producto.get('stock', 0)) < cantidad:
            return jsonify({'error': 'Producto no disponible o stock insuficiente'}), 409
        anterior = int(producto.get('stock', 0)); producto['stock'] = anterior - cantidad
        traslado = {'id': secrets.token_hex(8), 'fecha': obtener_tiempo_local(), 'codigo': codigo, 'producto': producto.get('nombre'), 'cantidad': cantidad, 'origen': origen, 'destino': destino, 'empresa': empresa.get('nombre_empresa'), 'estado': 'en_transito', 'creado_por': session.get('user_nombre')}
        TRASLADOS_INVENTARIO.insert(0, traslado)
        MOVIMIENTOS_INVENTARIO.insert(0, {'fecha': traslado['fecha'], 'codigo': codigo, 'producto': producto.get('nombre'), 'cantidad': -cantidad, 'tipo': 'traslado_salida', 'sede': origen, 'empresa': traslado['empresa'], 'stock_anterior': anterior, 'stock_nuevo': producto['stock'], 'responsable': session.get('user_nombre')})
        _auditar('Crear traslado', traslado['id'], empresa=traslado['empresa'], sede=origen)
        guardar_estado()
        return jsonify({'status': 'ok', 'traslado': traslado}), 201
    empresa = session.get('empresa_nombre')
    lista = TRASLADOS_INVENTARIO if session.get('user_type') == 'superadmin' else [t for t in TRASLADOS_INVENTARIO if t.get('empresa') == empresa and (session.get('user_type') == 'dueno' or session.get('user_sede') in (t.get('origen'), t.get('destino')))]
    return jsonify(lista[:500])

@app.route('/api/inventario/traslados/<traslado_id>/recibir', methods=['POST'])
def recibir_traslado(traslado_id):
    if session.get('user_type') not in ('manager', 'dueno', 'superadmin'):
        return jsonify({'error': 'No autorizado'}), 401
    traslado = next((t for t in TRASLADOS_INVENTARIO if t.get('id') == traslado_id), None)
    if not traslado or traslado.get('estado') != 'en_transito': return jsonify({'error': 'Traslado no disponible'}), 404
    if session.get('user_type') != 'superadmin' and traslado.get('empresa') != session.get('empresa_nombre'):
        return jsonify({'error': 'No autorizado'}), 403
    if session.get('user_type') == 'manager' and traslado.get('destino') != session.get('user_sede'):
        return jsonify({'error': 'Solo la sede destino puede recibirlo'}), 403
    destino_producto = buscar_producto(traslado.get('codigo'), traslado.get('destino'), traslado.get('empresa'))
    if destino_producto:
        destino_producto['stock'] = int(destino_producto.get('stock', 0)) + int(traslado.get('cantidad', 0))
    else:
        ficha = next((p for p in INVENTARIO_SUPER if p.get('codigo') == traslado.get('codigo') and p.get('empresa') == traslado.get('empresa')), None)
        if not ficha: return jsonify({'error': 'No se encontró la ficha maestra del producto'}), 404
        destino_producto = dict(ficha); destino_producto.update({'sede': traslado['destino'], 'stock': int(traslado['cantidad'])}); INVENTARIO_SUPER.append(destino_producto)
    traslado['estado'] = 'recibido'; traslado['recibido_en'] = obtener_tiempo_local()
    MOVIMIENTOS_INVENTARIO.insert(0, {'fecha': obtener_tiempo_local(), 'codigo': traslado['codigo'], 'producto': traslado['producto'], 'cantidad': int(traslado['cantidad']), 'tipo': 'traslado_entrada', 'sede': traslado['destino'], 'empresa': traslado['empresa'], 'stock_nuevo': destino_producto['stock'], 'responsable': session.get('user_nombre')})
    _auditar('Recibir traslado', traslado_id, empresa=traslado.get('empresa'), sede=traslado.get('destino'))
    guardar_estado()
    return jsonify({'status': 'ok', 'traslado': traslado})

@app.route('/api/reportes/pronostico', methods=['GET'])
def api_pronostico_demanda():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    empresa = session.get('empresa_nombre')
    sede = session.get('user_sede') if session.get('user_type') == 'manager' else None
    productos = [p for p in INVENTARIO_SUPER if (session.get('user_type') == 'superadmin' or p.get('empresa') == empresa) and (not sede or p.get('sede') == sede)]
    resultados = []
    for producto in productos:
        coincidencias = sum(1 for pedido in PEDIDOS_REGISTRADOS if (not empresa or session.get('user_type') == 'superadmin' or pedido.get('empresa') == empresa) and (not sede or pedido.get('sede') == sede) and producto.get('nombre', '') in str(pedido.get('productos', '')))
        resultados.append({'codigo': producto.get('codigo'), 'producto': producto.get('nombre'), 'stock_actual': int(producto.get('stock', 0)), 'pedidos_asociados_registrados': coincidencias, 'recomendacion': 'Revisar reposición' if int(producto.get('stock', 0)) <= 10 else 'Stock estable', 'nota': 'Estimación básica basada en menciones en pedidos registrados; no es un modelo estadístico de demanda.'})
    return jsonify(sorted(resultados, key=lambda x: (x['stock_actual'] > 10, x['pedidos_asociados_registrados'] * -1))[:300])

@app.route('/api/notificaciones', methods=['GET', 'POST'])
def api_notificaciones():
    rol = session.get('user_type')
    if rol not in ('superadmin', 'dueno', 'manager', 'empleado', 'cliente'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    if rol == 'superadmin':
        lista = list(NOTIFICACIONES_SISTEMA)
    elif rol == 'cliente':
        claves = {session.get('cliente_email'), session.get('cliente_nombre')}
        lista = [n for n in NOTIFICACIONES_SISTEMA if n.get('destinatario') in claves]
    else:
        empresa = session.get('empresa_nombre')
        lista = [n for n in NOTIFICACIONES_SISTEMA if n.get('empresa') == empresa and (rol == 'dueno' or n.get('sede') == session.get('user_sede'))]
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        identificador = str(data.get('id', ''))
        for notificacion in lista:
            if notificacion.get('id') == identificador:
                notificacion['leida'] = True
        guardar_estado()
        return jsonify({'status': 'ok'})
    return jsonify(lista[:200])

@app.route('/api/notificaciones/<notificacion_id>/leer', methods=['POST'])
def marcar_notificacion_leida(notificacion_id):
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager', 'empleado', 'cliente'):
        return jsonify({'error': 'No autorizado'}), 401
    notificacion = next((n for n in NOTIFICACIONES_SISTEMA if n.get('id') == notificacion_id), None)
    if not notificacion:
        return jsonify({'error': 'Notificación no encontrada'}), 404
    if session.get('user_type') == 'cliente':
        if notificacion.get('destinatario') not in (session.get('cliente_email'), session.get('cliente_nombre')):
            return jsonify({'error': 'No autorizado'}), 403
    elif session.get('user_type') != 'superadmin':
        if notificacion.get('empresa') != session.get('empresa_nombre'):
            return jsonify({'error': 'No autorizado'}), 403
        if session.get('user_type') in ('manager', 'empleado') and notificacion.get('sede') != session.get('user_sede'):
            return jsonify({'error': 'No autorizado para esta sede'}), 403
    notificacion['leida'] = True
    guardar_estado()
    return jsonify({'status': 'ok'})

@app.route('/api/auditoria', methods=['GET'])
def api_auditoria():
    if session.get('user_type') not in ('superadmin', 'dueno'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    registros = REGISTRO_AUDITORIA if session.get('user_type') == 'superadmin' else [r for r in REGISTRO_AUDITORIA if r.get('empresa') == session.get('empresa_nombre')]
    return jsonify(registros[:500])

@app.route('/reportes/exportar.csv', methods=['GET'])
def exportar_reportes_csv():
    if session.get('user_type') not in ('superadmin', 'dueno', 'manager'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado.'}), 403
    pedidos = PEDIDOS_REGISTRADOS
    if session.get('user_type') != 'superadmin':
        pedidos = [p for p in pedidos if p.get('empresa') == session.get('empresa_nombre')]
    if session.get('user_type') == 'manager':
        pedidos = [p for p in pedidos if p.get('sede') == session.get('user_sede')]
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(['Fecha', 'Cliente/Empleado', 'Empresa', 'Sede', 'Productos', 'Método de pago', 'Estado', 'Total'])
    for pedido in pedidos:
        escritor.writerow([pedido.get('hora', ''), pedido.get('cliente', ''), pedido.get('empresa', ''), pedido.get('sede', ''), pedido.get('productos', ''), pedido.get('metodo_pago', ''), pedido.get('estado', 'Registrado'), pedido.get('total', 0)])
    respuesta = make_response('\ufeff' + salida.getvalue())
    respuesta.headers['Content-Type'] = 'text/csv; charset=utf-8'
    respuesta.headers['Content-Disposition'] = 'attachment; filename=keepinventory_ventas.csv'
    return respuesta

@app.route('/admin/backup.json', methods=['GET'])
def exportar_respaldo():
    if session.get('user_type') != 'superadmin':
        return jsonify({'status': 'error', 'mensaje': 'Solo el superadministrador puede descargar el respaldo completo.'}), 403
    datos = {clave: globals().get(nombre_global, []) for clave, nombre_global in ESTADO_LISTAS.items()}
    contenido = io.BytesIO(json.dumps({'generado': obtener_tiempo_local(), 'version': 2, 'datos': datos}, ensure_ascii=False, indent=2).encode('utf-8'))
    return send_file(contenido, mimetype='application/json', as_attachment=True, download_name='keepinventory_respaldo.json')

@app.route('/api/pedidos/<pedido_id>/estado', methods=['POST'])
def actualizar_estado_pedido(pedido_id):
    if session.get('user_type') not in ('manager', 'dueno', 'superadmin', 'empleado'):
        return jsonify({'error': 'No autorizado'}), 401
    data = request.get_json(silent=True) or {}
    nuevo_estado = str(data.get('estado', '')).strip().lower()
    estados_validos = {'recibido', 'preparando', 'listo_para_recoger', 'entregado', 'cancelado'}
    if nuevo_estado not in estados_validos:
        return jsonify({'error': 'Estado no válido'}), 400
    pedido = next((p for p in PEDIDOS_REGISTRADOS if p.get('id') == pedido_id), None)
    if not pedido:
        return jsonify({'error': 'Pedido no encontrado'}), 404
    rol = session.get('user_type')
    if rol != 'superadmin':
        if pedido.get('empresa') != session.get('empresa_nombre'):
            return jsonify({'error': 'No autorizado para esta empresa'}), 403
        if rol in ('manager', 'empleado') and pedido.get('sede') != session.get('user_sede'):
            return jsonify({'error': 'No autorizado para esta sede'}), 403
        if rol == 'empleado' and nuevo_estado not in ('preparando', 'listo_para_recoger', 'entregado'):
            return jsonify({'error': 'El empleado solo puede preparar y entregar pedidos.'}), 403
    estado_anterior = pedido.get('estado', 'recibido')
    transiciones = {'recibido': {'preparando', 'cancelado'}, 'preparando': {'listo_para_recoger', 'cancelado'}, 'listo_para_recoger': {'entregado', 'cancelado'}, 'entregado': set(), 'cancelado': set()}
    if nuevo_estado not in transiciones.get(estado_anterior, set()):
        return jsonify({'error': f'Transición no permitida: {estado_anterior} -> {nuevo_estado}'}), 409
    if nuevo_estado == 'cancelado' and pedido.get('inventario_descontado') and not pedido.get('inventario_repuesto'):
        for linea in pedido.get('items', []):
            producto = buscar_producto(linea.get('codigo'), pedido.get('sede'), pedido.get('empresa'))
            if producto:
                producto['stock'] = int(producto.get('stock', 0)) + int(linea.get('cantidad', 0))
                MOVIMIENTOS_INVENTARIO.insert(0, {'fecha': obtener_tiempo_local(), 'codigo': linea.get('codigo'), 'producto': linea.get('nombre'), 'cantidad': int(linea.get('cantidad', 0)), 'tipo': 'reversion_cancelacion', 'sede': pedido.get('sede'), 'empresa': pedido.get('empresa'), 'responsable': session.get('user_nombre', rol)})
        pedido['inventario_repuesto'] = True
    pedido['estado'] = nuevo_estado
    pedido['actualizado_en'] = obtener_tiempo_local()
    _notificar('pedido', f"El pedido {pedido_id} cambió a: {nuevo_estado.replace('_', ' ')}.", empresa=pedido.get('empresa'), sede=pedido.get('sede'), destinatario=pedido.get('cliente_email') or pedido.get('cliente'))
    _auditar('Estado de pedido', f"{pedido_id}: {estado_anterior} -> {nuevo_estado}", empresa=pedido.get('empresa'), sede=pedido.get('sede'))
    guardar_estado()
    return jsonify({'status': 'ok', 'pedido': pedido})

@app.route('/api/reportes/<reporte_id>/respuesta', methods=['POST'])
def responder_reporte(reporte_id):
    if session.get('user_type') not in ('manager', 'dueno', 'superadmin'):
        return jsonify({'error': 'No autorizado'}), 401
    reporte = next((r for r in REPORTES_EMPLEADOS if r.get('id') == reporte_id), None)
    if not reporte:
        return jsonify({'error': 'Reporte no encontrado'}), 404
    if session.get('user_type') != 'superadmin':
        if reporte.get('empresa') != session.get('empresa_nombre'):
            return jsonify({'error': 'No autorizado'}), 403
        if session.get('user_type') == 'manager' and reporte.get('sede') != session.get('user_sede'):
            return jsonify({'error': 'No autorizado para esta sede'}), 403
    data = request.get_json(silent=True) or {}
    respuesta = str(data.get('respuesta', '')).strip()
    if not respuesta or len(respuesta) > 2000:
        return jsonify({'error': 'La respuesta debe tener entre 1 y 2000 caracteres'}), 400
    reporte['respuesta_manager'] = respuesta
    reporte['estado'] = 'resuelto' if data.get('resuelto') else 'en_seguimiento'
    reporte['resuelto'] = bool(data.get('resuelto'))
    reporte['respondido_en'] = obtener_tiempo_local()
    _notificar('respuesta_reporte', f"El manager respondió tu reporte: {respuesta[:180]}", empresa=reporte.get('empresa'), sede=reporte.get('sede'))
    _auditar('Respuesta a reporte', reporte_id)
    guardar_estado()
    return jsonify({'status': 'ok', 'reporte': reporte})

@app.route('/api/productos/<codigo>/archivar', methods=['POST'])
def archivar_producto(codigo):
    if session.get('user_type') not in ('manager', 'dueno'):
        return jsonify({'error': 'No autorizado'}), 401
    empresa = session.get('empresa_nombre')
    sede = session.get('user_sede') if session.get('user_type') == 'manager' else str((request.get_json(silent=True) or {}).get('sede') or request.form.get('sede') or '').strip()
    producto = buscar_producto(codigo, sede, empresa)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    pedido_pendiente = any(p.get('estado') not in ('entregado', 'cancelado') and any(i.get('codigo') == codigo for i in p.get('items', [])) for p in PEDIDOS_REGISTRADOS)
    if pedido_pendiente:
        return jsonify({'error': 'No se puede archivar: el producto está asociado a pedidos pendientes.'}), 409
    producto['activo'] = False
    PRODUCTOS_ARCHIVADOS.append(dict(producto, archivado_en=obtener_tiempo_local()))
    INVENTARIO_SUPER.remove(producto)
    _auditar('Producto archivado', f"{codigo} / {producto.get('nombre')}", empresa=empresa, sede=sede)
    guardar_estado()
    return jsonify({'status': 'ok', 'codigo_reservado': codigo})

@app.route('/mis-pedidos', methods=['GET'])
def pagina_mis_pedidos():
    if session.get('user_type') != 'cliente':
        return redirect(url_for('cliente_ubicacion'))
    email = session.get('cliente_email')
    pedidos = [p for p in PEDIDOS_REGISTRADOS if p.get('cliente_email') == email]
    return render_template_string("""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mis pedidos - KeepInventory</title><style>body{font-family:Arial,sans-serif;background:#f1f5f9;color:#1e293b;margin:0;padding:24px}main{max-width:1000px;margin:auto}.card{background:white;padding:22px;border-radius:14px;margin:14px 0;box-shadow:0 3px 12px #0000000c}a{color:#0f8a5f;font-weight:bold}</style></head><body><main><p><a href="/tienda">← Volver a la tienda</a></p><h1>Mis pedidos</h1>{% for pedido in pedidos %}<section class="card"><h3>Pedido #{{ pedido.id }}</h3><p>Fecha: {{ pedido.hora }} | Sede: {{ pedido.sede }} | Estado: <b>{{ pedido.estado }}</b></p><p>{{ pedido.productos }}</p><p><b>Total: ${{ "{:,.0f}".format(pedido.total) }}</b></p><a href="/comprobante/{{ pedido.id }}" target="_blank" rel="noopener">Ver comprobante</a></section>{% else %}<section class="card">Todavía no tienes pedidos registrados.</section>{% endfor %}</main></body></html>""", pedidos=pedidos)

@app.route('/api/mis-pedidos', methods=['GET'])
def mis_pedidos():
    if session.get('user_type') != 'cliente':
        return jsonify({'error': 'No autorizado'}), 401
    return jsonify([p for p in PEDIDOS_REGISTRADOS if p.get('cliente_email') == session.get('cliente_email')])

@app.route('/comprobante/<pedido_id>', methods=['GET'])
def ver_comprobante(pedido_id):
    pedido = next((p for p in PEDIDOS_REGISTRADOS if p.get('id') == pedido_id), None)
    if not pedido:
        return 'Comprobante no encontrado', 404
    rol = session.get('user_type')
    autorizado = rol == 'superadmin'
    if rol == 'cliente': autorizado = pedido.get('cliente_email') == session.get('cliente_email')
    elif rol == 'dueno': autorizado = pedido.get('empresa') == session.get('empresa_nombre')
    elif rol in ('manager', 'empleado'): autorizado = pedido.get('empresa') == session.get('empresa_nombre') and pedido.get('sede') == session.get('user_sede')
    if not autorizado:
        return 'No autorizado', 403
    return render_template_string("""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Comprobante</title><style>body{font-family:Arial,sans-serif;max-width:760px;margin:30px auto;padding:20px;color:#1f2937}table{width:100%;border-collapse:collapse}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:left}.total{text-align:right;font-size:22px;font-weight:bold;margin-top:20px}@media print{button{display:none}}</style></head><body><h1>KeepInventory - Comprobante</h1><p><b>Pedido:</b> {{ pedido.id }} | <b>Fecha:</b> {{ pedido.hora }}</p><p><b>Empresa:</b> {{ pedido.empresa }} | <b>Sede:</b> {{ pedido.sede }}</p><p><b>Cliente:</b> {{ pedido.cliente }} | <b>Estado:</b> {{ pedido.estado }}</p><table><thead><tr><th>Código</th><th>Producto</th><th>Cantidad</th><th>Precio</th><th>Subtotal</th></tr></thead><tbody>{% for item in pedido.items %}<tr><td>{{ item.codigo }}</td><td>{{ item.nombre }}</td><td>{{ item.cantidad }}</td><td>${{ "{:,.0f}".format(item.precio_unitario) }}</td><td>${{ "{:,.0f}".format(item.subtotal) }}</td></tr>{% endfor %}</tbody></table><p><b>Método de pago declarado:</b> {{ pedido.metodo_pago }}</p><div class="total">Total: ${{ "{:,.0f}".format(pedido.total) }}</div><button onclick="window.print()">Imprimir / Guardar como PDF</button></body></html>""", pedido=pedido)

@app.route('/api/clientes/favoritos', methods=['GET', 'POST'])
def gestionar_favoritos_cliente():
    if session.get('user_type') != 'cliente':
        return jsonify({'error': 'No autorizado'}), 401
    clave = session.get('cliente_email') or session.get('cliente_nombre')
    if request.method == 'GET':
        return jsonify(FAVORITOS_CLIENTES.get(clave, []))
    data = request.get_json(silent=True) or {}
    codigo = str(data.get('codigo', '')).strip()
    if not validar_codigo_producto(codigo):
        return jsonify({'error': 'Código inválido'}), 400
    favoritos = FAVORITOS_CLIENTES.setdefault(clave, [])
    if codigo in favoritos: favoritos.remove(codigo)
    else: favoritos.append(codigo)
    guardar_estado()
    return jsonify({'status': 'ok', 'favoritos': favoritos})

@app.route('/reportes/ventas.csv', methods=['GET'])
def exportar_ventas_csv():
    if session.get('user_type') not in ('manager', 'dueno', 'superadmin'):
        return redirect(url_for('login_staff'))
    pedidos = PEDIDOS_REGISTRADOS if session.get('user_type') == 'superadmin' else [p for p in PEDIDOS_REGISTRADOS if p.get('empresa') == session.get('empresa_nombre') and (session.get('user_type') == 'dueno' or p.get('sede') == session.get('user_sede'))]
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(['ID', 'Fecha', 'Empresa', 'Sede', 'Empleado/Cliente', 'Tipo', 'Estado', 'Productos', 'Método de pago', 'Total'])
    for pedido in pedidos:
        if es_venta_cerrada(pedido):
            escritor.writerow([pedido.get('id'), pedido.get('hora'), pedido.get('empresa'), pedido.get('sede'), pedido.get('empleado') or pedido.get('cliente'), pedido.get('tipo'), pedido.get('estado'), pedido.get('productos'), pedido.get('metodo_pago'), pedido.get('total')])
    respuesta = make_response('\ufeff' + salida.getvalue())
    respuesta.headers['Content-Type'] = 'text/csv; charset=utf-8'
    respuesta.headers['Content-Disposition'] = 'attachment; filename=ventas_keepinventory.csv'
    return respuesta

@app.route('/api/diagnostico', methods=['GET'])
def diagnostico_sistema():
    if session.get('user_type') != 'superadmin':
        return jsonify({'error': 'No autorizado'}), 401
    try:
        with _conexion_db() as conexion:
            conexion.execute('SELECT 1').fetchone()
        estado_db = 'ok'
    except sqlite3.Error:
        estado_db = 'error'
    return jsonify({'estado': 'ok' if estado_db == 'ok' else 'degradado', 'base_datos': estado_db, 'empresas': len(EMPRESAS_REGISTRADAS), 'productos_activos': len(INVENTARIO_SUPER), 'productos_archivados': len(PRODUCTOS_ARCHIVADOS), 'pedidos': len(PEDIDOS_REGISTRADOS), 'reportes': len(REPORTES_EMPLEADOS), 'hora_local': obtener_tiempo_local()})

@app.route('/logout')
def logout():
    _auditar("Cerrar sesión", "Sesión finalizada")
    guardar_estado()
    session.clear()
    return redirect(url_for('inicio'))

@app.route('/api/ping-mantener-activo', methods=['GET', 'HEAD'])
def ping_activo():
    return "OK", 200

if __name__ == '__main__':
    app.run(host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', '5000')), debug=os.getenv('FLASK_DEBUG', '0') == '1')
