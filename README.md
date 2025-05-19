# Foodgram API

[![CI](https://github.com/KozlovL/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/KozlovL/foodgram/actions)

## Описание

**Foodgram** — это API-сервис для публикации рецептов.  
Позволяет создавать рецепты и создавать список покупок.

Проект доступен по адресу:  
**https://foodgramhostname.zapto.org**

---

## Установка и запуск проекта

1. **Клонируйте репозиторий:**
```bash
git clone git@github.com:KozlovL/foodgram.git
cd foodgram
```
Для SSH потребуется добавить свой публичный ключ в настройки GitHub:
https://github.com/settings/ssh/new
2. **Создайте .env файл в корне:**
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
docker compose up --build
```

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