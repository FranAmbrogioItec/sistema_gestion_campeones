from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__, template_folder='templates')
    
    # Configuración básica
    app.config.from_mapping(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///stock_ventas.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        FLASK_ENV=os.getenv('FLASK_ENV', 'development')
    )
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Registrar blueprints (importación correcta para la opción A)
    from routes.auth import bp as auth_bp
    from routes.productos import bp as productos_bp
    from routes.ventas import bp as ventas_bp
    from routes.stock import bp as stock_bp
    from routes.caja import bp as caja_bp
    from routes.configuracion import bp as configuracion_bp
    from routes.api import bp as api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(caja_bp)
    app.register_blueprint(configuracion_bp)
    app.register_blueprint(api_bp)
    
    # Context processors
    @app.context_processor
    def inject_datetime():
        return {'datetime': datetime}
    
    # Comandos CLI (mantener igual)
    @app.cli.command('init-db')
    def init_db():
        """Inicializar la base de datos con datos básicos"""
        from models import Caja, Categoria, Usuario
        from werkzeug.security import generate_password_hash
        
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
        
        # Crear usuario admin
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                nombre='Administrador',
                email='admin@tienda.com',
                rol='admin'
            )
            db.session.add(admin)
        
        db.session.commit()
        print("Base de datos inicializada con éxito.")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)