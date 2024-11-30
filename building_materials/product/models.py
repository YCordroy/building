from django.db import models


def directory_path(instance, filename):
    if type(instance) is Category:
        return f'category/{instance.name}.png'
    if type(instance) is Product:
        return f'product/{instance.subcategory}/{instance.name}.png'


class VisibleModel(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=100,
        db_index=True
    )
    is_visible = models.BooleanField(
        verbose_name='В зоне видимости',
        default=True,
        help_text='Снимите галочку, что бы убрать из поиска'
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ImageDescriptionModel(models.Model):
    description = models.TextField(
        verbose_name='Описание',
        default='Описание отсутствует'
    )
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to=directory_path,
        null=True
    )

    class Meta:
        abstract = True


class Product(VisibleModel, ImageDescriptionModel):
    subcategory = models.ForeignKey(
        'Subcategory',
        verbose_name='Под категория',
        on_delete=models.PROTECT,
        related_name='product'
    )
    params = models.JSONField(
        verbose_name='Параметры'
    )
    price = models.DecimalField(
        verbose_name='Цена',
        max_digits=10,
        decimal_places=2
    )
    in_stock = models.BooleanField(
        verbose_name='В наличии',
        default=False
    )

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'Товары'


class Category(VisibleModel, ImageDescriptionModel):
    slug = models.SlugField(
        verbose_name='Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; '
                  'разрешены символы латиницы, цифры, дефис и подчёркивание.'

    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_category'
            )
        ]


class Subcategory(VisibleModel):
    category = models.ForeignKey(
        'Category',
        verbose_name='Категория',
        on_delete=models.PROTECT,
        related_name='subcategories'
    )
    slug = models.SlugField(
        verbose_name='Идентификатор',
        unique=True,
        help_text='Идентификатор страницы для URL; '
                  'разрешены символы латиницы, цифры, дефис и подчёркивание.'

    )

    class Meta:
        verbose_name = 'под категория'
        verbose_name_plural = 'Под категории'
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                name='unique_subcategory'
            )
        ]
