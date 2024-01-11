from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from bd import *
from sqlalchemy.exc import IntegrityError

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255))
    first_name = Column(String(255))
    role_user = Column(String(255))

    dop_info = relationship('DopInfo', back_populates='user')
    orders = relationship('OrderProduct', back_populates='user')


class DopInfo(Base):
    __tablename__ = 'dop_info'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    email = Column(String(255))
    phone = Column(String(255))
    address = Column(String(255))

    user = relationship('User', back_populates='dop_info')

class OrderProduct(Base):
    __tablename__ = 'order_product'

    user_id = Column(Integer, ForeignKey('users.user_id'), primary_key=True)
    id_product = Column(String(255))
    data_order = Column(Date)

    user = relationship('User', back_populates='orders')

class Product(Base):
    __tablename__ = 'product'

    id_product = Column(String(255), primary_key=True)
    count = Column(Integer)
    price = Column(Float)

class AdminSerf(Base):
    __tablename__ = 'admin_serf'

    admin_id = Column(Integer, primary_key=True, autoincrement=True)
    user_name = Column(String(255))
    password = Column(String(255))