"""
Conexión y creación de tablas.

Una sola variable manda: DATABASE_URL. En Railway apunta a Postgres; en
local, si no está definida, cae a SQLite. El mismo código corre en los dos
sitios sin flags ni ramas.
"""

from sqlmodel import create_engine, SQLModel, Session

from core.config import settings

# Railway entrega la URL como "postgres://" y SQLAlchemy sólo entiende
# "postgresql://". El replace va aquí porque es más seguro que confiar en que
# alguien recuerde editar a mano la URL que Railway generó.
_url = settings.database_url.replace("postgres://", "postgresql://", 1)

# check_same_thread sólo existe en SQLite: pasárselo a Postgres da TypeError.
_connect_args = {"check_same_thread": False} if _url.startswith("sqlite") else {}

# pool_pre_ping: Railway corta las conexiones ociosas. Sin esto, la primera
# petición tras un rato de calma falla con "server closed the connection".
engine = create_engine(_url, connect_args=_connect_args, pool_pre_ping=True)


def init_db() -> None:
    """Crea las tablas que falten. No altera ni borra las existentes."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependencia de FastAPI: abre una sesión y la cierra al terminar."""
    with Session(engine) as session:
        yield session
