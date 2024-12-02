from http import HTTPStatus

from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from product.models import Product, Subcategory, Category
from django.views.generic import ListView, DetailView


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

    return render(request, "pages/404.html", context, status=HTTPStatus.NOT_FOUND)


def csrf_failure(request, reason=''):
    return render(
        request,
        'pages/403csrf.html',
        status=HTTPStatus.FORBIDDEN,
        context={'error': True}
    )


def server_error(request, exception=None):
    return render(
        request,
        'pages/500.html',
        status=HTTPStatus.INTERNAL_SERVER_ERROR,
        context={'error': True}
    )


def index(request):
    return render(request, 'pages/index.html')


class CategoryListView(ListView):
    model = Category
    template_name = 'pages/categories.html'
    context_object_name = 'category_list'

    def get_queryset(self):
        status = self.kwargs['status']
        status_check(status)
        in_stock = True if status == 'in_stock' else False

        return Category.objects.filter(
            subcategories__product__in_stock=in_stock,
            is_visible=True,
            subcategories__product__is_visible=True,
            subcategories__is_visible=True
        ).distinct()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.kwargs['status']
        status_check(status)
        in_stock = True if status == 'in_stock' else False
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
    template_name = 'pages/subcategories.html'
    context_object_name = 'subcategory_list'

    def get_queryset(self):
        status = self.kwargs['status']
        status_check(status)
        in_stock = True if status == 'in_stock' else False
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
    template_name = 'pages/products.html'
    context_object_name = 'products_list'

    def get_queryset(self):
        status = self.kwargs['status']
        status_check(status)
        in_stock = True if status == 'in_stock' else False
        subcategory = get_object_or_404(
            Subcategory,
            slug=self.kwargs['subcategory_slug'],
            is_visible=True,
            category__is_visible=True
        )
        if not (data := subcategory.product.filter(
                in_stock=in_stock,
                is_visible=True
        )):
            raise Http404('Товары не найдены')
        return data

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        status = self.kwargs['status']
        subcategory = get_object_or_404(
            Subcategory,
            slug=self.kwargs['subcategory_slug']
        )
        category = subcategory.category.name
        # Навигация
        context['breadcrumbs'] = [
            {'name': 'Главная страница', 'url': '/'},
            {'name': "Категории товаров", 'url': f'/{status}/'},
            {'name': category, 'url': f'/{status}/{self.kwargs['category_slug']}'},
            {'name': subcategory.name, 'url': None}
        ]
        # Сайдбар
        context['sidebar_list'] = get_categories()

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'pages/product_detail.html'

    def get_object(self, queryset=None):
        status = self.kwargs['status']
        in_stock = True if status == 'in_stock' else False
        status_check(status)
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
    """Правильная работа поиска по сайту в хедере"""
    model = Product
    template_name = 'pages/search.html'
    context_object_name = 'search_list'

    def get_queryset(self):
        status = self.kwargs['status']
        status_check(status)
        query = self.request.GET.get('query', '').strip()
        in_stock = True if status == 'in_stock' else False
        if query:
            results = Product.objects.filter(
                Q(name__icontains=query),
                in_stock=in_stock,
                is_visible=True,
                subcategory__is_visible=True,
                subcategory__category__is_visible=True
            )
        else:
            results = Product.objects.none()
        return results

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        # Сайдбар
        context['sidebar_list'] = get_categories()
        return context


def status_check(status):
    """Проверка статуса в url"""
    if not (status in ('in_stock', 'on_order')):
        raise Http404('Необходимо выбрать статус товара: Под заказ или в наличии')


def get_categories():
    """Получение категорий для сайдбара"""
    return Category.objects.filter(
        is_visible=True,
    ).distinct()
