from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Producto, Variante, Club, Categoria, MovimientoStock
from forms import ProductoForm, VarianteForm

bp = Blueprint('productos', __name__, url_prefix='/productos')

@bp.route('/')
@login_required
def listar():
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

@bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def crear():
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
        return redirect(url_for('productos.agregar_variantes', producto_id=producto.id))
    
    return render_template('productos/crear.html', form=form)

@bp.route('/<int:producto_id>/variantes', methods=['GET', 'POST'])
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
        
        movimiento = MovimientoStock(
            variante_id=variante.id,
            tipo='entrada',
            cantidad=form.stock.data,
            motivo='Carga inicial de stock',
            usuario=current_user.username
        )
        db.session.add(movimiento)
        
        db.session.commit()
        flash('Variante agregada exitosamente!', 'success')
        return redirect(url_for('productos.agregar_variantes', producto_id=producto.id))
    
    variantes = Variante.query.filter_by(producto_id=producto.id).all()
    return render_template('productos/variantes.html', 
                        producto=producto, 
                        form=form, 
                        variantes=variantes)

@bp.route('/variantes/<int:variante_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_variante(variante_id):
    variante = Variante.query.get_or_404(variante_id)
    form = VarianteForm(obj=variante)
    
    if form.validate_on_submit():
        diferencia = form.stock.data - variante.stock
        
        variante.talle = form.talle.data
        variante.color = form.color.data
        variante.sku = form.sku.data
        variante.precio = form.precio.data
        variante.stock_minimo = form.stock_minimo.data
        
        if diferencia != 0:
            tipo = 'entrada' if diferencia > 0 else 'salida'
            movimiento = MovimientoStock(
                variante_id=variante.id,
                tipo=tipo,
                cantidad=abs(diferencia),
                motivo='Ajuste manual de stock',
                usuario=current_user.username
            )
            db.session.add(movimiento)
        
        db.session.commit()
        flash('Variante actualizada exitosamente!', 'success')
        return redirect(url_for('productos.agregar_variantes', producto_id=variante.producto_id))
    
    return render_template('productos/editar_variante.html', form=form, variante=variante)