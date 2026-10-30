from django.db import models

# Create your models here.
class Bocina(models.Model):
    nombre = models.CharField(max_length=50)
    codigo = models.CharField(max_length=20, unique=True)
    pin = models.PositiveBigIntegerField()
    estado_actual = models.BooleanField(default=False)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nombre

class EventoBocina(models.Model):
    ORIGENES = [
        ("WEB", "Pagina web"),
        ("BOTON", "Botón físico"),
        ("SISTEMA", "Sistema"),
    ]
    bocina = models.ForeignKey(Bocina,on_delete=models.CASCADE,related_name="eventos")
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
        return(f"{self.bocina.nombre} - "
               f"{estado_texto}")


class ComandoBocina(models.Model):
    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("ENVIADO", "Enviado"),
        ("CONFIRMADO", "Confirmado"),
        ("ERROR", "Error"),       
    ]
    bocina = models.ForeignKey(Bocina,on_delete=models.CASCADE,related_name="comandos")
    estado_deseado = models.BooleanField()
    estado =  models.CharField(max_length=20, choices=ESTADOS, default="PENDIENTE")
    creado_en = models.DateTimeField(auto_now_add=True)
    procesado_en=models.DateTimeField(null=True,blank=True)
    mesaje_error = models.TextField(blank=True)
        

            
    