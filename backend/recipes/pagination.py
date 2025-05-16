from rest_framework.pagination import PageNumberPagination


class PageLimitPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'
