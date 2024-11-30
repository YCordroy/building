from django.contrib import admin
from .models import Product, Category, Subcategory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
        'is_visible'
    )

    list_editable = (
        'is_visible',
    )


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'category',
        'is_visible'
    )

    list_editable = (
        'is_visible',
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
        'is_visible',
        'price',
        'in_stock'
    )

    list_editable = (
        'is_visible',
        'in_stock'
    )

