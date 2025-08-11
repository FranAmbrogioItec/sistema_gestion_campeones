from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db, Venta, VentaItem, Variante, Cliente, MovimientoStock, Caja, MovimientoCaja, Producto
from forms import VentaForm

bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    form = VentaForm()
    form.cliente_id.choices = [(0, 'Cliente ocasional')] + [(c.id, c.nombre) for c in Cliente.query.order_by(Cliente.nombre)]
    
    if request.method == 'POST':
        items = request.form.getlist('items[]')
        
        if not items:
            flash('Debe agregar al menos un producto a la venta', 'danger')
            return render_template('ventas/nueva.html', form=form)
        
        venta = Venta(
            cliente_id=form.cliente_id.data if form.cliente_id.data != 0 else None,
            tipo_venta='fisica',
            total=0
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
                
                if variante.stock < cantidad:
                    flash(f'Stock insuficiente para {variante.producto.nombre} - Talle: {variante.talle}', 'warning')
                    continue
                
                venta_item = VentaItem(
                    venta_id=venta.id,
                    variante_id=variante.id,
                    cantidad=cantidad,
                    precio_unitario=variante.precio,
                    subtotal=variante.precio * cantidad
                )
                db.session.add(venta_item)
                
                movimiento = MovimientoStock(
                    variante_id=variante.id,
                    tipo='salida',
                    cantidad=cantidad,
                    motivo=f'Venta #{venta.id}',
                    usuario=current_user.username
                )
                db.session.add(movimiento)
                
                total_venta += venta_item.subtotal
                items_validos += 1
                
            except ValueError:
                continue
        
        if items_validos == 0:
            db.session.rollback()
            flash('No se pudo procesar la venta. Verifique los productos seleccionados.', 'danger')
            return render_template('ventas/nueva.html', form=form)
        
        venta.total = total_venta
        
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
        return redirect(url_for('ventas.detalle', venta_id=venta.id))
    
    productos = Producto.query.options(
        db.joinedload(Producto.variantes)
    ).order_by(Producto.nombre).all()
    
    return render_template('ventas/nueva.html', form=form, productos=productos)

@bp.route('/<int:venta_id>')
@login_required
def detalle(venta_id):
    venta = Venta.query.options(
        db.joinedload(Venta.items).joinedload(VentaItem.variante).joinedload(Variante.producto),
        db.joinedload(Venta.cliente)
    ).get_or_404(venta_id)
    
    return render_template('ventas/detalle.html', venta=venta)

@bp.route('/')
@login_required
def listar():
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