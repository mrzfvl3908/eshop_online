from django.db import models


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
        verbose_name_plural = 'رنگ ها'

    def __str__(self):
        return self.title



class Products(models.Model):
    title = models.CharField(max_length=300)
    price = models.IntegerField()
    discount = models.SmallIntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='products/')
    size = models.ManyToManyField(Size, related_name='products')
    color = models.ManyToManyField(Color, related_name='products', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ['-created_at']
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'

    def __str__(self):
        return self.title
