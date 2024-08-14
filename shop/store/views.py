from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from .models import *
from random import randint
from .forms import LoginForm, RegistrationForm, ReviewForm, CustomerForm, ShippingForm
from django.contrib.auth import login, logout
from django.contrib import messages
from shop import settings
from django.core.mail import send_mail
from .utils import get_cart_data, CartForAuthenticatedUser
import stripe

# Create your views here.

class ProductList(ListView):
    model = Product
    context_object_name = 'categories'

    extra_context = {
        'title': 'TOTEMBO: Главная страница'
    }

    def get_queryset(self):
        categories = Category.objects.filter(parent=None)
        return categories

    template_name = 'store/product_list.html'





class CategoryView(ListView):
    model = Product
    context_object_name = 'products'
    template_name = 'store/category_page.html'
    paginate_by = 1

    def get_queryset(self):
        sort_field = self.request.GET.get('sort')
        type_field = self.request.GET.get('type')
        if type_field:
            products = Product.objects.filter(category__slug=type_field)
            return products

        main_category = Category.objects.get(slug=self.kwargs['slug'])
        subcategories = main_category.subcategories.all()
        products = Product.objects.filter(category__in=subcategories)
        if sort_field:
            products = products.order_by(sort_field)
        return products

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()
        main_category = Category.objects.get(slug=self.kwargs['slug'])
        context['category'] = main_category
        context['title'] = f'Категория: {main_category.title}'
        return context



class ProductDetail(DetailView):  # product_detail.html
    model = Product
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        product = Product.objects.get(slug=self.kwargs['slug'])
        context['title'] = f'Товар: {product.title}, {product.category}'


        products = Product.objects.all()
        data = []
        for i in range(4):
            random_index = randint(0, len(products)-1)
            p = products[random_index]
            if p not in data:
                data.append(p)
        context['products'] = data

        context['reviews'] = Review.objects.filter(product=product)

        if self.request.user.is_authenticated:
            context['review_form'] = ReviewForm()

        return context



def login_registration(request):
    context = {
        'title': 'Войти или зарегистрироваться',
        'login_form': LoginForm(),
        'registration_form': RegistrationForm()
    }

    return render(request, 'store/login_registration.html', context)

def user_login(request):
    form = LoginForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, 'Успешный вход в аккаунт')
        return redirect('product_list')
    else:
        messages.error(request, 'Не верное имя пользователя или пароль')
        return redirect('login_registration')

def user_logout(request):
    logout(request)
    messages.warning(request, 'Вы вышли из аккаунта')
    return redirect('product_list')

def register(request):
    form = RegistrationForm(data=request.POST)
    if form.is_valid():
        user = form.save()
        messages.success(request, 'Регистрация прошла успешно. Войдите в аккаунт')
    else:
        for field in form.errors:
            messages.error(request, form.errors[field].as_text())
    return redirect('login_registration')







# Функция для сохранений отзывов
def save_review(request, slug):
    form = ReviewForm(data=request.POST)
    if form.is_valid():
        review = form.save(commit=False)
        review.author = request.user
        product = Product.objects.get(slug=slug)
        review.product = product
        review.save()
    else:


        pass
    return redirect('product_detail', product.slug)


def save_favorite_product(request, product_slug):
    user = request.user if request.user.is_authenticated else None
    product = Product.objects.get(slug=product_slug)
    favorite_products = FavouriteProduct.objects.filter(user=user)
    if user:
        if product in [i.product for i in favorite_products]:
            fav_product = FavouriteProduct.objects.get(user=user, product=product)
            fav_product.delete()
            messages.error(request, 'Продукт удалён из избранного')
        else:
            FavouriteProduct.objects.create(user=user, product=product)
            messages.success(request, 'Продукт успешно добавлен в избранное')
    else:
        messages.warning(request, 'Войдите или зарегистрируйтесь, чтобы добавить в Избранное')
        return redirect('login_registration')
    next_page = request.META.get('HTTP_REFERER', 'product_list')
    return redirect(next_page)


class FavouriteProductView(LoginRequiredMixin, ListView):
    model = FavouriteProduct
    context_object_name = 'products'
    template_name = 'store/favourite_products.html'
    login_url = 'login_registration'

    def get_queryset(self):
        user = self.request.user
        favs = FavouriteProduct.objects.filter(user=user)
        products = [i.product for i in favs]
        return products



