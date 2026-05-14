from django.shortcuts import redirect, render

def login_page(request):
    return render(request, 'authentication/login.html')

def logout_view(request):
    request.session.flush()

    return redirect('/auth/login/')