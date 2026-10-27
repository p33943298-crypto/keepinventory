from flask import Flask, render_template_string, redirect, url_for, request, session, jsonify
import os
import sqlite3
import json
import secrets
import hashlib
import hmac
import csv
import io
import re
import math
from functools import wraps
from contextlib import contextmanager
from werkzeug.utils import secure_filename
from flask import make_response
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
# Clave secreta para manejo seguro de sesiones
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1", PERMANENT_SESSION_LIFETIME=timedelta(hours=8), MAX_CONTENT_LENGTH=5 * 1024 * 1024)

# Credenciales de administrador demo
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@keepinventory.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123password")

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

    # Aseo y Cuidado Personal (Imagen corregida de papel higiénico)
    {"codigo": "030", "nombre": "Detergente en Polvo Ariel 2Kg", "precio": 26900, "stock": 75, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8HKgqc_aKcS0OrABlzjz2xiHqQiQwOPnfDJXzPRFabQ&s=10"},
    {"codigo": "031", "nombre": "Jabón de Baño Palmolive x3", "precio": 11200, "stock": 105, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSjeDittM5iqnNji-aYFguLuYoWDMz8uQDJMQhHWMfVf7cTfgGfnZ_pUYsy&s=10"},
    {"codigo": "032", "nombre": "Papel Higiénico Familia 12 Rollos", "precio": 22500, "stock": 90, "sede": "Sede Central", "empresa": "Supermercados El Ahorro", "imagen": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTGn9vkHKlrIoX7X0EztD05bNpNtrsgCtlKu3I09C4ewQ&s=10"}
]

REPORTES_EMPLEADOS = []


# ---------------------------------------------------------------------------
# CAPA DE PERSISTENCIA Y SERVICIOS COMUNES
# Se conserva la estructura original: las listas existentes siguen siendo
# la interfaz principal de los módulos, pero ahora se respaldan en SQLite.
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.getenv("KEEPINVENTORY_DB", os.path.join(BASE_DIR, "keepinventory.sqlite3"))

PRODUCTOS_ARCHIVADOS = []
MOVIMIENTOS_INVENTARIO = []
TRANSFERENCIAS_INVENTARIO = []
NOTIFICACIONES = []
FAVORITOS_CLIENTES = {}
AUDITORIA_SISTEMA = []
PROVEEDORES = []

@contextmanager
def _db_connection():
    carpeta = os.path.dirname(os.path.abspath(DATABASE_PATH))
    if carpeta:
        os.makedirs(carpeta, exist_ok=True)
    conexion = sqlite3.connect(DATABASE_PATH, timeout=20)
    conexion.row_factory = sqlite3.Row
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()

def inicializar_persistencia():
    """Crea el almacén persistente y restaura el último estado guardado."""
    estado_inicial = False
    with _db_connection() as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS estado_aplicacion (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                datos TEXT NOT NULL,
                actualizado_en TEXT NOT NULL
            )
        """)
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS eventos_auditoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                actor TEXT NOT NULL,
                accion TEXT NOT NULL,
                detalle TEXT NOT NULL
            )
        """)
        fila = conexion.execute(
            "SELECT datos FROM estado_aplicacion WHERE id = 1"
        ).fetchone()
        if fila:
            try:
                estado = json.loads(fila["datos"])
                EMPRESAS_REGISTRADAS[:] = estado.get("empresas", EMPRESAS_REGISTRADAS)
                INVENTARIO_SUPER[:] = estado.get("inventario", INVENTARIO_SUPER)
                PEDIDOS_REGISTRADOS[:] = estado.get("pedidos", PEDIDOS_REGISTRADOS)
                REPORTES_EMPLEADOS[:] = estado.get("reportes", REPORTES_EMPLEADOS)
                PRODUCTOS_ARCHIVADOS[:] = estado.get("productos_archivados", [])
                MOVIMIENTOS_INVENTARIO[:] = estado.get("movimientos", [])
                TRANSFERENCIAS_INVENTARIO[:] = estado.get("transferencias", [])
                NOTIFICACIONES[:] = estado.get("notificaciones", [])
                FAVORITOS_CLIENTES.clear()
                FAVORITOS_CLIENTES.update(estado.get("favoritos", {}))
                AUDITORIA_SISTEMA[:] = estado.get("auditoria", [])
                PROVEEDORES[:] = estado.get("proveedores", [])
            except (ValueError, TypeError, KeyError) as exc:
                app.logger.exception("No se pudo restaurar el estado guardado: %s", exc)
                raise RuntimeError(
                    "La base de datos contiene un estado ilegible. "
                    "No se sobrescribió para proteger la información."
                ) from exc
        else:
            estado_inicial = True
    if estado_inicial:
        guardar_estado()


def guardar_estado():
    """Guarda una instantánea consistente de las listas de trabajo."""
    estado = {
        "empresas": EMPRESAS_REGISTRADAS,
        "inventario": INVENTARIO_SUPER,
        "pedidos": PEDIDOS_REGISTRADOS,
        "reportes": REPORTES_EMPLEADOS,
        "productos_archivados": PRODUCTOS_ARCHIVADOS,
        "movimientos": MOVIMIENTOS_INVENTARIO,
        "transferencias": TRANSFERENCIAS_INVENTARIO,
        "notificaciones": NOTIFICACIONES,
        "favoritos": FAVORITOS_CLIENTES,
        "auditoria": AUDITORIA_SISTEMA[-2000:],
        "proveedores": PROVEEDORES,
    }
    contenido = json.dumps(estado, ensure_ascii=False, separators=(",", ":"))
    with _db_connection() as conexion:
        conexion.execute("""
            INSERT INTO estado_aplicacion (id, datos, actualizado_en)
            VALUES (1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                datos = excluded.datos,
                actualizado_en = excluded.actualizado_en
        """, (contenido, obtener_tiempo_local()))

def registrar_auditoria(accion, detalle=""):
    evento = {
        "fecha": obtener_tiempo_local(),
        "actor": session.get("user_nombre") or session.get("cliente_nombre") or session.get("user_type", "sistema"),
        "accion": str(accion)[:100],
        "detalle": str(detalle)[:1000],
    }
    AUDITORIA_SISTEMA.insert(0, evento)
    AUDITORIA_SISTEMA[:] = AUDITORIA_SISTEMA[:2000]
    try:
        with _db_connection() as conexion:
            conexion.execute(
                "INSERT INTO eventos_auditoria (fecha, actor, accion, detalle) VALUES (?, ?, ?, ?)",
                (evento["fecha"], evento["actor"], evento["accion"], evento["detalle"])
            )
    except sqlite3.Error:
        app.logger.exception("No fue posible registrar el evento de auditoría")

def crear_notificacion(destinatario, mensaje, tipo="informacion", referencia=None):
    NOTIFICACIONES.insert(0, {
        "id": secrets.token_hex(8),
        "destinatario": str(destinatario),
        "mensaje": str(mensaje)[:500],
        "tipo": tipo,
        "referencia": referencia,
        "fecha": obtener_tiempo_local(),
        "leida": False,
    })
    NOTIFICACIONES[:] = NOTIFICACIONES[:5000]

def empresa_de_sesion():
    empresa_nombre = session.get("empresa_nombre")
    empresa_id = session.get("empresa_id")
    return next((e for e in EMPRESAS_REGISTRADAS
                 if (empresa_id is not None and e.get("id") == empresa_id)
                 or (empresa_nombre and e.get("nombre_empresa") == empresa_nombre)), None)

def usuario_autenticado(*roles):
    return session.get("user_type") in roles

def validar_codigo_producto(codigo):
    return bool(re.fullmatch(r"\d{3}", str(codigo or "").strip()))

def buscar_producto(codigo, sede=None, empresa=None):
    codigo = str(codigo or "").strip()
    return next((p for p in INVENTARIO_SUPER
                 if p.get("codigo") == codigo
                 and (sede is None or p.get("sede") == sede)
                 and (empresa is None or p.get("empresa") == empresa)), None)

def _normalizar_items(items):
    """Convierte el carrito enviado por el navegador en líneas validadas."""
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
    total = 0
    for codigo, cantidad in lineas.items():
        producto = buscar_producto(codigo, sede, empresa)
        if not producto:
            raise ValueError(f"El producto #{codigo} no existe en el inventario de esta sede.")
        if descontar and int(producto.get("stock", 0)) < cantidad:
            raise ValueError(f"Stock insuficiente para {producto.get('nombre', codigo)}.")
        precio = float(producto.get("precio", 0))
        if precio < 0:
            raise ValueError("Se encontró un precio inválido en el inventario.")
        detalle.append({
            "codigo": codigo,
            "nombre": producto.get("nombre", ""),
            "cantidad": cantidad,
            "precio_unitario": precio,
            "subtotal": precio * cantidad,
        })
        total += precio * cantidad
    if descontar:
        for linea in detalle:
            producto = buscar_producto(linea["codigo"], sede, empresa)
            producto["stock"] = int(producto.get("stock", 0)) - linea["cantidad"]
            MOVIMIENTOS_INVENTARIO.insert(0, {
                "fecha": obtener_tiempo_local(),
                "codigo": linea["codigo"],
                "producto": linea["nombre"],
                "cantidad": -linea["cantidad"],
                "tipo": "venta",
                "sede": sede,
                "empresa": empresa,
                "responsable": session.get("user_nombre") or session.get("cliente_nombre", "Cliente"),
            })
    return detalle, total

def es_venta_cerrada(pedido):
    return pedido.get("tipo") == "venta" or (
        pedido.get("tipo") == "pedido_recoger" and pedido.get("estado") == "entregado"
    )

def _importe_seguro(valor):
    try:
        importe = float(valor)
    except (TypeError, ValueError):
        raise ValueError("El importe no es válido.")
    if not math.isfinite(importe) or importe < 0 or importe > 1_000_000_000:
        raise ValueError("El importe está fuera del rango permitido.")
    return round(importe, 2)


def hashear_password(password):
    sal = secrets.token_bytes(16)
    derivada = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), sal, 260000)
    return "pbkdf2_sha256$260000$" + sal.hex() + "$" + derivada.hex()

def verificar_password(password_guardada, password_ingresada):
    guardada = str(password_guardada or "")
    if guardada.startswith("pbkdf2_sha256$"):
        try:
            _, iteraciones, sal_hex, hash_hex = guardada.split("$", 3)
            calculado = hashlib.pbkdf2_hmac(
                "sha256", str(password_ingresada).encode("utf-8"),
                bytes.fromhex(sal_hex), int(iteraciones)
            ).hex()
            return hmac.compare_digest(calculado, hash_hex)
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(guardada, str(password_ingresada or ""))

