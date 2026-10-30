const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;

// ==========================================
// CAMBIAR ESTADO DESDE WEB (LED O BOCINA)
// ==========================================
async function cambiarEstadoDispositivo(tipo, codigo) {
  // Busca el botón dinámicamente según sea led o bocina
  const boton = document.getElementById(`boton-${tipo}-${codigo}`);
  if (!boton) return;

  const estadoActual = boton.dataset.estado.trim() === "1";
  const nuevoEstado = !estadoActual;

  boton.disabled = true;
  boton.textContent = "Enviando...";

  try {
    // Apunta a la API correspondiente: /api/led/ o /api/bocina/
    const respuesta = await fetch(`/api/${tipo}/${codigo}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify({ estado: nuevoEstado })
    });

    const datos = await respuesta.json();

    if (!respuesta.ok || !datos.ok) {
      throw new Error(datos.error || "No se pudo enviar el comando.");
    }

    /*
    No cambiamos directamente el estado visual.
    Esperamos a que Arduino confirme y después /api/estado/ nos entregue el estado real.
    */
    setTimeout(actualizarSistema, 250);

  } catch (error) {
    console.error(error);
    alert("No se pudo enviar el comando.");
    boton.disabled = false;
    actualizarSistema();
  }
}

// ==========================================
// OBTENER ESTADO DEL SISTEMA
// ==========================================
async function actualizarSistema() {
  try {
    const respuesta = await fetch("/api/estado/", {
      cache: "no-store"
    });

    if (!respuesta.ok) {
      throw new Error("No se pudo consultar el sistema.");
    }

    const datos = await respuesta.json();

    // Actualiza componentes visuales
    actualizarComponentes("led", datos.leds);
    actualizarComponentes("bocina", datos.bocinas);
    
    // Tu backend devuelve 'historial', corregido el mapeo aquí
    actualizarHistorial(datos.historial || datos.eventos || []);
    
    // Envía ambos arreglos para calcular los totales unificados del resumen
    actualizarResumen(datos.leds, datos.bocinas);

  } catch (error) {
    console.error("Error actualizando dashboard:", error);
  }
}

// ==========================================
// ACTUALIZAR INTERFAZ (LEDS Y BOCINAS)
// ==========================================
function actualizarComponentes(tipo, listaDispositivos) {
  if (!listaDispositivos) return;

  listaDispositivos.forEach(dispositivo => {
    const boton = document.getElementById(`boton-${tipo}-${dispositivo.codigo}`);
    const badge = document.getElementById(`badge-${dispositivo.codigo}`);
    const bombilla = document.getElementById(`bombilla-${dispositivo.codigo}`);

    if (!boton || !badge || !bombilla) return;

    boton.dataset.estado = dispositivo.estado ? "1" : "0";
    boton.disabled = false;

    if (dispositivo.estado) {
      badge.textContent = "ENCENDIDO";
      badge.classList.add("badge-on");
      badge.classList.remove("badge-off");
      bombilla.classList.add("bombilla-on");

      boton.textContent = "Apagar";
      boton.classList.add("boton-apagar");
      boton.classList.remove("boton-encender");
    } else {
      badge.textContent = "APAGADO";
      badge.classList.add("badge-off");
      badge.classList.remove("badge-on");
      bombilla.classList.remove("bombilla-on");

      boton.textContent = "Encender";
      boton.classList.add("boton-encender");
      boton.classList.remove("boton-apagar");
    }
  });
}

// ==========================================
// HISTORIAL
// ==========================================
function actualizarHistorial(eventos) {
  const tbody = document.getElementById("historial");
  if (!tbody) return;

  tbody.innerHTML = "";

  if (!eventos || eventos.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4">Todavía no existen eventos registrados.</td>
      </tr>
    `;
    return;
  }

  eventos.forEach(evento => {
    const fila = document.createElement("tr");
    const estadoClase = evento.estado ? "on" : "off";
    const estadoTexto = evento.estado ? "ENCENDIDO" : "APAGADO";
    const origen = evento.origen === "BOTON" ? "BOTÓN" : evento.origen;
    
    // Soporta tanto evento.dispositivo (enviado por tu JSON de Django) como estructuras previas
    const nombreDispositivo = evento.dispositivo || evento.led || "Dispositivo";

    fila.innerHTML = `
      <td>${evento.fecha}</td>
      <td>${nombreDispositivo}</td>
      <td>
        <span class="estado-tabla ${estadoClase}">${estadoTexto}</span>
      </td>
      <td>
        <span class="origen">${origen}</span>
      </td>
    `;
    tbody.appendChild(fila);
  });
}

// ==========================================
// RESUMEN UNIFICADO
// ==========================================
function actualizarResumen(leds = [], bocinas = []) {
  const total = leds.length + bocinas.length;
  
  const encendidos = 
    leds.filter(l => l.estado).length + 
    bocinas.filter(b => b.estado).length;

  const apagados = total - encendidos;

  const domTotal = document.getElementById("total-dispositivos");
  const domEncendidos = document.getElementById("total-encendidos");
  const domApagados = document.getElementById("total-apagados");

  if (domTotal) domTotal.textContent = total;
  if (domEncendidos) domEncendidos.textContent = encendidos;
  if (domApagados) domApagados.textContent = apagados;
}

// ==========================================
// ASIGNACIÓN DE EVENTOS DE CLIC (DELEGACIÓN)
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
  document.body.addEventListener("click", (e) => {
    const boton = e.target.closest(".boton-led");
    if (boton) {
      const tipo = boton.dataset.tipo; // "led" o "bocina"
      const codigo = boton.dataset.codigo;
      if (tipo && codigo) {
        cambiarEstadoDispositivo(tipo, codigo);
      }
    }
  });

  // Primera carga y ciclo automático de actualización
  actualizarSistema();
  setInterval(actualizarSistema, 1000);
});
