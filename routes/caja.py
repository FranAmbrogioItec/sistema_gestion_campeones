from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Caja, MovimientoCaja, Venta
from forms import MovimientoCajaForm

bp = Blueprint('caja', __name__, url_prefix='/caja')

@bp.route('/')
@login_required
def gestion():
    caja = Caja.query.first()
    if not caja:
        caja = Caja(nombre="Caja Principal", saldo=0)
        db.session.add(caja)
        db.session.commit()
    
    movimientos = MovimientoCaja.query.filter_by(caja_id=caja.id)\
        .order_by(MovimientoCaja.fecha.desc())\
        .limit(10)\
        .all()
    
    return render_template('caja/gestion.html', caja=caja, movimientos=movimientos)

@bp.route('/movimientos/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_movimiento():
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
        
        if form.tipo.data == 'ingreso':
            caja.saldo += form.monto.data
        else:
            caja.saldo -= form.monto.data
        
        db.session.commit()
        flash('Movimiento registrado exitosamente!', 'success')
        return redirect(url_for('caja.gestion'))
    
    return render_template('caja/nuevo_movimiento.html', form=form)

@bp.route('/movimientos')
@login_required
def listar_movimientos():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    tipo = request.args.get('tipo')
    
    caja = Caja.query.first()
    if not caja:
        return redirect(url_for('caja.gestion'))
    
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