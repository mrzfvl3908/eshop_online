from django.shortcuts import render
from django.views import View
from .forms import LoginForm


class UserLogin(View):
    def get(self, request):
        form = LoginForm()
        return render(request, 'accounts_app/login.html', {'form': form})

