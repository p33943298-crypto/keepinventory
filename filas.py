from flask import Flask, render_template_string, redirect, url_for, request, session, jsonify
import os
from datetime import datetime

app = Flask(__name__)
# Clave secreta para manejo seguro de sesiones
app.secret_key = os.getenv("SECRET_KEY", "keepinventory_secret_key_12345")

# Credenciales de administrador demo
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@keepinventory.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123password")

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

INVENTARIO_SUPER = [
    {"codigo": "001", "nombre": "Huevos Kilo", "precio": 6500, "stock": 120, "sede": "Sede Central", "empresa": "Supermercados El Ahorro"},
    {"codigo": "002", "nombre": "Maíz tierno lata", "precio": 3200, "stock": 85, "sede": "Sede Central", "empresa": "Supermercados El Ahorro"},
    {"codigo": "003", "nombre": "Leche entera 1L", "precio": 4200, "stock": 200, "sede": "Sede Central", "empresa": "Supermercados El Ahorro"}
]

REPORTES_EMPLEADOS = []

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
                <p>Gestión inteligente de inventarios y cadenas de supermercados</p>
            </div>
            <div class="selector-grid">
                <a href="/login-staff" class="selector-card staff">
                    <div class="icon">💼</div>
                    <h2>Personal / Dueños / Staff</h2>
                    <p>Acceso para Superadmin, Dueños de Supermercado, Managers y Empleados.</p>
                    <span>INGRESAR COMO STAFF →</span>
                </a>
                <a href="/cliente-ubicacion" class="selector-card client">
                    <div class="icon">🍔</div>
                    <h2>Portal de Comidas</h2>
                    <p>Encuentra tu sede y pide hamburguesas, pizzas, bebidas y postres.</p>
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
                • Superadmin: admin@keepinventory.com / admin123password<br>
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

# DASHBOARD SUPERADMIN (Crear empresas y dueños)
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
                <a class="active">🏢 Empresas y Dueños</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión</a>
        </div>
        <div class="main">
            <div class="card">
                <h2>Crear Nueva Empresa / Cadena de Supermercados</h2>
                <form action="/superadmin/crear-empresa" method="POST" style="margin-top:15px; display:grid; gap:12px;">
                    <input type="text" name="nombre_empresa" placeholder="Nombre de la línea de supermercados" required style="padding:12px; border:1px solid var(--gray); border-radius:8px;">
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
                            <th>Nombre de Empresa</th>
                            <th>Correo del Dueño</th>
                            <th>Sedes Creadas</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for emp in empresas %}
                        <tr>
                            <td><b>#{{ emp.id }}</b></td>
                            <td>{{ emp.nombre_empresa }}</td>
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
                    <h2>Gestión de Sedes de Supermercado</h2>
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
                <div class="card">
                    <h2>📊 Reportes Mensuales y Desempeño</h2>
                    <p style="color:var(--gray-text); margin-bottom:15px;">Registro acumulado de ventas por empleado, entradas de productos y auditoría mensual.</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Fecha / Hora</th>
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

# DASHBOARD MANAGER (Agregar productos con código rápido de 3 dígitos)
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
                <a class="active">📦 Control Rápido de Inventario</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión</a>
        </div>
        <div class="main">
            <div class="card">
                <h2>Registrar Producto con Código Rápido (3 Dígitos)</h2>
                <p style="color:var(--gray-text); font-size:13px; margin-bottom:15px;">Usa códigos como 001, 002, 003 para facilitar el cobro y búsqueda de los empleados.</p>
                <form action="/manager/agregar-producto" method="POST" style="display:grid; grid-template-columns:120px 1fr 150px 120px auto; gap:10px;">
                    <input type="text" name="codigo" placeholder="Código (ej: 004)" maxlength="3" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="text" name="nombre" placeholder="Nombre del producto (Ej: Pan Integral)" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="number" name="precio" placeholder="Precio Unidad" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <input type="number" name="stock" placeholder="Cantidad" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                    <button type="submit" class="btn" style="margin:0;">+ Añadir</button>
                </form>
            </div>

            <div class="card">
                <h2>Inventario Activo en {{ user.sede }}</h2>
                <table>
                    <thead>
                        <tr>
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
                            <th>Fecha</th>
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
        </div>
    </div>
