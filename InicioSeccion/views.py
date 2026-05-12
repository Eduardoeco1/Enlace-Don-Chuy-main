from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/panel-control/')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/panel-control/')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos. Intente de nuevo.')
            return render(request, 'InicioSeccion/inisec.html', {'username_input': username})

    return render(request, 'InicioSeccion/inisec.html')