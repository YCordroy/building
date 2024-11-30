from random import randint, sample, choice, randrange
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from product.models import Product, Category, Subcategory

base_categories = (
    (
        ('Сантехника', 'santech'),
        (('Ванны', 'vanny'), ('Мойки', 'moyki'), ('Унитазы', 'sralniki'))
    ),
    (
        ('Насосы', 'nasosy'),
        (('Глубинные', 'glub'), ('Дренажные', 'drenaj'), ('Поверхностные', 'poverh'))
    ),
    (('Водомеры', 'vodomery'), (
        ('Водомеры', 'vodomery'),
        ('Шланги для подвода воды', 'shlangy-podvod'),
        ('Шланги для стиральных машин', 'shlangy-stiral')
    )),
    (
        ('Ёмкости', 'emkost'),
        (('Пластиковые', 'plastik'), ('Для душа', 'dush'), ('Врезки', 'vrezki'))
    ),
    (
        ('Инструменты и хоз.товары', 'instrumenty'),
        (('Инструменты', 'instrumenty'), ('Расходники', 'rashodniky'), ('Хомуты', 'homuts'))
    )
)

parameters = (
    ("Бренд", "KO&PO"),
    ("Ширина", "110 см"),
    ("Длина", "100 см"),
    ("Материал", "Аркил"),
    ("Oриентация", "Универсальная"),
    ("Тип установки", "Напольный"),
    ("Выпуск в канализацию", "Горизонтальный"),
    ("Тип монтажа", "Напольный"),
    ("Высота", "40 см")
)

image_path = Path(Path(__file__).resolve().parents[4], 'image_folder')
images = list(image_path.glob('*'))


class Command(BaseCommand):

    @staticmethod
    def get_params():
        # Генерация параметров товара.
        params = {}
        count = randint(0, 9)
        selected_params = sample(parameters, count)
        for key, value in selected_params:
            params[key] = value
        return params

    @staticmethod
    def create_categories():
        if not Category.objects.all():
            data_subcategories = []
            for name, subcategories in base_categories:
                random_image = choice(images)
                with random_image.open('rb') as f:
                    image_file = File(f, name=random_image.name)
                    category = Category(
                        name=name[0],
                        slug=name[1],
                        image=image_file,
                        description='Небольшое описание категории'
                    )
                    category.save()
                    for subcategory in subcategories:
                        data_subcategories.append(
                            Subcategory(
                                name=subcategory[0],
                                slug=subcategory[1],
                                category=category
                            )
                        )

            Subcategory.objects.bulk_create(data_subcategories)
        return

    def handle(self, *args, **options):
        self.create_categories()

        subcategories = Subcategory.objects.all()

        for i in range(999):
            name = 'Товар #' + str(i)
            price = float(randrange(500, 10000, 100))
            params = self.get_params()
            in_stock = choice((True, False))
            random_image = choice(images)
            subcategory = choice(subcategories)
            with random_image.open('rb') as f:
                image_file = File(f, name=random_image.name)
                Product(
                    name=name,
                    subcategory=subcategory,
                    price=price,
                    params=params,
                    in_stock=in_stock,
                    image=image_file
                ).save()
