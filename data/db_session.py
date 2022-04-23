import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()  # "база"

__factory = None  # фабрика создания сессий работы с БД


def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception('Необходимо указать файл базы данных.')

    conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
    print(f'Подключение к базе данных по адресу {conn_str}')

    engine = sa.create_engine(conn_str, echo=False)  # задает подход к работе с БД по ее типу (sqlite, postgresql)
    __factory = orm.sessionmaker(bind=engine)  # задает фабрику подключений к БД

    from . import __all_models

    SqlAlchemyBase.metadata.create_all(engine)  # init database


def create_session() -> Session:
    global __factory
    return __factory()  # получаем объект типа Session - средство для взаимодействия с БД
