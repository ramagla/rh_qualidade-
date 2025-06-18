from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render

@login_required
@permission_required("tecnico.acesso_tecnico", raise_exception=True)
def home_tecnico(request):
    return render(request, "dasboard_tecnico.html")
