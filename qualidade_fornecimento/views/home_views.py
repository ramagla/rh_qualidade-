from django.shortcuts import render


def home_qualidade(request):
    return render(request, "qualidade_fornecimento/home.html")
