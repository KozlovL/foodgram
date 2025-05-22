# Foodgram API

[![CI](https://github.com/KozlovL/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/KozlovL/foodgram/actions)

## Описание

**Foodgram** — это API-сервис для публикации рецептов с возможностью:
- Создания и редактирования рецептов
- Подписки на авторов
- Формирования списка покупок
- Фильтрации по тегам и ингредиентам

Проект доступен по адресу:  
**https://foodgramhostname.zapto.org**


## Автор
👨‍💻 **Козлов Леонид**  
📧 [GitHub](https://github.com/KozlovL) 


## Технологический стек
### Backend
- Python 3.9
- Django 4.2
- Django REST Framework
- Djoser (аутентификация)
- PostgreSQL
- Gunicorn
- Nginx

### Frontend
- React
- Bootstrap

### Инфраструктура
- Docker
- Docker Compose
- GitHub Actions (CI/CD)

## CI/CD
Проект автоматически разворачивается на сервер при пуше в ветку main с помощью GitHub Actions. Используется следующий workflow:

main.yml — собирает образы, прогоняет тесты, деплой на сервер через SSH + Docker

## Локальное развертывание с Docker

1. **Клонируйте репозиторий:**
```bash
git clone git@github.com:KozlovL/foodgram.git
cd foodgram
```
Для SSH потребуется добавить свой публичный ключ в настройки GitHub:

https://github.com/settings/ssh/new

2. **Создайте .env файл на основе шаблона:**
```bash
cp .env.example .env
```

```bash
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_pass
DB_HOST=foodgram_db
DB_PORT=5432
SECRET_KEY=ваш-secret-key
```

3. **Запустите проект в Docker-контейнерах**
```bash
docker compose up --build -d
```

4. **Подготовка базы данных**
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py loaddata /app/data/ingredients_fixture.json
```

5. **Сборка статики**
```bash
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```

6. **Запуск проекта**

Проект доступен по адресу:  
**http://localhost:7000**

## Локальное развертывание без Docker

1. **Клонируйте репозиторий:**
```bash
git clone git@github.com:KozlovL/foodgram.git
cd foodgram
```

Для SSH потребуется добавить свой публичный ключ в настройки GitHub:

https://github.com/settings/ssh/new

2. **Настройка виртуального окружения**
```bash
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Создайте .env файл на основе шаблона:**
```bash
cp .env.example .env
```

```bash
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_pass
DB_HOST=foodgram_db
DB_PORT=5432
SECRET_KEY=ваш-secret-key
```

4. **Подготовка базы данных**
```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py loaddata data/ingredients_fixture.json
```

5. **Запуск сервера**
```bash
python manage.py runserver
```

Проект доступен по адресу:  
**http://127.0.0.1:8000/**


## Документация
```bash
cd infra
docker compose up
```

Документация будет доступна по адресу:
**http://localhost/api/docs/**

## Примеры API-запросов

1. **Аутентификация**
```bash
POST /api/auth/token/login
Content-Type: application/json

{
  "email": "ваш_email",
  "password": "ваш_пароль"
}
```

2. **Получение списка записей**
```bash
GET /api/recipes
```

3. **Создание записи**
```bash
POST /api/recipes
Authorization: Token <ваш_токен>
Content-Type: application/json
{
  "ingredients": [
    {
      "id": id,
      "amount": количество
    }
  ],
  "tags": [
    id,
    id
  ],
  "image": "картинка в формате base64",
  "name": "навзвание",
  "text": "описание",
  "cooking_time": время приготовления
}
```

4. **Редактирование записи**
```bash
PATCH /api/recipes/<id>
Authorization: Token <ваш_токен>
Content-Type: application/json
{
  "ingredients": [
    {
      "id": id,
      "amount": количество
    }
  ],
  "tags": [
    id,
    id
  ],
  "image": "картинка в формате base64",
  "name": "навзвание",
  "text": "описание",
  "cooking_time": время приготовления
}
```

5. **Удаление записи**
```bash
DELETE /api/recipes/<id>
Authorization: Token <ваш_токен>
```