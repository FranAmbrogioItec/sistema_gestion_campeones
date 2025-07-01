from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
from datetime import datetime

from models import db, Producto, Variante, Venta, VentaItem, Caja, MovimientoCaja, MovimientoStock

from forms import VentaForm, ProductoForm, VarianteForm, MovimientoCajaForm

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una_clave_muy_secreta') # Usa una variable de entorno para producción
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_ventas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializa db con la aplicación Flask
db.init_app(app)


# Context processor para hacer 'datetime' disponible en todas las plantillas
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# Rutas de la aplicación

@app.route('/')
def index():
    productos = Producto.query.all()
    # Para cada producto, cargar sus variantes. Esto es importante para mostrar el stock en el index.html
    for producto in productos:
        producto.variantes  # Carga explícitamente las variantes para evitar LazyLoadingError en la plantilla

    return render_template('index.html', productos=productos)

@app.route('/cargar_producto', methods=['GET', 'POST'])
def cargar_producto():
    form = ProductoForm()
    if form.validate_on_submit():
        nuevo_producto = Producto(
            nombre=form.nombre.data,
            categoria=form.categoria.data,
            equipo=form.equipo.data,
            temporada=form.temporada.data
        )
        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto cargado exitosamente!', 'success')
        return redirect(url_for('index'))
    return render_template('cargar_producto.html', form=form)

