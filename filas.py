from flask import Flask, render_template_string, redirect, url_for, request, session, jsonify
import os

app = Flask(__name__)
# Clave secreta para manejo seguro de sesiones
app.secret_key = os.getenv("SECRET_KEY", "keepinventory_secret_key_12345")

# Credenciales de administrador demo
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@keepinventory.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123password")

# Lista global en memoria para simular la base de datos de pedidos recibidos en tiempo real
PEDIDOS_REGISTRADOS = []

# CSS COMPLETO CON ANIMACIONES Y DISEÑO MEJORADO
CSS_ESTILOS = """
:root{
  --primary:#0f8a5f;
  --primary-dark:#064e3b;
  --primary-light:#e6f4ea;
  --dark:#1e293b;
  --light:#f8fafc;
  --gray:#e2e8f0;
  --gray-text:#64748b;
  --red:#dc2626;
  --blue:#2563eb;
  --accent:#f59e0b;
}

*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI', system-ui, -apple-system, sans-serif;}
body{background:var(--light); color:var(--dark); line-height:1.5; overflow-x:hidden;}

/* ANIMACIONES */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(15px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes pulseGlow {
  0% { box-shadow: 0 0 0 0 rgba(15, 138, 95, 0.4); }
  70% { box-shadow: 0 0 0 12px rgba(15, 138, 95, 0); }
  100% { box-shadow: 0 0 0 0 rgba(15, 138, 95, 0); }
}

.fade-in { animation: fadeIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }

/* BRANDING */
.brand{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.logo{width:42px;height:42px;background:var(--primary);color:white;display:flex;align-items:center;justify-content:center;border-radius:12px;font-weight:900;font-size:18px;flex-shrink:0;box-shadow:0 4px 10px rgba(15,138,95,0.3);}
.brand-large{color:white;margin-bottom:30px; text-align:center;}
.logo-large{width:80px;height:80px;background:white;color:var(--primary);font-size:36px;font-weight:900;border-radius:20px;display:flex;align-items:center;justify-content:center;margin:0 auto 15px;box-shadow:0 10px 25px rgba(0,0,0,0.2);}
.brand-large h1{font-size:38px; margin-bottom:5px; font-weight:800;}
.brand-large p{opacity:0.9; font-size:15px;}

/* LANDING SELECTOR */
.landing-body{display:flex;justify-content:center;align-items:center;min-height:100vh;background:linear-gradient(135deg,var(--primary),var(--primary-dark));padding:20px;}
.landing-container{max-width:850px;width:100%;text-align:center;}
.selector-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
.selector-card{background:white;padding:35px 25px;border-radius:20px;cursor:pointer;transition:all .3s cubic-bezier(0.16, 1, 0.3, 1);box-shadow:0 10px 30px rgba(0,0,0,.15);text-align:center;text-decoration:none;color:inherit;display:block;position:relative;overflow:hidden;}
.selector-card:hover{transform:translateY(-8px) scale(1.02); box-shadow:0 20px 40px rgba(0,0,0,.25);}
.selector-card .icon{font-size:50px;margin-bottom:15px; transition:transform 0.3s ease;}
.selector-card:hover .icon{transform:scale(1.15) rotate(5deg);}
.selector-card h2{margin-bottom:8px; font-size:22px;}
.selector-card p{color:var(--gray-text);margin-bottom:18px; font-size:14px;}
.selector-card span{color:var(--primary);font-weight:bold;font-size:13px;letter-spacing:0.5px;}
.selector-card.staff{border-top:6px solid var(--dark);}
.selector-card.client{border-top:6px solid var(--primary);}

/* FORMULARIOS Y LOGIN */
.login-body{display:flex;justify-content:center;align-items:center;min-height:100vh;background:linear-gradient(135deg,var(--primary),var(--primary-dark));padding:20px;}
.login-container{background:white;padding:35px;border-radius:20px;width:100%;max-width:420px;box-shadow:0 20px 50px rgba(0,0,0,.25);text-align:center;}
.login-container input, .login-container select, .login-container textarea{width:100%;padding:12px 14px;margin:8px 0;border:1.5px solid var(--gray);border-radius:10px;outline:none; font-size:14px; transition:all 0.2s;}
.login-container input:focus{border-color:var(--primary); box-shadow:0 0 0 4px rgba(15,138,95,.15);}
.btn{width:100%;padding:12px 16px;background:var(--primary);color:white;border:none;border-radius:10px;cursor:pointer;font-weight:bold;margin-top:12px; font-size:14px; transition:all .2s ease; display:inline-flex; align-items:center; justify-content:center; gap:8px;}
.btn:hover{background:var(--primary-dark); transform:translateY(-1px);}
.btn-outline{background:transparent; color:var(--primary); border:2px solid var(--primary);}
.btn-outline:hover{background:var(--primary-light);}
.btn-danger{background:var(--red);} .btn-danger:hover{background:#b91c1c;}
.demo-creds{margin-top:15px; font-size:12px; background:#f1f5f9; padding:12px; border-radius:10px; text-align:left; border-left:4px solid var(--primary);}

/* DASHBOARD STAFF */
.dashboard{display:flex;min-height:100vh;}
.sidebar{width:260px;background:var(--dark);color:white;padding:24px;flex-shrink:0;display:flex;flex-direction:column;justify-content:space-between;}
.sidebar .brand{margin-bottom:25px;}
.sidebar a{display:flex;align-items:center;gap:10px;color:#cbd5e1;padding:12px 14px;text-decoration:none;border-radius:10px;margin:5px 0; font-size:14px; transition:all .2s; cursor:pointer;}
.sidebar a:hover,.sidebar a.active{background:var(--primary);color:white; transform:translateX(4px);}
.main{flex:1;padding:30px; overflow-y:auto; background:#f1f5f9;}
.card{background:white;padding:24px;border-radius:16px;box-shadow:0 4px 15px rgba(0,0,0,.03);margin-bottom:20px; border:1px solid #e2e8f0; transition:all 0.2s;}
.card:hover{box-shadow:0 8px 25px rgba(0,0,0,.06);}
.grid{display:grid;grid-template-columns:repeat(auto-fill, minmax(230px, 1fr));gap:20px;}
table{width:100%;border-collapse:collapse;margin-top:15px; font-size:14px;}
th,td{padding:12px 15px;border-bottom:1px solid var(--gray);text-align:left;}
th{background:#f8fafc; font-weight:700; color:var(--gray-text); font-size:12px; text-transform:uppercase;}
.tag{padding:4px 10px;border-radius:20px;font-size:11px;color:white; font-weight:700;}
.tag-admin{background:var(--red);} .tag-empleado{background:var(--primary);}

/* TIENDA CLIENTE */
.header-cliente{display:flex; justify-content:space-between; align-items:center; background:white; padding:15px 30px; border-radius:16px; margin-bottom:25px; box-shadow:0 2px 10px rgba(0,0,0,0.04);}
.sede-selector-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin:20px 0;}
.sede-card-interactive{background:white;border:2px solid var(--gray);border-radius:16px;padding:22px;text-align:center;cursor:pointer;transition:all .3s ease;}
.sede-card-interactive:hover{border-color:var(--primary);transform:translateY(-4px); box-shadow:0 10px 20px rgba(0,0,0,.08);}
.sede-card-interactive.active{border-color:var(--primary);background:var(--primary-light); animation:pulseGlow 2s infinite;}
.product-card{background:white; border-radius:16px; border:1px solid var(--gray); padding:18px; display:flex; flex-direction:column; justify-content:space-between; transition:all 0.3s ease; position:relative; overflow:hidden;}
.product-card:hover{transform:translateY(-5px); box-shadow:0 12px 25px rgba(0,0,0,0.1); border-color:var(--primary);}
.product-badge{position:absolute; top:12px; right:12px; background:var(--accent); color:white; font-size:10px; font-weight:bold; padding:3px 8px; border-radius:12px;}

/* CARRITO MODAL Y NOTIFICACIONES */
.cart-floating-btn{position:fixed; bottom:25px; right:25px; background:var(--primary); color:white; padding:15px 22px; border-radius:50px; cursor:pointer; font-weight:bold; box-shadow:0 10px 25px rgba(15,138,95,0.4); display:flex; align-items:center; gap:10px; z-index:99; transition:transform 0.2s;}
.cart-floating-btn:hover{transform:scale(1.05);}
.modal{display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:1000; justify-content:center; align-items:center;}
.modal-content{background:white; padding:30px; border-radius:20px; width:90%; max-width:480px; position:relative; animation:fadeIn 0.3s ease;}
.btn-remove{background:#fee2e2; color:#dc2626; border:none; border-radius:6px; padding:4px 8px; cursor:pointer; font-size:12px; font-weight:bold;}
.btn-remove:hover{background:#fca5a5;}

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
                <p>Gestión inteligente de inventarios y catálogo digital</p>
            </div>
            <div class="selector-grid">
                <a href="/login-staff" class="selector-card staff">
                    <div class="icon">💼</div>
                    <h2>Personal / Staff</h2>
                    <p>Acceso administrativo a la gestión de inventario y sedes.</p>
                    <span>INGRESAR COMO STAFF →</span>
                </a>
                <a href="/cliente-ubicacion" class="selector-card client">
                    <div class="icon">🛒</div>
                    <h2>Portal Clientes</h2>
                    <p>Encuentra tu sede más cercana y consulta disponibilidad.</p>
                    <span>SELECCIONAR MI SEDE →</span>
                </a>
            </div>
        </div>
    </div>
</body>
</html>
"""

