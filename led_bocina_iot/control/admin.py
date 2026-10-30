from django.contrib import admin

from .models import Bocina, ComandoBocina, ComandoLed, EventoBocina, EventoLed, Led


# Para el led
@admin.register(Led)
class LedAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "codigo",
        "pin",
        "color",
        "estado_actual",
        "actualizado_en",
    )

    list_filter = (
        "estado_actual",
        "color",
    )

    search_fields = (
        "nombre",
        "codigo",
    )


@admin.register(EventoLed)
class EventoLedAdmin(admin.ModelAdmin):
    list_display = (
        "led",
        "estado",
        "origen",
        "fecha",
    )

    list_filter = (
        "estado",
        "origen",
        "led",
    )


@admin.register(ComandoLed)
class ComandoLedAdmin(admin.ModelAdmin):
    list_display = (
        "led",
        "estado_deseado",
        "estado",
        "creado_en",
        "procesado_en",
    )

    list_filter = (
        "estado",
        "estado_deseado",
    )


# Para la bocina
@admin.register(Bocina)
class BocinaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "codigo",
        "pin",
        "estado_actual",
        "actualizado_en",
    )

    list_filter = ("estado_actual",)

    search_fields = (
        "nombre",
        "codigo",
    )


@admin.register(EventoBocina)
class EventoBocinaAdmin(admin.ModelAdmin):
    list_display = (
        "bocina",
        "estado",
        "origen",
        "fecha",
    )

    list_filter = (
        "estado",
        "origen",
        "bocina",
    )


@admin.register(ComandoBocina)
class ComandoBocinaAdmin(admin.ModelAdmin):  # Se corrigió error tipográfico en el nombre de la clase
    list_display = (
        "bocina",
        "estado_deseado",
        "estado",
        "creado_en",
        "procesado_en",
    )

    list_filter = (
        "estado",
        "estado_deseado",
    )
