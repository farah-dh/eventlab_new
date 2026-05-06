<template>
  <div class="footer-wrapper">
    <!-- Footer principal -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-4 py-2">
      <!-- Gauche : Branding -->
      <div class="d-flex align-center gap-2">
        <VIcon icon="tabler-ticket" color="primary" size="20" />
        <span class="text-body-2 text-medium-emphasis">
          &copy; {{ new Date().getFullYear() }}
          <strong class="text-primary">EventLab</strong>
          — Plateforme de réservation d'événements en Tunisie
        </span>
      </div>

      <!-- Droite : Liens & Contact -->
      <div class="d-md-flex align-center gap-x-4 d-none">
        <a href="mailto:contact@eventlab.tn" class="footer-link">
          <VIcon icon="tabler-mail" size="16" class="me-1" />
          contact@eventlab.tn
        </a>
        <span class="text-disabled">|</span>
        <a href="tel:+21658271569" class="footer-link">
          <VIcon icon="tabler-phone" size="16" class="me-1" />
          +216 58 271 569
        </a>
        <span class="text-disabled">|</span>
        <a href="https://facebook.com" target="_blank" rel="noopener noreferrer" class="footer-icon">
          <VIcon icon="tabler-brand-facebook" size="18" />
        </a>
        <a href="https://instagram.com" target="_blank" rel="noopener noreferrer" class="footer-icon">
          <VIcon icon="tabler-brand-instagram" size="18" />
        </a>
        <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" class="footer-icon">
          <VIcon icon="tabler-brand-linkedin" size="18" />
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped>
.footer-link {
  display: inline-flex;
  align-items: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-decoration: none;
  font-size: 0.8125rem;
  transition: color 0.2s;
}

.footer-link:hover {
  color: rgb(var(--v-theme-primary));
}

.footer-icon {
  display: inline-flex;
  align-items: center;
  color: rgba(var(--v-theme-on-surface), 0.5);
  transition: color 0.2s;
}

.footer-icon:hover {
  color: rgb(var(--v-theme-primary));
}
</style>