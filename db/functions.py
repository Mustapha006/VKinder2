import sqlalchemy as sq
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from sqlalchemy_utils import database_exists, create_database
from db.models import Users, Variants, UsersVariants, create_tables

load_dotenv()

# загружаем данные из переменной окружения .env
USER = os.getenv('USER_')
PASSWORD = os.getenv('PASSWORD')
HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

name_db = 'vk_tinder'
DSN = f'postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{name_db}'


class DbVkSearch:
    """ Класс для взаимодействия с базой данных vk_tinder с помощью библиотеки SQLalchemy """

    def __init__(self):
        """ При создании экземпляра класса, создается БД, таблицы в ней и открывается сессия для работы с ней. """

        engine = sq.create_engine(DSN)

        if not database_exists(engine.url):
            create_database(engine)
            create_tables(engine.url)

        Session = sessionmaker(bind=engine)
        self.session = Session()

    def add_new_user(self, id_vk: str or int) -> bool:
        """ Метод класса позволяет добавить данные о новом пользователе в таблицу Users """

        new_user = Users(id_vk=id_vk)
        self.session.add(new_user)
        self.session.commit()

        return True

    def user_in_db(self, id_vk: str) -> bool:
        """ Метод класса позволяет проверить существует ли данные об этом пользователе VK, по его ID """

        q = self.session.query(Users).filter(Users.id_vk == id_vk).first()
        return q is not None

    def get_id_user(self, id_vk: str) -> int:
        """ Метод класса позволяет получить Users.id по ID VK пользователя """

        q = self.session.query(Users.id).filter(Users.id_vk == id_vk).first()
        return q.id if q is not None else None

    def get_age_user(self, id_vk: str) -> str:
        """ Метод класса позволяет получить Users.age по ID VK пользователя """

        q = self.session.query(Users).filter(Users.id_vk == id_vk).first()
        return q.age if q is not None else None

    def add_new_variants(self, user_id_vk: str, status="INERT", **kwargs) -> bool:
        """ Метод класса позволяет добавить данные о новом варианте в таблицу Variants """

        user_id = self.get_id_user(user_id_vk)
        new_variants = Variants(id_vk=kwargs['id_vk'],
                                )
        self.session.add(new_variants)
        q = self.session.query(Variants).filter(Variants.id_vk == kwargs['id_vk'])
        id = None
        for row in q:
            id = row.id
            break
        new_users_variants = UsersVariants(id_user=user_id, id_variant=id, status=status)
        self.session.add(new_users_variants)
        self.session.commit()

        return True

    def new_status_for_variants(self, user_id_vk: str, variants_id: str, status: str) -> None:
        """ Метод класса позволяющий обновить статус варианта в таблице UsersVariants """

        query_id_user = self.session.query(Users.id).where(Users.id_vk == user_id_vk).one()

        query = self.session.query(UsersVariants)
        query = query.filter(UsersVariants.id_user == query_id_user[0]). \
            filter(UsersVariants.id_variant == variants_id). \
            update({'status': status})
        self.session.commit()

    def count_new_variant(self, user_id_vk: str) -> int:
        """ Метод класса для нахождения новоой записи в таблице UsersVariants """

        query_max = self.session.query(func.max(UsersVariants.id_variant)).join(Users)
        query_max = query_max.where(Users.id_vk == user_id_vk).one()

        return query_max[0]

    def get_all_variants_for_user(self, id_vk: str, status: str) -> list:
        """ Метод для нахождения вариантов со статусом `status` в UsersVariants для опеределенного пользователя """

        list_variants = []
        q = self.session.query(Variants).join(UsersVariants).join(Users).filter(Users.id_vk == id_vk). \
            where(UsersVariants.status == status)
        for res in q:
            for var in res.users_variants:
                variant_info = f"https://vk.com/id{var.variant.id_vk} "
                list_variants.append(variant_info)

        return list_variants

    def variant_in_db_for_user(self, id_vk: str, id_vk_variant: str) -> bool:
        """ Метод для нахождения указанного варината для конкретного пользователя. """

        q = self.session.query(UsersVariants).join(UsersVariants.user).join(UsersVariants.variant).filter(
            Users.id_vk == id_vk, Variants.id_vk == id_vk_variant).first()

        return q is not None

    def close(self) -> None:
        """ Метод для закрытия текущей сессии """

        self.session.close()
