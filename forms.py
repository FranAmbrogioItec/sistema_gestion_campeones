from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, FloatField
from wtforms.validators import DataRequired, NumberRange, Length, ValidationError
from models import Variante 

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre del Producto', validators=[DataRequired(), Length(max=100)])
    categoria = StringField('Categoría', validators=[DataRequired(), Length(max=50)])
    equipo = StringField('Equipo', validators=[DataRequired(), Length(max=100)])
    temporada = StringField('Temporada (Ej: 2024, 2023/2024)', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Cargar Producto')

class VarianteForm(FlaskForm):
    talle = StringField('Talle', validators=[DataRequired(), Length(max=10)])
    sku = StringField('SKU (Identificador Único)', validators=[DataRequired(), Length(max=50)])
    precio = FloatField('Precio', validators=[DataRequired(), NumberRange(min=0.01, message="El precio debe ser mayor que 0.")])
    stock = IntegerField('Stock Inicial', validators=[DataRequired(), NumberRange(min=0, message="El stock no puede ser negativo.")])
    submit = SubmitField('Cargar Variante')

    def validate_sku(self, sku):
        existing_sku = Variante.query.filter_by(sku=sku.data).first()
        if existing_sku:
            raise ValidationError('Este SKU ya existe. Por favor, usa uno diferente.')

class VentaForm(FlaskForm):
    sku = StringField('SKU del Producto', validators=[DataRequired(), Length(max=50)])
    cantidad = IntegerField('Cantidad', validators=[DataRequired(), NumberRange(min=1, message="La cantidad debe ser al menos 1.")])
    precio_unitario = FloatField('Precio Unitario', validators=[DataRequired(), NumberRange(min=0.01, message="El precio debe ser mayor que 0.")])
    submit = SubmitField('Registrar Venta')

class MovimientoCajaForm(FlaskForm):
    tipo = SelectField('Tipo de Movimiento', choices=[('ingreso', 'Ingreso'), ('egreso', 'Egreso')], validators=[DataRequired()])
    monto = FloatField('Monto', validators=[DataRequired(), NumberRange(min=0.01, message="El monto debe ser mayor que 0.")])
    motivo = StringField('Motivo', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Registrar Movimiento')