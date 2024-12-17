import re
from http import HTTPStatus
from urllib.parse import urlencode

from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from product.models import Product, Subcategory, Category
from django.views.generic import ListView, DetailView
from .forms import DynamicFilterForm


# Сайдбар - Работа сайдбара с категориями
# Отображается на всех страницах, кроме стартовой и страниц ошибок

# Навигация - Навигация по хлебным крошкам
# Начинает работать после выбора на стартовой
# Реализовано через разбивание url во вьюхах

def custom_404(request, exception):
    context = {
        'error_message': 'Страница не найдена!',
        'link_text': 'Вернуться на главную',
        'link_url': 'pages:index',
        'error': True
    }

    # Анализируем URL для определения типа ошибки
    path_parts = request.path.strip('/').split('/')
    if len(path_parts) >= 2:  # Убедимся, что в URL есть статус и, например, категория
        status = path_parts[0]
        if not (status in ('in_stock', 'on_order')):
            context['error_message'] = (
                'Необходимо выбрать статус товара: Под заказ или в наличии'
            )
        if len(path_parts) == 2:  # Ошибка на уровне категории
            context['error_message'] = (
                'Товаров в данной категории нет в наличии.'
            )
            context['link_text'] = 'Посмотреть товары под заказ'
            context['link_url'] = f'/on_order/'
        elif len(path_parts) == 3:  # Ошибка на уровне подкатегории
            context['error_message'] = (
                'Товаров в данной подкатегории нет в наличии.'
            )
            context['link_text'] = 'Посмотреть товары под заказ'
            context['link_url'] = f'/on_order/'
        elif len(path_parts) == 4:  # Ошибка на уровне товара
            context['error_message'] = (
                'Данного товара нет в наличии. Вы можете заказать его под заказ.'
            )
            context["link_text"] = 'Заказать товар'
            context["link_url"] = f'/on_order/'

    return render(request, "errors/404.html", context, status=HTTPStatus.NOT_FOUND)


def csrf_failure(request, reason=''):
    return render(
        request,
        'errors/403csrf.html',
        status=HTTPStatus.FORBIDDEN,
        context={'error': True}
    )


def server_error(request, exception=None):
    return render(
        request,
        'errors/500.html',
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        context={'error': True}
    )


def index(request):
    return render(request, 'pages/index.html')


class CategoryListView(ListView):
    model = Category
    template_name = 'pages/category_list.html'
    context_object_name = 'category_list'

    def get_queryset(self):
        in_stock = status_check(self)

        return Category.objects.filter(
            subcategories__product__in_stock=in_stock,
            is_visible=True,
            subcategories__product__is_visible=True,
            subcategories__is_visible=True
        ).distinct()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        in_stock = status_check(self)
        # Название страницы
        context['page_title'] = 'Категории товаров'
        # Навигация
        context['breadcrumbs'] = [
            {'name': 'Главная страница', 'url': '/'},
            {"name": "Категории товаров", "url": None},
        ]
        # Правильное отображение подкатегорий на карточке категории
        for category in context['category_list']:
            category.filtered_subcategories = category.subcategories.filter(
                product__in_stock=in_stock
            ).distinct()
        # Сайдбар
        context['sidebar_list'] = get_categories()
        return context


class SubcategoryListView(ListView):
    model = Subcategory
    template_name = 'pages/subcategory_list.html'
    context_object_name = 'subcategory_list'

    def get_queryset(self):
        in_stock = status_check(self)
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_visible=True,
        )
        data = category.subcategories.filter(is_visible=True)

        if not (queryset := data.filter(
                product__in_stock=in_stock,
                product__is_visible=True
        ).distinct()):
            raise Http404('Запрошенная страница не найдена')
        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.kwargs['status']
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_visible=True
        )
        # Название страницы
        context['page_title'] = category.name

        # Навигация
        context['breadcrumbs'] = [
            {'name': 'Главная страница', 'url': '/'},
            {"name": "Категории товаров", 'url': f'/{status}/'},
            {'name': category.name, 'url': None}
        ]
        # Сайдбар
        context['sidebar_list'] = get_categories()

        return context