@app.route('/cargar_variante/<int:producto_id>', methods=['GET', 'POST'])
def cargar_variante(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    form = VarianteForm()
    if form.validate_on_submit():
        nueva_variante = Variante(
            producto_id=producto.id,
            talle=form.talle.data,
            color=form.color.data,
            sku=form.sku.data,
            stock_inicial=form.stock.data,
            stock_actual=form.stock.data # El stock actual es igual al inicial al cargar
        )
        db.session.add(nueva_variante)
        
        # Registrar movimiento de stock inicial
        movimiento = MovimientoStock(
            variante=nueva_variante,
            tipo='entrada',
            cantidad=form.stock.data,
            motivo='Carga inicial de variante'
        )
        db.session.add(movimiento)

        db.session.commit()
        flash(f'Variante para {producto.nombre} ({nueva_variante.sku}) cargada exitosamente!', 'success')
        return redirect(url_for('index'))
    return render_template('cargar_variante.html', form=form, producto=producto)


@app.route('/registrar_venta', methods=['GET', 'POST'])
def registrar_venta():
    form = VentaForm()
    if form.validate_on_submit():
        sku = form.sku.data
        cantidad = form.cantidad.data
        precio_unitario = form.precio_unitario.data

        variante = Variante.query.filter_by(sku=sku).first()

        if not variante:
            flash(f'SKU "{sku}" no encontrado.', 'danger')
        elif variante.stock_actual < cantidad:
            flash(f'Stock insuficiente para {variante.producto.nombre} ({variante.talle}, {variante.color}). Stock actual: {variante.stock_actual}', 'warning')
        else:
            # Crear la venta y el ítem de venta
            nueva_venta = Venta(total=cantidad * precio_unitario)
            db.session.add(nueva_venta)
            db.session.flush() # Para obtener el ID de la venta antes de commit

            venta_item = VentaItem(
                venta_id=nueva_venta.id,
                variante_id=variante.id,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )
            db.session.add(venta_item)

            # Actualizar stock de la variante
            variante.stock_actual -= cantidad
            
            # Registrar movimiento de stock
            movimiento_stock = MovimientoStock(
                variante=variante,
                tipo='salida',
                cantidad=cantidad,
                motivo=f'Venta #{nueva_venta.id}'
            )
            db.session.add(movimiento_stock)

            # Registrar movimiento en caja
            caja = Caja.query.first()
            if not caja:
                caja = Caja(saldo=0.0)
                db.session.add(caja)
                db.session.flush()
            
            caja.saldo += nueva_venta.total
            movimiento_caja = MovimientoCaja(
                caja_id=caja.id,
                tipo='ingreso',
                monto=nueva_venta.total,
                motivo=f'Venta de SKU {sku} (Venta #{nueva_venta.id})'
            )
            db.session.add(movimiento_caja)

            db.session.commit()
            flash(f'Venta de {cantidad} unidades de {variante.producto.nombre} ({variante.talle}, {variante.color}) registrada exitosamente!', 'success')
            return redirect(url_for('registrar_venta'))
            
    return render_template('venta.html', form=form)

@app.route('/stock_actual')
def stock_actual():
    # Obtener todas las variantes con sus productos asociados
    variantes = Variante.query.options(db.joinedload(Variante.producto)).all()
    return render_template('stock_actual.html', variantes=variantes)

@app.route('/ver_ventas')
def ver_ventas():
    ventas = Venta.query.order_by(Venta.fecha_venta.desc()).all()
    return render_template('ver_ventas.html', ventas=ventas)

@app.route('/ver_venta/<int:venta_id>')
def ver_venta(venta_id):
    venta = Venta.query.options(db.joinedload(Venta.items).joinedload(VentaItem.variante).joinedload(Variante.producto)).get_or_404(venta_id)
    return render_template('ver_venta.html', venta=venta)

@app.route('/movimientos_caja', methods=['GET', 'POST'])
def movimientos_caja():
    form = MovimientoCajaForm()
    caja = Caja.query.first()
    if not caja:
        caja = Caja(saldo=0.0)
        db.session.add(caja)
        db.session.commit()

    if form.validate_on_submit():
        tipo = form.tipo.data
        monto = form.monto.data
        motivo = form.motivo.data

        if tipo == 'egreso' and caja.saldo < monto:
            flash('No hay suficiente saldo en caja para registrar este egreso.', 'danger')
        else:
            movimiento = MovimientoCaja(
                caja_id=caja.id,
                tipo=tipo,
                monto=monto,
                motivo=motivo
            )
            db.session.add(movimiento)
            if tipo == 'ingreso':
                caja.saldo += monto
            else: # tipo == 'egreso'
                caja.saldo -= monto
            db.session.commit()
            flash(f'Movimiento de {tipo} registrado exitosamente!', 'success')
            return redirect(url_for('movimientos_caja'))

    movimientos = MovimientoCaja.query.filter_by(caja_id=caja.id).order_by(MovimientoCaja.fecha.desc()).all()

    # Calcular el balance total de caja
    # Se recomienda calcularlo directamente desde la base de datos para mayor eficiencia en grandes volúmenes
    # Aquí un ejemplo simple basado en el saldo actual de la tabla Caja
    balance_total = caja.saldo

    return render_template('movimientos_caja.html', form=form, caja=caja, movimientos=movimientos, balance_total=balance_total)


# Nueva ruta para modificar un movimiento existente
@app.route('/modificar_movimiento/<int:movimiento_id>', methods=['GET', 'POST'])
def modificar_movimiento(movimiento_id):
    movimiento = MovimientoCaja.query.get_or_404(movimiento_id)
    # Crea el formulario con los datos existentes del movimiento
    form = MovimientoCajaForm(obj=movimiento) # Esto pre-llena el formulario

    if form.validate_on_submit():
        # Calcular el cambio en el saldo de caja antes de aplicar la modificación
        caja = Caja.query.first()
        if not caja: # Debería existir si ya hay movimientos
            flash('Error: No se encontró la caja principal.', 'danger')
            return redirect(url_for('movimientos_caja'))

        monto_anterior = movimiento.monto
        tipo_anterior = movimiento.tipo
        
        monto_nuevo = form.monto.data
        tipo_nuevo = form.tipo.data

        # Revertir el impacto del movimiento anterior en el saldo de caja
        if tipo_anterior == 'ingreso':
            caja.saldo -= monto_anterior
        else: # egreso
            caja.saldo += monto_anterior
        
        # Aplicar el impacto del nuevo movimiento al saldo de caja
        if tipo_nuevo == 'ingreso':
            caja.saldo += monto_nuevo
        else: # egreso
            # Verificar si hay suficiente saldo para el nuevo egreso
            if caja.saldo < monto_nuevo:
                flash('No hay suficiente saldo en caja para el nuevo egreso. Revierta el cambio o ajuste el monto.', 'danger')
                # Revertir los cambios si no hay saldo
                if tipo_anterior == 'ingreso':
                    caja.saldo += monto_anterior
                else:
                    caja.saldo -= monto_anterior
                db.session.rollback() # Deshacer cualquier cambio potencial en la sesión
                return render_template('form_modificar_movimiento.html', form=form, movimiento=movimiento)
            caja.saldo -= monto_nuevo

        # Actualizar los datos del movimiento
        movimiento.tipo = tipo_nuevo
        movimiento.motivo = form.motivo.data
        movimiento.monto = monto_nuevo
        # No actualizamos la fecha por defecto para mantener el registro original,
        # pero puedes añadirla si lo necesitas: movimiento.fecha = datetime.utcnow()

        db.session.commit()
        flash('Movimiento de caja actualizado exitosamente.', 'success')
        return redirect(url_for('movimientos_caja'))
    
    # Para la solicitud GET, simplemente renderiza el formulario pre-llenado
    return render_template('form_modificar_movimiento.html', form=form, movimiento=movimiento)


# Nueva ruta para eliminar un movimiento
@app.route('/eliminar_movimiento/<int:movimiento_id>', methods=['POST']) # Usar POST para eliminación es más seguro
def eliminar_movimiento(movimiento_id):
    movimiento = MovimientoCaja.query.get_or_404(movimiento_id)
    
    caja = Caja.query.first()
    if not caja:
        flash('Error: No se encontró la caja principal.', 'danger')
        return redirect(url_for('movimientos_caja'))

    # Revertir el impacto del movimiento en el saldo de caja antes de eliminarlo
    if movimiento.tipo == 'ingreso':
        caja.saldo -= movimiento.monto
    elif movimiento.tipo == 'egreso':
        caja.saldo += movimiento.monto # Si era un egreso, el saldo debe aumentar al eliminarlo
    
    db.session.delete(movimiento)
    db.session.commit()
    flash('Movimiento de caja eliminado exitosamente.', 'success')
    return redirect(url_for('movimientos_caja'))


# Punto de entrada de la aplicación
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not Caja.query.first():
            db.session.add(Caja(saldo=0.0))
            db.session.commit()

    app.run(debug=True)