inicializar_persistencia()

# CSS COMPLETO CON ANIMACIONES Y DISEÑO MEJORADO
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

/* ANIMACIONES AVANZADAS */
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

/* BRANDING */
.brand{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.logo{width:44px;height:44px;background:var(--primary-gradient);color:white;display:flex;align-items:center;justify-content:center;border-radius:14px;font-weight:800;font-size:20px;flex-shrink:0;box-shadow:0 8px 16px rgba(15,138,95,0.3); transition: transform 0.3s ease;}
.logo:hover{transform: rotate(5deg) scale(1.05);}
.brand-large{color:white;margin-bottom:35px; text-align:center;}
.logo-large{width:90px;height:90px;background:white;color:var(--primary);font-size:40px;font-weight:900;border-radius:24px;display:flex;align-items:center;justify-content:center;margin:0 auto 20px;box-shadow:0 20px 40px rgba(0,0,0,0.3); animation: float 4s ease-in-out infinite;}
.brand-large h1{font-size:42px; margin-bottom:8px; font-weight:800; letter-spacing:-1px;}
.brand-large p{opacity:0.9; font-size:16px; font-weight:300;}

/* LANDING SELECTOR */
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

/* FORMULARIOS Y LOGIN */
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

/* DASHBOARD STAFF */
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

/* TIENDA CLIENTE */
.header-cliente{display:flex; justify-content:space-between; align-items:center; background:white; padding:20px 32px; border-radius:20px; margin-bottom:30px; box-shadow:var(--card-shadow); border:1px solid #f1f5f9;}
.sede-selector-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;margin:25px 0;}
.sede-card-interactive{background:white;border:2px solid var(--gray);border-radius:20px;padding:28px 22px;text-align:center;cursor:pointer;transition:all .3s ease; position:relative;}
.sede-card-interactive:hover{border-color:var(--primary);transform:translateY(-6px); box-shadow:0 15px 35px rgba(15,138,95,0.12);}
.sede-card-interactive.active{border-color:var(--primary);background:var(--primary-light); animation:pulseGlow 2s infinite;}
.product-card{background:white; border-radius:20px; border:1px solid #e2e8f0; padding:22px; display:flex; flex-direction:column; justify-content:space-between; transition:all 0.3s cubic-bezier(0.16, 1, 0.3, 1); position:relative; overflow:hidden; box-shadow:var(--card-shadow);}
.product-card:hover{transform:translateY(-8px); box-shadow:0 20px 35px rgba(0,0,0,0.08); border-color:var(--primary);}
.product-badge{position:absolute; top:15px; right:15px; background:var(--accent); color:white; font-size:11px; font-weight:800; padding:4px 10px; border-radius:30px; letter-spacing:0.5px; box-shadow:0 4px 10px rgba(245,158,11,0.3);}
.product-img-container{width:100%; height:160px; border-radius:12px; overflow:hidden; margin-bottom:12px; background:#f1f5f9; display:flex; align-items:center; justify-content:center;}
.product-img-container img{width:100%; height:100%; object-fit:cover; transition:transform 0.4s ease;}
.product-card:hover .product-img-container img{transform:scale(1.08);}

/* CARRITO MODAL Y PASARELA DE PAGOS */
.cart-floating-btn{position:fixed; bottom:30px; right:30px; background:var(--primary-gradient); color:white; padding:16px 26px; border-radius:50px; cursor:pointer; font-weight:700; box-shadow:0 10px 30px rgba(15,138,95,0.4); display:flex; align-items:center; gap:12px; z-index:99; transition:all 0.3s ease;}
.cart-floating-btn:hover{transform:scale(1.08) translateY(-3px); box-shadow:0 15px 35px rgba(15,138,95,0.5);}
.modal{display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.6); backdrop-filter:blur(6px); z-index:1000; justify-content:center; align-items:center;}
.modal-content{background:white; padding:35px; border-radius:24px; width:90%; max-width:520px; position:relative; animation:fadeIn 0.3s ease; box-shadow:0 25px 50px rgba(0,0,0,0.25); max-height:90vh; overflow-y:auto;}
.btn-remove{background:#fee2e2; color:#dc2626; border:none; border-radius:8px; padding:6px 10px; cursor:pointer; font-size:12px; font-weight:700; transition:all 0.2s;}
.btn-remove:hover{background:#fca5a5; transform:scale(1.05);}
.payment-method-box{border:2px solid var(--gray); border-radius:12px; padding:12px 16px; margin:10px 0; cursor:pointer; transition:all 0.2s;}
.payment-method-box:hover{border-color:var(--primary); background:var(--primary-light);}

/* RESPONSIVE */
@media(max-width:800px){
  .selector-grid{grid-template-columns:1fr;}
  .dashboard{flex-direction:column;}
  .sidebar{width:100%;}
  .header-cliente{flex-direction:column; gap:15px; align-items:flex-start;}
}
"""

# LANDING PRINCIPAL
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

# LOGIN STAFF (Maneja Superadmin, Dueños, Managers y Empleados)
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

            <div class="demo-creds">
                <b>Credenciales Demo:</b><br>
                • Dueño Empresa: dueno@elahorro.com / dueno123<br>
                • Manager: manager@elahorro.com / mgr123<br>
                • Empleado (Cajero): empleado@elahorro.com / emp123
            </div>

            <a href="/" style="display:block; margin-top:20px; color:var(--gray-text); text-decoration:none; font-size:13px;">← Volver al inicio</a>
        </div>
    </div>
</body>
</html>
"""

# DASHBOARD SUPERADMIN (Crear empresas y dueños especificando nombre de cadena)
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

# DASHBOARD DUEÑO (Crear sedes, managers, empleados, ver reportes mensuales)
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
            <!-- GESTIÓN DE SEDES -->
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

            <!-- GESTIÓN DE PERSONAL (MANAGERS Y EMPLEADOS) -->
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

            <!-- REPORTES MENSUALES -->
            <div id="sec-reportes" class="tab-sec fade-in" style="display:none;">
                <div class="card" style="display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:15px;">
                    <div><small>Ventas de hoy</small><h2>${{ "{:,.0f}".format(total_hoy|default(0)) }}</h2></div>
                    <div><small>Ventas del mes</small><h2>${{ "{:,.0f}".format(total_mes|default(0)) }}</h2></div>
                    <div><small>Transacciones del mes</small><h2>{{ cantidad_ventas_mes|default(0) }}</h2></div>
                    <div><small>Sedes registradas</small><h2>{{ empresa.sedes|length }}</h2></div>
                </div>
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

# DASHBOARD MANAGER (Agregar productos con código rápido de 3 dígitos e imagen de producto)
HTML_DASHBOARD_MANAGER = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel Manager - {{ user.sede }}</title>
    <style>{{ css | safe }}</style>
    <script>
        async function actualizarPedido(id) {
            const estado = document.getElementById('estado-' + id).value;
            const respuesta = await fetch('/api/pedidos/' + id + '/estado', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({estado})
            });
            const datos = await respuesta.json();
            if(!respuesta.ok) { alert(datos.error || 'No se pudo actualizar el pedido.'); return; }
            alert('Estado del pedido actualizado.');
            location.reload();
        }
        async function responderReporte(event, id) {
            event.preventDefault();
            const respuesta = document.getElementById('respuesta-' + id).value;
            const resuelto = document.getElementById('resuelto-' + id).checked;
            const response = await fetch('/api/reportes/' + id + '/respuesta', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({respuesta, resuelto})
            });
            const data = await response.json();
            if(!response.ok) { alert(data.error || 'No se pudo responder el reporte.'); return; }
            location.reload();
        }
    </script>
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
                <h2>Resumen de la sede {{ user.sede }}</h2>
                <p>Ventas registradas hoy: <b>${{ "{:,.0f}".format(total_hoy|default(0)) }}</b></p>
                <p>Productos con stock bajo: <b>{{ inventario|selectattr('stock', 'le', 5)|list|length }}</b></p>
                <p><a href="/reportes/ventas.csv">Descargar reporte de ventas CSV</a></p>
            </div>
            <div class="card">
                <h2>Pedidos y ventas recientes</h2>
                <table>
                    <thead><tr><th>Fecha</th><th>Cliente / Empleado</th><th>Productos</th><th>Total</th><th>Estado</th><th>Actualizar</th></tr></thead>
                    <tbody>
                    {% for pedido in pedidos %}
                    <tr>
                        <td>{{ pedido.hora }}</td><td>{{ pedido.cliente }}</td>
                        <td>{{ pedido.productos }}</td><td>${{ "{:,.0f}".format(pedido.total) }}</td>
                        <td>{{ pedido.estado or 'registrado' }}</td>
                        <td>
                            {% if pedido.tipo == 'pedido_recoger' and pedido.estado not in ['entregado', 'cancelado'] %}
                            <select id="estado-{{ pedido.id }}">
                                <option value="recibido">Recibido</option><option value="preparando">Preparando</option>
                                <option value="listo_para_recoger">Listo para recoger</option>
                                <option value="entregado">Entregado</option><option value="cancelado">Cancelar</option>
                            </select>
                            <button type="button" onclick="actualizarPedido('{{ pedido.id }}')">Guardar</button>
                            {% else %}—{% endif %}
                        </td>
                    </tr>
                    {% else %}<tr><td colspan="6">No hay pedidos ni ventas registrados.</td></tr>{% endfor %}
                    </tbody>
                </table>
            </div>
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
                            <th>Fotografía</th><th>Estado / Respuesta</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for rep in reportes %}
                        <tr>
                            <td>{{ rep.fecha }}</td>
                            <td><b>{{ rep.empleado }}</b></td>
                            <td>{{ rep.mensaje }}</td>
                            <td>{% if rep.fotografia %}<a href="{{ rep.fotografia }}" target="_blank" rel="noopener">Ver foto</a>{% else %}—{% endif %}</td>
                            <td>
                                {{ rep.estado }}{% if rep.respuesta_manager %}<br>{{ rep.respuesta_manager }}{% endif %}
                                <form onsubmit="responderReporte(event, '{{ rep.id }}')" style="margin-top:6px;">
                                    <input id="respuesta-{{ rep.id }}" placeholder="Respuesta del manager" required>
                                    <label><input id="resuelto-{{ rep.id }}" type="checkbox"> Solucionado</label>
                                    <button type="submit">Responder</button>
                                </form>
                            </td>
                        </tr>
                        {% else %}
                        <tr><td colspan="5" style="text-align:center; color:var(--gray-text);">No hay reportes de empleados pendientes.</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

# DASHBOARD EMPLEADO / CAJERO (Sistema de cobro rápido por código de 3 dígitos + soporte de imágenes y reportes)
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

        function escapeHTML(value) {
            return String(value).replace(/[&<>"']/g, character => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            }[character]));
        }

        function buscarPorCodigoRapido(event) {
            event.preventDefault();
            let codigo = document.getElementById('input-codigo-rapido').value.trim();
            
            // Petición AJAX para buscar el producto por código de 3 dígitos
            fetch('/api/buscar-codigo?codigo=' + codigo)
                .then(res => res.json())
                .then(data => {
                    if(data.encontrado) {
                        carritoCaja.push(data.producto);
                        actualizarCajaUI();
                        document.getElementById('input-codigo-rapido').value = '';
                    } else {
                        alert('❌ Producto con código #' + codigo + ' no encontrado en esta sede.');
                    }
                });
        }

        function quitarItemCaja(index) {
            carritoCaja.splice(index, 1);
            actualizarCajaUI();
        }

        function actualizarCajaUI() {
            let total = carritoCaja.reduce((sum, p) => sum + p.precio, 0);
            document.getElementById('caja-total').innerText = '$' + total.toLocaleString();

            let html = '';
            carritoCaja.forEach((p, idx) => {
                html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid #e2e8f0;">
                    <span>[#${escapeHTML(p.codigo)}] ${escapeHTML(p.nombre)}</span>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <b>$${p.precio.toLocaleString()}</b>
                        <button class="btn-remove" onclick="quitarItemCaja(${idx})">❌</button>
                    </div>
                </div>`;
            });
            document.getElementById('lista-caja-items').innerHTML = html || '<p style="color:var(--gray-text);">Ningún producto agregado a la venta actual</p>';
        }

        function cobrarVenta() {
            if(carritoCaja.length === 0) { alert('Agregue productos usando el código rápido primero'); return; }
            let total = carritoCaja.reduce((sum, p) => sum + p.precio, 0);
            let nombres = carritoCaja.map(p => p.nombre).join(', ');

            fetch('/api/registrar-venta-cajero', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    productos: nombres,
                    items: carritoCaja.map(p => ({codigo: p.codigo, cantidad: 1})),
                    total: total,
                })
            }).then(async res => {
                const data = await res.json();
                if(!res.ok || data.status !== 'ok') {
                    alert(data.mensaje || 'No fue posible registrar la venta.');
                    return;
                }
                alert('✅ ¡Venta cobrada con éxito por $' + Number(data.total).toLocaleString() + '!');
                carritoCaja = [];
                actualizarCajaUI();
            }).catch(() => alert('Error de conexión al registrar la venta.'));
        }
        async function actualizarEstadoEmpleado(id) {
            const estado = document.getElementById('estado-empleado-' + id).value;
            const response = await fetch('/api/pedidos/' + id + '/estado', {
                method: 'POST', headers: {'Content-Type':'application/json'},
                body: JSON.stringify({estado})
            });
            const data = await response.json();
            if(!response.ok) { alert(data.error || 'No se pudo actualizar el pedido.'); return; }
            location.reload();
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
            <div class="card">
                <h2>Pedidos para preparar y entregar</h2>
                <table>
                    <thead><tr><th>Pedido</th><th>Cliente</th><th>Productos</th><th>Estado</th><th>Acción</th></tr></thead>
                    <tbody>
                    {% for pedido in pedidos %}
                    <tr>
                        <td>{{ pedido.id }}</td><td>{{ pedido.cliente }}</td><td>{{ pedido.productos }}</td>
                        <td>{{ pedido.estado }}</td>
                        <td>
                            <select id="estado-empleado-{{ pedido.id }}">
                                {% if pedido.estado == 'recibido' %}<option value="preparando">Comenzar preparación</option>{% endif %}
                                {% if pedido.estado == 'preparando' %}<option value="listo_para_recoger">Marcar listo</option>{% endif %}
                                {% if pedido.estado == 'listo_para_recoger' %}<option value="entregado">Confirmar entrega</option>{% endif %}
                            </select>
                            <button type="button" onclick="actualizarEstadoEmpleado('{{ pedido.id }}')">Guardar</button>
                        </td>
                    </tr>
                    {% else %}<tr><td colspan="5">No hay pedidos pendientes.</td></tr>{% endfor %}
                    </tbody>
                </table>
            </div>
            <div style="display:grid; grid-template-columns:2fr 1fr; gap:20px;">
                // MÓDULO DE COBRO CON CÓDIGOS RÁPIDOS
                <div class="card">
                    <h2>Módulo de Caja - Búsqueda por Código Rápido</h2>
                    <p style="color:var(--gray-text); font-size:13px; margin-bottom:15px;">Introduce el código de 3 dígitos (Ej: 001, 006, 016, 026) para agregar el producto a la venta.</p>
                    
                    <form onsubmit="buscarPorCodigoRapido(event)" style="display:flex; gap:10px; margin-bottom:20px;">
                        <input type="text" id="input-codigo-rapido" placeholder="Ej: 001" maxlength="3" required style="padding:12px; font-size:18px; font-weight:bold; border:2px solid var(--primary); border-radius:8px; width:150px;">
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

                // RESUMEN DE TICKET DE CAJA
                <div class="card">
                    <h3>Ticket de Venta Actual</h3>
                    <div id="lista-caja-items" style="margin:15px 0; max-height:250px; overflow-y:auto;">
                        <p style="color:var(--gray-text);">Ningún producto agregado</p>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; font-size:18px; border-top:2px solid var(--gray); padding-top:10px;">
                        <span>Total:</span>
                        <b id="caja-total" style="color:var(--primary);">$0</b>
                    </div>
                    <button class="btn" onclick="cobrarVenta()" style="margin-top:15px;">💵 Cobrar Venta</button>
                </div>
            </div>

            // MÓDULO DE REPORTES A MANAGER
            <div class="card" style="margin-top:20px;">
                <h2>Reportar Problema o Incidencia al Manager</h2>
                <form action="/empleado/enviar-reporte" method="POST" enctype="multipart/form-data" style="margin-top:10px;">
                    <textarea name="mensaje" placeholder="Describe aquí si hay un problema en caja, falta de cambio, producto averiado..." required style="padding:12px; border:1px solid var(--gray); border-radius:8px; width:100%; height:80px;"></textarea>
                    <label style="display:block; margin-top:10px;">Fotografía de soporte (JPG, PNG o WEBP; máximo 5 MB)
                        <input type="file" name="fotografia" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp">
                    </label>
                    <button type="submit" class="btn" style="width:auto; padding:10px 20px;">📤 Enviar Reporte al Supervisor</button>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
"""

# PASO 1 CLIENTE: SELECCIÓN DE UBICACIÓN Y SEDE
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

# PASO 2 CLIENTE: INICIO DE SESIÓN O REGISTRO
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

            <div style="display:flex; gap:10px; margin-bottom:15px;">
                <button id="tab-login" type="button" class="btn" onclick="alternarModo('login')" style="flex:1;">Ingresar</button>
                <button id="tab-registro" type="button" class="btn btn-outline" onclick="alternarModo('registro')" style="flex:1;">Registrarse</button>
            </div>

            # FORMULARIO LOGIN CLIENTE
            <form id="form-login" action="/login-cliente" method="POST">
                <input type="email" name="email" placeholder="Tu correo electrónico" required>
                <input type="password" name="password" placeholder="Tu contraseña" required>
                <button type="submit" class="btn">🛒 Entrar a Hacer Mercado</button>
            </form>

            # FORMULARIO REGISTRO CLIENTE
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

# CATÁLOGOS CON GRAN VARIEDAD DE PRODUCTOS DE SUPERMERCADO E IMÁGENES CORREGIDAS
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

        function escapeHTML(value) {
            return String(value).replace(/[&<>"']/g, character => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            }[character]));
        }

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
                    <span>${escapeHTML(p.nombre)}</span>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <b>$${p.precio.toLocaleString()}</b>
                        <button class="btn-remove" onclick="quitarProducto(${index})">❌</button>
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
            let itemsPedido = carrito.map(p => ({codigo: p.codigo, cantidad: 1}));

            fetch('/api/crear-pedido', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    productos: detallesItems,
                    items: itemsPedido,
                    total: total,
                    metodo_pago: metodoNombre
                })
            }).then(async res => {
                const data = await res.json();
                if(!res.ok || data.status !== 'ok') {
                    alert(data.mensaje || 'No fue posible registrar el pedido.');
                    return;
                }
                alert('🎉 Pedido recibido. Número: ' + data.pedido_id + '. Estado: ' + data.estado + '.');
                carrito = [];
                actualizarCarritoUI();
                cerrarCarrito();
            }).catch(() => alert('Error de conexión al registrar el pedido.'));
        }

        function filtrarCategoria(cat, btn) {
            document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('btn'));
            document.querySelectorAll('.cat-btn').forEach(b => b.classList.add('btn-outline'));
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
        
        # HEADER CLIENTE
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
                <a href="/mis-pedidos" class="btn btn-outline" style="text-decoration:none;">Mis pedidos</a>
                <a href="/cliente-ubicacion" class="btn btn-outline" style="padding:8px 12px; font-size:12px;">📍 Cambiar Sede</a>
                <a href="/logout" class="btn btn-danger" style="padding:8px 12px; font-size:12px;">Cerrar Sesión</a>
            </div>
        </div>

        # FILTROS DE CATEGORÍA DE SUPERMERCADO
        <div style="display:flex; gap:10px; margin-bottom:25px; overflow-x:auto; padding-bottom:5px;">
            <button class="btn cat-btn" onclick="filtrarCategoria('todos', this)">🏪 Todo el Mercado</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('lacteos', this)">🥛 Lácteos y Huevos</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('despensa', this)">🌾 Despensa y Granos</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('carnes', this)">🥩 Carnes y Embutidos</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('frutas', this)">🍎 Frutas y Verduras</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('bebidas', this)">🥤 Bebidas</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('aseo', this)">🧹 Aseo y Limpieza</button>
        </div>

        # GRID DE PRODUCTOS DE SUPERMERCADO CON IMÁGENES CORREGIDAS
        <div class="grid">
            
            # LÁCTEOS Y HUEVOS
            <div class="product-card" data-cat="lacteos">
                <span class="product-badge">OFERTA</span>
                <div class="product-img-container"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQVO8fktZ9PsqGMtJtLrIpxWMrEry8Zt100S55llzxX3Q&s=10" alt="Huevos AA x30 unidades"></div>
                <h3 style="font-size:16px;">Huevos Frescos AA x30 Unidades</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Cubeta de 30 huevos rojos categoría AA de granja.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$18.500</b>
                    <button class="btn" onclick="agregarProducto('Huevos Frescos AA x30', 18500, '001')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="lacteos">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&auto=format&fit=crop&q=80" alt="Leche Entera 1L Colanta"></div>
                <h3 style="font-size:16px;">Leche Entera Colanta 1L</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Leche pasteurizada enriquecida con vitaminas A y D.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$4.300</b>
                    <button class="btn" onclick="agregarProducto('Leche Entera Colanta 1L', 4300, '002')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="lacteos">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1452195100486-9cc805987862?w=400&auto=format&fit=crop&q=80" alt="Queso Campesino 500g"></div>
                <h3 style="font-size:16px;">Queso Campesino Fresco 500g</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Queso blanco tajado, ideal para desayunos y arepas.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$12.800</b>
                    <button class="btn" onclick="agregarProducto('Queso Campesino 500g', 12800, '003')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            # DESPENSA Y GRANOS
            <div class="product-card" data-cat="despensa">
                <span class="product-badge">MAS VENDIDO</span>
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&auto=format&fit=crop&q=80" alt="Arroz Roa 1Kg"></div>
                <h3 style="font-size:16px;">Arroz Roa Superior 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Arroz blanco de grano entero de la más alta calidad.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$4.800</b>
                    <button class="btn" onclick="agregarProducto('Arroz Roa Superior 1Kg', 4800, '006')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="despensa">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&auto=format&fit=crop&q=80" alt="Aceite Premier 900ml"></div>
                <h3 style="font-size:16px;">Aceite Vegetal Premier 900ml</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Aceite puro libre de grasas trans para cocinar diariamente.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$14.500</b>
                    <button class="btn" onclick="agregarProducto('Aceite Vegetal Premier 900ml', 14500, '007')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="despensa">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=400&auto=format&fit=crop&q=80" alt="Pasta Espagueti Doria 500g"></div>
                <h3 style="font-size:16px;">Pasta Espagueti Doria 500g</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Pasta tradicional fortificada con hierro y nutrición.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$3.800</b>
                    <button class="btn" onclick="agregarProducto('Pasta Espagueti Doria 500g', 3800, '012')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            # CARNES Y EMBUTIDOS
            <div class="product-card" data-cat="carnes">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=400&auto=format&fit=crop&q=80" alt="Pechuga de Pollo 1Kg"></div>
                <h3 style="font-size:16px;">Pechuga de Pollo Entera 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Pechuga limpia, fresca y refrigerada de primera opción.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$16.900</b>
                    <button class="btn" onclick="agregarProducto('Pechuga de Pollo 1Kg', 16900, '016')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="carnes">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1588168333986-5078d3ae3976?w=400&auto=format&fit=crop&q=80" alt="Carne Molida 1Kg"></div>
                <h3 style="font-size:16px;">Carne Molida de Res 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Corte de res magro molido al día sin conservantes.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$24.500</b>
                    <button class="btn" onclick="agregarProducto('Carne Molida de Res 1Kg', 24500, '017')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            # FRUTAS Y VERDURAS
            <div class="product-card" data-cat="frutas">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?w=400&auto=format&fit=crop&q=80" alt="Aguacate Hass 1Kg"></div>
                <h3 style="font-size:16px;">Aguacate Hass Selección 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Aguacates cremosos y perfectos para madurar.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$8.900</b>
                    <button class="btn" onclick="agregarProducto('Aguacate Hass 1Kg', 8900, '021')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="frutas">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400&auto=format&fit=crop&q=80" alt="Manzana Roja 1Kg"></div>
                <h3 style="font-size:16px;">Manzana Roja Importada 1Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Manzanas crujientes y dulces seleccionadas.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$9.500</b>
                    <button class="btn" onclick="agregarProducto('Manzana Roja 1Kg', 9500, '025')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            # BEBIDAS
            <div class="product-card" data-cat="bebidas">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&auto=format&fit=crop&q=80" alt="Café Sello Rojo 500g"></div>
                <h3 style="font-size:16px;">Café Sello Rojo Molido 500g</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Café 100% colombiano de tueste medio y gran aroma.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$18.900</b>
                    <button class="btn" onclick="agregarProducto('Café Sello Rojo 500g', 18900, '026')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="bebidas">
                <div class="product-img-container"><img src="https://images.unsplash.com/photo-1622483767028-3f66f32aef97?w=400&auto=format&fit=crop&q=80" alt="Coca-Cola 1.5L"></div>
                <h3 style="font-size:16px;">Coca-Cola Sabor Original 1.5L</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Gaseosa refrescante ideal para acompañar tus comidas.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$6.200</b>
                    <button class="btn" onclick="agregarProducto('Coca-Cola 1.5L', 6200, '027')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            # ASEO Y LIMPIEZA
            <div class="product-card" data-cat="aseo">
                <div class="product-img-container"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQxsUE3LQsQMoxScMRP2K-RuDYFVLafI9H-mJXnETKUKTCTBl0bkF_vPIlh&s=10" alt="Detergente Ariel 2Kg"></div>
                <h3 style="font-size:16px;">Detergente en Polvo Ariel 2Kg</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Limpieza profunda y remoce de manchas difíciles en la ropa.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$26.900</b>
                    <button class="btn" onclick="agregarProducto('Detergente Ariel 2Kg', 26900, '030')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="aseo">
                <div class="product-img-container"><img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTEvjy-zrI9DcLCFmEKgE1NFuS60y0_AE8FFKuY6ybZFg&s" alt="Papel Higiénico Familia 12 Rollos"></div>
                <h3 style="font-size:16px;">Papel Higiénico Familia 12 Rollos</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Rendidor, doble hoja acolchada y suavidad superior.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$22.500</b>
                    <button class="btn" onclick="agregarProducto('Papel Higiénico Familia x12', 22500, '032')" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            # PRODUCTOS DINÁMICOS SUBIDOS POR MANAGERS
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
                    <button class="btn" onclick="agregarProducto({{ prod.nombre|tojson }}, {{ prod.precio }}, {{ prod.codigo|tojson }})" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>
            {% endfor %}

        </div>
    </div>

    # BOTÓN FLOTANTE DEL CARRITO
    <div class="cart-floating-btn" onclick="abrirCarrito()">
        🛒 Carrito de Mercado (<span id="cart-count">0</span>)
    </div>

    # MODAL DEL CARRITO Y PASARELA DE PAGOS
    <div id="modal-carrito" class="modal">
        <div class="modal-content">
            
            # PASO A: REVISIÓN DE CARRITO
            <div id="paso-carrito">
                <h3>Tu Pedido - <span style="color:var(--primary);">{{ sede_actual }}</span></h3>
                <div id="cart-items" style="margin:20px 0; max-height:220px; overflow-y:auto;">
                    <p style="color:var(--gray-text);">El carrito está vacío</p>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:18px; border-top:2px solid var(--gray); padding-top:10px;">
                    <span>Total a Pagar:</span>
                    <b id="cart-total" style="color:var(--primary);">$0</b>
                </div>
                <button class="btn" onclick="irAPago()" style="margin-top:20px;">💳 Proceder al Pago Seguro</button>
                <button class="btn btn-outline" onclick="cerrarCarrito()" style="margin-top:8px;">Seguir Mercando</button>
            </div>

            # PASO B: MÉTODOS DE PAGO REALES CON DATOS INVENTADOS
            <div id="paso-pago" style="display:none;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <h3>Selecciona Método de Pago</h3>
                    <b id="monto-pagar" style="color:var(--primary); font-size:18px;">$0</b>
                </div>
                <p style="font-size:13px; color:var(--gray-text); margin-bottom:15px;">Pasarela integrada simulada (Rellena con datos ficticios)</p>

                # Selector de métodos
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

                # FORMULARIO 1: TARJETA
                <div id="pago-tarjeta" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Datos de la Tarjeta (Inventados)</p>
                    <input type="text" placeholder="Número de Tarjeta (ej: 4532 •••• •••• 8890)" value="4532 8821 9012 3456" style="padding:10px; font-size:13px;">
                    <div style="display:flex; gap:10px;">
                        <input type="text" placeholder="MM/AA" value="12/28" style="padding:10px; font-size:13px;">
                        <input type="text" placeholder="CVV" value="482" style="padding:10px; font-size:13px;">
                    </div>
                    <button class="btn" onclick="confirmarPagoFinal('Tarjeta de Crédito')">Pagar Mercado</button>
                </div>

                # FORMULARIO 2: PSE
                <div id="pago-pse" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Conexión Bancaria PSE (Inventado)</p>
                    <select style="padding:10px; font-size:13px; width:100%; border:1px solid var(--gray); border-radius:8px; margin-bottom:10px;">
                        <option>Bancolombia (Demo)</option>
                        <option>Banco de Bogotá (Demo)</option>
                        <option>Davivienda (Demo)</option>
                        <option>BBVA Colombia (Demo)</option>
                    </select>
                    <input type="text" placeholder="Correo electrónico asociado" value="cliente.demo@correo.com" style="padding:10px; font-size:13px;">
                    <button class="btn" onclick="confirmarPagoFinal('PSE Bancario')">Autorizar Pago en Banco</button>
                </div>

                # FORMULARIO 3: NEQUI
                <div id="pago-nequi" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Billetera Móvil (Inventado)</p>
                    <input type="text" placeholder="Número Celular (ej: 310 456 7890)" value="312 456 7890" style="padding:10px; font-size:13px;">
                    <button class="btn" onclick="confirmarPagoFinal('Nequi/Daviplata')">Generar Notificación Push</button>
                </div>

                # FORMULARIO 4: EFECTIVO
                <div id="pago-efectivo" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Pago contra entrega</p>
                    <input type="text" placeholder="¿Con cuánto dinero vas a pagar?" value="$100.000" style="padding:10px; font-size:13px;">
                    <button class="btn" onclick="confirmarPagoFinal('Efectivo contra entrega')">Confirmar Mercado</button>
                </div>

                <button class="btn btn-outline" onclick="abrirCarrito()" style="margin-top:15px;">← Volver al Carrito</button>
            </div>

        </div>
    </div>
</body>
</html>
"""

# DASHBOARD STAFF ANTIGUO
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Panel - Staff</title>
    <style>{{ css | safe }}</style>
    <script>
        function escapeHTML(value) {
            return String(value).replace(/[&<>"']/g, character => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
            }[character]));
        }

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
                            <td><b>${escapeHTML(p.hora)}</b></td>
                            <td>${escapeHTML(p.cliente)}</td>
                            <td>${escapeHTML(p.sede)}</td>
                            <td>${escapeHTML(p.productos)}</td>
                            <td><span class="tag" style="background:#3b82f6;">${escapeHTML(p.metodo_pago || 'Tarjeta')}</span></td>
                            <td><b style="color:var(--primary);">$${p.total.toLocaleString()}</b></td>
                        </tr>`;
                    });
                    tabla.innerHTML = html;
                });
        }

        setInterval(cargarPedidosEnTiempoReal, 2000);
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

# RUTAS Y CONTROLADORES FLASK
@app.route('/')
def inicio():
    return render_template_string(HTML_LANDING, css=CSS_ESTILOS)

# RUTAS LOGIN STAFF JERÁRQUICO
@app.route('/login-staff', methods=['GET', 'POST'])
def login_staff():
    error = None
    if request.method == 'POST':
        usuario = (request.form.get('usuario') or '').strip().lower()
        password = request.form.get('password') or ''

        if usuario == ADMIN_EMAIL.lower() and verificar_password(ADMIN_PASSWORD, password):
            session.clear()
            session.permanent = True
            session['user_type'] = 'superadmin'
            registrar_auditoria("inicio_sesion", "Superadministrador")
            return redirect(url_for('superadmin_dashboard'))

        for emp in EMPRESAS_REGISTRADAS:
            if emp.get('email_dueno', '').lower() == usuario and verificar_password(emp.get('password_dueno'), password):
                session.clear()
                session.permanent = True
                session['user_type'] = 'dueno'
                session['empresa_id'] = emp['id']
                session['empresa_nombre'] = emp['nombre_empresa']
                registrar_auditoria("inicio_sesion", "Dueño: " + emp['nombre_empresa'])
                return redirect(url_for('dueno_dashboard'))

            for staff in emp.get('usuarios_staff', []):
                if staff.get('email', '').lower() == usuario and verificar_password(staff.get('password'), password):
                    session.clear()
                    session.permanent = True
                    session['user_type'] = staff['rol']
                    session['user_nombre'] = staff['nombre']
                    session['user_sede'] = staff['sede']
                    session['empresa_nombre'] = emp['nombre_empresa']
                    registrar_auditoria("inicio_sesion", staff['rol'] + ": " + staff['email'])
                    guardar_estado()
                    if staff['rol'] == 'manager':
                        return redirect(url_for('manager_dashboard'))
                    return redirect(url_for('empleado_dashboard'))

        error = "Credenciales incorrectas o usuario no encontrado"
    return render_template_string(HTML_LOGIN_STAFF, css=CSS_ESTILOS, error=error)

@app.route('/superadmin/dashboard')
def superadmin_dashboard():
    if session.get('user_type') != 'superadmin':
        return redirect(url_for('login_staff'))
    return render_template_string(HTML_DASHBOARD_SUPERADMIN, css=CSS_ESTILOS, empresas=EMPRESAS_REGISTRADAS)

@app.route('/superadmin/crear-empresa', methods=['POST'])
def superadmin_crear_empresa():
    if not usuario_autenticado('superadmin'):
        return redirect(url_for('login_staff'))
    nombre = (request.form.get('nombre_empresa') or '').strip()
    email = (request.form.get('email_dueno') or '').strip().lower()
    password = request.form.get('password_dueno') or ''
    if not nombre or not email or len(password) < 8:
        return redirect(url_for('superadmin_dashboard'))
    correos_existentes = [e.get('email_dueno', '').lower() for e in EMPRESAS_REGISTRADAS]
    correos_existentes += [u.get('email', '').lower() for e in EMPRESAS_REGISTRADAS for u in e.get('usuarios_staff', [])]
    if email in correos_existentes:
        return redirect(url_for('superadmin_dashboard'))
    nueva_empresa = {
        "id": max([int(e.get("id", 0)) for e in EMPRESAS_REGISTRADAS] + [0]) + 1,
        "nombre_empresa": nombre,
        "email_dueno": email,
        "password_dueno": hashear_password(password),
        "sedes": [],
        "usuarios_staff": []
    }
    EMPRESAS_REGISTRADAS.append(nueva_empresa)
    registrar_auditoria("empresa_creada", nombre)
    guardar_estado()
    return redirect(url_for('superadmin_dashboard'))

@app.route('/dueno/dashboard')
def dueno_dashboard():
    if not usuario_autenticado('dueno'):
        return redirect(url_for('login_staff'))
    empresa = empresa_de_sesion()
    if not empresa:
        session.clear()
        return redirect(url_for('login_staff'))
    pedidos_empresa = [p for p in PEDIDOS_REGISTRADOS if p.get('empresa') == empresa['nombre_empresa']]
    mes_actual = obtener_tiempo_local()[:7]
    ventas_mes = [p for p in pedidos_empresa if str(p.get('hora', '')).startswith(mes_actual) and es_venta_cerrada(p)]
    total_mes = sum(float(p.get('total', 0) or 0) for p in ventas_mes)
    ventas_hoy = [p for p in pedidos_empresa if str(p.get('hora', '')).startswith(obtener_tiempo_local()[:10]) and es_venta_cerrada(p)]
    return render_template_string(
        HTML_DASHBOARD_DUENO, css=CSS_ESTILOS, empresa=empresa,
        pedidos_empresa=pedidos_empresa, total_mes=total_mes,
        cantidad_ventas_mes=len(ventas_mes), total_hoy=sum(float(p.get('total', 0) or 0) for p in ventas_hoy)
    )

@app.route('/dueno/crear-sede', methods=['POST'])
def dueno_crear_sede():
    if not usuario_autenticado('dueno'):
        return redirect(url_for('login_staff'))
    empresa = empresa_de_sesion()
    nombre = (request.form.get('nombre_sede') or '').strip()
    direccion = (request.form.get('direccion_sede') or '').strip()
    if not empresa or not nombre or not direccion:
        return redirect(url_for('dueno_dashboard'))
    if any(s.get('nombre', '').lower() == nombre.lower() for s in empresa.get('sedes', [])):
        return redirect(url_for('dueno_dashboard'))
    empresa['sedes'].append({"nombre": nombre, "direccion": direccion})
    registrar_auditoria("sede_creada", nombre)
    guardar_estado()
    return redirect(url_for('dueno_dashboard'))

@app.route('/dueno/crear-personal', methods=['POST'])
def dueno_crear_personal():
    if not usuario_autenticado('dueno'):
        return redirect(url_for('login_staff'))
    empresa = empresa_de_sesion()
    nombre = (request.form.get('nombre') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    rol = request.form.get('rol') or ''
    sede = request.form.get('sede') or ''
    if not empresa or not nombre or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return redirect(url_for('dueno_dashboard'))
    if len(password) < 8 or rol not in ('manager', 'empleado'):
        return redirect(url_for('dueno_dashboard'))
    if sede not in [s.get('nombre') for s in empresa.get('sedes', [])]:
        return redirect(url_for('dueno_dashboard'))
    correos = [e.get('email_dueno', '').lower() for e in EMPRESAS_REGISTRADAS]
    correos += [u.get('email', '').lower() for e in EMPRESAS_REGISTRADAS for u in e.get('usuarios_staff', [])]
    if email in correos:
        return redirect(url_for('dueno_dashboard'))
    empresa['usuarios_staff'].append({
        "nombre": nombre, "email": email, "password": hashear_password(password),
        "rol": rol, "sede": sede
    })
    registrar_auditoria("personal_creado", f"{email} / {rol} / {sede}")
    guardar_estado()
    return redirect(url_for('dueno_dashboard'))

@app.route('/dueno/eliminar-personal', methods=['POST'])
def dueno_eliminar_personal():
    if not usuario_autenticado('dueno'):
        return redirect(url_for('login_staff'))
    email_eliminar = (request.form.get('email') or '').strip().lower()
    empresa = empresa_de_sesion()
    if not empresa:
        return redirect(url_for('login_staff'))
    antes = len(empresa.get('usuarios_staff', []))
    empresa['usuarios_staff'] = [s for s in empresa['usuarios_staff'] if s.get('email', '').lower() != email_eliminar]
    if len(empresa['usuarios_staff']) != antes:
        registrar_auditoria("personal_eliminado", email_eliminar)
        guardar_estado()
    return redirect(url_for('dueno_dashboard'))

@app.route('/manager/dashboard')
def manager_dashboard():
    if not usuario_autenticado('manager'):
        return redirect(url_for('login_staff'))
    user_sede = session.get('user_sede')
    empresa_nombre = session.get('empresa_nombre')
    inv_sede = [i for i in INVENTARIO_SUPER if i.get('sede') == user_sede and i.get('empresa') == empresa_nombre]
    rep_sede = [r for r in REPORTES_EMPLEADOS if r.get('sede') == user_sede and r.get('empresa') == empresa_nombre]
    pedidos_sede = [p for p in PEDIDOS_REGISTRADOS if p.get('sede') == user_sede and p.get('empresa') == empresa_nombre]
    ventas_hoy = [p for p in pedidos_sede if es_venta_cerrada(p) and str(p.get('hora', '')).startswith(obtener_tiempo_local()[:10])]
    return render_template_string(
        HTML_DASHBOARD_MANAGER, css=CSS_ESTILOS,
        user={'sede': user_sede}, inventario=inv_sede, reportes=rep_sede,
        pedidos=pedidos_sede, total_hoy=sum(float(p.get('total', 0) or 0) for p in ventas_hoy),
        error=request.args.get('error')
    )

@app.route('/manager/agregar-producto', methods=['POST'])
def manager_agregar_producto():
    if not usuario_autenticado('manager'):
        return redirect(url_for('login_staff'))
    codigo = (request.form.get('codigo') or '').strip()
    nombre = (request.form.get('nombre') or '').strip()
    user_sede = session.get('user_sede')
    empresa_nombre = session.get('empresa_nombre')
    try:
        precio = _importe_seguro(request.form.get('precio', 0))
        stock = int(request.form.get('stock', 0))
    except (ValueError, TypeError):
        return redirect(url_for('manager_dashboard', error="Precio o stock inválido."))
    if not validar_codigo_producto(codigo):
        return redirect(url_for('manager_dashboard', error="El código debe tener exactamente tres dígitos."))
    codigo_usado = any(p.get('codigo') == codigo for p in INVENTARIO_SUPER) or any(
        p.get('codigo') == codigo for p in PRODUCTOS_ARCHIVADOS
    )
    if codigo_usado:
        return redirect(url_for('manager_dashboard', error=f"El código #{codigo} ya fue utilizado y no puede reutilizarse."))
    imagen = (request.form.get('imagen') or '').strip()
    if imagen and not imagen.lower().startswith(('https://', 'http://')):
        return redirect(url_for('manager_dashboard', error="La imagen debe usar una dirección HTTP o HTTPS."))
    if not nombre or stock < 0 or stock > 1_000_000 or precio <= 0:
        return redirect(url_for('manager_dashboard', error="Completa nombre, precio y stock con valores válidos."))
    empresa = empresa_de_sesion()
    if not empresa or user_sede not in [s.get('nombre') for s in empresa.get('sedes', [])]:
        return redirect(url_for('login_staff'))
    INVENTARIO_SUPER.append({
        "codigo": codigo, "nombre": nombre, "precio": precio, "stock": stock,
        "sede": user_sede, "empresa": empresa_nombre,
        "imagen": imagen,
        "stock_minimo": 5, "activo": True
    })
    MOVIMIENTOS_INVENTARIO.insert(0, {
        "fecha": obtener_tiempo_local(), "codigo": codigo, "producto": nombre,
        "cantidad": stock, "tipo": "alta_inicial", "sede": user_sede,
        "empresa": empresa_nombre, "responsable": session.get('user_nombre')
    })
    registrar_auditoria("producto_creado", f"{codigo} - {nombre} - {user_sede}")
    guardar_estado()
    return redirect(url_for('manager_dashboard'))

@app.route('/empleado/dashboard')
def empleado_dashboard():
    if not usuario_autenticado('empleado'):
        return redirect(url_for('login_staff'))
    user_sede = session.get('user_sede')
    empresa_nombre = session.get('empresa_nombre')
    inv_sede = [i for i in INVENTARIO_SUPER if i.get('sede') == user_sede and i.get('empresa') == empresa_nombre]
    return render_template_string(
        HTML_DASHBOARD_EMPLEADO, css=CSS_ESTILOS,
        user={'nombre': session.get('user_nombre'), 'sede': user_sede},
        inventario=inv_sede,
        pedidos=[p for p in PEDIDOS_REGISTRADOS if p.get('empresa') == empresa_nombre
                 and p.get('sede') == user_sede and p.get('tipo') == 'pedido_recoger'
                 and p.get('estado') not in ('entregado', 'cancelado')]
    )

@app.route('/api/buscar-codigo', methods=['GET'])
def buscar_codigo():
    if not usuario_autenticado('empleado'):
        return jsonify({'encontrado': False, 'error': 'No autorizado'}), 401
    codigo = request.args.get('codigo', '').strip()
    user_sede = session.get('user_sede')
    producto = buscar_producto(codigo, user_sede, session.get('empresa_nombre'))
    if producto and int(producto.get('stock', 0)) > 0:
        return jsonify({'encontrado': True, 'producto': {
            'codigo': producto['codigo'], 'nombre': producto['nombre'],
            'precio': producto['precio'], 'stock': producto['stock']
        }})
    return jsonify({'encontrado': False, 'error': 'Producto no disponible'})

@app.route('/api/registrar-venta-cajero', methods=['POST'])
def registrar_venta_cajero():
    if not usuario_autenticado('empleado'):
        return jsonify({'status': 'error', 'mensaje': 'No autorizado'}), 401
    data = request.get_json(silent=True) or {}
    try:
        detalle, total = procesar_items_inventario(
            data.get('items'), session.get('user_sede'), session.get('empresa_nombre'), descontar=True
        )
    except ValueError as exc:
        return jsonify({'status': 'error', 'mensaje': str(exc)}), 400
    nuevo_pedido = {
        'id': secrets.token_hex(8), 'hora': obtener_tiempo_local(),
        'cliente': session.get('user_nombre', 'Cajero'),
        'empleado': session.get('user_nombre'),
        'sede': session.get('user_sede'),
        'productos': ', '.join(f"{x['nombre']} x{x['cantidad']}" for x in detalle),
        'items': detalle, 'total': total, 'metodo_pago': 'Caja Registradora',
        'empresa': session.get('empresa_nombre'), 'tipo': 'venta',
        'estado': 'entregado', 'actualizado_en': obtener_tiempo_local()
    }
    PEDIDOS_REGISTRADOS.insert(0, nuevo_pedido)
    registrar_auditoria("venta_registrada", f"{nuevo_pedido['id']} / ${total}")
    guardar_estado()
    return jsonify({'status': 'ok', 'pedido_id': nuevo_pedido['id'], 'total': total})

@app.route('/empleado/enviar-reporte', methods=['POST'])
def empleado_enviar_reporte():
    if not usuario_autenticado('empleado'):
        return redirect(url_for('login_staff'))
    mensaje = (request.form.get('mensaje') or '').strip()
    if not mensaje or len(mensaje) > 2000:
        return redirect(url_for('empleado_dashboard'))
    fotografia = request.files.get('fotografia')
    ruta_fotografia = ''
    if fotografia and fotografia.filename:
        nombre_seguro = secure_filename(fotografia.filename)
        extension = os.path.splitext(nombre_seguro)[1].lower()
        if extension not in ('.jpg', '.jpeg', '.png', '.webp'):
            return redirect(url_for('empleado_dashboard'))
        carpeta_reportes = os.path.join(BASE_DIR, 'static', 'reportes')
        os.makedirs(carpeta_reportes, exist_ok=True)
        nombre_archivo = secrets.token_hex(16) + extension
        fotografia.save(os.path.join(carpeta_reportes, nombre_archivo))
        ruta_fotografia = '/static/reportes/' + nombre_archivo
    reporte = {
        'id': secrets.token_hex(8), 'fecha': obtener_tiempo_local(),
        'empleado': session.get('user_nombre'), 'sede': session.get('user_sede'),
        'empresa': session.get('empresa_nombre'), 'mensaje': mensaje,
        'fotografia': ruta_fotografia, 'estado': 'pendiente',
        'respuesta_manager': '', 'resuelto': False
    }
    REPORTES_EMPLEADOS.insert(0, reporte)
    crear_notificacion(session.get('empresa_nombre'), f"Nuevo reporte de {reporte['empleado']} en {reporte['sede']}.", "reporte", reporte['id'])
    registrar_auditoria("reporte_empleado", mensaje[:200])
    guardar_estado()
    return redirect(url_for('empleado_dashboard'))

@app.route('/cliente-ubicacion')
def cliente_ubicacion():
    return render_template_string(HTML_CLIENTE_UBICACION, css=CSS_ESTILOS)

@app.route('/api/set-sede', methods=['POST'])
def set_sede():
    data = request.get_json(silent=True) or {}
    sede_solicitada = (data.get('sede') or '').strip()
    direccion = (data.get('direccion') or '').strip()
    equivalencias = {
        'Sede Principal (Centro)': 'Sede Central',
        'Sede Norte (Plaza)': 'Sede Norte',
        'Sede Sur (Express)': 'Sede Sur Express',
        'Sede Central': 'Sede Central',
        'Sede Norte': 'Sede Norte',
        'Sede Sur Express': 'Sede Sur Express',
    }
    if sede_solicitada not in equivalencias:
        return jsonify({'status': 'error', 'mensaje': 'Sede no válida'}), 400
    session['sede_cliente'] = sede_solicitada
    session['sede'] = equivalencias[sede_solicitada]
    session['direccion_sede'] = direccion[:250]
    return jsonify({'status': 'ok'})

@app.route('/cliente-auth')
def cliente_auth():
    sede = session.get('sede', 'No seleccionada')
    return render_template_string(HTML_CLIENTE_AUTH, css=CSS_ESTILOS, sede_seleccionada=sede)

@app.route('/login-cliente', methods=['POST'])
def login_cliente():
    email = (request.form.get('email') or '').strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return redirect(url_for('cliente_auth'))
    session['user_type'] = 'cliente'
    session['cliente_email'] = email
    session['cliente_nombre'] = email.split('@')[0].replace('.', ' ').title()
    session.permanent = True
    return redirect(url_for('tienda'))

@app.route('/registro-cliente', methods=['POST'])
def registro_cliente():
    nombre = (request.form.get('nombre') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    if not nombre or len(nombre) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return redirect(url_for('cliente_auth'))
    session['user_type'] = 'cliente'
    session['cliente_nombre'] = nombre
    session['cliente_email'] = email
    session.permanent = True
    return redirect(url_for('tienda'))

@app.route('/tienda')
def tienda():
    if session.get('user_type') != 'cliente':
        return redirect(url_for('cliente_ubicacion'))
    sede_actual = session.get('sede', 'Sede Central')
    cliente_nombre = session.get('cliente_nombre', 'Cliente')
    empresa = EMPRESAS_REGISTRADAS[0] if EMPRESAS_REGISTRADAS else None
    empresa_nombre = empresa.get('nombre_empresa') if empresa else 'Supermercados El Ahorro'
    codigos_base = [f"{i:03d}" for i in range(1, 33)]
    productos_dinamicos = [
        i for i in INVENTARIO_SUPER
        if i.get('codigo') not in codigos_base
        and i.get('sede') == sede_actual
        and i.get('empresa') == empresa_nombre
        and int(i.get('stock', 0)) > 0
    ]
    return render_template_string(
        HTML_TIENDA, css=CSS_ESTILOS, sede_actual=sede_actual,
        cliente_nombre=cliente_nombre, productos_dinamicos=productos_dinamicos
    )

@app.route('/api/crear-pedido', methods=['POST'])
def crear_pedido():
    if session.get('user_type') != 'cliente':
        return jsonify({'status': 'error', 'mensaje': 'Inicia sesión para realizar un pedido.'}), 401
    data = request.get_json(silent=True) or {}
    sede = session.get('sede')
    empresa = EMPRESAS_REGISTRADAS[0].get('nombre_empresa') if EMPRESAS_REGISTRADAS else None
    try:
        detalle, total = procesar_items_inventario(data.get('items'), sede, empresa, descontar=True)
    except ValueError as exc:
        return jsonify({'status': 'error', 'mensaje': str(exc)}), 400
    pedido_id = secrets.token_hex(8)
    nuevo_pedido = {
        'id': pedido_id, 'hora': obtener_tiempo_local(),
        'cliente': session.get('cliente_nombre', 'Cliente'),
        'cliente_email': session.get('cliente_email', ''),
        'sede': sede, 'productos': ', '.join(f"{x['nombre']} x{x['cantidad']}" for x in detalle),
        'items': detalle, 'total': total,
        'metodo_pago': str(data.get('metodo_pago', 'Por confirmar'))[:40],
        'empresa': empresa, 'tipo': 'pedido_recoger',
        'estado': 'recibido', 'actualizado_en': obtener_tiempo_local()
    }
    PEDIDOS_REGISTRADOS.insert(0, nuevo_pedido)
    crear_notificacion(empresa, f"Nuevo pedido para recoger #{pedido_id} en {sede}.", "pedido", pedido_id)
    registrar_auditoria("pedido_cliente_creado", f"{pedido_id} / ${total}")
    guardar_estado()
    return jsonify({'status': 'ok', 'pedido_id': pedido_id, 'total': total, 'estado': nuevo_pedido['estado']})

@app.route('/api/pedidos', methods=['GET'])
def obtener_pedidos():
    if not usuario_autenticado('manager', 'dueno', 'superadmin'):
        return jsonify({'error': 'No autorizado'}), 401
    if session.get('user_type') == 'superadmin':
        pedidos = PEDIDOS_REGISTRADOS
    elif session.get('user_type') == 'dueno':
        empresa = empresa_de_sesion()
        pedidos = [p for p in PEDIDOS_REGISTRADOS if empresa and p.get('empresa') == empresa.get('nombre_empresa')]
    else:
        pedidos = [p for p in PEDIDOS_REGISTRADOS
                   if p.get('empresa') == session.get('empresa_nombre')
                   and p.get('sede') == session.get('user_sede')]
    return jsonify(pedidos)



@app.route('/api/pedidos/<pedido_id>/estado', methods=['POST'])
def actualizar_estado_pedido(pedido_id):
    if not usuario_autenticado('manager', 'dueno', 'superadmin', 'empleado'):
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
    transiciones = {
        'recibido': {'preparando', 'cancelado'},
        'preparando': {'listo_para_recoger', 'cancelado'},
        'listo_para_recoger': {'entregado', 'cancelado'},
        'entregado': set(), 'cancelado': set()
    }
    if nuevo_estado not in transiciones.get(estado_anterior, set()):
        return jsonify({'error': f'Transición no permitida: {estado_anterior} -> {nuevo_estado}'}), 409
    if nuevo_estado == 'cancelado':
        for linea in pedido.get('items', []):
            producto = buscar_producto(linea.get('codigo'), pedido.get('sede'), pedido.get('empresa'))
            if producto:
                producto['stock'] = int(producto.get('stock', 0)) + int(linea.get('cantidad', 0))
                MOVIMIENTOS_INVENTARIO.insert(0, {
                    'fecha': obtener_tiempo_local(), 'codigo': linea.get('codigo'),
                    'producto': linea.get('nombre'), 'cantidad': int(linea.get('cantidad', 0)),
                    'tipo': 'reversion_cancelacion', 'sede': pedido.get('sede'),
                    'empresa': pedido.get('empresa'), 'responsable': session.get('user_nombre', rol)
                })
    pedido['estado'] = nuevo_estado
    pedido['actualizado_en'] = obtener_tiempo_local()
    crear_notificacion(pedido.get('cliente_email') or pedido.get('cliente'), f"Tu pedido {pedido_id} cambió a: {nuevo_estado.replace('_', ' ')}.", "pedido", pedido_id)
    registrar_auditoria("estado_pedido", f"{pedido_id}: {estado_anterior} -> {nuevo_estado}")
    guardar_estado()
    return jsonify({'status': 'ok', 'pedido': pedido})

@app.route('/api/reportes/<reporte_id>/respuesta', methods=['POST'])
def responder_reporte(reporte_id):
    if not usuario_autenticado('manager', 'dueno', 'superadmin'):
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
    crear_notificacion(reporte.get('empleado'), f"El manager respondió tu reporte: {respuesta[:180]}", "reporte", reporte_id)
    registrar_auditoria("respuesta_reporte", reporte_id)
    guardar_estado()
    return jsonify({'status': 'ok', 'reporte': reporte})

@app.route('/api/inventario/ajustar', methods=['POST'])
def ajustar_inventario():
    if not usuario_autenticado('manager', 'dueno'):
        return jsonify({'error': 'No autorizado'}), 401
    data = request.get_json(silent=True) or {}
    codigo = str(data.get('codigo', '')).strip()
    tipo = str(data.get('tipo', 'ajuste')).strip().lower()
    try:
        cantidad = int(data.get('cantidad', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Cantidad inválida'}), 400
    if cantidad <= 0 or cantidad > 100000:
        return jsonify({'error': 'La cantidad debe ser positiva y razonable'}), 400
    empresa = session.get('empresa_nombre')
    sede = session.get('user_sede') if session.get('user_type') == 'manager' else str(data.get('sede', '')).strip()
    producto = buscar_producto(codigo, sede, empresa)
    if not producto:
        return jsonify({'error': 'Producto no encontrado en esa sede'}), 404
    if tipo not in ('entrada', 'salida', 'danado', 'ajuste'):
        return jsonify({'error': 'Tipo de movimiento no válido'}), 400
    delta = cantidad if tipo == 'entrada' else -cantidad
    if int(producto.get('stock', 0)) + delta < 0:
        return jsonify({'error': 'No hay stock suficiente para ese movimiento'}), 409
    producto['stock'] = int(producto.get('stock', 0)) + delta
    movimiento = {
        'fecha': obtener_tiempo_local(), 'codigo': codigo, 'producto': producto.get('nombre'),
        'cantidad': delta, 'tipo': tipo, 'sede': sede, 'empresa': empresa,
        'responsable': session.get('user_nombre', 'Dueño'), 'observacion': str(data.get('observacion', ''))[:500]
    }
    MOVIMIENTOS_INVENTARIO.insert(0, movimiento)
    registrar_auditoria("ajuste_inventario", f"{codigo}: {tipo} {cantidad}")
    guardar_estado()
    return jsonify({'status': 'ok', 'stock': producto['stock'], 'movimiento': movimiento})

@app.route('/api/inventario/traslados', methods=['POST'])
def crear_traslado():
    if not usuario_autenticado('manager', 'dueno'):
        return jsonify({'error': 'No autorizado'}), 401
    data = request.get_json(silent=True) or {}
    codigo = str(data.get('codigo', '')).strip()
    destino = str(data.get('destino', '')).strip()
    try:
        cantidad = int(data.get('cantidad', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Cantidad inválida'}), 400
    empresa = next((e for e in EMPRESAS_REGISTRADAS if e.get('nombre_empresa') == session.get('empresa_nombre')), None)
    origen = session.get('user_sede') if session.get('user_type') == 'manager' else str(data.get('origen', '')).strip()
    sedes = [s.get('nombre') for s in empresa.get('sedes', [])] if empresa else []
    if not empresa or destino not in sedes or origen not in sedes or origen == destino or cantidad <= 0:
        return jsonify({'error': 'Origen, destino o cantidad no válidos'}), 400
    producto = buscar_producto(codigo, origen, empresa.get('nombre_empresa'))
    if not producto or int(producto.get('stock', 0)) < cantidad:
        return jsonify({'error': 'Producto no disponible o stock insuficiente'}), 409
    producto['stock'] = int(producto.get('stock', 0)) - cantidad
    traslado = {
        'id': secrets.token_hex(8), 'fecha': obtener_tiempo_local(),
        'codigo': codigo, 'producto': producto.get('nombre'), 'cantidad': cantidad,
        'origen': origen, 'destino': destino, 'empresa': empresa.get('nombre_empresa'),
        'estado': 'en_transito', 'creado_por': session.get('user_nombre')
    }
    TRANSFERENCIAS_INVENTARIO.insert(0, traslado)
    registrar_auditoria("traslado_creado", traslado['id'])
    guardar_estado()
    return jsonify({'status': 'ok', 'traslado': traslado})

@app.route('/api/inventario/traslados/<traslado_id>/recibir', methods=['POST'])
def recibir_traslado(traslado_id):
    if not usuario_autenticado('manager', 'dueno'):
        return jsonify({'error': 'No autorizado'}), 401
    traslado = next((t for t in TRANSFERENCIAS_INVENTARIO if t.get('id') == traslado_id), None)
    if not traslado or traslado.get('estado') != 'en_transito':
        return jsonify({'error': 'Traslado no disponible'}), 404
    if traslado.get('empresa') != session.get('empresa_nombre'):
        return jsonify({'error': 'No autorizado'}), 403
    if session.get('user_type') == 'manager' and traslado.get('destino') != session.get('user_sede'):
        return jsonify({'error': 'Solo la sede destino puede recibirlo'}), 403
    destino_producto = buscar_producto(traslado.get('codigo'), traslado.get('destino'), traslado.get('empresa'))
    if destino_producto:
        destino_producto['stock'] = int(destino_producto.get('stock', 0)) + int(traslado.get('cantidad', 0))
    else:
        origen_producto = next((p for p in INVENTARIO_SUPER if p.get('codigo') == traslado.get('codigo')
                                and p.get('empresa') == traslado.get('empresa')), None)
        if not origen_producto:
            return jsonify({'error': 'No se encontró la ficha maestra del producto'}), 404
        nuevo = dict(origen_producto)
        nuevo.update({'sede': traslado['destino'], 'stock': int(traslado['cantidad'])})
        INVENTARIO_SUPER.append(nuevo)
    traslado['estado'] = 'recibido'
    traslado['recibido_en'] = obtener_tiempo_local()
    registrar_auditoria("traslado_recibido", traslado_id)
    guardar_estado()
    return jsonify({'status': 'ok', 'traslado': traslado})

@app.route('/api/productos/<codigo>/archivar', methods=['POST'])
def archivar_producto(codigo):
    if not usuario_autenticado('manager', 'dueno'):
        return jsonify({'error': 'No autorizado'}), 401
    empresa = session.get('empresa_nombre')
    sede = session.get('user_sede') if session.get('user_type') == 'manager' else request.form.get('sede')
    producto = buscar_producto(codigo, sede, empresa)
    if not producto:
        return jsonify({'error': 'Producto no encontrado'}), 404
    pedido_pendiente = any(
        p.get('estado') not in ('entregado', 'cancelado')
        and any(i.get('codigo') == codigo for i in p.get('items', []))
        for p in PEDIDOS_REGISTRADOS
    )
    if pedido_pendiente:
        return jsonify({'error': 'No se puede archivar: el producto está asociado a pedidos pendientes.'}), 409
    producto['activo'] = False
    PRODUCTOS_ARCHIVADOS.append(dict(producto, archivado_en=obtener_tiempo_local()))
    INVENTARIO_SUPER.remove(producto)
    registrar_auditoria("producto_archivado", f"{codigo} / {producto.get('nombre')}")
    guardar_estado()
    return jsonify({'status': 'ok', 'codigo_reservado': codigo})

@app.route('/api/proveedores', methods=['POST'])
def agregar_proveedor():
    if not usuario_autenticado('manager', 'dueno'):
        return jsonify({'error': 'No autorizado'}), 401
    data = request.get_json(silent=True) or {}
    nombre = str(data.get('nombre', '')).strip()
    contacto = str(data.get('contacto', '')).strip()
    if not nombre or len(nombre) > 150:
        return jsonify({'error': 'Nombre de proveedor no válido'}), 400
    proveedor = {
        'id': secrets.token_hex(8), 'nombre': nombre, 'contacto': contacto[:200],
        'empresa': session.get('empresa_nombre'), 'creado_en': obtener_tiempo_local()
    }
    PROVEEDORES.append(proveedor)
    registrar_auditoria("proveedor_creado", nombre)
    guardar_estado()
    return jsonify({'status': 'ok', 'proveedor': proveedor})


@app.route('/mis-pedidos', methods=['GET'])
def pagina_mis_pedidos():
    if session.get('user_type') != 'cliente':
        return redirect(url_for('cliente_ubicacion'))
    email = session.get('cliente_email')
    pedidos = [p for p in PEDIDOS_REGISTRADOS if p.get('cliente_email') == email]
    return render_template_string("""
    <!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Mis pedidos - KeepInventory</title><style>
    body{font-family:Arial,sans-serif;background:#f1f5f9;color:#1e293b;margin:0;padding:24px}
    main{max-width:1000px;margin:auto}.card{background:white;padding:22px;border-radius:14px;margin:14px 0;box-shadow:0 3px 12px #0000000c}
    table{width:100%;border-collapse:collapse}td,th{padding:11px;border-bottom:1px solid #e2e8f0;text-align:left}
    a{color:#0f8a5f;font-weight:bold}button{padding:9px 14px;border:0;border-radius:8px;background:#0f8a5f;color:white}
    </style></head><body><main><p><a href="/tienda">← Volver a la tienda</a></p><h1>Mis pedidos</h1>
    {% for pedido in pedidos %}<section class="card"><h3>Pedido #{{ pedido.id }}</h3>
    <p>Fecha: {{ pedido.hora }} | Sede: {{ pedido.sede }} | Estado: <b>{{ pedido.estado }}</b></p>
    <p>{{ pedido.productos }}</p><p><b>Total: ${{ "{:,.0f}".format(pedido.total) }}</b></p>
    <a href="/comprobante/{{ pedido.id }}" target="_blank" rel="noopener">Ver comprobante</a>
    </section>{% else %}<section class="card">Todavía no tienes pedidos registrados.</section>{% endfor %}
    </main></body></html>
    """, pedidos=pedidos)

@app.route('/api/mis-pedidos', methods=['GET'])
def mis_pedidos():
    if session.get('user_type') != 'cliente':
        return jsonify({'error': 'No autorizado'}), 401
    email = session.get('cliente_email')
    pedidos = [p for p in PEDIDOS_REGISTRADOS if p.get('cliente_email') == email]
    return jsonify(pedidos)

@app.route('/comprobante/<pedido_id>', methods=['GET'])
def ver_comprobante(pedido_id):
    pedido = next((p for p in PEDIDOS_REGISTRADOS if p.get('id') == pedido_id), None)
    if not pedido:
        return "Comprobante no encontrado", 404
    rol = session.get('user_type')
    autorizado = rol == 'superadmin'
    if rol == 'cliente':
        autorizado = pedido.get('cliente_email') == session.get('cliente_email')
    elif rol == 'dueno':
        autorizado = pedido.get('empresa') == session.get('empresa_nombre')
    elif rol in ('manager', 'empleado'):
        autorizado = pedido.get('empresa') == session.get('empresa_nombre') and pedido.get('sede') == session.get('user_sede')
    if not autorizado:
        return "No autorizado", 403
    return render_template_string("""
    <!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><title>Comprobante</title>
    <style>body{font-family:Arial,sans-serif;max-width:760px;margin:30px auto;padding:20px;color:#1f2937}
    table{width:100%;border-collapse:collapse}td,th{padding:9px;border-bottom:1px solid #ddd;text-align:left}
    .total{text-align:right;font-size:22px;font-weight:bold;margin-top:20px}
    @media print{button{display:none}}</style></head><body>
    <h1>KeepInventory - Comprobante</h1>
    <p><b>Pedido:</b> {{ pedido.id }} | <b>Fecha:</b> {{ pedido.hora }}</p>
    <p><b>Empresa:</b> {{ pedido.empresa }} | <b>Sede:</b> {{ pedido.sede }}</p>
    <p><b>Cliente:</b> {{ pedido.cliente }} | <b>Estado:</b> {{ pedido.estado }}</p>
    <table><thead><tr><th>Código</th><th>Producto</th><th>Cantidad</th><th>Precio</th><th>Subtotal</th></tr></thead><tbody>
    {% for item in pedido.items %}<tr><td>{{ item.codigo }}</td><td>{{ item.nombre }}</td><td>{{ item.cantidad }}</td><td>${{ "{:,.0f}".format(item.precio_unitario) }}</td><td>${{ "{:,.0f}".format(item.subtotal) }}</td></tr>{% endfor %}
    </tbody></table><p><b>Método de pago declarado:</b> {{ pedido.metodo_pago }}</p>
    <div class="total">Total: ${{ "{:,.0f}".format(pedido.total) }}</div>
    <button onclick="window.print()">Imprimir / Guardar como PDF</button>
    </body></html>
    """, pedido=pedido)

@app.route('/api/notificaciones', methods=['GET'])
def listar_notificaciones():
    if not session.get('user_type'):
        return jsonify({'error': 'No autorizado'}), 401
    if session.get('user_type') == 'superadmin':
        destino = None
    elif session.get('user_type') == 'dueno':
        destino = session.get('empresa_nombre')
    elif session.get('user_type') in ('manager', 'empleado'):
        destino = session.get('empresa_nombre')
    else:
        destino = session.get('cliente_email') or session.get('cliente_nombre')
    resultados = [n for n in NOTIFICACIONES if n.get('destinatario') in (destino, session.get('cliente_email'), session.get('cliente_nombre'))]
    return jsonify(resultados[:100])

@app.route('/api/notificaciones/<notificacion_id>/leer', methods=['POST'])
def marcar_notificacion_leida(notificacion_id):
    if not session.get('user_type'):
        return jsonify({'error': 'No autorizado'}), 401
    notificacion = next((n for n in NOTIFICACIONES if n.get('id') == notificacion_id), None)
    if not notificacion:
        return jsonify({'error': 'Notificación no encontrada'}), 404
    if session.get('user_type') != 'superadmin':
        destinatarios_permitidos = {
            session.get('empresa_nombre'), session.get('cliente_email'),
            session.get('cliente_nombre')
        }
        if notificacion.get('destinatario') not in destinatarios_permitidos:
            return jsonify({'error': 'No autorizado'}), 403
    notificacion['leida'] = True
    guardar_estado()
    return jsonify({'status': 'ok'})

@app.route('/api/clientes/favoritos', methods=['GET', 'POST'])
def gestionar_favoritos():
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
    if codigo in favoritos:
        favoritos.remove(codigo)
    else:
        favoritos.append(codigo)
    guardar_estado()
    return jsonify({'status': 'ok', 'favoritos': favoritos})

@app.route('/reportes/ventas.csv', methods=['GET'])
def exportar_ventas_csv():
    if not usuario_autenticado('manager', 'dueno', 'superadmin'):
        return redirect(url_for('login_staff'))
    if session.get('user_type') == 'superadmin':
        pedidos = PEDIDOS_REGISTRADOS
    elif session.get('user_type') == 'dueno':
        pedidos = [p for p in PEDIDOS_REGISTRADOS if p.get('empresa') == session.get('empresa_nombre')]
    else:
        pedidos = [p for p in PEDIDOS_REGISTRADOS if p.get('empresa') == session.get('empresa_nombre')
                   and p.get('sede') == session.get('user_sede')]
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(['ID', 'Fecha', 'Empresa', 'Sede', 'Empleado/Cliente', 'Tipo', 'Estado', 'Productos', 'Método de pago', 'Total'])
    for p in pedidos:
        if es_venta_cerrada(p):
            escritor.writerow([p.get('id'), p.get('hora'), p.get('empresa'), p.get('sede'),
                               p.get('empleado') or p.get('cliente'), p.get('tipo'), p.get('estado'),
                               p.get('productos'), p.get('metodo_pago'), p.get('total')])
    respuesta = make_response('\ufeff' + salida.getvalue())
    respuesta.headers['Content-Type'] = 'text/csv; charset=utf-8'
    respuesta.headers['Content-Disposition'] = 'attachment; filename=ventas_keepinventory.csv'
    return respuesta

@app.route('/api/diagnostico', methods=['GET'])
def diagnostico_sistema():
    if not usuario_autenticado('superadmin'):
        return jsonify({'error': 'No autorizado'}), 401
    try:
        with _db_connection() as conexion:
            conexion.execute("SELECT 1").fetchone()
        estado_db = 'ok'
    except sqlite3.Error:
        estado_db = 'error'
    return jsonify({
        'estado': 'ok' if estado_db == 'ok' else 'degradado',
        'base_datos': estado_db,
        'empresas': len(EMPRESAS_REGISTRADAS),
        'productos_activos': len(INVENTARIO_SUPER),
        'productos_archivados': len(PRODUCTOS_ARCHIVADOS),
        'pedidos': len(PEDIDOS_REGISTRADOS),
        'reportes': len(REPORTES_EMPLEADOS),
        'hora_local': obtener_tiempo_local()
    })


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

@app.route('/api/ping-mantener-activo', methods=['GET'])
def ping_activo():
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=os.getenv('FLASK_DEBUG', '0') == '1')
