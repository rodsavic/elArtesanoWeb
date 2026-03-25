from django.contrib import messages
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, "Has iniciado sesion exitosamente.")
            next_url = request.POST.get('next') or request.GET.get('next')
            return redirect(next_url or 'home:index')
        messages.error(request, "Nombre de usuario o contrasena incorrectos.")
    else:
        form = AuthenticationForm()

    return render(request, 'authentication/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesion exitosamente.")
    return redirect('authentication:login')
