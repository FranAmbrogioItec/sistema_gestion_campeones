from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Club(db.Model):
    __tablename__ = 'clubes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    liga = db.Column(db.String(50))
    logo = db.Column(db.String(100))
    productos = db.relationship('Producto', back_populates='club', cascade='all, delete-orphan')

class Categoria(db.Model):
    __tablename__ = 'categorias'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.String(200))
    productos = db.relationship('Producto', back_populates='categoria', cascade='all, delete-orphan')

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
    
    # Relaciones
    club = db.relationship('Club', back_populates='productos')
    categoria = db.relationship('Categoria', back_populates='productos')
    variantes = db.relationship('Variante', back_populates='producto', cascade='all, delete-orphan')

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
    
    # Relaciones
    producto = db.relationship('Producto', back_populates='variantes')
    ventas = db.relationship('VentaItem', back_populates='variante', cascade='all, delete-orphan')
    movimientos = db.relationship('MovimientoStock', back_populates='variante', cascade='all, delete-orphan')

class Cliente(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.Text)
    ventas = db.relationship('Venta', back_populates='cliente', cascade='all, delete-orphan')

class Venta(db.Model):
    __tablename__ = 'ventas'
    id = db.Column(db.Integer, primary_key=True)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    total = db.Column(db.Float, nullable=False)
    tipo_venta = db.Column(db.String(20))
    estado = db.Column(db.String(20), default='completada')
    
    # Relaciones
    cliente = db.relationship('Cliente', back_populates='ventas')
    items = db.relationship('VentaItem', back_populates='venta', cascade='all, delete-orphan')
    movimiento_caja = db.relationship('MovimientoCaja', back_populates='venta', uselist=False)

class VentaItem(db.Model):
    __tablename__ = 'ventas_items'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('ventas.id'), nullable=False)
    variante_id = db.Column(db.Integer, db.ForeignKey('variantes.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    
    # Relaciones
    venta = db.relationship('Venta', back_populates='items')
    variante = db.relationship('Variante', back_populates='ventas')

class Caja(db.Model):
    __tablename__ = 'cajas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    saldo = db.Column(db.Float, default=0.0)
    movimientos = db.relationship('MovimientoCaja', back_populates='caja', cascade='all, delete-orphan')

class MovimientoCaja(db.Model):
    __tablename__ = 'movimientos_caja'
    id = db.Column(db.Integer, primary_key=True)
    caja_id = db.Column(db.Integer, db.ForeignKey('cajas.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False)
    motivo = db.Column(db.String(255), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    
    # Relaciones
    caja = db.relationship('Caja', back_populates='movimientos')
    venta = db.relationship('Venta', back_populates='movimiento_caja', uselist=False)

class MovimientoStock(db.Model):
    __tablename__ = 'movimientos_stock'
    id = db.Column(db.Integer, primary_key=True)
    variante_id = db.Column(db.Integer, db.ForeignKey('variantes.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255))
    usuario = db.Column(db.String(50))
    
    # Relaciones
    variante = db.relationship('Variante', back_populates='movimientos')

class Proveedor(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    contacto = db.Column(db.String(100))
    telefono = db.Column(db.String(20))
    email = db.Column(db.String(100))
    productos = db.relationship('ProductoProveedor', back_populates='proveedor', cascade='all, delete-orphan')

class ProductoProveedor(db.Model):
    __tablename__ = 'productos_proveedores'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    codigo_proveedor = db.Column(db.String(50))
    precio_compra = db.Column(db.Float)
    
    # Relaciones
    proveedor = db.relationship('Proveedor', back_populates='productos')
    producto = db.relationship('Producto')

class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    rol = db.Column(db.String(20), default='usuario')
    activo = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Usuario {self.username}>'