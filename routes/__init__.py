from .auth import bp as auth_bp
from .productos import bp as productos_bp
from .ventas import bp as ventas_bp
from .stock import bp as stock_bp
from .caja import bp as caja_bp
from .configuracion import bp as configuracion_bp
from .api import bp as api_bp

__all__ = ['auth_bp', 'productos_bp', 'ventas_bp', 'stock_bp', 'caja_bp', 'configuracion_bp', 'api_bp']