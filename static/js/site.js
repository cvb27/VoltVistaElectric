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
