from models import *


# Ваш текущий класс UserManager, дополните его следующим методом
class UserManager:
    def __init__(self, session):
        self.session = session

    def register_user(self, user_id, username, first_name, role_user):
        try:
            # Создаем нового пользователя с предоставленными данными
            new_user = User(user_id=user_id, username=username, first_name=first_name, role_user=role_user)
            # Добавляем пользователя в сессию
            self.session.add(new_user)
            # Коммитим изменения в базу данных
            self.session.commit()
        except IntegrityError as e:
            # Если произошло нарушение уникального ограничения, просто пропускаем и не выдаем ошибку
            self.session.rollback()

    def check_admin_role(self, user_id):
        # Получаем пользователя по user_id
        user = self.session.query(User).filter_by(user_id=user_id).first()
        # Проверяем, является ли роль пользователя администратором
        if user and user.role_user == 'admin':
            return True
        else:
            return False

class ProductManager:
    def __init__(self, session):
        self.session = session
    
    def get_list(self):
        # Получаем информацию о видах кофе из базы данных
        products = self.session.query(Product).all()
        return products
        
    def get_price(self, id_product):
            # Получаем цену товара из базы данных по его id_product
            product = self.session.query(Product).filter_by(id_product=id_product).first()

            # Если товар существует, возвращаем его цену, иначе возвращаем None
            if product:
                return product.price
            else:
                return None
    
    def update_product_count(self, id_product, new_count):
        # Обновляем количество продукта в базе данных по его id_product
        product = self.session.query(Product).filter_by(id_product=id_product).first()

        # Если товар существует, обновляем его количество, иначе ничего не делаем
        if product:
            product.count = new_count
            self.session.commit()