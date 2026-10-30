from django.shortcuts import render

# Create your views here.
import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Bocina, ComandoBocina, ComandoLed, EventoBocina, EventoLed, Led


def dashboard(request):
    leds = Led.objects.all().order_by("id")
    bocinas = Bocina.objects.all().order_by("id")
    eventos = EventoLed.objects.select_related("led").all()[:20]

    return render(
        request,
        "control/dashboard.html",
        {
            "leds": leds,
            "bocinas": bocinas,
            "eventos": eventos,
        }
    )


def estado_sistema(request):
    # ESTADOS DE LOS LED
    datos_leds = []
    for led in Led.objects.all():
        datos_leds.append({
            "codigo": led.codigo,
            "nombre": led.nombre,
            "estado": led.estado_actual
        })

    # ESTADOS DE LAS BOCINAS
    datos_bocinas = []
    for bocina in Bocina.objects.all():
        datos_bocinas.append({
            "codigo": bocina.codigo,
            "nombre": bocina.nombre,
            "estado": bocina.estado_actual
        })

    # HISTORIAL DE LED
    eventos_led = EventoLed.objects.select_related("led")[:20]

    # HISTORIAL DE BOCINAS
    eventos_bocina = EventoBocina.objects.select_related("bocina")[:20]

    historial = []

    for evento in eventos_led:
        historial.append({
            "fecha": timezone.localtime(evento.fecha).strftime("%d/%m/%Y %H:%M:%S"),
            "orden": evento.fecha.timestamp(),
            "dispositivo": evento.led.nombre,
            "estado": evento.estado,
            "origen": evento.origen
        })

    for evento in eventos_bocina:
        historial.append({
            "fecha": timezone.localtime(evento.fecha).strftime("%d/%m/%Y %H:%M:%S"),
            "orden": evento.fecha.timestamp(),
            "dispositivo": evento.bocina.nombre,
            "estado": evento.estado,
            "origen": evento.origen
        })

    # Ordenar eventos más recientes primero
    historial.sort(
        key=lambda evento: evento["orden"],
        reverse=True
    )

    return JsonResponse({
        "leds": datos_leds,
        "bocinas": datos_bocinas,
        "historial": historial[:20]
    })


@require_POST
def controlar_led(request, codigo):
    # Buscar LED en MySQL
    led = get_object_or_404(Led, codigo=codigo)

    # Recibir información de JavaScript
    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({
            "ok": False,
            "error": "JSON inválido"
        }, status=400)

    # Obtener el estado solicitado
    nuevo_estado = datos.get("estado")

    if type(nuevo_estado) is not bool:
        return JsonResponse({
            "ok": False,
            "error": "Estado inválido"
        }, status=400)

    # Crear comando pendiente para Arduino
    comando = ComandoLed.objects.create(
        led=led,
        estado_deseado=nuevo_estado,
        estado="PENDIENTE"
    )

    return JsonResponse({
        "ok": True,
        "comando_id": comando.id,
        "led": led.codigo,
        "estado_deseado": nuevo_estado
    })


@require_POST
def controlar_bocina(request, codigo):
    bocina = get_object_or_404(Bocina, codigo=codigo)

    try:
        datos = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "ok": False,
            "error": "JSON inválido",
        }, status=400)

    nuevo_estado = datos.get("estado")

    if not isinstance(nuevo_estado, bool):
        return JsonResponse({
            "ok": False,
            "error": "Estado inválido",
        }, status=400)

    comando = ComandoBocina.objects.create(
        bocina=bocina,
        estado_deseado=nuevo_estado,
        estado="PENDIENTE"
    )

    return JsonResponse({
        "ok": True,
        "comando_id": comando.id,
        "bocina": bocina.codigo,
        "estado_deseado": nuevo_estado,
    })
