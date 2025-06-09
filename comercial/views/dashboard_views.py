from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def dashboard_comercial(request):
    return render(request, 'comercial/dashboard_comercial.html')
