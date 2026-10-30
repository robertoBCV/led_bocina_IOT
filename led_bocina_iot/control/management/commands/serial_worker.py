import time
import serial

from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone

from control.models import Led, EventoLed, ComandoLed
from control.models import Bocina, EventoBocina, ComandoBocina


class Command(BaseCommand):
    help = "Comunicación serial entre Django y Arduino Mega-UNO"

    # ==================================================
    # ARGUMENTOS
    def add_arguments(self, parser):
        parser.add_argument(
            "--port",
            type=str,
          
            help="Puerto serial del Arduino"
        )
        parser.add_argument(
            "--baudrate",
            type=int,
            default=9600,
            help="Velocidad serial"
        )

    # ==================================================
    # EJECUCIÓN PRINCIPAL
    def handle(self, *args, **options):
        puerto = options["port"]
        baudrate = options["baudrate"]
        self.stdout.write("--------------------------------")
        self.stdout.write("Worker IoT iniciado")
        self.stdout.write(f"Puerto: {puerto}")
        self.stdout.write(f"Baudrate: {baudrate}")
        self.stdout.write("--------------------------------")
        
        try:
            arduino = serial.Serial(port=puerto, baudrate=baudrate, timeout=0.1)
        except serial.SerialException as error:
            self.stderr.write(self.style.ERROR(f"No se pudo abrir {puerto}"))
            self.stderr.write(str(error))
            return

        # Cuando se abre el puerto, Arduino normalmente se reinicia.
        self.stdout.write("Esperando al Arduino...")
        time.sleep(2)

        # Limpiamos cualquier basura anterior que pudiera existir en el buffer.
        # arduino.reset_input_buffer()

        self.stdout.write(self.style.SUCCESS("Arduino conectado correctamente."))

        self.buffer_serial = b""

        try:
            while True:
                close_old_connections()
                # 1. LEER INFORMACIÓN DEL ARDUINO
                self.leer_arduino(arduino)
                # 2. BUSCAR COMANDOS DE LA WEB
                self.enviar_comando_pendiente(arduino)

                time.sleep(0.05)

        except KeyboardInterrupt:
            self.stdout.write("\nDeteniendo worker...")

        finally:
            if arduino.is_open:
                arduino.close()

            self.stdout.write(self.style.SUCCESS("Puerto serial cerrado."))

    # ==================================================
    # LEER ARDUINO
    def leer_arduino(self, arduino):
        disponibles = arduino.in_waiting

        if disponibles == 0:
            return

        nuevos_datos = arduino.read(disponibles)
        self.buffer_serial += nuevos_datos

        while b"\n" in self.buffer_serial:
            linea_bytes, self.buffer_serial = self.buffer_serial.split(b"\n", 1)

            linea = linea_bytes.decode(
                "utf-8",
                errors="replace"
            ).strip()

            if not linea:
                continue

            self.stdout.write(f"Arduino -> {linea}")
            self.procesar_linea(linea)

        # Evitar crecimiento ilimitado por mensajes dañados
        if len(self.buffer_serial) > 1024:
            self.stderr.write(
                "Mensaje serial demasiado largo o sin salto de línea"
            )
            self.buffer_serial = b""

    # ==================================================
    # PROCESAR MENSAJES QUE ENVÍA ARDUINO
    # ==================================================
    def procesar_linea(self, linea):
        partes = [p.strip() for p in linea.split(",")]

        # Arduino envia:
        # ESTADO,CUARTO01,1
        # EVENTO,CUARTO01,1,BOTON
        # EVENTO,CUARTO01,1,WEB

        tipo = partes[0]

        if tipo not in ("ESTADO", "EVENTO"):
            self.stderr.write(f"Mensaje no reconocido: {linea}")
            return

        if tipo == "ESTADO" and len(partes) != 3:
            self.stderr.write("Formato ESTADO incorrecto")
            return

        if tipo == "EVENTO" and len(partes) != 4:
            self.stderr.write("Formato EVENTO incorrecto")
            return

        codigo = partes[1]

        if partes[2] not in ("0", "1"):
            self.stderr.write("Estado inválido")
            return

        estado = partes[2] == "1"
        origen = partes[3] if tipo == "EVENTO" else "SISTEMA"

        if origen not in ("WEB", "BOTON", "SISTEMA"):
            self.stderr.write("Origen inválido")
            return

        # BUSCAR DISPOSITIVO
        led = Led.objects.filter(codigo=codigo).first()
        bocina = Bocina.objects.filter(codigo=codigo).first()

        if led and bocina:
            self.stderr.write(f"Código duplicado: {codigo}")
            return

        if led:
            dispositivo = led
        elif bocina:
            dispositivo = bocina
        else:
            self.stderr.write(f"Dispositivo no registrado: {codigo}")
            return

        # ACTUALIZAR MYSQL
        dispositivo.estado_actual = estado
        dispositivo.save(update_fields=["estado_actual", "actualizado_en"])

        # GUARDAR EVENTO
        if tipo == "EVENTO":
            if led:
                EventoLed.objects.create(
                    led=led,
                    estado=estado,
                    origen=origen
                )
            else:
                EventoBocina.objects.create(
                    bocina=bocina,
                    estado=estado,
                    origen=origen
                )

        # CONFIRMAR COMANDOS DE LA WEB
        # ESTADO también puede ser respuesta de Arduino
        # cuando el dispositivo ya tenía el estado solicitado.
        if origen == "WEB" or tipo == "ESTADO":
            self.confirmar_comando(dispositivo, estado)

        self.stdout.write(f"{codigo}: {'ON' if estado else 'OFF'}")

    # ==================================================
    # ENVIAR COMANDO PENDIENTE
    def enviar_comando_pendiente(self, arduino):
        # Buscar comando LED
        comando_led = (
            ComandoLed.objects
            .filter(estado="PENDIENTE")
            .order_by("id")
            .first()
        )

        # Buscar comando bocina
        comando_bocina = (
            ComandoBocina.objects
            .filter(estado="PENDIENTE")
            .order_by("id")
            .first()
        )

        if comando_led:
            comando = comando_led
            codigo = comando.led.codigo
        elif comando_bocina:
            comando = comando_bocina
            codigo = comando.bocina.codigo
        else:
            return

        valor = 1 if comando.estado_deseado else 0
        mensaje = f"{codigo}:{valor}\n"

        try:
            arduino.write(mensaje.encode("utf-8"))
            arduino.flush()

            comando.estado = "ENVIADO"
            comando.procesado_en = timezone.now()
            comando.save()

            self.stdout.write(f"Django -> {mensaje.strip()}")

        except serial.SerialException as error:
            comando.estado = "ERROR"
            comando.mensaje_error = str(error)
            comando.procesado_en = timezone.now()
            comando.save()

    # ==================================================
    # CONFIRMAR COMANDO
    def confirmar_comando(self, dispositivo, estado):

        if isinstance(dispositivo, Led):
            consulta = ComandoLed.objects.filter(
                led=dispositivo
            )
        else:
            consulta = ComandoBocina.objects.filter(
                bocina=dispositivo
            )

        comando = consulta.filter(
            estado="ENVIADO",
            estado_deseado=estado
        ).order_by("-id").first()

        if comando:
            comando.estado = "CONFIRMADO"
            comando.procesado_en = timezone.now()

            comando.save(
                update_fields=["estado", "procesado_en"]
            )

            self.stdout.write(
                f"Confirmado: {dispositivo.codigo} -> {int(estado)}"
            )