class ProductListView(ListView):
    model = Product
    template_name = 'pages/product_list.html'
    context_object_name = 'products_list'

    def setup(self, request, *args, **kwargs) -> None:
        # Убираем параметр page из запроса
        query_params = request.GET.copy()
        query_params.pop("page", None)  # Убираем параметр page, если он есть
        # Перезаписываем строку запроса без параметра page
        request.META["QUERY_STRING"] = urlencode(query_params, doseq=True)
        return super().setup(request, *args, **kwargs)

    def get_paginate_by(self, queryset):
        """Возвращаем количество товаров на странице из GET-параметра `page_size`"""
        page_size = self.request.GET.get('page_size', 10)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 10
        return page_size

    def get_queryset(self):
        in_stock = status_check(self)
        subcategory = get_object_or_404(
            Subcategory,
            slug=self.kwargs['subcategory_slug'],
            is_visible=True,
            category__is_visible=True
        )
        queryset = subcategory.product.filter(
            in_stock=in_stock,
            is_visible=True
        )

        # Применение фильтров на основе параметров, переданных через GET
        filters = self.request.GET

        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        for key, value in filters.items():
            if value and key not in ['page', 'page_size', 'min_price', 'max_price']:
                # Фильтрация по полям в JSONField
                queryset = queryset.filter(
                    Q(params__contains={key: value})
                )

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.kwargs['status']
        subcategory = get_object_or_404(
            Subcategory,
            slug=self.kwargs['subcategory_slug']
        )
        category = subcategory.category.name
        # Название страницы
        context['page_title'] = subcategory.name
        # Навигация
        context['breadcrumbs'] = [
            {'name': 'Главная страница', 'url': '/'},
            {'name': "Категории товаров", 'url': f'/{status}/'},
            {'name': category, 'url': f'/{status}/{self.kwargs['category_slug']}'},
            {'name': subcategory.name, 'url': None}
        ]
        # Сайдбар с фильтрами
        filterable_attributes = get_filterable_attributes(
            self.get_queryset()
        )
        if not filterable_attributes:
            context['form'] = None
        else:
            form = DynamicFilterForm(
                self.request.GET,
                attributes=filterable_attributes
            )

            context['form'] = form

        # Сайдбар
        context['sidebar_list'] = get_categories()

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'pages/product_detail.html'

    def get_object(self, queryset=None):
        in_stock = status_check(self)
        pk = self.kwargs['pk']
        product = get_object_or_404(Product, pk=pk, in_stock=in_stock)
        return product

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.kwargs['status']
        product = get_object_or_404(Product, pk=self.kwargs['pk'])
        subcategory = product.subcategory
        category = subcategory.category.name

        # Навигация
        context['breadcrumbs'] = [
            {'name': 'Главная страница', 'url': '/'},
            {'name': "Категории товаров", 'url': f'/{status}/'},
            {'name': category, 'url': f'/{status}/{self.kwargs['category_slug']}'},
            {'name': subcategory.name,
             'url': f'/{status}/{self.kwargs['category_slug']}/{self.kwargs['subcategory_slug']}'},
            {'name': product.name}
        ]
        # Сайдбар
        context['sidebar_list'] = get_categories()

        return context


class SearchListView(ListView):
    """Поиска по сайту в хедере шаблона"""
    model = Product
    template_name = 'pages/search_list.html'
    context_object_name = 'search_list'

    def setup(self, request, *args, **kwargs) -> None:
        # Убираем параметр page из запроса
        query_params = request.GET.copy()
        query_params.pop("page", None)  # Убираем параметр page, если он есть
        # Перезаписываем строку запроса без параметра page
        request.META["QUERY_STRING"] = urlencode(query_params, doseq=True)
        return super().setup(request, *args, **kwargs)

    def get_paginate_by(self, queryset):
        """Возвращаем количество товаров на странице из GET-параметра `page_size`"""
        page_size = self.request.GET.get('page_size', 10)
        try:
            page_size = int(page_size)
        except ValueError:
            page_size = 10
        return page_size

    def get_queryset(self):
        # Отдельный поиск в разделах сайта
        in_stock = status_check(self)
        query = self.request.GET.get('query', '').strip()

        if query:
            results = Product.objects.filter(
                Q(name__icontains=query),
                in_stock=in_stock,
                is_visible=True,
                subcategory__is_visible=True,
                subcategory__category__is_visible=True
            )
            if subcategory := self.request.GET.get('subcategory'):
                results = results.filter(subcategory=subcategory)

        else:
            results = Product.objects.none()

        return results

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = get_categories()
        # Сайдбар
        context['sidebar_list'] = categories
        # фильтр по категориям
        context['category_filters'] = {
            key: key.subcategories.filter(is_visible=True)
            for key in categories
        }
        if selected_subcategory := self.request.GET.get('subcategory'):
            context['selected_subcategory'] = Subcategory.objects.get(pk=selected_subcategory)

        context['page_title'] = 'Результаты поиска'
        return context


def status_check(self):
    """Проверка статуса в url"""
    status = self.kwargs['status']
    if not (status in ('in_stock', 'on_order')):
        raise Http404('Необходимо выбрать статус товара: Под заказ или в наличии')
    return True if status == 'in_stock' else False


def get_categories():
    """Получение категорий для сайдбара"""
    return Category.objects.filter(
        is_visible=True,
    ).distinct()


def get_filterable_attributes(queryset):
    """Получение уникальных значений параметров для фильтрации"""
    attributes = {}
    for product in queryset.values_list('params', flat=True):
        for key, value in product.items():
            attributes.setdefault(key, set()).add(value)
    return {key: list(values) for key, values in attributes.items()}
