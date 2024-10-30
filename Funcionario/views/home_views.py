from django.shortcuts import render
import requests

# Página inicial com a listagem de feriados
def home(request):
    url = 'https://brasilapi.com.br/api/feriados/v1/2025'
    feriados = []
    try:
        response = requests.get(url)
        if response.status_code == 200:
            feriados = response.json()
    except Exception as e:
        print("Exceção ao chamar a API:", e)
    return render(request, 'home.html', {'feriados': feriados})

def sucesso_view(request):
    return render(request, 'sucesso.html') 