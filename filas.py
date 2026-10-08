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
                <p>Gestión inteligente de inventarios y alimentos gourmet</p>
            </div>
            <div class="selector-grid">
                <a href="/login-staff" class="selector-card staff">
                    <div class="icon">💼</div>
                    <h2>Personal / Staff</h2>
                    <p>Acceso administrativo a la gestión de inventario y sedes.</p>
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

# DASHBOARD STAFF CON MONITOREO DE PEDIDOS EN TIEMPO REAL Y MÉTODO DE PAGO
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

        // Consultar pedidos y compras de comida en tiempo real
        function cargarPedidosEnTiempoReal() {
            fetch('/api/pedidos')
                .then(res => res.json())
                .then(pedidos => {
                    let tabla = document.getElementById('tabla-pedidos-realtime');
                    document.getElementById('total-pedidos-count').innerText = pedidos.length;
                    
                    if(pedidos.length === 0) {
                        tabla.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--gray-text);">No hay pedidos de comida recientes</td></tr>';
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
                <a onclick="cambiarSeccion('pedidos-live', this)">🔴 Pedidos de Comida (<span id="total-pedidos-count">0</span>)</a>
                <a onclick="cambiarSeccion('inventario', this)">🍔 Control de Cocina</a>
                <a onclick="cambiarSeccion('sedes', this)">🏪 Puntos de Venta</a>
            </div>
            <a href="/logout" style="background:#334155; margin-top:20px;">🚪 Cerrar Sesión Staff</a>
        </div>

        <div class="main">
            <!-- PANEL PRINCIPAL -->
            <div id="panel" class="seccion-tab fade-in">
                <div class="card">
                    <h2>Panel de Administración de Alimentos</h2>
                    <p style="color:var(--gray-text);">Monitoreo de pedidos en línea, métodos de pago autorizados y stock de cocina.</p>
                </div>
                <div class="grid">
                    <div class="card">
                        <h3>Sede Centro (Cocina)</h3>
                        <p style="font-size:24px; font-weight:bold; color:var(--primary); margin-top:5px;">420 <span style="font-size:14px; color:var(--dark);">órdenes hoy</span></p>
                    </div>
                    <div class="card">
                        <h3>Sede Norte Gourmet</h3>
                        <p style="font-size:24px; font-weight:bold; color:var(--primary); margin-top:5px;">310 <span style="font-size:14px; color:var(--dark);">órdenes hoy</span></p>
                    </div>
                    <div class="card">
                        <h3>Sede Sur Express</h3>
                        <p style="font-size:24px; font-weight:bold; color:var(--primary); margin-top:5px;">190 <span style="font-size:14px; color:var(--dark);">órdenes hoy</span></p>
                    </div>
                </div>
            </div>

            <!-- PEDIDOS EN TIEMPO REAL -->
            <div id="pedidos-live" class="seccion-tab fade-in" style="display:none;">
                <div class="card">
                    <h2>🔴 Órdenes de Comida en Tiempo Real</h2>
                    <p style="color:var(--gray-text); margin-bottom:10px;">Clientes ordenando platillos con métodos de pago reales (datos de prueba).</p>
                    <table>
                        <thead>
                            <tr>
                                <th>Hora</th>
                                <th>Cliente</th>
                                <th>Sede</th>
                                <th>Platillos Ordenados</th>
                                <th>Método de Pago</th>
                                <th>Total</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-pedidos-realtime">
                            <tr><td colspan="6" style="text-align:center; color:var(--gray-text);">Cargando actividad...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- GESTIÓN INVENTARIO / COCINA -->
            <div id="inventario" class="seccion-tab fade-in" style="display:none;">
                <div class="card">
                    <h3>Registrar Nuevo Ingrediente o Platillo</h3>
                    <form id="form-prod" onsubmit="agregarNuevoProducto(event)" style="display:grid; grid-template-columns:1fr 1fr 1fr auto; gap:10px; margin-top:15px;">
                        <input type="text" id="prod-nombre" placeholder="Nombre del Platillo" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <select id="prod-sede" style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                            <option>Sede Centro</option>
                            <option>Sede Norte</option>
                            <option>Sede Sur Express</option>
                        </select>
                        <input type="number" id="prod-stock" placeholder="Porciones Stock" required style="padding:10px; border:1px solid var(--gray); border-radius:8px;">
                        <button type="submit" class="btn" style="margin:0;">+ Guardar</button>
                    </form>
                </div>

                <div class="card">
                    <h2>Stock Actual de Cocina</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Platillo / Alimento</th>
                                <th>Sede</th>
                                <th>Disponibilidad</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody id="tabla-inventario">
                            <tr>
                                <td>Hamburguesa Doble Angus BBQ</td>
                                <td>Sede Centro</td>
                                <td>25 porciones</td>
                                <td><span class="tag tag-empleado">Disponible</span></td>
                            </tr>
                            <tr>
                                <td>Pizza Pepperoni Suprema Gde</td>
                                <td>Sede Norte Gourmet</td>
                                <td>4 porciones</td>
                                <td><span class="tag tag-admin">Stock Bajo</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- SEDES -->
            <div id="sedes" class="seccion-tab fade-in" style="display:none;">
                <div class="card">
                    <h2>Puntos de Distribución de Alimentos</h2>
                    <div class="grid" style="margin-top:15px;">
                        <div class="card"><b>Sede Centro</b><br><span style="font-size:13px; color:var(--gray-text);">Av. Las Acacias #45-18, Zona Gastronómica</span></div>
                        <div class="card"><b>Sede Norte Gourmet</b><br><span style="font-size:13px; color:var(--gray-text);">Calle Del Sol #102-15, Mall Gourmet</span></div>
                        <div class="card"><b>Sede Sur Express</b><br><span style="font-size:13px; color:var(--gray-text);">Transversal 78 #12-30, Autopista Sur</span></div>
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
        'total': data.get('total', 0),
        'metodo_pago': data.get('metodo_pago', 'Tarjeta')
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
