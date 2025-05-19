MIN_COOKING_TIME = 1
RECIPE_IMAGE_FOLDER = 'recipes/images/'
AVATAR_IMAGE_FOLDER = 'users/images/'
NAME_STR_WIDTH = 30
MEASUREMENT_UNIT_MAX_LENGTH = 256
TAG_SLUG_MAX_LENGTH = 256
NAME_MAX_LENGTH = 150
EMAIL_MAX_LENGTH = 254
SHORT_LINK_MAX_LENGTH = 6
IS_SUBSCRIBED_FIELD_NAME = 'is_subscribed'
IS_FAVORITED_FIELD_NAME = 'is_favorited'
IS_IN_SHOPPING_CART_FIELD_NAME = 'is_in_shopping_cart'
LIST_NAME_CHOICES = (
    ('favorites', 'Избранное'),
    ('subscriptions', 'Подписки'),
    ('shopping', 'Список покупок')
)
AVATAR_FIELD_NAME = 'avatar'
IMAGE_FIELD_NAME = 'image'
SHOPPING_CART_FILENAME = "shopping_cart.txt"
DOWNLOAD_SHOPPING_CART_URL = 'download_shopping_cart'
FAVORITE_URL = 'favorite'
SHOPPING_CART_URL = 'shopping_cart'
GET_LINK_URL = 'get-link'
SELF_URL = 'me'
AVATAR_URL = f'{SELF_URL}/avatar'
SUBSCRIPTIONS_URL = 'subscriptions'
SUBSCRIBE_URL = 'subscribe'
SET_PASSWORD_URL = 'set_password'
