from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path('', views.index, name='index'),
    path('<str:status>/', views.CategoryListView.as_view(), name='categories'),
    path('<str:status>/search/', views.SearchListView.as_view(), name='search'),
    path('<str:status>/<str:category_slug>/', views.SubcategoryListView.as_view(), name='subcategories'),
    path('<str:status>/<str:category_slug>/<str:subcategory_slug>/', views.ProductListView.as_view(),
         name='products'),
    path('<str:status>/<str:category_slug>/<str:subcategory_slug>/<int:pk>', views.ProductDetailView.as_view(),
         name='product_detail'),
]