</body>
</html>
"""

# DASHBOARD EMPLEADO / CAJERO (Sistema de cobro rápido por código de 3 dígitos + reporte a manager)
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
                    <span>[#${p.codigo}] ${p.nombre}</span>
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
                    total: total,
                    sede: '{{ user.sede }}',
                    empleado: '{{ user.nombre }}'
                })
            }).then(() => {
                alert('✅ ¡Venta cobrada con éxito por $' + total.toLocaleString() + '!');
                carritoCaja = [];
                actualizarCajaUI();
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
                <!-- MÓDULO DE COBRO CON CÓDIGOS RÁPIDOS -->
                <div class="card">
                    <h2>Módulo de Caja - Búsqueda por Código Rápido</h2>
                    <p style="color:var(--gray-text); font-size:13px; margin-bottom:15px;">Introduce el código de 3 dígitos (Ej: 001, 002, 003) para agregar el producto a la venta.</p>
                    
                    <form onsubmit="buscarPorCodigoRapido(event)" style="display:flex; gap:10px; margin-bottom:20px;">
                        <input type="text" id="input-codigo-rapido" placeholder="Ej: 001" maxlength="3" required style="padding:12px; font-size:18px; font-weight:bold; border:2px solid var(--primary); border-radius:8px; width:150px;">
                        <button type="submit" class="btn" style="margin:0; width:auto; padding:12px 25px;">🔍 Buscar y Agregar</button>
                    </form>

                    <h3>Productos Disponibles en Referencia Rápida:</h3>
                    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; margin-top:10px;">
                        {% for prod in inventario %}
                        <div style="background:#f8fafc; padding:10px; border-radius:8px; border:1px solid var(--gray); font-size:13px;">
                            <b>#{{ prod.codigo }}</b> - {{ prod.nombre }}<br>
                            <span style="color:var(--primary); font-weight:bold;">${{ "{:,.0f}".format(prod.precio) }}</span>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- RESUMEN DE TICKET DE CAJA -->
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

            <!-- MÓDULO DE REPORTES A MANAGER -->
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
            <h2>Paso 1: Selecciona tu Sede de Comida Cercana</h2>
        </div>
        <p style="color:var(--gray-text); margin-bottom:25px;">Elige el restaurante o punto express para preparar tu pedido al instante.</p>

        <div class="sede-selector-grid">
            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Principal (Centro)', 'Av. Las Acacias #45-18, Zona Gastronómica')">
                <div style="font-size:40px; margin-bottom:10px;">🏢</div>
                <h3>Sede Centro</h3>
                <p style="color:var(--gray-text); font-size:13px;">Av. Las Acacias #45-18, Zona Gastronómica</p>
                <span style="color:var(--primary); font-weight:bold; font-size:13px; margin-top:10px; display:inline-block;">SELECCIONAR ESTA SEDE →</span>
            </div>

            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Norte (Plaza)', 'Calle Del Sol #102-15, Mall Gourmet')">
                <div style="font-size:40px; margin-bottom:10px;">🏬</div>
                <h3>Sede Norte Gourmet</h3>
                <p style="color:var(--gray-text); font-size:13px;">Calle Del Sol #102-15, Mall Gourmet</p>
                <span style="color:var(--primary); font-weight:bold; font-size:13px; margin-top:10px; display:inline-block;">SELECCIONAR ESTA SEDE →</span>
            </div>

            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Sur (Autoservicio)', 'Transversal 78 #12-30, Autopista Sur')">
                <div style="font-size:40px; margin-bottom:10px;">🏪</div>
                <h3>Sede Sur Express</h3>
                <p style="color:var(--gray-text); font-size:13px;">Transversal 78 #12-30, Autopista Sur</p>
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

            <!-- FORMULARIO LOGIN CLIENTE -->
            <form id="form-login" action="/login-cliente" method="POST">
                <input type="email" name="email" placeholder="Tu correo electrónico" required>
                <input type="password" name="password" placeholder="Tu contraseña" required>
                <button type="submit" class="btn">🍔 Entrar a Pedir Comida</button>
            </form>

            <!-- FORMULARIO REGISTRO CLIENTE -->
            <form id="form-registro" action="/registro-cliente" method="POST" style="display:none;">
                <input type="text" name="nombre" placeholder="Nombre Completo" required>
                <input type="email" name="email" placeholder="Correo electrónico" required>
                <input type="password" name="password" placeholder="Crea una Contraseña" required>
                <button type="submit" class="btn">✨ Crear Cuenta y Pedir</button>
            </form>

            <a href="/cliente-ubicacion" style="display:block; margin-top:20px; color:var(--gray-text); text-decoration:none; font-size:13px;">← Cambiar de Sede</a>
        </div>
    </div>
</body>
</html>
"""

