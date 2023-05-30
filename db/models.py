import sqlalchemy
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from enum import Enum

Base = declarative_base()


class Users(Base):
    """Дочерний класс от declarative_base. Хранит сведения о пользователе VK"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    id_vk = Column(Integer, nullable=False)


class StatusType(Enum):
    """
    Creating a new data type to add variants in blacklist or whitelist.
    Создаем новый тип данных для добавления варантов в черный или белый список.
    """
    INERT = 1
    LIKE = 2
    DISLIKE = 3


class Variants(Base):
    """Дочерний класс от declarative_base. Хранит сведения о варианте найденом на платформе VK"""
    __tablename__ = 'variants'

    id = Column(Integer, primary_key=True)
    id_vk = Column(Integer, nullable=False)


class UsersVariants(Base):
    """
    Дочерний класс от declarative_base. Хранит сведения о Users и Variants
    Необходим для создание связи "многие-ко-многим"
    """
    __tablename__ = 'users_variants'

    id = Column(Integer, primary_key=True)
    id_user = Column(Integer, ForeignKey('users.id'), nullable=False)
    id_variant = Column(Integer, ForeignKey('variants.id'), nullable=False)
    status = Column(sqlalchemy.Enum(StatusType), nullable=False, default=StatusType.INERT.value)

    user = relationship('Users', backref='users_variants')
    variant = relationship('Variants', backref='users_variants')


def create_tables(engine):
    """Функция для создания моделей в БД"""
    Base.metadata.create_all(engine)
