from app import db
from models import *

def calcular_stock_disponible(variante_id):
    """Calcula el stock disponible restando el reservado"""
    variante = Variante.query.get(variante_id)
    if not variante:
        return 0
    return variante.stock

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

# Otras funciones útiles pueden ir aquí