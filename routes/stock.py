from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Variante, Producto, Categoria, Club, MovimientoStock
from forms import VarianteForm

bp = Blueprint('stock', __name__, url_prefix='/stock')

@bp.route('/')
@login_required
def gestion():
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

@bp.route('/ajustar/<int:variante_id>', methods=['GET', 'POST'])
@login_required
def ajustar(variante_id):
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
                return redirect(url_for('stock.ajustar', variante_id=variante_id))
            
            if cantidad <= 0:
                flash('La cantidad debe ser mayor a cero', 'danger')
                return redirect(url_for('stock.ajustar', variante_id=variante_id))
            
            if tipo == 'salida' and variante.stock < cantidad:
                flash('No hay suficiente stock para este ajuste', 'danger')
                return redirect(url_for('stock.ajustar', variante_id=variante_id))
            
            movimiento = MovimientoStock(
                variante_id=variante.id,
                tipo=tipo,
                cantidad=cantidad,
                motivo=motivo,
                usuario=current_user.username
            )
            db.session.add(movimiento)
            
            if tipo == 'entrada':
                variante.stock += cantidad
            else:
                variante.stock -= cantidad
            
            db.session.commit()
            flash(f'Stock ajustado exitosamente ({tipo} de {cantidad} unidades)', 'success')
            return redirect(url_for('stock.gestion'))
        
        except ValueError:
            flash('Cantidad inválida', 'danger')
            return redirect(url_for('stock.ajustar', variante_id=variante_id))
    
    return render_template('stock/ajustar.html', variante=variante)

@bp.route('/movimientos')
@login_required
def movimientos():
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