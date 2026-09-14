from django.db.models import Avg, Count, Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView

from .forms import ReviewForm
from .models import Product


class ProductListView(ListView):
    model = Product
    template_name = 'product_app/product_list.html'
    context_object_name = 'products'
    paginate_by = 9

    def get_queryset(self):

        queryset = (
            Product.objects
            .filter(status=True)
            .prefetch_related(
                'category',
                'size',
                'color',
            )
        )

        search_query = self.request.GET.get(
            'search',
            ''
        ).strip()

        if search_query:
            queryset = queryset.filter(
                title__icontains=search_query
            )

        selected_prices = self.request.GET.getlist('price')

        price_filters = {
            '0-100': (0, 100),
            '100-200': (100, 200),
            '200-300': (200, 300),
            '300-400': (300, 400),
            '400-500': (400, 500),
            '500+': (500, None),
        }

        price_query = Q()

        for price_range in selected_prices:

            if price_range not in price_filters:
                continue

            minimum, maximum = price_filters[price_range]

            if maximum is None:
                price_query |= Q(
                    price__gte=minimum
                )
            else:
                price_query |= Q(
                    price__gte=minimum,
                    price__lt=maximum
                )

        if price_query:
            queryset = queryset.filter(
                price_query
            )

        selected_colors = self.request.GET.getlist('color')

        if selected_colors:
            queryset = queryset.filter(
                color__id__in=selected_colors
            )

        selected_sizes = self.request.GET.getlist('size')

        if selected_sizes:
            queryset = queryset.filter(
                size__id__in=selected_sizes
            )

        sort = self.request.GET.get(
            'sort',
            'latest'
        )

        if sort == 'price_low':
            queryset = queryset.order_by('price')

        elif sort == 'price_high':
            queryset = queryset.order_by('-price')

        elif sort == 'name':
            queryset = queryset.order_by('title')

        else:
            queryset = queryset.order_by('-created_at')

        return queryset.distinct()

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context['search_query'] = self.request.GET.get(
            'search',
            ''
        ).strip()

        context['selected_prices'] = self.request.GET.getlist(
            'price'
        )

        context['selected_colors'] = self.request.GET.getlist(
            'color'
        )

        context['selected_sizes'] = self.request.GET.getlist(
            'size'
        )

        context['current_sort'] = self.request.GET.get(
            'sort',
            'latest'
        )

        context['price_filters'] = [
            {
                'value': '0-100',
                'label': '$0 - $100',
            },
            {
                'value': '100-200',
                'label': '$100 - $200',
            },
            {
                'value': '200-300',
                'label': '$200 - $300',
            },
            {
                'value': '300-400',
                'label': '$300 - $400',
            },
            {
                'value': '400-500',
                'label': '$400 - $500',
            },
            {
                'value': '500+',
                'label': '$500+',
            },
        ]

        context['colors'] = (
            Product.objects
            .filter(
                status=True,
                color__isnull=False
            )
            .values(
                'color__id',
                'color__title',
            )
            .annotate(
                product_count=Count(
                    'id',
                    distinct=True
                )
            )
            .order_by(
                'color__title'
            )
        )

        query_params = self.request.GET.copy()

        query_params.pop(
            'page',
            None
        )

        query_params.pop(
            'sort',
            None
        )

        context['filter_query'] = query_params.urlencode()

        base_url = '?'

        if context['filter_query']:
            base_url += (
                    context['filter_query']
                    + '&'
            )

        context['sort_latest_url'] = (
                base_url + 'sort=latest'
        )

        context['sort_price_low_url'] = (
                base_url + 'sort=price_low'
        )

        context['sort_price_high_url'] = (
                base_url + 'sort=price_high'
        )

        context['sort_name_url'] = (
                base_url + 'sort=name'
        )

        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'product_app/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):

        return (
            Product.objects
            .filter(status=True)
            .prefetch_related(
                'category',
                'size',
                'color',
            )
        )

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        product = self.object

        context['review_form'] = kwargs.get(
            'review_form',
            ReviewForm()
        )

        reviews = (
            product.reviews
            .select_related('user')
            .order_by('-created_at')
        )

        paginator = Paginator(
            reviews,
            5
        )

        review_page_number = self.request.GET.get(
            'review_page'
        )

        context['review_page'] = paginator.get_page(
            review_page_number
        )

        review_stats = (
            product.reviews
            .aggregate(
                average=Avg('rating'),
                count=Count('id')
            )
        )

        average = review_stats['average']

        context['review_average'] = (
            round(average, 1)
            if average is not None
            else 0
        )

        context['review_count'] = review_stats['count']

        category_ids = (
            product.category
            .values_list(
                'id',
                flat=True
            )
        )

        context['related_products'] = (
            Product.objects
            .filter(
                status=True,
                category__id__in=category_ids
            )
            .exclude(
                id=product.id
            )
            .prefetch_related(
                'category'
            )
            .distinct()[:8]
        )

        if self.request.user.is_authenticated:

            context['user_review'] = (
                product.reviews
                .filter(
                    user=self.request.user
                )
                .first()
            )

        else:

            context['user_review'] = None

        return context

    def post(self, request, *args, **kwargs):

        self.object = self.get_object()

        if not request.user.is_authenticated:
            messages.warning(
                request,
                'Please login to submit a review.'
            )

            return redirect(
                f'{self.object.get_absolute_url()}#reviews'
            )

        if self.object.reviews.filter(
                user=request.user
        ).exists():
            messages.warning(
                request,
                'You have already reviewed this product.'
            )

            return redirect(
                f'{self.object.get_absolute_url()}#reviews'
            )

        form = ReviewForm(
            request.POST
        )

        if form.is_valid():

            review = form.save(
                commit=False
            )

            review.product = self.object
            review.user = request.user

            try:

                review.save()

                messages.success(
                    request,
                    'Your review has been submitted successfully.'
                )

                return redirect(
                    f'{self.object.get_absolute_url()}#reviews'
                )

            except IntegrityError:

                messages.warning(
                    request,
                    'You have already reviewed this product.'
                )

                return redirect(
                    f'{self.object.get_absolute_url()}#reviews'
                )

        context = self.get_context_data(
            review_form=form
        )

        return self.render_to_response(
            context
        )
