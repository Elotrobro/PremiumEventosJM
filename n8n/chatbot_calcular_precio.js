// ═══════════════════════════════════════════════════════════════════════
// Herramienta "calcular_precio" del chatbot (nodo Code Tool del workflow
// "Chatbot" en n8n). Se copia y pega tal cual en el campo JavaScript de
// ese nodo.
//
// Es la misma tabla y el mismo cálculo de calcular_precio_estimado en
// Bd_PremiumEventos/views.py y de core/static/js/modal.js: si se cambia un
// precio allá, hay que cambiarlo también aquí (y volver a pegarlo en n8n).
//
// n8n le pasa a la herramienta lo que escribió el modelo en la variable
// `query` (debería ser solo el número de invitados) y el modelo recibe el
// texto que devuelve este código.
// ═══════════════════════════════════════════════════════════════════════
const TABLA_PAQUETES = [
  { invitados: 20, precio: 1800000 },
  { invitados: 30, precio: 2600000 },
  { invitados: 40, precio: 3200000 },
  { invitados: 50, precio: 3900000 },
  { invitados: 60, precio: 4500000 },
  { invitados: 70, precio: 4900000 },
  { invitados: 80, precio: 5440000 },
  { invitados: 90, precio: 5850000 },
  { invitados: 100, precio: 5800000 },
];
const TARIFA_INVITADO_ADICIONAL = 58000;

// Si llega un rango ("entre 50 y 60") se toma el número más alto.
// "1.200" es mil doscientos (punto de miles), no 1 y 200.
const numeros = (String(query).replace(/(\d)\.(?=\d{3})/g, "$1").match(/\d+/g) || []).map(Number);
const n = numeros.length ? Math.max(...numeros) : 0;
if (!n || n <= 0) {
  return 'No entendí el número de invitados. Pídele al cliente un número aproximado de invitados.';
}

let precio;
const primero = TABLA_PAQUETES[0];
const ultimo = TABLA_PAQUETES[TABLA_PAQUETES.length - 1];
if (n <= primero.invitados) {
  precio = primero.precio;
} else if (n >= ultimo.invitados) {
  precio = ultimo.precio + (n - ultimo.invitados) * TARIFA_INVITADO_ADICIONAL;
} else {
  for (let i = 0; i < TABLA_PAQUETES.length - 1; i++) {
    const inferior = TABLA_PAQUETES[i];
    const superior = TABLA_PAQUETES[i + 1];
    if (n > inferior.invitados && n <= superior.invitados) {
      const proporcion = (n - inferior.invitados) / (superior.invitados - inferior.invitados);
      precio = Math.round((inferior.precio + proporcion * (superior.precio - inferior.precio)) / 1000) * 1000;
      break;
    }
  }
}

const formateado = '$' + precio.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
return `Estimado base para ${n} invitados: ${formateado} COP. Es un valor aproximado; ` +
       'el precio final depende del tipo de evento, la fecha y los servicios elegidos.';
