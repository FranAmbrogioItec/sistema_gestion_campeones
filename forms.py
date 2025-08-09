from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Optional, NumberRange

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    club_id = SelectField('Club', coerce=int, validators=[DataRequired()])
    categoria_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    temporada = StringField('Temporada', validators=[DataRequired()])
    precio = FloatField('Precio Base', validators=[Optional()])
    descripcion = TextAreaField('Descripción', validators=[Optional()])

class VarianteForm(FlaskForm):
    talle = SelectField('Talle', choices=[
        ('XS', 'XS'), ('S', 'S'), ('M', 'M'), 
        ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'),
        ('28', '28'), ('30', '30'), ('32', '32'), ('34', '34'), ('36', '36'),
        ('38', '38'), ('40', '40'), ('42', '42'), ('44', '44'), ('46', '46')
    ], validators=[DataRequired()])
    color = StringField('Color', validators=[Optional()])
    sku = StringField('SKU', validators=[DataRequired()])
    precio = FloatField('Precio', validators=[DataRequired()])
    stock = IntegerField('Stock Inicial', validators=[DataRequired(), NumberRange(min=0)])
    stock_minimo = IntegerField('Stock Mínimo', validators=[Optional(), NumberRange(min=0)])

class VentaForm(FlaskForm):
    cliente_id = SelectField('Cliente', coerce=int, validators=[Optional()])

class MovimientoCajaForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('ingreso', 'Ingreso'), ('egreso', 'Egreso')], validators=[DataRequired()])
    monto = FloatField('Monto', validators=[DataRequired(), NumberRange(min=0.01)])
    motivo = StringField('Motivo', validators=[DataRequired()])

class ClubForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    liga = StringField('Liga', validators=[Optional()])

class CategoriaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = StringField('Descripción', validators=[Optional()])

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    telefono = StringField('Teléfono', validators=[Optional()])
    direccion = StringField('Dirección', validators=[Optional()])

class ProveedorForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    contacto = StringField('Contacto', validators=[Optional()])
    telefono = StringField('Teléfono', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])