from django.contrib.auth.views import LoginView
from .forms import LoginForm


class UserLogin(LoginView):
    template_name = 'accounts_app/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True