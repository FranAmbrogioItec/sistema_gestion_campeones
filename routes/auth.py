from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, LoginManager
from werkzeug.security import check_password_hash
from models import db, Usuario, Producto, Venta, Cliente, Variante
from forms import LoginForm

bp = Blueprint('auth', __name__)

# Configuración del user_loader
@bp.record_once
def setup_login(state):
    login_manager = LoginManager()
    login_manager.init_app(state.app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

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
        usuario = Usuario.query.filter_by(email=form.email.data).first()
        
        if usuario and usuario.check_password(form.password.data):
            login_user(usuario, remember=form.remember.data)
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('auth.dashboard'))
        
        flash('Email o contraseña incorrectos', 'danger')
    
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