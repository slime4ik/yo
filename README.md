Клонируйте репозиторий
# Создайте и активируйте виртуальное окружение (опционально)
python -m venv venv / 
source venv/bin/activate  # Linux/MacOS / 
venv\Scripts\activate    # Windows
# Установите зависимости
pip install -r requirements.txt
# Создание и применение миграций
python manage.py makemigrations /
python manage.py migrate
# Создание суперпользоваеля
python manage.py createsuperuser
# Запуск сервера
python manage.py runserver
Авторизация и создание пользователей в localhost:8000/admin/ входим по логину и паролю суперюзера которого создали / 
Главная страница сайта - localhost:8000
# Запуск тестов
Используем в settings.py in-memory базу для тестов которая закоментирована / 
python manage.py test / pytest --cov= 
