from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts_app.models import User


class Category(models.Model):
    name = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'

    def __str__(self):
        return self.name


class Size(models.Model):
    title = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'سایز'
        verbose_name_plural = 'سایزها'

    def __str__(self):
        return self.title


class Color(models.Model):
    title = models.CharField(max_length=10)

    class Meta:
        verbose_name = 'رنگ'
        verbose_name_plural = 'رنگ‌ها'

    def __str__(self):
        return self.title


class Product(models.Model):
    category = models.ManyToManyField(
        Category,
        related_name='products'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='products',
        blank=True,
        null=True
    )

    title = models.CharField(max_length=300)

    price = models.PositiveIntegerField()

    discount = models.PositiveSmallIntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ]
    )

    description = models.TextField()

    image = models.ImageField(
        upload_to='products/'
    )

    size = models.ManyToManyField(
        Size,
        related_name='products',
        blank=True,
        null=True
    )

    color = models.ManyToManyField(
        Color,
        related_name='products',
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    slug = models.SlugField(
        unique=True,
        blank=True,
        allow_unicode=True
    )

    status = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(
                self.title,
                allow_unicode=True
            )

        super().save(*args, **kwargs)

    @property
    def final_price(self):
        return self.price - (
                self.price * self.discount // 100
        )

    def get_absolute_url(self):
        return reverse(
            'product_app:product-detail',
            kwargs={
                'slug': self.slug
            }
        )

    def __str__(self):
        return self.title


class Review(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_reviews'
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ]
    )

    comment = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        ordering = ['-created_at']

        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'

        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_product_user_review'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.product}'