# CATÁLOGO DE COMIDAS CON PAGO REAL ELEGIBLE Y DATOS INVENTADOS
HTML_TIENDA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Menú Gourmet - Cliente</title>
    <style>{{ css | safe }}</style>
    <script>
        let carrito = [];

        function agregarProducto(nombre, precio) {
            carrito.push({nombre, precio});
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
            if(carrito.length === 0) { alert('Añade productos de comida primero'); return; }
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

            // Enviar pedido al servidor en tiempo real
            fetch('/api/crear-pedido', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    cliente: '{{ cliente_nombre }}',
                    sede: '{{ sede_actual }}',
                    productos: detallesItems,
                    total: total,
                    metodo_pago: metodoNombre
                })
            }).then(() => {
                alert('🎉 ¡Pago exitoso vía ' + metodoNombre + '! Tu pedido de comida está en camino en ' + '{{ sede_actual }}.');
                carrito = [];
                actualizarCarritoUI();
                cerrarCarrito();
            });
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
        
        <!-- HEADER CLIENTE -->
        <div class="header-cliente">
            <div class="brand">
                <div class="logo">KI</div>
                <div>
                    <h2 style="font-size:20px;">Menú de Alimentos y Consumibles</h2>
                    <p style="font-size:12px; color:var(--gray-text);">Sede activa: <b>📍 {{ sede_actual }}</b></p>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:15px;">
                <span style="font-size:14px;">Hola, <b>{{ cliente_nombre }}</b></span>
                <a href="/cliente-ubicacion" class="btn btn-outline" style="padding:8px 12px; font-size:12px;">📍 Cambiar Sede</a>
                <a href="/logout" class="btn btn-danger" style="padding:8px 12px; font-size:12px;">Cerrar Sesión</a>
            </div>
        </div>

        <!-- FILTROS DE CATEGORÍA -->
        <div style="display:flex; gap:10px; margin-bottom:25px; overflow-x:auto; padding-bottom:5px;">
            <button class="btn cat-btn" onclick="filtrarCategoria('todos', this)">🍔 Todo el Menú</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('hamburguesas', this)">🔥 Hamburguesas</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('pizzas', this)">🍕 Pizzas Artesanales</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('bebidas', this)">🥤 Bebidas & Jugos</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('postres', this)">🍰 Postres</button>
        </div>

        <!-- GRID DE PRODUCTOS COMIBLES -->
        <div class="grid">
            <!-- Hamburguesas -->
            <div class="product-card" data-cat="hamburguesas">
                <span class="product-badge">BEST SELLER</span>
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍔</div>
                <h3 style="font-size:16px;">Hamburguesa Doble Angus BBQ</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Carne 100% angus, queso cheddar fundido, tocino crujiente y salsa BBQ artesanal.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$28.900</b>
                    <button class="btn" onclick="agregarProducto('Hamburguesa Doble Angus BBQ', 28900)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="hamburguesas">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍟</div>
                <h3 style="font-size:16px;">Hamburguesa Crispy Chicken</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Pechuga de pollo apanada crujiente, ensalada coleslaw y aderezo especial de la casa.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$24.500</b>
                    <button class="btn" onclick="agregarProducto('Hamburguesa Crispy Chicken', 24500)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <!-- Pizzas -->
            <div class="product-card" data-cat="pizzas">
                <span class="product-badge">FAVORITA</span>
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍕</div>
                <h3 style="font-size:16px;">Pizza Pepperoni Suprema (Grande)</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Masa madre fermentada 48 horas, doble pepperoni italiano y queso mozzarella.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$45.000</b>
                    <button class="btn" onclick="agregarProducto('Pizza Pepperoni Suprema Gde', 45000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="pizzas">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍅</div>
                <h3 style="font-size:16px;">Pizza Margarita Tradicional</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Salsa de tomate pomodoro natural, albahaca fresca y bocconcini de mozzarella.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$38.000</b>
                    <button class="btn" onclick="agregarProducto('Pizza Margarita Tradicional', 38000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <!-- Bebidas -->
            <div class="product-card" data-cat="bebidas">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🥤</div>
                <h3 style="font-size:16px;">Gaseosa Helada 400ml</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Refrescante bebida gaseosa bien fría en presentación personal.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$6.000</b>
                    <button class="btn" onclick="agregarProducto('Gaseosa Helada 400ml', 6000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="bebidas">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍹</div>
                <h3 style="font-size:16px;">Limonada de Coco Natural</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Bebida tropical cremosa con limón fresco, crema de coco y hielo frappé.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$11.000</b>
                    <button class="btn" onclick="agregarProducto('Limonada de Coco Natural', 11000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <!-- Postres -->
            <div class="product-card" data-cat="postres">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍰</div>
                <h3 style="font-size:16px;">Cheesecake de Frutos Rojos</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Suave pastel de queso estilo Nueva York con compota de moras y arándanos.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$14.000</b>
                    <button class="btn" onclick="agregarProducto('Cheesecake de Frutos Rojos', 14000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="postres">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍫</div>
                <h3 style="font-size:16px;">Volcán de Chocolate Tibio</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Bizcocho de chocolate relleno con fudge fundido y acompañado de helado de vainilla.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$15.500</b>
                    <button class="btn" onclick="agregarProducto('Volcán de Chocolate Tibio', 15500)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>
        </div>
    </div>

    <!-- BOTÓN FLOTANTE DEL CARRITO -->
    <div class="cart-floating-btn" onclick="abrirCarrito()">
        🛒 Carrito de Comida (<span id="cart-count">0</span>)
    </div>

    <!-- MODAL DEL CARRITO Y PASARELA DE PAGOS -->
    <div id="modal-carrito" class="modal">
        <div class="modal-content">
            
            <!-- PASO A: REVISIÓN DE CARRITO -->
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
                <button class="btn btn-outline" onclick="cerrarCarrito()" style="margin-top:8px;">Seguir Eligiendo Comida</button>
            </div>

            <!-- PASO B: MÉTODOS DE PAGO REALES CON DATOS INVENTADOS -->
            <div id="paso-pago" style="display:none;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <h3>Selecciona Método de Pago</h3>
                    <b id="monto-pagar" style="color:var(--primary); font-size:18px;">$0</b>
                </div>
                <p style="font-size:13px; color:var(--gray-text); margin-bottom:15px;">Pasarela integrada simulada (Rellena con datos ficticios)</p>

                <!-- Selector de métodos -->
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

                <!-- FORMULARIO 1: TARJETA -->
                <div id="pago-tarjeta" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Datos de la Tarjeta (Inventados)</p>
                    <input type="text" placeholder="Número de Tarjeta (ej: 4532 •••• •••• 8890)" value="4532 8821 9012 3456" style="padding:10px; font-size:13px;">
                    <div style="display:flex; gap:10px;">
                        <input type="text" placeholder="MM/AA" value="12/28" style="padding:10px; font-size:13px;">
                        <input type="text" placeholder="CVV" value="482" style="padding:10px; font-size:13px;">
                    </div>
                    <button class="btn" onclick="confirmarPagoFinal('Tarjeta de Crédito')">Pagar con Tarjeta</button>
                </div>

                <!-- FORMULARIO 2: PSE -->
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

                <!-- FORMULARIO 3: NEQUI -->
                <div id="pago-nequi" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Billetera Móvil (Inventado)</p>
                    <input type="text" placeholder="Número Celular (ej: 310 456 7890)" value="312 456 7890" style="padding:10px; font-size:13px;">
                    <button class="btn" onclick="confirmarPagoFinal('Nequi/Daviplata')">Generar Notificación Push</button>
                </div>

                <!-- FORMULARIO 4: EFECTIVO -->
                <div id="pago-efectivo" class="payment-sec" style="display:none; margin-top:15px; background:#f8fafc; padding:15px; border-radius:12px;">
                    <p style="font-size:13px; font-weight:bold; margin-bottom:8px;">Pago contra entrega</p>
                    <input type="text" placeholder="¿Con cuánto dinero vas a pagar?" value="$50.000" style="padding:10px; font-size:13px;">
                    <button class="btn" onclick="confirmarPagoFinal('Efectivo contra entrega')">Confirmar Pedido</button>
                </div>

                <button class="btn btn-outline" onclick="abrirCarrito()" style="margin-top:15px;">← Volver al Carrito</button>
            </div>

        </div>
    </div>