# LOGIN STAFF
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
                <h2>Acceso Staff</h2>
            </div>
            <p style="color:var(--gray-text); margin-bottom:15px; font-size:14px;">Ingresa tus credenciales de administrador</p>
            
            {% if error %}
            <div style="color:#dc2626; background:#fee2e2; padding:10px; border-radius:8px; font-size:13px; margin-bottom:12px;">
                {{ error }}
            </div>
            {% endif %}

            <form action="/login-staff" method="POST">
                <input type="email" name="usuario" placeholder="Correo del Administrador" required>
                <input type="password" name="password" placeholder="Contraseña" required>
                <button type="submit" class="btn">🔑 Iniciar Sesión Staff</button>
            </form>

            <div class="demo-creds">
                <b>Credenciales Demo:</b><br>
                Correo: admin@keepinventory.com<br>
                Clave: admin123password
            </div>

            <a href="/" style="display:block; margin-top:20px; color:var(--gray-text); text-decoration:none; font-size:13px;">← Volver al inicio</a>
        </div>
    </div>
</body>
</html>
"""

# PASO 1 CLIENTE: SELECCIÓN DE UBICACIÓN Y SEDE CON DIRECCIONES INVENTADAS
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
            <h2>Paso 1: Selecciona tu Ubicación de Atención</h2>
        </div>
        <p style="color:var(--gray-text); margin-bottom:25px;">Elige tu sede o almacén preferido para verificar stock local e itinerario de entregas.</p>

        <div class="sede-selector-grid">
            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Principal (Centro)', 'Av. Las Acacias #45-18, Sector Comercial')">
                <div style="font-size:40px; margin-bottom:10px;">🏢</div>
                <h3>Sede Centro</h3>
                <p style="color:var(--gray-text); font-size:13px;">Av. Las Acacias #45-18, Sector Comercial</p>
                <span style="color:var(--primary); font-weight:bold; font-size:13px; margin-top:10px; display:inline-block;">SELECCIONAR ESTA SEDE →</span>
            </div>

            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Norte', 'Calle Del Sol #102-15, Plaza Mayor')">
                <div style="font-size:40px; margin-bottom:10px;">🏬</div>
                <h3>Sede Norte</h3>
                <p style="color:var(--gray-text); font-size:13px;">Calle Del Sol #102-15, Plaza Mayor</p>
                <span style="color:var(--primary); font-weight:bold; font-size:13px; margin-top:10px; display:inline-block;">SELECCIONAR ESTA SEDE →</span>
            </div>

            <div class="sede-card-interactive" onclick="guardarSedeYContinuar('Sede Sur (Express)', 'Transversal 78 #12-30, Parque Industrial')">
                <div style="font-size:40px; margin-bottom:10px;">🏪</div>
                <h3>Sede Sur Express</h3>
                <p style="color:var(--gray-text); font-size:13px;">Transversal 78 #12-30, Parque Industrial</p>
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
                <button type="submit" class="btn">🛒 Entrar a Comprar</button>
            </form>

            <!-- FORMULARIO REGISTRO CLIENTE -->
            <form id="form-registro" action="/registro-cliente" method="POST" style="display:none;">
                <input type="text" name="nombre" placeholder="Nombre Completo" required>
                <input type="email" name="email" placeholder="Correo electrónico" required>
                <input type="password" name="password" placeholder="Crea una Contraseña" required>
                <button type="submit" class="btn">✨ Crear Cuenta y Continuar</button>
            </form>

            <a href="/cliente-ubicacion" style="display:block; margin-top:20px; color:var(--gray-text); text-decoration:none; font-size:13px;">← Cambiar de Sede</a>
        </div>
    </div>
</body>
</html>
"""

