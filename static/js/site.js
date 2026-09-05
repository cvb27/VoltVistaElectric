/**
 * Tracking de eventos GA4 para VoltVista.
 * Registra las 3 conversiones principales: llamadas, WhatsApp y estimados.
 * Cada listener es silencioso si gtag no está cargado (GA4_ID vacío en .env).
 */

// Helper: dispara evento solo si gtag está definido (cuando GA4_ID falta, no existe).
function trackEvent(name, label) {
  if (typeof gtag !== 'function') return;
  gtag('event', name, {
    event_category: 'conversion',
    event_label: label,
  });
}

// Conversión: clic en enlaces tel: — llamada directa al negocio.
document.querySelectorAll('a[href^="tel:"]').forEach(function (el) {
  el.addEventListener('click', function () {
    trackEvent('phone_call', el.getAttribute('href'));
  });
});

// Conversión: clic en WhatsApp — inicio de conversación por mensajería.
document.querySelectorAll('a[href*="wa.me"]').forEach(function (el) {
  el.addEventListener('click', function () {
    trackEvent('whatsapp_contact', el.getAttribute('href'));
  });
});

// Conversión: submit del formulario de estimado — lead capturado.
// Nota: también disparamos estimate_submitted al cargar estimate_success.html,
// así captamos la conversión aunque el navegador cancele el beacon durante la navegación.
var estimateForm = document.querySelector('form#estimate-form');
if (estimateForm) {
  estimateForm.addEventListener('submit', function () {
    trackEvent('estimate_request', 'estimate_form_submit');
  });
}

// Conversión: lead completado — dispara al cargar estimate_success.html.
// Backup del submit listener por si la navegación canceló el beacon.
if (document.body.dataset.page === 'estimate-success') {
  trackEvent('estimate_submitted', 'estimate_success_page_view');
}

// Nav: transparente sobre el hero, oscuro al scrollear fuera de él (solo home).
// IntersectionObserver observa el .hero; cuando sale del viewport, añade .nav-scrolled.
if (document.body.dataset.page === 'home') {
  var hero = document.querySelector('.hero');
  var navbar = document.querySelector('.navbar');
  if (hero && navbar) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        navbar.classList.toggle('nav-scrolled', !entry.isIntersecting);
      });
    }, { threshold: 0, rootMargin: '-80px 0px 0px 0px' });
    observer.observe(hero);
  }
}

// Vídeo de la sección "Expert Electrical Work": 2,4 MB que antes se
// descargaban al cargar la página, porque el elemento llevaba autoplay
// aunque está muy por debajo del pliegue. Eso ocupaba el canal y retrasaba
// el LCP del hero, que pesa 45 KB.
//
// Ahora la descarga arranca cuando la sección se acerca a la pantalla.
// El rootMargin de 200px la adelanta un poco para que ya esté reproduciendo
// cuando el usuario llegue, sin pagar nada al cargar la página.
var lazyVideo = document.querySelector('.js-lazy-video');
if (lazyVideo && lazyVideo.dataset.src && 'IntersectionObserver' in window) {
  var videoObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      var v = entry.target;
      v.src = v.dataset.src;
      // play() devuelve una promesa que el navegador puede rechazar. Se
      // captura para no dejar un error suelto en consola: si no reproduce,
      // se queda el póster, que es un fallback perfectamente válido.
      var intento = v.play();
      if (intento && intento.catch) { intento.catch(function () {}); }
      videoObserver.unobserve(v);
    });
  }, { rootMargin: '200px' });
  videoObserver.observe(lazyVideo);
}

// Bloque "Why Orlando Homes Need Surge Protection" de la landing de surge.
// El HTML lo trae con `open`: así en escritorio se lee entero y, si este JS
// no llegara a ejecutarse, seguiría visible en todas partes — el fallo seguro.
// En móvil se cierra, porque sus cuatro párrafos empujaban los precios fuera
// de la primera pantalla, que es lo que el visitante viene a ver.
var whySurge = document.querySelector('.why-surge');
if (whySurge && window.matchMedia('(max-width: 767.98px)').matches) {
  whySurge.open = false;
}
