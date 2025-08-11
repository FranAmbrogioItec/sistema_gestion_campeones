from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Club, Categoria, Cliente, Proveedor, Usuario
from forms import ClubForm, CategoriaForm, ClienteForm, ProveedorForm, UsuarioForm

bp = Blueprint('configuracion', __name__, url_prefix='/configuracion')

@bp.route('/clubes', methods=['GET', 'POST'])
@login_required
def clubes():
    form = ClubForm()
    
    if form.validate_on_submit():
        club = Club(
            nombre=form.nombre.data,
            liga=form.liga.data
        )
        db.session.add(club)
        db.session.commit()
        flash('Club agregado exitosamente!', 'success')
        return redirect(url_for('configuracion.clubes'))
    
    clubes = Club.query.order_by(Club.nombre).all()
    return render_template('configuracion/clubes.html', form=form, clubes=clubes)

@bp.route('/categorias', methods=['GET', 'POST'])
@login_required
def categorias():
    form = CategoriaForm()
    
    if form.validate_on_submit():
        categoria = Categoria(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data
        )
        db.session.add(categoria)
        db.session.commit()
        flash('Categoría agregada exitosamente!', 'success')
        return redirect(url_for('configuracion.categorias'))
    
    categorias = Categoria.query.order_by(Categoria.nombre).all()
    return render_template('configuracion/categorias.html', form=form, categorias=categorias)

@bp.route('/clientes', methods=['GET', 'POST'])
@login_required
def clientes():
    form = ClienteForm()
    
    if form.validate_on_submit():
        cliente = Cliente(
            nombre=form.nombre.data,
            email=form.email.data,
            telefono=form.telefono.data,
            direccion=form.direccion.data
        )
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente agregado exitosamente!', 'success')
        return redirect(url_for('configuracion.clientes'))
    
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template('configuracion/clientes.html', form=form, clientes=clientes)

@bp.route('/proveedores', methods=['GET', 'POST'])
@login_required
def proveedores():
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
        return redirect(url_for('configuracion.proveedores'))
    
    proveedores = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template('configuracion/proveedores.html', form=form, proveedores=proveedores)

@bp.route('/usuarios', methods=['GET', 'POST'])
@login_required
def usuarios():
    if current_user.rol != 'admin':
        flash('No tienes permiso para acceder a esta sección', 'danger')
        return redirect(url_for('dashboard'))
    
    form = UsuarioForm()
    
    if form.validate_on_submit():
        usuario = Usuario(
            username=form.username.data,
            nombre=form.nombre.data,
            email=form.email.data,
            rol=form.rol.data
        )
        usuario.set_password(form.password.data)
        db.session.add(usuario)
        db.session.commit()
        flash('Usuario creado exitosamente!', 'success')
        return redirect(url_for('configuracion.usuarios'))
    
    usuarios = Usuario.query.order_by(Usuario.nombre).all()
    return render_template('configuracion/usuarios.html', form=form, usuarios=usuarios)