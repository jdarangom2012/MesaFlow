from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


class MesaFlowLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    return redirect('login')
