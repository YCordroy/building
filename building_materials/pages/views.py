from http import HTTPStatus

from django.http import Http404
from django.shortcuts import render, get_object_or_404

from product.models import Product, Subcategory, Category
from django.views.generic import ListView, DetailView


def page_not_found(request, exception=None):
    return render(
        request,
        'pages/404.html',
        status=HTTPStatus.NOT_FOUND
    )


def csrf_failure(request, reason=''):
    return render(
        request,
        'pages/403csrf.html',
        status=HTTPStatus.FORBIDDEN
    )


def server_error(request, exception=None):
    return render(
        request,
        'pages/500.html',
        status=HTTPStatus.INTERNAL_SERVER_ERROR
    )


def index(request):
    return render(request, 'pages/index.html')


class CategoryListView(ListView):
    model = Category
    template_name = 'pages/categories.html'
    context_object_name = 'category_list'

    def get_queryset(self):
        status = self.kwargs['status']
        return get_categories(status)

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        # Навигация
        context['breadcrumbs'] = [
            {'name': 'Главная страница', 'url': '/'},
            {"name": "Категории товаров", "url": None},
        ]
        # Правильное отображение подкатегорий на карточке категории
        for category in context['category_list']:
            category.filtered_subcategories = category.subcategories.filter(product__in_stock=True).distinct()
        return context


class SubcategoryListView(ListView):
    model = Subcategory
    template_name = 'pages/subcategories.html'
    context_object_name = 'subcategory_list'

    def get_queryset(self):
        status = self.kwargs['status']
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_visible=True
        )
        if not (
                data := category.subcategories.filter(
                    is_visible=True
                )
        ):
            raise Http404("Товары не найдены")

        if status == 'in_stock':
            return data.filter(
                product__in_stock=True,
                product__is_visible=True
            ).distinct()
        elif status == 'on_order':
            return data.filter(
                product__in_stock=False,
                product__is_visible=True
            ).distinct()
        raise Http404('Товары не найдены')

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
        context['category_list'] = get_categories(status)
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'pages/products.html'
    context_object_name = 'products_list'

    def get_queryset(self):
        status = self.kwargs['status']
        subcategory = get_object_or_404(
            Subcategory,
            slug=self.kwargs['subcategory_slug']
        )
        if status == 'in_stock':
            if not (data := subcategory.product.filter(
                    in_stock=True,
                    is_visible=True
            )):
                raise Http404('Товары не найдены')
            return data

        elif status == 'on_order':
            if not (data := subcategory.product.filter(
                    in_stock=False,
                    is_visible=True
            )):
                raise Http404('Товары не найдены')
            return data
        raise Http404('Товары не найдены')

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
        context['category_list'] = get_categories(status)

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'pages/product_detail.html'

    def get_object(self, queryset=None):
        status = self.kwargs['status']
        pk = self.kwargs['pk']
        product = get_object_or_404(Product, pk=pk)
        if status == 'in_stock':
            if product.in_stock:
                return product
            raise Http404('Товар не найден')
        elif status == 'on_order':
            if not product.in_stock:
                return product
            raise Http404('Товар не найден')
        raise Http404('Товар не найден')

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
        context['category_list'] = get_categories(status)

        return context


def get_categories(status):
    if status == 'in_stock':
        return Category.objects.filter(
            subcategories__product__in_stock=True,
            is_visible=True,
            subcategories__product__is_visible=True,
            subcategories__is_visible=True
        ).distinct()
    elif status == 'on_order':
        return Category.objects.filter(
            subcategories__product__in_stock=False,
            is_visible=True,
            subcategories__product__is_visible=True,
            subcategories__is_visible=True
        ).distinct()
    raise Http404('Товары не найдены')
