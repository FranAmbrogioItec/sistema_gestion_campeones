from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, TextAreaField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Optional, NumberRange, Length, ValidationError
from models import Usuario, Variante, Club, Categoria, Cliente, Proveedor  # AGREGADOS LOS IMPORTS FALTANTES

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired("El email es obligatorio"),
        Email("Ingrese un email válido")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired("La contraseña es obligatoria"),
        Length(min=6, message="La contraseña debe tener al menos 6 caracteres")
    ])
    remember = BooleanField('Recordarme')

class ProductoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    club_id = SelectField('Club', coerce=int, validators=[DataRequired()])
    categoria_id = SelectField('Categoría', coerce=int, validators=[DataRequired()])
    temporada = StringField('Temporada', validators=[DataRequired()])
    precio = FloatField('Precio Base', validators=[Optional()])
    descripcion = TextAreaField('Descripción', validators=[Optional()])

class VarianteForm(FlaskForm):
    talle = SelectField('Talle', choices=[
        ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'),
        ('6', '6'), ('8', '8'), ('10', '10'), ('12', '12'), ('14', '14'),('16', '16'), 
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')
    ], validators=[DataRequired()])
    color = StringField('Color', validators=[Optional()])
    sku = StringField('SKU', validators=[DataRequired()])
    precio = FloatField('Precio', validators=[DataRequired()])
    stock = IntegerField('Stock Inicial', validators=[DataRequired(), NumberRange(min=0)])
    stock_minimo = IntegerField('Stock Mínimo', validators=[Optional(), NumberRange(min=0)])
    
    def validate_sku(self, field):
        if Variante.query.filter_by(sku=field.data).first():
            raise ValidationError('Este SKU ya está en uso. Por favor elija otro.')

class VentaForm(FlaskForm):
    cliente_id = SelectField('Cliente', coerce=int, validators=[Optional()])

class MovimientoCajaForm(FlaskForm):
    tipo = SelectField('Tipo', choices=[('ingreso', 'Ingreso'), ('egreso', 'Egreso')], validators=[DataRequired()])
    monto = FloatField('Monto', validators=[DataRequired(), NumberRange(min=0.01)])
    motivo = StringField('Motivo', validators=[DataRequired()])

class ClubForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    liga = StringField('Liga', validators=[Optional()])
    
    def validate_nombre(self, field):
        if Club.query.filter_by(nombre=field.data).first():
            raise ValidationError('Este nombre de club ya existe.')

class CategoriaForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    descripcion = StringField('Descripción', validators=[Optional()])
    
    def validate_nombre(self, field):
        if Categoria.query.filter_by(nombre=field.data).first():
            raise ValidationError('Esta categoría ya existe.')

class ClienteForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    telefono = StringField('Teléfono', validators=[Optional()])
    direccion = StringField('Dirección', validators=[Optional()])
    
    def validate_email(self, field):
        if field.data and Cliente.query.filter_by(email=field.data).first():
            raise ValidationError('Este email ya está registrado.')

class ProveedorForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    contacto = StringField('Contacto', validators=[Optional()])
    telefono = StringField('Teléfono', validators=[Optional()])
    email = StringField('Email', validators=[Optional(), Email()])
    
    def validate_email(self, field):
        if field.data and Proveedor.query.filter_by(email=field.data).first():
            raise ValidationError('Este email ya está registrado.')

class UsuarioForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired(), Length(min=4, max=50)])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    nombre = StringField('Nombre completo', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    rol = SelectField('Rol', choices=[('admin', 'Administrador'), ('usuario', 'Usuario')], validators=[DataRequired()])
    
    def validate_username(self, field):
        if Usuario.query.filter_by(username=field.data).first():
            raise ValidationError('Este nombre de usuario ya está en uso.')
    
    def validate_email(self, field):
        if Usuario.query.filter_by(email=field.data).first():
            raise ValidationError('Este email ya está registrado.')