</body>
</html>
"""

# DASHBOARD STAFF ANTIGUO (Se mantiene por retrocompatibilidad con las 959 líneas originales)
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
                <td>${stock} porciones</td>
                <td><span class="tag tag-empleado">Disponible</span></td>
            </tr>`;
            tabla.innerHTML += nuevaFila;
            alert('¡Alimento agregado al stock de cocina!');
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
                <a onclick="cambiarSeccion('inventario', this)">🍔 Control de Cocina</a>
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
                                <th>Hora</th><th>Cliente</th><th>Sede</th><th>Productos</th><th>Pago</th><th>Total</th>
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
                    <h2>Inventario de Cocina</h2>
                    <form id="form-prod" onsubmit="agregarNuevoProducto(event)" style="display:grid; grid-template-columns:1fr 1fr 1fr auto; gap:10px; margin-top:15px;">
                        <input type="text" id="prod-nombre" placeholder="Nombre" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <select id="prod-sede" style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                            <option>Sede Centro</option><option>Sede Norte</option><option>Sede Sur Express</option>
                        </select>
                        <input type="number" id="prod-stock" placeholder="Stock" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <button type="submit" class="btn" style="margin:0;">+ Guardar</button>
                    </form>
                    <table style="margin-top:15px;">
                        <thead><tr><th>Platillo</th><th>Sede</th><th>Disponibilidad</th><th>Estado</th></tr></thead>
                        <tbody id="tabla-inventario">
                            <tr><td>Hamburguesa Doble Angus BBQ</td><td>Sede Centro</td><td>25 porciones</td><td><span class="tag tag-empleado">Disponible</span></td></tr>
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
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        # 1. Verificar si es Superadmin principal
        if usuario == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['user_type'] = 'superadmin'
            return redirect(url_for('superadmin_dashboard'))
        
        # 2. Verificar si es Dueño, Manager o Empleado en alguna empresa registrada
        for emp in EMPRESAS_REGISTRADAS:
            if emp['email_dueno'] == usuario and emp['password_dueno'] == password:
                session['user_type'] = 'dueno'
                session['empresa_id'] = emp['id']
                return redirect(url_for('dueno_dashboard'))
            
            for staff in emp['usuarios_staff']:
                if staff['email'] == usuario and staff['password'] == password:
                    session['user_type'] = staff['rol'] # 'manager' o 'empleado'
                    session['user_nombre'] = staff['nombre']
                    session['user_sede'] = staff['sede']
                    session['empresa_nombre'] = emp['nombre_empresa']
                    if staff['rol'] == 'manager':
                        return redirect(url_for('manager_dashboard'))
                    else:
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
    if session.get('user_type') != 'superadmin':
        return redirect(url_for('login_staff'))
    nueva_empresa = {
        "id": len(EMPRESAS_REGISTRADAS) + 1,
        "nombre_empresa": request.form.get('nombre_empresa'),
        "email_dueno": request.form.get('email_dueno'),
        "password_dueno": request.form.get('password_dueno'),
        "sedes": [],
        "usuarios_staff": []
    }
    EMPRESAS_REGISTRADAS.append(nueva_empresa)
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
    empresa['sedes'].append({
        "nombre": request.form.get('nombre_sede'),
        "direccion": request.form.get('direccion_sede')
    })
    return redirect(url_for('dueno_dashboard'))

@app.route('/dueno/crear-personal', methods=['POST'])
def dueno_crear_personal():
    if session.get('user_type') != 'dueno':
        return redirect(url_for('login_staff'))
    emp_id = session.get('empresa_id')
    empresa = next((e for e in EMPRESAS_REGISTRADAS if e['id'] == emp_id), EMPRESAS_REGISTRADAS[0])
    empresa['usuarios_staff'].append({
        "nombre": request.form.get('nombre'),
        "email": request.form.get('email'),
        "password": request.form.get('password'),
        "rol": request.form.get('rol'),
        "sede": request.form.get('sede')
    })
    return redirect(url_for('dueno_dashboard'))

@app.route('/dueno/eliminar-personal', methods=['POST'])
def dueno_eliminar_personal():
    if session.get('user_type') != 'dueno':
        return redirect(url_for('login_staff'))
    email_eliminar = request.form.get('email')
    emp_id = session.get('empresa_id')
    empresa = next((e for e in EMPRESAS_REGISTRADAS if e['id'] == emp_id), EMPRESAS_REGISTRADAS[0])
    empresa['usuarios_staff'] = [s for s in empresa['usuarios_staff'] if s['email'] != email_eliminar]
    return redirect(url_for('dueno_dashboard'))

@app.route('/manager/dashboard')
def manager_dashboard():
    if session.get('user_type') != 'manager':
        return redirect(url_for('login_staff'))
    user_sede = session.get('user_sede')
    emp_nombre = session.get('empresa_nombre')
    inv_sede = [i for i in INVENTARIO_SUPER if i['sede'] == user_sede]
    rep_sede = [r for r in REPORTES_EMPLEADOS if r.get('sede') == user_sede]
    return render_template_string(HTML_DASHBOARD_MANAGER, css=CSS_ESTILOS, user={'sede': user_sede}, inventario=inv_sede, reportes=rep_sede)

@app.route('/manager/agregar-producto', methods=['POST'])
def manager_agregar_producto():
    if session.get('user_type') != 'manager':
        return redirect(url_for('login_staff'))
    INVENTARIO_SUPER.append({
        "codigo": request.form.get('codigo'),
        "nombre": request.form.get('nombre'),
        "precio": float(request.form.get('precio', 0)),
        "stock": int(request.form.get('stock', 0)),
        "sede": session.get('user_sede'),
        "empresa": session.get('empresa_nombre')
    })
    return redirect(url_for('manager_dashboard'))

@app.route('/empleado/dashboard')
def empleado_dashboard():
    if session.get('user_type') != 'empleado':
        return redirect(url_for('login_staff'))
    user_sede = session.get('user_sede')
    inv_sede = [i for i in INVENTARIO_SUPER if i['sede'] == user_sede]
    return render_template_string(HTML_DASHBOARD_EMPLEADO, css=CSS_ESTILOS, user={'nombre': session.get('user_nombre'), 'sede': user_sede}, inventario=inv_sede)

@app.route('/api/buscar-codigo', methods=['GET'])
def buscar_codigo():
    codigo = request.args.get('codigo', '').strip()
    user_sede = session.get('user_sede', 'Sede Central')
    producto = next((i for i in INVENTARIO_SUPER if i['codigo'] == codigo and i['sede'] == user_sede), None)
    if producto:
        return jsonify({'encontrado': True, 'producto': producto})
    return jsonify({'encontrado': False})

@app.route('/api/registrar-venta-cajero', methods=['POST'])
def registrar_venta_cajero():
    data = request.json or {}
    nuevo_pedido = {
        'hora': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'cliente': data.get('empleado', 'Cajero'),
        'sede': data.get('sede', 'Sede Central'),
        'productos': data.get('productos', ''),
        'total': data.get('total', 0),
        'metodo_pago': 'Caja Registradora',
        'empresa': session.get('empresa_nombre', 'Supermercados El Ahorro')
    }
    PEDIDOS_REGISTRADOS.insert(0, nuevo_pedido)
    return jsonify({'status': 'ok'})

@app.route('/empleado/enviar-reporte', methods=['POST'])
def empleado_enviar_reporte():
    if session.get('user_type') != 'empleado':
        return redirect(url_for('login_staff'))
    REPORTES_EMPLEADOS.insert(0, {
        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'empleado': session.get('user_nombre'),
        'sede': session.get('user_sede'),
        'mensaje': request.form.get('mensaje')
    })
    return redirect(url_for('empleado_dashboard'))

# RUTAS CLIENTE
@app.route('/cliente-ubicacion')
def cliente_ubicacion():
    return render_template_string(HTML_CLIENTE_UBICACION, css=CSS_ESTILOS)

@app.route('/api/set-sede', methods=['POST'])
def set_sede():
    data = request.json or {}
    session['sede'] = data.get('sede')
    session['direccion_sede'] = data.get('direccion')
    return {'status': 'ok'}

@app.route('/cliente-auth')
def cliente_auth():
    sede = session.get('sede', 'No seleccionada')
    return render_template_string(HTML_CLIENTE_AUTH, css=CSS_ESTILOS, sede_seleccionada=sede)

@app.route('/login-cliente', methods=['POST'])
def login_cliente():
    session['user_type'] = 'cliente'
    email = request.form.get('email', 'cliente@demo.com')
    session['cliente_nombre'] = email.split('@')[0].capitalize() if '@' in email else email
    return redirect(url_for('tienda'))

@app.route('/registro-cliente', methods=['POST'])
def registro_cliente():
    session['user_type'] = 'cliente'
    session['cliente_nombre'] = request.form.get('nombre', 'Cliente')
    return redirect(url_for('tienda'))

@app.route('/tienda')
def tienda():
    if session.get('user_type') != 'cliente':
        return redirect(url_for('cliente_ubicacion'))
    sede_actual = session.get('sede', 'Sede Centro')
    cliente_nombre = session.get('cliente_nombre', 'Cliente')
    return render_template_string(HTML_TIENDA, css=CSS_ESTILOS, sede_actual=sede_actual, cliente_nombre=cliente_nombre)

@app.route('/api/crear-pedido', methods=['POST'])
def crear_pedido():
    data = request.json or {}
    nuevo_pedido = {
        'hora': datetime.now().strftime("%H:%M:%S"),
        'cliente': data.get('cliente', 'Anonimo'),
        'sede': data.get('sede', 'Sede Centro'),
        'productos': data.get('productos', ''),
        'total': data.get('total', 0),
        'metodo_pago': data.get('metodo_pago', 'Tarjeta'),
        'empresa': 'Supermercados El Ahorro'
    }
    PEDIDOS_REGISTRADOS.insert(0, nuevo_pedido)
    return jsonify({'status': 'ok'})

@app.route('/api/pedidos', methods=['GET'])
def obtener_pedidos():
    return jsonify(PEDIDOS_REGISTRADOS)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
