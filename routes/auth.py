from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, LoginManager
from werkzeug.security import check_password_hash
from models import db, Usuario, Producto, Venta, Cliente, Variante
from forms import LoginForm

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email_input = form.email.data
        password_input = form.password.data
        
        # DEBUG: Imprimir lo que se está buscando
        print(f"DEBUG - Buscando usuario con email: '{email_input}'")
        print(f"DEBUG - Password ingresado: '{password_input}'")
        
        # Buscar usuario por email O username
        usuario = Usuario.query.filter(
            (Usuario.email == email_input) | (Usuario.username == email_input)
        ).first()
        
        # DEBUG: Verificar si se encontró el usuario
        if usuario:
            print(f"DEBUG - Usuario encontrado: {usuario.username}, Email: {usuario.email}")
            print(f"DEBUG - Password hash en BD: {usuario.password_hash}")
            
            # Verificar contraseña
            password_ok = usuario.check_password(password_input)
            print(f"DEBUG - Password válido: {password_ok}")
            
            if password_ok:
                login_user(usuario, remember=form.remember.data)
                flash('Inicio de sesión exitoso', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('auth.dashboard'))
            else:
                flash('Contraseña incorrecta', 'danger')
        else:
            print("DEBUG - Usuario no encontrado")
            # Mostrar todos los usuarios para verificar
            todos_usuarios = Usuario.query.all()
            print("DEBUG - Usuarios en la base de datos:")
            for u in todos_usuarios:
                print(f"  - Username: '{u.username}', Email: '{u.email}'")
            flash('Usuario no encontrado', 'danger')
    
    return render_template('auth/login.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
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