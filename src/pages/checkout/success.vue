<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, onMounted, computed } from 'vue'
import QRCode from 'qrcode'

const router = useRouter()

const order     = ref<any>(null)
const qrDataUrl = ref('')
const isReady   = ref(false)
const showAnim  = ref(false)

onMounted(async () => {
  const stored = localStorage.getItem('last_order')
  if (!stored) { router.push('/'); return }

  order.value = JSON.parse(stored)

  // Générer le QR code avec les infos de la commande
  const qrContent = JSON.stringify({
    orderNumber:  order.value.orderNumber,
    event:        order.value.items?.[0]?.title || 'EventLab',
    customer:     `${order.value.customer?.firstname} ${order.value.customer?.lastname}`,
    email:        order.value.customer?.email,
    date:         order.value.date,
    total:        order.value.total,
    tickets:      order.value.items?.reduce((acc: number, i: any) => acc + i.quantity, 0) || 1,
  })

  try {
    qrDataUrl.value = await QRCode.toDataURL(qrContent, {
      width: 220,
      margin: 2,
      color: { dark: '#3d2c35', light: '#ffffff' },
      errorCorrectionLevel: 'H',
    })
  } catch {}

  isReady.value = true
  setTimeout(() => showAnim.value = true, 100)
})

const totalTickets = computed(() =>
  order.value?.items?.reduce((acc: number, i: any) => acc + i.quantity, 0) || 1
)

