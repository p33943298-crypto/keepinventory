from flask import Flask, render_template_string

app = Flask(__name__)

# Todo el estilo CSS de KeepInventoryLite
CSS_ESTILOS = """
/* ========== KeepInventoryLite - CSS COMPLETO FINAL ========== */
:root{
  --primary:#0f8a5f;
  --primary-dark:#064e3b;
  --dark:#1e293b;
  --light:#f8fafc;
  --gray:#e2e8f0;
  --gray-text:#64748b;
  --red:#dc2626;
  --blue:#2563eb;
}

*{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI', system-ui, -apple-system, sans-serif;}
body{background:var(--light); color:var(--dark); line-height:1.5;}

/* --- BRANDING --- */
.brand{display:flex;align-items:center;gap:12px;margin-bottom:10px;}
.logo{width:48px;height:48px;background:var(--primary);color:white;display:flex;align-items:center;justify-content:center;border-radius:12px;font-weight:900;font-size:20px;flex-shrink:0;}
.brand-large{color:white;margin-bottom:40px; text-align:center;}
.logo-large{width:80px;height:80px;background:white;color:var(--primary);font-size:36px;font-weight:900;border-radius:20px;display:flex;align-items:center;justify-content:center;margin:0 auto 15px;}
.brand-large h1{font-size:42px; margin-bottom:5px;}
.brand-large p{opacity:0.9; font-size:16px;}

/* --- LANDING SELECTOR (index.html) --- */
.landing-body{display:flex;justify-content:center;align-items:center;min-height:100vh;background:linear-gradient(135deg,var(--primary),var(--primary-dark));padding:20px;}
.landing-container{max-width:900px;width:100%;text-align:center;}
.selector-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
.selector-card{background:white;padding:40px 30px;border-radius:20px;cursor:pointer;transition:all .2s ease;box-shadow:0 10px 30px rgba(0,0,0,.25);text-align:center;}
.selector-card:hover{transform:translateY(-8px); box-shadow:0 20px 40px rgba(0,0,0,.3);}
.selector-card .icon{font-size:56px;margin-bottom:15px;}
.selector-card h2{margin-bottom:8px; font-size:22px;}
.selector-card p{color:var(--gray-text);margin-bottom:15px;}
.selector-card span{color:var(--primary);font-weight:bold;font-size:14px;}
.selector-card.staff{border-top:6px solid var(--dark);}
.selector-card.client{border-top:6px solid var(--primary);}

/* --- LOGIN --- */
.login-body{display:flex;justify-content:center;align-items:center;min-height:100vh;background:linear-gradient(135deg,var(--primary),var(--primary-dark));padding:20px;}
.login-container{background:white;padding:40px;border-radius:20px;width:100%;max-width:420px;box-shadow:0 20px 50px rgba(0,0,0,.3);text-align:center;}
.login-container p{color:var(--gray-text); margin-bottom:15px;}
.login-container input, .login-container select, .login-container textarea{width:100%;padding:12px 14px;margin:8px 0;border:1px solid var(--gray);border-radius:10px;outline:none; font-size:14px;}
.login-container input:focus{border-color:var(--primary); box-shadow:0 0 0 3px rgba(15,138,95,.1);}
button{width:100%;padding:12px 16px;background:var(--primary);color:white;border:none;border-radius:10px;cursor:pointer;font-weight:bold;margin-top:10px; font-size:14px; transition:opacity .2s;}
button:hover{opacity:.9;} button:disabled{opacity:.5; cursor:not-allowed;}
.guest-btn{background:var(--dark);} .divider{margin:18px 0;color:#94a3b8; font-size:13px;}
.demo-creds{margin-top:15px; font-size:11px; background:#f1f5f9; padding:10px; border-radius:8px; text-align:left;}

/* --- DASHBOARD STAFF --- */
.dashboard{display:flex;min-height:100vh;}
.sidebar{width:280px;background:var(--dark);color:white;padding:24px;flex-shrink:0;}
.sidebar .brand{margin-bottom:30px;}
.sidebar .brand .logo{width:38px;height:38px;font-size:16px;}
.sidebar a{display:block;color:#cbd5e1;padding:12px 14px;text-decoration:none;border-radius:8px;margin:6px 0; font-size:14px; transition:all .2s;}
.sidebar a:hover,.sidebar a.active{background:var(--primary);color:white;}
.sidebar button{margin-top:30px; background:#334155;}
.main{flex:1;padding:30px; overflow-y:auto;}
.card{background:white;padding:24px;border-radius:16px;box-shadow:0 2px 10px rgba(0,0,0,.05);margin-bottom:24px; border:1px solid #f1f5f9;}
.card h2, .card h3{margin-bottom:12px;}
.grid{display:grid;grid-template-columns:repeat(auto-fill, minmax(220px, 1fr));gap:20px;}
table{width:100%;border-collapse:collapse;margin-top:15px; font-size:14px;}
th,td{padding:12px;border-bottom:1px solid var(--gray);text-align:left;}
th{background:#f8fafc; font-weight:700; color:var(--gray-text); font-size:12px; text-transform:uppercase;}
.tag{padding:4px 10px;border-radius:20px;font-size:11px;color:white; font-weight:700; text-transform:uppercase;}
.tag-admin{background:var(--red);} .tag-manager{background:var(--blue);} .tag-empleado{background:var(--primary);}
.select-sede{padding:10px 14px;border-radius:10px;border:1px solid var(--gray);margin-bottom:20px; background:white; min-width:200px;}

/* --- TIENDA CLIENTE - SEDE MUY OBVIA --- */
.sede-selector{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin:20px 0;}
.sede-card{background:white;border:3px solid var(--gray);border-radius:16px;padding:26px;text-align:center;cursor:pointer;transition:all .2s ease;}
.sede-card:hover{border-color:var(--primary);transform:scale(1.02); box-shadow:0 8px 20px rgba(0,0,0,.08);}
.sede-card.active{border-color:var(--primary);background:#f0fdf4; box-shadow:0 8px 20px rgba(15,138,95,.15);}
.sede-card .sede-icon{font-size:52px;margin-bottom:12px;}
.sede-card h3{font-size:18px; margin-bottom:6px;}
.sede-card p{font-size:13px; color:var(--gray-text); margin-bottom:10px;}
.product-shop{border:1px solid var(--gray);border-radius:16px;padding:18px;text-align:center;background:white;transition:all .2s;}
.product-shop:hover{box-shadow:0 6px 18px rgba(0,0,0,.08); transform:translateY(-2px);}
.product-shop h4{margin-bottom:6px; font-size:15px;}
.product-shop b{color:var(--primary); font-size:16px;}

/* --- RESPONSIVE --- */
@media(max-width:800px){
  .selector-grid{grid-template-columns:1fr;}
  .dashboard{flex-direction:column;}
  .sidebar{width:100%;}
  .brand-large h1{font-size:32px;}
}
"""

# Plantilla HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KeepInventoryLite</title>
    <style>
        {{ css | safe }}
    </style>
</head>
<body>
    <div class="landing-body">
        <div class="landing-container">
            <div class="brand-large">
                <div class="logo-large">KI</div>
                <h1>KeepInventoryLite</h1>
                <p>Sistema de Gestión e Inventario</p>
            </div>
            <div class="selector-grid">
                <div class="selector-card staff">
                    <div class="icon">💼</div>
                    <h2>Personal / Staff</h2>
                    <p>Acceso a administración y control de inventarios.</p>
                    <span>INGRESAR COMO STAFF →</span>
                </div>
                <div class="selector-card client">
                    <div class="icon">🛒</div>
                    <h2>Clientes</h2>
                    <p>Consulta de catálogo y disponibilidad por sede.</p>
                    <span>VER CATÁLOGO →</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, css=CSS_ESTILOS)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)