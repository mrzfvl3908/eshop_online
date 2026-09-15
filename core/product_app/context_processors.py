from .models import Category


def categories(request):

    return {
        'header_categories': Category.objects.all()
    }