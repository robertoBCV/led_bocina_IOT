from django.db import models

# Create your models here.
class Led(models.Model):
    nombre = models.CharField(max_length=50)
    codigo = models.CharField(max_length=20, unique=True)
    pin = models.PositiveBigIntegerField()
    color = models.CharField(max_length=20)
    color_hex = models.CharField(max_length=10, default="#ffffff")
    estado_actual = models.BooleanField(default=False)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre

class EventoLed(models.Model):
    ORIGENES = [
        ("WEB", "Pagina web"),
        ("BOTON", "Botón físico"),
        ("SISTEMA", "Sistema"),
    ]
    led = models.ForeignKey(Led,on_delete=models.CASCADE,related_name="eventos")
    estado = models.BooleanField()
    origen = models.CharField(max_length=20, choices=ORIGENES)
    fecha = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["-fecha"]
        
    def __str__(self):
        estado_texto = (
            "ENCENDIDO"
            if self.estado
            else "APAGADO"
        )
        return(f"{self.led.nombre} - "
               f"{estado_texto}")


class ComandoLed(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("ENVIADO", "Enviado"),
        ("CONFIRMADO", "Confirmado"),
        ("ERROR", "Error"),       
    ]
    led = models.ForeignKey(Led,on_delete=models.CASCADE,related_name="comandos")
    estado_deseado = models.BooleanField()
    estado =  models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")
    creado_en = models.DateTimeField(auto_now_add=True)
    procesado_en=models.DateTimeField(null=True,blank=True)
    mesaje_error = models.TextField(blank=True)
        
    class Meta:
        ordering = ["-creado_en"]
            
    def __str__(self):
        estado_texto = (
                "ON"
                if self.estado_deseado
                else "OFF"
        )
        return( f"{self.led.nombre} "
                f"{self.estado_deseado}"
                f"{self.estado}")