def save_mail(request):
    email = request.POST.get('email')
    user = request.user if request.user.is_authenticated else None
    mail_user = Mail.objects.all()
    if user:
        if email not in [i.mail for i in mail_user]:
            Mail.objects.create(mail=email, user=user)
            messages.success(request, 'Ваша почта успешно добавлена')
        else:
            messages.warning(request, 'Ваша почта уже добавлена')

    else:
        messages.error(request, 'Войдите или Зарегистрируйтесь')
        return redirect('login_registration')

    next_page = request.META.get('HTTP_REFERER', 'product_list')
    return redirect(next_page)


def send_mail_to_customer(request):
    superuser = request.user if request.user.is_superuser else None
    if superuser:
        if request.method == 'POST':
            text = request.POST.get('text')
            mail_list = Mail.objects.all()
            for email in mail_list:
                mail = send_mail(
                    subject='У нас для Вас важная новость',
                    message=text,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False
                )
                print(f'Отправлено сообщение на почту {email}? - {bool(mail)}')
    else:
        return redirect('product_list')

    return render(request, 'store/send_mail.html')




def cart(request):
    if request.user.is_authenticated:
        cart_info = get_cart_data(request)

        context = {
            'cart_total_quantity': cart_info['cart_total_quantity'],
            'order': cart_info['order'],
            'products': cart_info['products']
        }

        return render(request, 'store/cart.html', context)
    else:
        return redirect('login_registration')


def to_cart(request, product_id, action):
    if request.user.is_authenticated:
        user_cart = CartForAuthenticatedUser(request, product_id, action)
        next_page = request.META.get('HTTP_REFERER', 'product_list')
        return redirect(next_page)
    else:
        messages.warning(request, 'Авторизуйтесь или зарегистрируйтесь')
        return redirect('login_registration')



def checkout(request):
    cart_info = get_cart_data(request)

    context = {
        'cart_total_quantity': cart_info['cart_total_quantity'],
        'order': cart_info['order'],
        'items': cart_info['products'],

        'customer_form': CustomerForm(),
        'shipping_form': ShippingForm(),
        'title': 'Оформление заказа'
    }

    return render(request, 'store/checkout.html', context)



def clear_cart(request):
    user_cart = CartForAuthenticatedUser(request)
    order = user_cart.get_cart_info()['order']
    order_products = order.orderproduct_set.all()
    for order_product in order_products:
        quantity = order_product.quantity
        product = order_product.product
        order_product.delete()
        product.quantity += quantity
        product.save()
    return redirect('cart')




def create_checkout_session(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if request.method == 'POST':
        user_cart = CartForAuthenticatedUser(request)
        cart_info = user_cart.get_cart_info()

        customer_form = CustomerForm(data=request.POST)
        if customer_form.is_valid():
            customer = Customer.objects.get(user=request.user)
            customer.first_name = customer_form.cleaned_data['first_name']
            customer.last_name = customer_form.cleaned_data['last_name']
            customer.save()
            user = User.objects.get(username=request.user.username)
            user.first_name = customer_form.cleaned_data['first_name']
            user.last_name = customer_form.cleaned_data['last_name']
            user.save()

        shipping_form = ShippingForm(data=request.POST)
        if shipping_form.is_valid():
            address = shipping_form.save(commit=False)
            address.customer = Customer.objects.get(user=request.user)
            address.order = user_cart.get_cart_info()['order']
            address.save()

        total_price = cart_info['cart_total_price']
        total_quantity = cart_info['cart_total_quantity']
        session = stripe.checkout.Session.create(
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data':{
                        'name': 'Товары с Totembo'
                    },
                    'unit_amount': int(total_price * 100)
                },
                'quantity': 1
            }],
            mode='payment',
            success_url=request.build_absolute_uri(reverse('success')),
            cancel_url=request.build_absolute_uri(reverse('checkout'))
        )
        return redirect(session.url, 303)


def success_payment(request):
    user_cart = CartForAuthenticatedUser(request)
    user_cart.clear()
    messages.success(request, 'Оплата прошла успешно')
    return render(request, 'store/success.html')