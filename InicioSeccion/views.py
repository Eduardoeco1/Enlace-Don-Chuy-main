from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/panel-control/')

    username = ''
    login_error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/panel-control/')
        else:
            login_error = 'Usuario o contraseña incorrectos. Verifique sus credenciales e intente nuevamente.'

    return render(request, 'InicioSeccion/inisec.html', {
        'username_input': username,
        'login_error': login_error,
    })
