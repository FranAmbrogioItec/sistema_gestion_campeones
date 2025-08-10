from flask import render_template, request, redirect, url_for, flash, session, jsonify
from models import *
from forms import *
from sqlalchemy import or_
from datetime import datetime
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db

# =============================================
# Funciones de Utilidad
# =============================================

def calcular_stock_disponible(variante_id):
    """Calcula el stock disponible para una variante"""
    variante = Variante.query.get(variante_id)
    return variante.stock if variante else 0

def actualizar_stock(variante_id, cantidad, tipo, motivo, usuario="Sistema"):
    """Actualiza el stock y registra el movimiento"""
    variante = Variante.query.get(variante_id)
    if not variante:
        return False
    
    if tipo == 'entrada':
        variante.stock += cantidad
    elif tipo == 'salida':
        if variante.stock < cantidad:
            return False
        variante.stock -= cantidad
    
    movimiento = MovimientoStock(
        variante_id=variante_id,
        tipo=tipo,
        cantidad=cantidad,
        motivo=motivo,
        usuario=usuario
    )
    db.session.add(movimiento)
    db.session.commit()
    return True

# =============================================
# Rutas de Autenticación
# =============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # Crea una instancia del formulario
    
    if form.validate_on_submit():
        # Lógica para procesar el login
        email = form.email.data
        password = form.password.data
        remember = form.remember.data
        
        # Aquí iría tu lógica de autenticación
        flash('Inicio de sesión exitoso', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/login.html', form=form)  # Pasa el formulario a la plantilla

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('login'))

# =============================================
# Rutas del Dashboard
# =============================================

@app.route('/dashboard')
@login_required
def dashboard():
    total_productos = Producto.query.count()
    total_ventas = Venta.query.count()
    total_clientes = Cliente.query.count()
    
    ventas_recientes = Venta.query.order_by(Venta.fecha_venta.desc()).limit(5).all()
    productos_bajo_stock = Variante.query.filter(Variante.stock <= Variante.stock_minimo).count()
    
    return render_template('dashboard.html',
                         total_productos=total_productos,
                         total_ventas=total_ventas,
                         total_clientes=total_clientes,
                         ventas_recientes=ventas_recientes,
                         productos_bajo_stock=productos_bajo_stock)

# =============================================
# Rutas de Productos
# =============================================

@app.route('/productos')
@login_required
def listar_productos():
    # Filtros
    club_id = request.args.get('club')
    temporada = request.args.get('temporada')
    categoria_id = request.args.get('categoria')
    talle = request.args.get('talle')
    
    query = Producto.query
    
    if club_id:
        query = query.filter_by(club_id=club_id)
    if temporada:
        query = query.filter_by(temporada=temporada)
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    if talle:
        query = query.join(Variante).filter(Variante.talle == talle)
    
    productos = query.order_by(Producto.nombre).all()
    clubes = Club.query.order_by(Club.nombre).all()
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    talles = db.session.query(Variante.talle).distinct().all()
    
    return render_template('productos/listar.html', 
                         productos=productos,
                         clubes=clubes,
                         categorias=categorias,
                         talles=[t[0] for t in talles],
                         filtros={
                             'club': club_id,
                             'temporada': temporada,
                             'categoria': categoria_id,
                             'talle': talle
                         })

@app.route('/productos/nuevo', methods=['GET', 'POST'])
@login_required
def crear_producto():
    form = ProductoForm()
    form.club_id.choices = [(c.id, c.nombre) for c in Club.query.order_by(Club.nombre)]
    form.categoria_id.choices = [(c.id, c.nombre) for c in Categoria.query.order_by(Categoria.nombre)]
    
    if form.validate_on_submit():
        producto = Producto(
            nombre=form.nombre.data,
            club_id=form.club_id.data,
            categoria_id=form.categoria_id.data,
            temporada=form.temporada.data,
            descripcion=form.descripcion.data,
            precio=form.precio.data if form.precio.data else 0
        )
        db.session.add(producto)
        db.session.commit()
        flash('Producto creado exitosamente!', 'success')
        return redirect(url_for('agregar_variantes', producto_id=producto.id))
    
    return render_template('productos/crear.html', form=form)

