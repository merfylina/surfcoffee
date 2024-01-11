from sqlalchemy import create_engine 
from sqlalchemy.ext.declarative import declarative_base 
from sqlalchemy.orm import sessionmaker 
from sqlalchemy.exc import SQLAlchemyError  # Импортируем исключение SQLAlchemyError для обработки ошибок
import sqlalchemy  # Новый импорт

#Параметры вашей базы данных
db_params = { 
    'dbname': 'surfcoffe', 
    'user': 'postgres', 
    'password': '1111', 
    'host': '127.0.0.1', 
    'port': '5432' 
} 

Base = declarative_base() 

engine = create_engine(
    f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}",
    connect_args={'options': '-c client_encoding=utf8'}
)

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
conn = Session()

# Этот код предназначен для создания соединения с базой данных PostgreSQL 
# с использованием библиотеки SQLAlchemy в Python