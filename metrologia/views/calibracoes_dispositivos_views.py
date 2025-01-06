from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
import Funcionario
from metrologia.models import CalibracaoDispositivo, Dispositivo, Cota, Afericao
from metrologia.forms.CalibracaoDispositivoForm import CalibracaoDispositivoForm
from metrologia.models.models_tabelatecnica import TabelaTecnica



def lista_calibracoes_dispositivos(request):
    calibracoes = CalibracaoDispositivo.objects.all()
    return render(request, 'calibracoes/lista_calibracoes_dispositivos.html', {'calibracoes': calibracoes})

def cadastrar_calibracao_dispositivo(request):
    try:
        if request.method == 'POST':
            form = CalibracaoDispositivoForm(request.POST)
            if form.is_valid():
                calibracao = form.save()

                # Salvar aferições
                afericoes_data = request.POST.getlist('afericoes')
                for index, afericao in enumerate(afericoes_data):
                    cota = Cota.objects.get(numero=afericao['numero'], dispositivo=calibracao.codigo_dispositivo)
                    Afericao.objects.create(
                        calibracao_dispositivo=calibracao,
                        cota=cota,
                        valor=afericao['valor']
                    )
                messages.success(request, 'Calibração salva com sucesso!')
                return redirect('calibracoes_dispositivos')
            else:
                messages.error(request, 'Erro ao salvar calibração. Verifique os dados informados.')
        else:
            form = CalibracaoDispositivoForm()

        dispositivos = Dispositivo.objects.all()
        return render(request, 'calibracoes/cadastrar_calibracao_dispositivo.html', {
            'form': form,
            'dispositivos': dispositivos,
        })
    except Exception as e:
        messages.error(request, f'Erro inesperado: {str(e)}')
        return redirect('calibracoes_dispositivos')

@csrf_exempt
def get_dispositivo_info(request, dispositivo_id):
    dispositivo = get_object_or_404(Dispositivo, id=dispositivo_id)
    cotas = Cota.objects.filter(dispositivo=dispositivo)

    data = {
        'codigo_peca': dispositivo.codigo[:-2] if len(dispositivo.codigo) > 2 else dispositivo.codigo,
        'desenho_url': dispositivo.desenho_anexo.url if dispositivo.desenho_anexo else None,
        'cotas': [
            {'numero': cota.numero, 'valor_minimo': float(cota.valor_minimo), 'valor_maximo': float(cota.valor_maximo)}
            for cota in cotas
        ]
    }
    return JsonResponse(data)


def editar_calibracao_dispositivo(request, pk):
    calibracao = get_object_or_404(CalibracaoDispositivo, pk=pk)
    if request.method == 'POST':
        form = CalibracaoDispositivoForm(request.POST, instance=calibracao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Calibração editada com sucesso.')
            return redirect('calibracoes_dispositivos')
    else:
        form = CalibracaoDispositivoForm(instance=calibracao)

    return render(request, 'calibracoes/editar_calibracao_dispositivo.html', {'form': form, 'calibracao': calibracao})

def excluir_calibracao_dispositivo(request, id):
    calibracao = get_object_or_404(CalibracaoDispositivo, id=id)
    if request.method == 'POST':
        calibracao.delete()
        messages.success(request, 'Calibração excluída com sucesso.')
        return redirect('calibracoes_dispositivos')

    return render(request, 'calibracoes/excluir_calibracao_dispositivo.html', {'calibracao': calibracao})
