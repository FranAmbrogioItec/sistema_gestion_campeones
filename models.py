from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50))
    equipo = db.Column(db.String(50))
    temporada = db.Column(db.String(50))
    variantes = db.relationship('Variante', backref='producto', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Producto {self.nombre}>'

class Variante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    talle = db.Column(db.String(10), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    precio = db.Column(db.Float, nullable=False)  # <-- Recomendado para simplificar
    stock_inicial = db.Column(db.Integer, default=0)
    stock_actual = db.Column(db.Integer, default=0)
    ventas = db.relationship('VentaItem', backref='variante', lazy=True)
    movimientos_stock = db.relationship('MovimientoStock', backref='variante', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Variante {self.sku}>'


class Venta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    items = db.relationship('VentaItem', backref='venta', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Venta {self.id}>'

class VentaItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    variante_id = db.Column(db.Integer, db.ForeignKey('variante.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<VentaItem {self.id} (Venta: {self.venta_id})>'

class Caja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    saldo = db.Column(db.Float, default=0.0)
    # Define la relación con MovimientoCaja
    movimientos = db.relationship('MovimientoCaja', backref='caja', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Caja {self.id} (Saldo: {self.saldo})>'

class MovimientoCaja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caja_id = db.Column(db.Integer, db.ForeignKey('caja.id'), nullable=False) # <--- ¡CLAVE! Esto es lo que faltaba o estaba mal.
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False) # 'ingreso' o 'egreso'
    motivo = db.Column(db.String(255), nullable=False)
    monto = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<MovimientoCaja {self.id}: {self.tipo} - {self.monto}>"

class MovimientoStock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    variante_id = db.Column(db.Integer, db.ForeignKey('variante.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False) # 'entrada' o 'salida'
    cantidad = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255))

    def __repr__(self):
        return f"<MovimientoStock {self.id}: {self.tipo} - {self.cantidad}>"