# CATÁLOGO INTERACTIVO DE CLIENTES CON ELIMINACIÓN DE PRODUCTOS Y NOTIFICACIÓN AL ADMIN
HTML_TIENDA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo - Cliente</title>
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
                        <button class="btn-remove" onclick="quitarProducto(${index})">❌ Quitar</button>
                    </div>
                </div>`;
            });
            document.getElementById('cart-items').innerHTML = listaHtml || '<p style="color:var(--gray-text);">El carrito está vacío</p>';
        }

        function abrirCarrito() { document.getElementById('modal-carrito').style.display = 'flex'; }
        function cerrarCarrito() { document.getElementById('modal-carrito').style.display = 'none'; }
        
        function procesarCompra() {
            if(carrito.length === 0) { alert('Añade productos primero'); return; }
            
            let total = carrito.reduce((sum, p) => sum + p.precio, 0);
            let detallesItems = carrito.map(p => p.nombre).join(', ');

            // Enviar pedido al servidor para reflejarse en tiempo real al Administrador
            fetch('/api/crear-pedido', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    cliente: '{{ cliente_nombre }}',
                    sede: '{{ sede_actual }}',
                    productos: detallesItems,
                    total: total
                })
            }).then(() => {
                alert('🎉 ¡Pedido realizado con éxito para entrega en ' + '{{ sede_actual }}!');
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
                    <h2 style="font-size:20px;">Catálogo Digital</h2>
                    <p style="font-size:12px; color:var(--gray-text);">Sede activa: <b>📍 {{ sede_actual }}</b></p>
                </div>
            </div>
            <div style="display:flex; align-items:center; gap:15px;">
                <span style="font-size:14px;">Hola, <b>{{ cliente_nombre }}</b></span>
                <a href="/cliente-ubicacion" class="btn btn-outline" style="padding:8px 12px; font-size:12px;">📍 Cambiar Ubicación</a>
                <a href="/logout" class="btn btn-danger" style="padding:8px 12px; font-size:12px;">Cerrar Sesión</a>
            </div>
        </div>

        <!-- FILTROS DE CATEGORÍA -->
        <div style="display:flex; gap:10px; margin-bottom:25px; overflow-x:auto; padding-bottom:5px;">
            <button class="btn cat-btn" onclick="filtrarCategoria('todos', this)">Todos los productos</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('hardware', this)">Hardware & Pos</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('consumibles', this)">Consumibles</button>
        </div>

        <!-- GRID DE PRODUCTOS -->
        <div class="grid">
            <div class="product-card" data-cat="hardware">
                <span class="product-badge">POPULAR</span>
                <div style="font-size:45px; text-align:center; margin:10px 0;">📦</div>
                <h3 style="font-size:16px;">Lector Código de Barras 2D</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Escáner omnidireccional USB de alta velocidad.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$120.000</b>
                    <button class="btn" onclick="agregarProducto('Lector Código de Barras 2D', 120000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="hardware">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🖨️</div>
                <h3 style="font-size:16px;">Impresora Térmica POS</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Impresora de recibos 80mm con corte automático.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$280.000</b>
                    <button class="btn" onclick="agregarProducto('Impresora Térmica POS', 280000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="consumibles">
                <div style="font-size:45px; text-align:center; margin:10px 0;">📄</div>
                <h3 style="font-size:16px;">Caja Papel Térmico (50 Rollos)</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Rollos de alta durabilidad 80x60mm libre de BPA.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$85.000</b>
                    <button class="btn" onclick="agregarProducto('Caja Papel Térmico', 85000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>
        </div>
    </div>

    <!-- BOTÓN FLOTANTE DEL CARRITO -->
    <div class="cart-floating-btn" onclick="abrirCarrito()">
        🛒 Mi Carrito (<span id="cart-count">0</span>)
    </div>

    <!-- MODAL DEL CARRITO -->
    <div id="modal-carrito" class="modal">
        <div class="modal-content">
            <h3>Tu Pedido - <span style="color:var(--primary);">{{ sede_actual }}</span></h3>
            <div id="cart-items" style="margin:20px 0; max-height:200px; overflow-y:auto;">
                <p style="color:var(--gray-text);">El carrito está vacío</p>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:18px; border-top:2px solid var(--gray); padding-top:10px;">
                <span>Total:</span>
                <b id="cart-total" style="color:var(--primary);">$0</b>
            </div>
            <button class="btn" onclick="procesarCompra()" style="margin-top:20px;">💳 Confirmar y Finalizar Pedido</button>
            <button class="btn btn-outline" onclick="cerrarCarrito()" style="margin-top:8px;">Seguir Comprando</button>
        </div>
    </div>
</body>
</html>
"""

# DASHBOARD STAFF CON MONITOREO DE PEDIDOS EN TIEMPO REAL
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
            alert('¡Producto agregado al inventario!');
            document.getElementById('form-prod').reset();
        }

        // Función para consultar y actualizar en tiempo real las compras de los clientes
        function cargarPedidosEnTiempoReal() {
            fetch('/api/pedidos')
                .then(res => res.json())
                .then(pedidos => {
                    let tabla = document.getElementById('tabla-pedidos-realtime');
                    document.getElementById('total-pedidos-count').innerText = pedidos.length;
                    
                    if(pedidos.length === 0) {
                        tabla.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--gray-text);">No hay actividad de clientes reciente</td></tr>';
                        return;
                    }

                    let html = '';
                    pedidos.forEach(p => {
                        html += `<tr>
                            <td><b>${p.hora}</b></td>
                            <td>${p.cliente}</td>
                            <td>${p.sede}</td>
                            <td>${p.productos}</td>
                            <td><b style="color:var(--primary);">$${p.total.toLocaleString()}</b></td>
                        </tr>`;
                    });
                    tabla.innerHTML = html;
                });
        }

        // Consultar cada 2 segundos
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
                <a onclick="cambiarSeccion('pedidos-live', this)">🛒 Pedidos en Vivo (<span id="total-pedidos-count">0</span>)</a>
                <a onclick="cambiarSeccion('inventario', this)">📦 Inventario</a>
                <a onclick="cambiarSeccion('sedes', this)">🏪 Sedes</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión Staff</a>
        </div>

        <div class="main">
            <!-- PANEL PRINCIPAL -->
            <div id="panel" class="seccion-tab fade-in">
                <div class="card">
                    <h2>Bienvenido al Panel de Administración Staff</h2>
                    <p style="color:var(--gray-text);">Control de mercancía, movimiento entre sedes y monitoreo en tiempo real.</p>
                </div>
                <div class="grid">
                    <div class="card">
                        <h3>Sede Principal Centro</h3>
                        <p style="font-size:24px; font-weight:bold; color:var(--primary); margin-top:5px;">1,240 <span style="font-size:14px; color:var(--dark);">ítems</span></p>
                    </div>
                    <div class="card">
                        <h3>Sede Norte</h3>
                        <p style="font-size:24px; font-weight:bold; color:var(--primary); margin-top:5px;">850 <span style="font-size:14px; color:var(--dark);">ítems</span></p>
                    </div>
                    <div class="card">
                        <h3>Sede Sur Express</h3>
                        <p style="font-size:24px; font-weight:bold; color:var(--primary); margin-top:5px;">410 <span style="font-size:14px; color:var(--dark);">ítems</span></p>
                    </div>
                </div>
            </div>

            <!-- ACTIVIDAD DE PEDIDOS EN TIEMPO REAL -->
            <div id="pedidos-live" class="seccion-tab fade-in" style="display:none;">
                <div class="card">
                    <h2>🔴 Ventas y Pedidos en Tiempo Real</h2>
                    <p style="color:var(--gray-text); margin-bottom:10px;">Esta lista se actualiza automáticamente con la actividad del portal de clientes.</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Hora</th>
                                <th>Cliente</th>
                                <th>Sede</th>
                                <th>Detalle Pedido</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-pedidos-realtime">
                            <tr><td colspan="5" style="text-align:center; color:var(--gray-text);">Cargando actividad...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- GESTIÓN INVENTARIO -->
            <div id="inventario" class="seccion-tab fade-in" style="display:none;">
                <div class="card">
                    <h3>Registrar Nuevo Ítem de Inventario</h3>
                    <form id="form-prod" onsubmit="agregarNuevoProducto(event)" style="display:grid; grid-template-columns:1fr 1fr 1fr auto; gap:10px; margin-top:15px;">
                        <input type="text" id="prod-nombre" placeholder="Nombre del Producto" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <select id="prod-sede" style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                            <option>Sede Centro</option>
                            <option>Sede Norte</option>
                            <option>Sede Sur</option>
                        </select>
                        <input type="number" id="prod-stock" placeholder="Cantidad" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <button type="submit" class="btn" style="margin:0;">+ Guardar</button>
                    </form>
                </div>

                <div class="card">
                    <h2>Stock Global Registrado</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Producto</th>
                                <th>Sede</th>
                                <th>Cantidad</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-inventario">
                            <tr>
                                <td>Lector Código de Barras 2D</td>
                                <td>Sede Centro</td>
                                <td>15 unidades</td>
                                <td><span class="tag tag-empleado">Disponible</span></td>
                            </tr>
                            <tr>
                                <td>Impresora Térmica POS</td>
                                <td>Sede Norte</td>
                                <td>3 unidades</td>
                                <td><span class="tag tag-admin">Bajo Stock</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- SEDES CON DIRECCIONES INVENTADAS -->
            <div id="sedes" class="seccion-tab fade-in" style="display:none;">
                <div class="card">
                    <h2>Configuración de Puntos de Atención</h2>
                    <div class="grid" style="margin-top:15px;">
                        <div class="card"><b>Sede Centro</b><br><span style="font-size:13px; color:var(--gray-text);">Av. Las Acacias #45-18, Sector Comercial</span></div>
                        <div class="card"><b>Sede Norte</b><br><span style="font-size:13px; color:var(--gray-text);">Calle Del Sol #102-15, Plaza Mayor</span></div>
                        <div class="card"><b>Sede Sur Express</b><br><span style="font-size:13px; color:var(--gray-text);">Transversal 78 #12-30, Parque Industrial</span></div>
                    </div>
                </div>
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

# RUTAS STAFF
@app.route('/login-staff', methods=['GET', 'POST'])
def login_staff():
    error = None
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        if usuario == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['user_type'] = 'staff'
            return redirect(url_for('dashboard'))
        else:
            error = "Credenciales de Administrador Incorrectas"
    return render_template_string(HTML_LOGIN_STAFF, css=CSS_ESTILOS, error=error)

@app.route('/dashboard')
def dashboard():
    if session.get('user_type') != 'staff':
        return redirect(url_for('login_staff'))
    return render_template_string(HTML_DASHBOARD, css=CSS_ESTILOS)

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

# ENDPOINTS API PARA TIEMPO REAL
@app.route('/api/crear-pedido', methods=['POST'])
def crear_pedido():
    from datetime import datetime
    data = request.json or {}
    nuevo_pedido = {
        'hora': datetime.now().strftime("%H:%M:%S"),
        'cliente': data.get('cliente', 'Anonimo'),
        'sede': data.get('sede', 'Sede Centro'),
        'productos': data.get('productos', ''),
        'total': data.get('total', 0)
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
