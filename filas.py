# CATÁLOGO INTERACTIVO DE CLIENTES CON PRODUCTOS COMESTIBLES Y MÉTODO DE PAGO REAL
HTML_TIENDA = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catálogo Comestibles - Cliente</title>
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
        
        function abrirPasarelaPago() {
            if(carrito.length === 0) { alert('Añade productos comestibles primero'); return; }
            cerrarCarrito();
            document.getElementById('modal-pago').style.display = 'flex';
        }

        function cerrarPasarelaPago() {
            document.getElementById('modal-pago').style.display = 'none';
        }
        
        function procesarPagoReal(event) {
            event.preventDefault();
            
            // Datos inventados de la tarjeta recolectados del formulario
            let tarjetaNum = document.getElementById('pay-card-num').value;
            let tarjetaExp = document.getElementById('pay-card-exp').value;
            let tarjetaCvc = document.getElementById('pay-card-cvc').value;
            let tarjetaNombre = document.getElementById('pay-card-name').value;

            if(!tarjetaNum || !tarjetaExp || !tarjetaCvc || !tarjetaNombre) {
                alert('Por favor complete todos los datos de pago.');
                return;
            }

            let total = carrito.reduce((sum, p) => sum + p.precio, 0);
            let detallesItems = carrito.map(p => p.nombre).join(', ');

            // Enviar pedido al servidor con pasarela de pago simulada y aprobada
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
                alert('💳 ¡Pago procesado con éxito por $' + total.toLocaleString() + '! Pedido confirmado para entrega en ' + '{{ sede_actual }}');
                carrito = [];
                actualizarCarritoUI();
                cerrarPasarelaPago();
                document.getElementById('form-pago-real').reset();
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
                    <h2 style="font-size:20px;">Catálogo de Comestibles</h2>
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
            <button class="btn cat-btn" onclick="filtrarCategoria('todos', this)">Todos los comestibles</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('snacks', this)">Snacks & Comida Rápida</button>
            <button class="btn btn-outline cat-btn" onclick="filtrarCategoria('bebidas', this)">Bebidas</button>
        </div>

        <!-- GRID DE PRODUCTOS COMESTIBLES -->
        <div class="grid">
            <div class="product-card" data-cat="snacks">
                <span class="product-badge">DELICIOSO</span>
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍔</div>
                <h3 style="font-size:16px;">Hamburguesa Artesanal Doble Carne</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Con queso cheddar fundido, tocino crujiente y papas.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$24.000</b>
                    <button class="btn" onclick="agregarProducto('Hamburguesa Artesanal Doble', 24000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="snacks">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🍕</div>
                <h3 style="font-size:16px;">Pizza Familiar Pepperoni</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Masa madre crujiente, extra queso mozzarella y pepperoni.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$45.000</b>
                    <button class="btn" onclick="agregarProducto('Pizza Familiar Pepperoni', 45000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
                </div>
            </div>

            <div class="product-card" data-cat="bebidas">
                <div style="font-size:45px; text-align:center; margin:10px 0;">🥤</div>
                <h3 style="font-size:16px;">Malteada de Chocolate Belga</h3>
                <p style="color:var(--gray-text); font-size:13px; margin:8px 0;">Helado artesanal de chocolate con crema batida.</p>
                <div style="margin-top:15px; display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:18px; color:var(--primary);">$12.000</b>
                    <button class="btn" onclick="agregarProducto('Malteada de Chocolate Belga', 12000)" style="width:auto; padding:8px 12px;">+ Añadir</button>
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
            <button class="btn" onclick="abrirPasarelaPago()" style="margin-top:20px;">💳 Proceder al Pago Seguro</button>
            <button class="btn btn-outline" onclick="cerrarCarrito()" style="margin-top:8px;">Seguir Comprando</button>
        </div>
    </div>

    <!-- MODAL DE PASARELA DE PAGO REAL (CON DATOS INVENTADOS) -->
    <div id="modal-pago" class="modal">
        <div class="modal-content">
            <h3>Pasarela de Pago Segura</h3>
            <p style="color:var(--gray-text); font-size:13px; margin-bottom:15px;">Ingrese los datos de su tarjeta de crédito o débito:</p>
            <form id="form-pago-real" onsubmit="procesarPagoReal(event)">
                <input type="text" id="pay-card-name" placeholder="Nombre en la tarjeta (Ej: Juan Pérez)" required>
                <input type="text" id="pay-card-num" placeholder="Número de Tarjeta (Ej: 4532 •••• •••• 8910)" maxlength="19" required>
                <div style="display:flex; gap:10px;">
                    <input type="text" id="pay-card-exp" placeholder="MM/AA" maxlength="5" required>
                    <input type="password" id="pay-card-cvc" placeholder="CVC" maxlength="4" required>
                </div>
                <button type="submit" class="btn" style="margin-top:15px;">🔒 Pagar Ahora de Forma Segura</button>
                <button type="button" class="btn btn-outline" onclick="cerrarPasarelaPago()" style="margin-top:8px;">Volver al Carrito</button>
            </form>
        </div>
    </div>
</body>
</html>
"""