const formatDate = (d: string) => {
  if (!d) return ''
  return new Date(d).toLocaleDateString('fr-FR', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
}
const formatTime = (d: string) => {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}
const formatOrderDate = (d: string) => {
  if (!d) return ''
  return new Date(d).toLocaleString('fr-FR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const downloadTicket = () => {
  const el = document.getElementById('ticket-print')
  if (!el) return
  window.print()
}

const goHome = () => router.push('/')
const goEvents = () => router.push('/')
</script>

<template>
  <div class="sp">

    <!-- NAV -->
    <nav class="sp-nav">
      <div class="sp-nav__inner">
        <div class="sp-logo" @click="goHome">
          <div class="sp-logo__mark">E</div>
          <span class="sp-logo__name">EventLab</span>
        </div>
      </div>
    </nav>

    <div v-if="!isReady" class="sp-loading">
      <div class="sp-loading__ring"></div>
      <p>Génération de votre billet…</p>
    </div>

    <div v-else class="sp-page" :class="{ 'sp-page--in': showAnim }">

      <!-- SUCCESS HEADER -->
      <div class="sp-hero">
        <div class="sp-hero__rings">
          <div class="sp-ring sp-ring--1"></div>
          <div class="sp-ring sp-ring--2"></div>
          <div class="sp-ring sp-ring--3"></div>
        </div>
        <div class="sp-hero__check">
          <svg width="46" height="46" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
        <h1 class="sp-hero__title">Paiement confirmé !</h1>
        <p class="sp-hero__sub">
          Votre commande <strong>{{ order?.orderNumber }}</strong> a été traitée avec succès.
          <br>Un e-mail de confirmation a été envoyé à <strong>{{ order?.customer?.email }}</strong>
        </p>
        <div class="sp-hero__meta">
          <div class="sp-hero__tag">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>
            </svg>
            {{ formatOrderDate(order?.date) }}
          </div>
          <div class="sp-hero__tag">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 12V22H4V12"/><path d="M22 7H2v5h20V7z"/><path d="M12 22V7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/>
            </svg>
            {{ totalTickets }} billet{{ totalTickets > 1 ? 's' : '' }}
          </div>
          <div class="sp-hero__tag sp-hero__tag--green">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {{ order?.total?.toFixed(2) }} DT payés
          </div>
        </div>
      </div>

      <!-- TICKET(S) -->
      <div class="sp-tickets" id="ticket-print">
        <div
          v-for="(item, idx) in order?.items"
          :key="idx"
          class="sp-ticket"
        >
          <!-- Ticket top -->
          <div class="sp-ticket__main">
            <div class="sp-ticket__left">

              <!-- Event badge -->
              <div class="sp-ticket__event-badge">
                <div class="sp-ticket__date-block">
                  <span class="sp-ticket__day">
                    {{ new Date(item.date).getDate().toString().padStart(2,'0') }}
                  </span>
                  <span class="sp-ticket__month">
                    {{ new Date(item.date).toLocaleDateString('fr-FR',{month:'short'}).toUpperCase().replace('.','') }}
                  </span>
                  <span class="sp-ticket__year">
                    {{ new Date(item.date).getFullYear() }}
                  </span>
                </div>
                <div class="sp-ticket__event-info">
                  <div class="sp-ticket__label">ÉVÉNEMENT</div>
                  <div class="sp-ticket__event-name">{{ item.title }}</div>
                  <div v-if="item.location" class="sp-ticket__location">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                    </svg>
                    {{ item.location }}
                  </div>
                  <div class="sp-ticket__time">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                    </svg>
                    {{ formatTime(item.date) }}
                  </div>
                </div>
              </div>

              <!-- Divider -->
              <div class="sp-ticket__divider">
                <div class="sp-ticket__notch sp-ticket__notch--left"></div>
                <div class="sp-ticket__dashes"></div>
                <div class="sp-ticket__notch sp-ticket__notch--right"></div>
              </div>

              <!-- Customer + order info -->
              <div class="sp-ticket__details">
                <div class="sp-ticket__detail-col">
                  <div class="sp-ticket__detail-label">TITULAIRE</div>
                  <div class="sp-ticket__detail-value">
                    {{ order.customer?.firstname }} {{ order.customer?.lastname }}
                  </div>
                </div>
                <div class="sp-ticket__detail-col">
                  <div class="sp-ticket__detail-label">COMMANDE</div>
                  <div class="sp-ticket__detail-value">{{ order.orderNumber }}</div>
                </div>
                <div class="sp-ticket__detail-col">
                  <div class="sp-ticket__detail-label">QUANTITÉ</div>
                  <div class="sp-ticket__detail-value">{{ item.quantity }} billet{{ item.quantity > 1 ? 's' : '' }}</div>
                </div>
                <div class="sp-ticket__detail-col">
                  <div class="sp-ticket__detail-label">MONTANT</div>
                  <div class="sp-ticket__detail-value sp-ticket__detail-value--pink">
                    {{ (item.price * item.quantity).toFixed(2) }} DT
                  </div>
                </div>
              </div>
            </div>

            <!-- QR Code side -->
            <div class="sp-ticket__qr-side">
              <div class="sp-ticket__qr-wrap">
                <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR Code" class="sp-ticket__qr-img" />
                <div v-else class="sp-ticket__qr-placeholder">QR</div>
              </div>
              <div class="sp-ticket__qr-label">Scanner pour valider</div>
              <div class="sp-ticket__seat">
                <div class="sp-ticket__seat-label">BILLET</div>
                <div class="sp-ticket__seat-num">#{{ String(Number(idx) + 1).padStart(3, '0') }}</div>
              </div>
            </div>
          </div>

          <!-- Barcode footer -->
          <div class="sp-ticket__barcode">
            <div class="sp-ticket__bars">
              <div v-for="i in 60" :key="i" class="sp-ticket__bar"
                :style="{ height: (Math.random() * 20 + 14) + 'px', opacity: Math.random() * 0.5 + 0.5 }">
              </div>
            </div>
            <div class="sp-ticket__barcode-num">
              {{ order.orderNumber }}-{{ String(Number(idx) + 1).padStart(2,'0') }}-EVL-{{ Date.now().toString().slice(-6) }}
            </div>
          </div>
        </div>
      </div>

      <!-- ACTIONS -->
      <div class="sp-actions">
        <button class="sp-btn sp-btn--primary" @click="downloadTicket">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Télécharger mon billet
        </button>
        <button class="sp-btn sp-btn--outline" @click="goEvents">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
          </svg>
          Retour à l'accueil
        </button>
      </div>

      <!-- INFO BOX -->
      <div class="sp-info">
        <div class="sp-info__icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#e8405a" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
        </div>
        <div class="sp-info__text">
          <strong>Présentez ce billet à l'entrée</strong> — Le QR code sera scanné pour valider votre accès.
          Conservez ce billet ou l'e-mail de confirmation envoyé à <em>{{ order?.customer?.email }}</em>.
        </div>
      </div>

    </div>

    <footer class="sp-footer">
      <span>© 2026 EventLab. Tous droits réservés.</span>
      <span class="sp-footer__heart">Fait avec 💖 en Tunisie</span>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&family=Playfair+Display:wght@700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.sp {
  font-family: 'DM Sans', sans-serif;
  background: #fdf6f8;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  color: #3d2c35;
}

/* NAV */
.sp-nav {
  background: #fff;
  border-bottom: 1px solid #f5dce5;
  padding: 0 40px;
  box-shadow: 0 1px 12px rgba(232,64,90,0.05);
}
.sp-nav__inner {
  max-width: 900px;
  margin: 0 auto;
  height: 66px;
  display: flex;
  align-items: center;
}
.sp-logo { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.sp-logo__mark {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e8405a, #c4184a);
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  font-family: 'Playfair Display', serif;
  font-weight: 800; font-size: 17px;
  box-shadow: 0 4px 14px rgba(232,64,90,0.3);
}
.sp-logo__name {
  font-family: 'Playfair Display', serif;
  font-weight: 800; font-size: 20px;
  color: #c4184a;
}

/* LOADING */
.sp-loading {
  flex: 1;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  gap: 16px; color: #b08090; font-size: 14px;
}
.sp-loading__ring {
  width: 40px; height: 40px;
  border: 3px solid #f5dce5;
  border-top-color: #e8405a;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* PAGE ANIMATION */
.sp-page {
  flex: 1;
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 28px 60px;
  width: 100%;
  opacity: 0;
  transform: translateY(24px);
  transition: opacity 0.5s ease, transform 0.5s ease;
}
.sp-page--in { opacity: 1; transform: translateY(0); }

/* HERO */
.sp-hero {
  text-align: center;
  margin-bottom: 44px;
  position: relative;
}
.sp-hero__rings {
  position: absolute;
  inset: 0;
  display: flex; align-items: center; justify-content: center;
  pointer-events: none; overflow: hidden;
}
.sp-ring {
  position: absolute;
  border-radius: 50%;
  border: 1.5px solid rgba(232,64,90,0.1);
}
.sp-ring--1 { width: 160px; height: 160px; animation: ringOut 2.5s ease-out infinite; }
.sp-ring--2 { width: 260px; height: 260px; animation: ringOut 2.5s ease-out infinite 0.5s; }
.sp-ring--3 { width: 360px; height: 360px; animation: ringOut 2.5s ease-out infinite 1s; }
@keyframes ringOut {
  0%  { transform: scale(0.6); opacity: 0.8; }
  100%{ transform: scale(1.2); opacity: 0; }
}
.sp-hero__check {
  width: 88px; height: 88px;
  border-radius: 50%;
  background: linear-gradient(135deg, #34d399, #059669);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 22px;
  box-shadow: 0 12px 36px rgba(5,150,105,0.35);
  position: relative; z-index: 1;
  animation: popIn 0.6s cubic-bezier(0.175,0.885,0.32,1.275);
}
@keyframes popIn {
  0%  { transform: scale(0); opacity: 0; }
  70% { transform: scale(1.15); }
  100%{ transform: scale(1); opacity: 1; }
}
.sp-hero__title {
  font-family: 'Playfair Display', serif;
  font-size: 32px; font-weight: 800;
  color: #3d2c35;
  margin-bottom: 10px;
  letter-spacing: -0.5px;
  position: relative; z-index: 1;
}
.sp-hero__sub {
  font-size: 15px; color: #b08090;
  line-height: 1.6; margin-bottom: 18px;
  position: relative; z-index: 1;
}
.sp-hero__sub strong { color: #3d2c35; }
.sp-hero__meta {
  display: flex; align-items: center; justify-content: center;
  gap: 10px; flex-wrap: wrap;
  position: relative; z-index: 1;
}
.sp-hero__tag {
  display: flex; align-items: center; gap: 6px;
  background: #fff; border: 1px solid #f5dce5;
  padding: 6px 14px; border-radius: 100px;
  font-size: 12px; font-weight: 600; color: #7d5a68;
  box-shadow: 0 2px 8px rgba(232,64,90,0.06);
}
.sp-hero__tag--green {
  background: #f0fdf6; color: #059669;
  border-color: #bbf7d0;
}

/* TICKET */
.sp-tickets { display: flex; flex-direction: column; gap: 28px; margin-bottom: 32px; }
.sp-ticket {
  background: #fff;
  border-radius: 22px;
  overflow: hidden;
  box-shadow: 0 8px 40px rgba(232,64,90,0.12), 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #f5dce5;
}
.sp-ticket__main {
  display: grid;
  grid-template-columns: 1fr 180px;
  min-height: 240px;
}
.sp-ticket__left {
  padding: 28px 28px 22px;
  border-right: none;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Event badge */
.sp-ticket__event-badge {
  display: flex;
  gap: 18px;
  align-items: flex-start;
  margin-bottom: 20px;
}
.sp-ticket__date-block {
  background: linear-gradient(135deg, #e8405a, #c4184a);
  border-radius: 14px;
  padding: 12px 14px;
  display: flex; flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  box-shadow: 0 6px 18px rgba(232,64,90,0.3);
}
.sp-ticket__day   { font-family:'Playfair Display',serif; font-size:28px; font-weight:800; color:#fff; line-height:1; }
.sp-ticket__month { font-size:11px; font-weight:700; color:rgba(255,255,255,0.85); letter-spacing:1px; margin-top:2px; }
.sp-ticket__year  { font-size:10px; font-weight:600; color:rgba(255,255,255,0.6); margin-top:1px; }
.sp-ticket__event-info { flex: 1; }
.sp-ticket__label {
  font-size: 10px; font-weight: 700;
  color: #e8405a; letter-spacing: 1.5px;
  text-transform: uppercase; margin-bottom: 5px;
}
.sp-ticket__event-name {
  font-family: 'Playfair Display', serif;
  font-size: 19px; font-weight: 800;
  color: #3d2c35; line-height: 1.25;
  margin-bottom: 8px;
}
.sp-ticket__location,
.sp-ticket__time {
  display: flex; align-items: center; gap: 5px;
  font-size: 12px; color: #b08090; margin-bottom: 3px;
}

/* Tear divider */
.sp-ticket__divider {
  display: flex; align-items: center;
  margin: 14px 0;
  position: relative;
}
.sp-ticket__notch {
  width: 20px; height: 20px;
  border-radius: 50%;
  background: #fdf6f8;
  flex-shrink: 0;
  border: 1px solid #f5dce5;
}
.sp-ticket__notch--left  { margin-left: -39px; }
.sp-ticket__notch--right { margin-right: -39px; }
.sp-ticket__dashes {
  flex: 1;
  border-top: 2px dashed #f5dce5;
  margin: 0 4px;
}

/* Details grid */
.sp-ticket__details {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.sp-ticket__detail-label {
  font-size: 9px; font-weight: 700;
  color: #c5a8b5; text-transform: uppercase; letter-spacing: 1px;
  margin-bottom: 4px;
}
.sp-ticket__detail-value {
  font-size: 12px; font-weight: 700;
  color: #3d2c35;
}
.sp-ticket__detail-value--pink { color: #e8405a; }

/* QR Side */
.sp-ticket__qr-side {
  background: linear-gradient(160deg, #fff8fa, #fef0f4);
  border-left: 2px dashed #f5dce5;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 24px 18px;
  gap: 10px;
}
.sp-ticket__qr-wrap {
  background: #fff;
  border-radius: 14px;
  padding: 10px;
  box-shadow: 0 4px 16px rgba(232,64,90,0.1);
  border: 1px solid #f5dce5;
}
.sp-ticket__qr-img { width: 120px; height: 120px; display: block; }
.sp-ticket__qr-placeholder {
  width: 120px; height: 120px;
  background: #f5e8ed;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px; color: #e8405a;
}
.sp-ticket__qr-label {
  font-size: 10px; font-weight: 600;
  color: #c5a8b5; text-transform: uppercase; letter-spacing: 0.8px;
  text-align: center;
}
.sp-ticket__seat { text-align: center; }
.sp-ticket__seat-label {
  font-size: 9px; font-weight: 700;
  color: #c5a8b5; text-transform: uppercase; letter-spacing: 1px;
}
.sp-ticket__seat-num {
  font-family: 'Space Mono', monospace;
  font-size: 18px; font-weight: 700; color: #e8405a;
}

/* Barcode */
.sp-ticket__barcode {
  background: linear-gradient(135deg, #3d2c35, #5d3a48);
  padding: 14px 28px;
  display: flex; flex-direction: column;
  align-items: center; gap: 6px;
}
.sp-ticket__bars {
  display: flex; align-items: flex-end;
  gap: 2px; height: 40px;
}
.sp-ticket__bar {
  width: 2px;
  background: rgba(255,255,255,0.7);
  border-radius: 1px;
}
.sp-ticket__barcode-num {
  font-family: 'Space Mono', monospace;
  font-size: 10px; color: rgba(255,255,255,0.5);
  letter-spacing: 2px; text-transform: uppercase;
}

/* ACTIONS */
.sp-actions {
  display: flex; gap: 14px; justify-content: center;
  margin-bottom: 24px; flex-wrap: wrap;
}
.sp-btn {
  display: flex; align-items: center; gap: 9px;
  padding: 13px 26px;
  border-radius: 13px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.25s;
  border: none;
}
.sp-btn--primary {
  background: linear-gradient(135deg, #e8405a, #c4184a);
  color: #fff;
  box-shadow: 0 6px 20px rgba(232,64,90,0.3);
}
.sp-btn--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(232,64,90,0.4);
}
.sp-btn--outline {
  background: #fff;
  color: #e8405a;
  border: 1.5px solid #f0d0dc;
}
.sp-btn--outline:hover {
  background: #fff5f7;
  border-color: #e8405a;
}

/* INFO */
.sp-info {
  display: flex; align-items: flex-start; gap: 12px;
  background: #fff5f7;
  border: 1px solid #ffd6de;
  border-radius: 14px;
  padding: 16px 18px;
  max-width: 640px;
  margin: 0 auto;
  font-size: 13px; color: #7d5a68; line-height: 1.6;
}
.sp-info__icon { flex-shrink: 0; margin-top: 1px; }
.sp-info__text strong { color: #3d2c35; }
.sp-info__text em    { color: #e8405a; font-style: normal; font-weight: 600; }

/* FOOTER */
.sp-footer {
  background: #fdf0f4;
  border-top: 1px solid #f5dce5;
  padding: 18px 40px;
  display: flex; justify-content: space-between;
  font-size: 12px; color: #c5a8b5;
}
.sp-footer__heart { color: #e8405a; }

/* PRINT */
@media print {
  .sp-nav, .sp-hero, .sp-actions, .sp-info, .sp-footer { display: none !important; }
  .sp-page { padding: 0; }
  .sp-ticket { box-shadow: none; border: 1px solid #ddd; }
}

/* RESPONSIVE */
@media (max-width: 640px) {
  .sp-ticket__main  { grid-template-columns: 1fr; }
  .sp-ticket__qr-side { border-left: none; border-top: 2px dashed #f5dce5; flex-direction: row; justify-content: space-around; padding: 18px; }
  .sp-ticket__details { grid-template-columns: repeat(2, 1fr); }
  .sp-ticket__notch--left  { margin-left: -39px; }
  .sp-ticket__notch--right { margin-right: -39px; }
  .sp-page { padding: 24px 14px 40px; }
  .sp-footer { flex-direction: column; gap: 4px; align-items: center; }
}
</style>