from flask import Blueprint, request, jsonify
from flask_login import login_required
from sqlalchemy import or_
from models import db, Producto, Variante, Club

bp = Blueprint('api', __name__)

@bp.route('/buscar_productos')
@login_required
def buscar_productos():
    termino = request.args.get('q', '')
    
    if not termino:
        return jsonify([])
    
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

@bp.route('/stock/<sku>')
@login_required
def stock(sku):
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