@app.route('/productos/<int:producto_id>/variantes', methods=['GET', 'POST'])
@login_required
def agregar_variantes(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    form = VarianteForm()
    
    if form.validate_on_submit():
        variante = Variante(
            producto_id=producto.id,
            talle=form.talle.data,
            color=form.color.data,
            sku=form.sku.data,
            precio=form.precio.data,
            stock=form.stock.data,
            stock_minimo=form.stock_minimo.data
        )
        db.session.add(variante)
        
        # Registrar movimiento de stock inicial
        actualizar_stock(
            variante_id=variante.id,
            cantidad=form.stock.data,
            tipo='entrada',
            motivo='Carga inicial de stock',
            usuario=current_user.username
        )
        
        db.session.commit()
        flash('Variante agregada exitosamente!', 'success')
        return redirect(url_for('agregar_variantes', producto_id=producto.id))
    
    variantes = Variante.query.filter_by(producto_id=producto.id).all()
    return render_template('productos/variantes.html', 
                         producto=producto, 
                         form=form, 
                         variantes=variantes)

@app.route('/variantes/<int:variante_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_variante(variante_id):
    variante = Variante.query.get_or_404(variante_id)
    form = VarianteForm(obj=variante)
    
    if form.validate_on_submit():
        # Calcular diferencia de stock
        diferencia = form.stock.data - variante.stock
        
        variante.talle = form.talle.data
        variante.color = form.color.data
        variante.sku = form.sku.data
        variante.precio = form.precio.data
        variante.stock_minimo = form.stock_minimo.data
        
        if diferencia != 0:
            tipo = 'entrada' if diferencia > 0 else 'salida'
            actualizar_stock(
                variante_id=variante.id,
                cantidad=abs(diferencia),
                tipo=tipo,
                motivo='Ajuste manual de stock',
                usuario=current_user.username
            )
        else:
            db.session.commit()
        
        flash('Variante actualizada exitosamente!', 'success')
        return redirect(url_for('agregar_variantes', producto_id=variante.producto_id))
    
    return render_template('productos/editar_variante.html', form=form, variante=variante)

# =============================================
# Rutas de Ventas
# =============================================

@app.route('/ventas/nueva', methods=['GET', 'POST'])
@login_required
def nueva_venta():
    form = VentaForm()
    form.cliente_id.choices = [(0, 'Cliente ocasional')] + [(c.id, c.nombre) for c in Cliente.query.order_by(Cliente.nombre)]
    
    if request.method == 'POST':
        items = request.form.getlist('items[]')
        
        if not items:
            flash('Debe agregar al menos un producto a la venta', 'danger')
            return render_template('ventas/nueva.html', form=form)
        
        # Crear venta
        venta = Venta(
            cliente_id=form.cliente_id.data if form.cliente_id.data != 0 else None,
            tipo_venta='fisica',
            total=0  # Se calculará con los items
        )
        db.session.add(venta)
        db.session.flush()
        
        total_venta = 0
        items_validos = 0
        
        for item in items:
            try:
                variante_id, cantidad = map(int, item.split('_'))
                variante = Variante.query.get(variante_id)
                
                if not variante or cantidad <= 0:
                    continue
                
                # Verificar stock
                if variante.stock < cantidad:
                    flash(f'Stock insuficiente para {variante.producto.nombre} - Talle: {variante.talle}', 'warning')
                    continue
                
                # Crear item de venta
                venta_item = VentaItem(
                    venta_id=venta.id,
                    variante_id=variante.id,
                    cantidad=cantidad,
                    precio_unitario=variante.precio,
                    subtotal=variante.precio * cantidad
                )
                db.session.add(venta_item)
                
                # Actualizar stock
                actualizar_stock(
                    variante_id=variante.id,
                    cantidad=cantidad,
                    tipo='salida',
                    motivo=f'Venta #{venta.id}',
                    usuario=current_user.username
                )
                
                total_venta += venta_item.subtotal
                items_validos += 1
                
            except ValueError:
                continue
        
        if items_validos == 0:
            db.session.rollback()
            flash('No se pudo procesar la venta. Verifique los productos seleccionados.', 'danger')
            return render_template('ventas/nueva.html', form=form)
        
        # Actualizar total de venta
        venta.total = total_venta
        
        # Registrar movimiento en caja
        caja = Caja.query.first()
        if not caja:
            caja = Caja(nombre="Caja Principal", saldo=0)
            db.session.add(caja)
        
        caja.saldo += total_venta
        movimiento = MovimientoCaja(
            caja_id=caja.id,
            tipo='ingreso',
            monto=total_venta,
            motivo=f'Venta #{venta.id}'
        )
        db.session.add(movimiento)
        venta.movimiento_caja_id = movimiento.id
        
        db.session.commit()
        flash(f'Venta registrada exitosamente! Total: ${total_venta:.2f}', 'success')
        return redirect(url_for('detalle_venta', venta_id=venta.id))
    
    # Para GET, mostrar formulario
    productos = Producto.query.options(
        db.joinedload(Producto.variantes)
    ).order_by(Producto.nombre).all()
    
    return render_template('ventas/nueva.html', form=form, productos=productos)

@app.route('/ventas/<int:venta_id>')
@login_required
def detalle_venta(venta_id):
    venta = Venta.query.options(
        db.joinedload(Venta.items).joinedload(VentaItem.variante).joinedload(Variante.producto),
        db.joinedload(Venta.cliente)
    ).get_or_404(venta_id)
    
    return render_template('ventas/detalle.html', venta=venta)

@app.route('/ventas')
@login_required
def listar_ventas():
    # Filtros
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    cliente_id = request.args.get('cliente_id')
    tipo_venta = request.args.get('tipo_venta')
    
    query = Venta.query
    
    if fecha_desde:
        query = query.filter(Venta.fecha_venta >= fecha_desde)
    if fecha_hasta:
        query = query.filter(Venta.fecha_venta <= fecha_hasta)
    if cliente_id:
        query = query.filter(Venta.cliente_id == cliente_id)
    if tipo_venta:
        query = query.filter(Venta.tipo_venta == tipo_venta)
    
    ventas = query.order_by(Venta.fecha_venta.desc()).all()
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    
    return render_template('ventas/listar.html', 
                         ventas=ventas,
                         clientes=clientes,
                         filtros={
                             'fecha_desde': fecha_desde,
                             'fecha_hasta': fecha_hasta,
                             'cliente_id': cliente_id,
                             'tipo_venta': tipo_venta
                         })

# =============================================
# Rutas de Gestión de Stock
# =============================================

@app.route('/stock')
@login_required
def gestion_stock():
    # Filtros
    stock_bajo = request.args.get('stock_bajo', 'false') == 'true'
    categoria_id = request.args.get('categoria_id')
    club_id = request.args.get('club_id')
    
    query = Variante.query.join(Variante.producto)
    
    if stock_bajo:
        query = query.filter(Variante.stock <= Variante.stock_minimo)
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    if club_id:
        query = query.filter(Producto.club_id == club_id)
    
    variantes = query.options(
        db.joinedload(Variante.producto).joinedload(Producto.club),
        db.joinedload(Variante.producto).joinedload(Producto.categoria_rel)
    ).order_by(Producto.nombre, Variante.talle).all()
    
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    clubes = Club.query.order_by(Club.nombre).all()
    
    return render_template('stock/gestion.html', 
                         variantes=variantes,
                         categorias=categorias,
                         clubes=clubes,
                         filtros={
                             'stock_bajo': stock_bajo,
                             'categoria_id': categoria_id,
                             'club_id': club_id
                         })

@app.route('/stock/ajustar/<int:variante_id>', methods=['GET', 'POST'])
@login_required
def ajustar_stock(variante_id):
    variante = Variante.query.options(
        db.joinedload(Variante.producto)
    ).get_or_404(variante_id)
    
    if request.method == 'POST':
        try:
            cantidad = int(request.form.get('cantidad'))
            tipo = request.form.get('tipo')
            motivo = request.form.get('motivo', 'Ajuste manual de stock')
            
            if tipo not in ['entrada', 'salida']:
                flash('Tipo de movimiento inválido', 'danger')
                return redirect(url_for('ajustar_stock', variante_id=variante_id))
            
            if cantidad <= 0:
                flash('La cantidad debe ser mayor a cero', 'danger')
                return redirect(url_for('ajustar_stock', variante_id=variante_id))
            
            if tipo == 'salida' and variante.stock < cantidad:
                flash('No hay suficiente stock para este ajuste', 'danger')
                return redirect(url_for('ajustar_stock', variante_id=variante_id))
            
            # Realizar ajuste
            actualizar_stock(
                variante_id=variante.id,
                cantidad=cantidad,
                tipo=tipo,
                motivo=motivo,
                usuario=current_user.username
            )
            
            flash(f'Stock ajustado exitosamente ({tipo} de {cantidad} unidades)', 'success')
            return redirect(url_for('gestion_stock'))
        
        except ValueError:
            flash('Cantidad inválida', 'danger')
            return redirect(url_for('ajustar_stock', variante_id=variante_id))
    
    return render_template('stock/ajustar.html', variante=variante)

@app.route('/stock/movimientos')
@login_required
def movimientos_stock():
    # Filtros
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    tipo = request.args.get('tipo')
    producto_id = request.args.get('producto_id')
    
    query = MovimientoStock.query.join(MovimientoStock.variante)
    
    if fecha_desde:
        query = query.filter(MovimientoStock.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(MovimientoStock.fecha <= fecha_hasta)
    if tipo:
        query = query.filter(MovimientoStock.tipo == tipo)
    if producto_id:
        query = query.filter(Variante.producto_id == producto_id)
    
    movimientos = query.options(
        db.joinedload(MovimientoStock.variante).joinedload(Variante.producto)
    ).order_by(MovimientoStock.fecha.desc()).all()
    
    productos = Producto.query.order_by(Producto.nombre).all()
    
    return render_template('stock/movimientos.html', 
                         movimientos=movimientos,
                         productos=productos,
                         filtros={
                             'fecha_desde': fecha_desde,
                             'fecha_hasta': fecha_hasta,
                             'tipo': tipo,
                             'producto_id': producto_id
                         })

# =============================================
# Rutas de Gestión de Caja
# =============================================

@app.route('/caja')
@login_required
def gestion_caja():
    caja = Caja.query.first()
    if not caja:
        caja = Caja(nombre="Caja Principal", saldo=0)
        db.session.add(caja)
        db.session.commit()
    
    # Obtener últimos movimientos
    movimientos = MovimientoCaja.query.filter_by(caja_id=caja.id)\
        .order_by(MovimientoCaja.fecha.desc())\
        .limit(10)\
        .all()
    
    return render_template('caja/gestion.html', caja=caja, movimientos=movimientos)

@app.route('/caja/movimientos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_movimiento_caja():
    form = MovimientoCajaForm()
    
    if form.validate_on_submit():
        caja = Caja.query.first()
        if not caja:
            caja = Caja(nombre="Caja Principal", saldo=0)
            db.session.add(caja)
        
        if form.tipo.data == 'egreso' and caja.saldo < form.monto.data:
            flash('No hay suficiente saldo en caja para este egreso', 'danger')
            return render_template('caja/nuevo_movimiento.html', form=form)
        
        movimiento = MovimientoCaja(
            caja_id=caja.id,
            tipo=form.tipo.data,
            monto=form.monto.data,
            motivo=form.motivo.data
        )
        db.session.add(movimiento)
        
        # Actualizar saldo de caja
        if form.tipo.data == 'ingreso':
            caja.saldo += form.monto.data
        else:
            caja.saldo -= form.monto.data
        
        db.session.commit()
        flash('Movimiento registrado exitosamente!', 'success')
        return redirect(url_for('gestion_caja'))
    
    return render_template('caja/nuevo_movimiento.html', form=form)

@app.route('/caja/movimientos')
@login_required
def listar_movimientos_caja():
    # Filtros
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    tipo = request.args.get('tipo')
    
    caja = Caja.query.first()
    if not caja:
        return redirect(url_for('gestion_caja'))
    
    query = MovimientoCaja.query.filter_by(caja_id=caja.id)
    
    if fecha_desde:
        query = query.filter(MovimientoCaja.fecha >= fecha_desde)
    if fecha_hasta:
        query = query.filter(MovimientoCaja.fecha <= fecha_hasta)
    if tipo:
        query = query.filter(MovimientoCaja.tipo == tipo)
    
    movimientos = query.order_by(MovimientoCaja.fecha.desc()).all()
    
    return render_template('caja/movimientos.html', 
                         movimientos=movimientos,
                         caja=caja,
                         filtros={
                             'fecha_desde': fecha_desde,
                             'fecha_hasta': fecha_hasta,
                             'tipo': tipo
                         })

# =============================================
# Rutas de Configuración
# =============================================

@app.route('/configuracion/clubes', methods=['GET', 'POST'])
@login_required
def gestion_clubes():
    form = ClubForm()
    
    if form.validate_on_submit():
        club = Club(
            nombre=form.nombre.data,
            liga=form.liga.data
        )
        db.session.add(club)
        db.session.commit()
        flash('Club agregado exitosamente!', 'success')
        return redirect(url_for('gestion_clubes'))
    
    clubes = Club.query.order_by(Club.nombre).all()
    return render_template('configuracion/clubes.html', form=form, clubes=clubes)

@app.route('/configuracion/categorias', methods=['GET', 'POST'])
@login_required
def gestion_categorias():
    form = CategoriaForm()
    
    if form.validate_on_submit():
        categoria = Categoria(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data
        )
        db.session.add(categoria)
        db.session.commit()
        flash('Categoría agregada exitosamente!', 'success')
        return redirect(url_for('gestion_categorias'))
    
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('configuracion/categorias.html', form=form, categorias=categorias)

@app.route('/configuracion/clientes', methods=['GET', 'POST'])
@login_required
def gestion_clientes():
    form = ClienteForm()
    
    if form.validate_on_submit():
        cliente = Cliente(
            nombre=form.nombre.data,
            email=form.email.data,
            telefono=form.telefono.data,
            direccion=form.descripcion.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente agregado exitosamente!', 'success')
        return redirect(url_for('gestion_clientes'))
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('configuracion/clientes.html', form=form, clientes=clientes)

@app.route('/configuracion/proveedores', methods=['GET', 'POST'])
@login_required
def gestion_proveedores():
    form = ProveedorForm()
    
    if form.validate_on_submit():
        proveedor = Proveedor(
            nombre=form.nombre.data,
            contacto=form.contacto.data,
            telefono=form.telefono.data,
            email=form.email.data
        )
        db.session.add(proveedor)
        db.session.commit()
        flash('Proveedor agregado exitosamente!', 'success')
        return redirect(url_for('gestion_proveedores'))
    
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template('configuracion/proveedores.html', form=form, proveedores=proveedores)

# =============================================
# API Endpoints
# =============================================

@app.route('/api/buscar_productos')
@login_required
def buscar_productos():
    termino = request.args.get('q', '')
    
    if not termino:
        return jsonify([])
    
    # Buscar por nombre de producto, SKU o club
    productos = Producto.query.join(Club).join(Variante).filter(
        or_(
            Producto.nombre.ilike(f'%{termino}%'),
            Variante.sku.ilike(f'%{termino}%'),
            Club.nombre.ilike(f'%{termino}%')
        )
    ).options(
        db.joinedload(Producto.variantes),
        db.joinedload(Producto.club)
    ).limit(10).all()
    
    resultados = []
    for p in productos:
        for v in p.variantes:
            resultados.append({
                'id': v.id,
                'text': f"{p.nombre} - {p.club.nombre} ({v.talle}) - SKU: {v.sku} - Stock: {v.stock}",
                'precio': v.precio,
                'stock': v.stock
            })
    
    return jsonify(resultados)

@app.route('/api/stock/<sku>')
def api_stock(sku):
    variante = Variante.query.filter_by(sku=sku).first()
    if not variante:
        return jsonify({'error': 'SKU no encontrado'}), 404
    
    return jsonify({
        'sku': variante.sku,
        'producto': variante.producto.nombre,
        'talle': variante.talle,
        'stock': variante.stock,
        'precio': variante.precio
    })

# =============================================
# Otras Rutas
# =============================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))