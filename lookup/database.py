from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker

session = scoped_session(sessionmaker())


def init_db(db_url):
    session.configure(bind=get_engine(db_url))


def get_engine(db_url, echo=False):
    return create_engine(db_url, pool_recycle=3600, echo=echo)


def init_app(app, echo=False):
    db_url = app.config["DB_URL"]
    session.configure(bind=get_engine(db_url, echo=echo))

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        session.remove()
