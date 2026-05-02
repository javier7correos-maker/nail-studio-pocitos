const navToggle = document.querySelector('.nav-toggle');
const siteNav = document.querySelector('.site-nav');
const formMode = "whatsapp_capture";
const whatsappBaseUrl = "https://wa.me/59891234567";
const contactEmail = "";

if (navToggle && siteNav) {
  navToggle.addEventListener('click', () => {
    const expanded = navToggle.getAttribute('aria-expanded') === 'true';
    navToggle.setAttribute('aria-expanded', String(!expanded));
    siteNav.classList.toggle('open');
  });

  siteNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      navToggle.setAttribute('aria-expanded', 'false');
      siteNav.classList.remove('open');
    });
  });
}

const form = document.querySelector('.contact-form');
const statusNode = document.getElementById('form-status');

function buildLeadMessage() {
  const data = new FormData(form);
  const nombre = String(data.get('nombre') || '').trim();
  const contacto = String(data.get('contacto') || '').trim();
  const detalle = String(data.get('detalle') || '').trim();
  const mensaje = String(data.get('mensaje') || '').trim();
  const blocks = [
    nombre ? `Nombre: ${nombre}` : '',
    contacto ? `Contacto: ${contacto}` : '',
    detalle ? `Detalle: ${detalle}` : '',
    mensaje ? `Mensaje: ${mensaje}` : ''
  ].filter(Boolean);
  return blocks.join('\n');
}

if (form && formMode !== 'formspree') {
  form.addEventListener('submit', (event) => {
    event.preventDefault();

    if (formMode === 'whatsapp_capture' && whatsappBaseUrl) {
      const url = `${whatsappBaseUrl}?text=${encodeURIComponent(buildLeadMessage())}`;
      if (statusNode) {
        statusNode.hidden = false;
        statusNode.textContent = 'Abriendo WhatsApp para enviar tu consulta.';
      }
      window.open(url, '_blank', 'noopener');
      return;
    }

    if (formMode === 'mailto_capture' && contactEmail) {
      const subject = encodeURIComponent('Consulta desde la web');
      const body = encodeURIComponent(buildLeadMessage());
      window.location.href = `mailto:${contactEmail}?subject=${subject}&body=${body}`;
      return;
    }

    if (statusNode) {
      statusNode.hidden = false;
      statusNode.textContent = 'Falta configurar un canal de contacto real en esta instalacion.';
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  if (typeof gsap === 'undefined') {
    return;
  }

  gsap.fromTo('.eyebrow', { opacity: 0, y: 18 }, { opacity: 1, y: 0, duration: 0.55, ease: 'power2.out' });
  gsap.fromTo('h1', { opacity: 0, y: 34 }, { opacity: 1, y: 0, duration: 0.8, delay: 0.12, ease: 'power2.out' });
  gsap.fromTo('.hero-subtitle', { opacity: 0, y: 24 }, { opacity: 1, y: 0, duration: 0.7, delay: 0.28, ease: 'power2.out' });
  gsap.fromTo('.hero-actions', { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.55, delay: 0.42, ease: 'power2.out' });
  gsap.fromTo('.metric-strip li', { opacity: 0, y: 14 }, { opacity: 1, y: 0, duration: 0.45, delay: 0.52, stagger: 0.08, ease: 'power2.out' });
  gsap.fromTo('.hero-visual', { opacity: 0, scale: 0.97 }, { opacity: 1, scale: 1, duration: 0.95, delay: 0.22, ease: 'power2.out' });

  if (typeof ScrollTrigger === 'undefined') {
    return;
  }

  gsap.registerPlugin(ScrollTrigger);
  gsap.utils.toArray('.section-head, .info-card, .step-card, .quote-card, .gallery-card, .benefit-item, .faq-item, .contact-form').forEach((element) => {
    gsap.fromTo(element, { opacity: 0, y: 24 }, {
      opacity: 1,
      y: 0,
      duration: 0.58,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: element,
        start: 'top 88%',
        once: true
      }
    });
  });
});
