from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from dotenv import load_dotenv
from datetime import datetime
from models import *
from forms import *


app = Flask(__name__, template_folder='templates')  

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///stock_ventas.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Context processor para hacer 'datetime' disponible en todas las plantillas
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# Modelos de la base de datos
class Club(db.Model):
    __tablename__ = 'clubes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    liga = db.Column(db.String(50))
    logo = db.Column(db.String(100))
    productos = db.relationship('Producto', backref='club', lazy=True)

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    productos = db.relationship('Producto', backref='categoria_rel', lazy=True)

class Producto(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    club_id = db.Column(db.Integer, db.ForeignKey('clubes.id'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'), nullable=False)
    temporada = db.Column(db.String(10), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float)
    imagen_principal = db.Column(db.String(100))
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    variantes = db.relationship('Variante', backref='producto', lazy=True, cascade="all, delete-orphan")

class Variante(db.Model):
    __tablename__ = 'variantes'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    talle = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(30))
    sku = db.Column(db.String(50), unique=True, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    ventas = db.relationship('VentaItem', backref='variante', lazy=True)
    movimientos = db.relationship('MovimientoStock', backref='variante', lazy=True, cascade="all, delete-orphan")

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    ventas = db.relationship('Venta', backref='cliente', lazy=True)

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    total = db.Column(db.Float, nullable=False)
    tipo_venta = db.Column(db.String(20))
    estado = db.Column(db.String(20), default='completada')
    items = db.relationship('VentaItem', backref='venta', lazy=True, cascade="all, delete-orphan")
    movimiento_caja_id = db.Column(db.Integer, db.ForeignKey('movimientos_caja.id'))

class VentaItem(db.Model):
    __tablename__ = 'ventas_items'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    variante_id = db.Column(db.Integer, db.ForeignKey('variantes.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

class Caja(db.Model):
    __tablename__ = 'cajas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    saldo = db.Column(db.Float, default=0.0)
    movimientos = db.relationship('MovimientoCaja', backref='caja', lazy=True, cascade="all, delete-orphan")

class MovimientoCaja(db.Model):
    __tablename__ = 'movimientos_caja'
    id = db.Column(db.Integer, primary_key=True)
    caja_id = db.Column(db.Integer, db.ForeignKey('cajas.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False)
    motivo = db.Column(db.String(255), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    venta = db.relationship('Venta', backref='movimiento_caja', uselist=False)

class MovimientoStock(db.Model):
    __tablename__ = 'movimientos_stock'
    id = db.Column(db.Integer, primary_key=True)
    variante_id = db.Column(db.Integer, db.ForeignKey('variantes.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255))
    usuario = db.Column(db.String(50))

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    productos = db.relationship('ProductoProveedor', backref='proveedor', lazy=True)

class ProductoProveedor(db.Model):
    __tablename__ = 'productos_proveedores'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    codigo_proveedor = db.Column(db.String(50))
    precio_compra = db.Column(db.Float)

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    rol = db.Column(db.String(20), default='usuario')
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Usuario {self.username}>'

# Configuración de Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# Funciones de utilidad
def calcular_stock_disponible(variante_id):
    variante = Variante.query.get(variante_id)
    return variante.stock if variante else 0

def actualizar_stock(variante_id, cantidad, tipo, motivo, usuario="Sistema"):
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

# Inicialización de datos
def inicializar_datos():
    with app.app_context():
        db.create_all()
        
        # Crear caja principal si no existe
        if not Caja.query.first():
            caja = Caja(nombre="Caja Principal", saldo=0.0)
            db.session.add(caja)
        
        # Crear categorías básicas
        categorias_base = ['Camisetas', 'Shorts', 'Buzos', 'Conjuntos', 'Medias', 'Accesorios']
        for nombre in categorias_base:
            if not Categoria.query.filter_by(nombre=nombre).first():
                db.session.add(Categoria(nombre=nombre))
        
        # Crear usuario admin si no existe
        if not Usuario.query.filter_by(username='admin').first():
            from werkzeug.security import generate_password_hash
            admin = Usuario(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                nombre='Administrador',
                email='admin@tienda.com',
                rol='admin'
            )
            db.session.add(admin)
        
        db.session.commit()

if __name__ == '__main__':
    inicializar_datos()
    app.run(debug=True)

from routes import *