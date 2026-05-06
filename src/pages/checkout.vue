<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, computed, onMounted } from 'vue'
import { useCartStore } from '@/stores/cart'
import type { CartItem } from '@/stores/cart'

const router = useRouter()
const cart   = useCartStore()

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'
const getToken     = () => localStorage.getItem('access_token') || localStorage.getItem('token')

const apiFetch = async (endpoint: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) throw { status: res.status, data }
  return data
}

const isAuthenticated = ref(false)
const isLoadingUser   = ref(true)
const isProcessing    = ref(false)
const apiError        = ref('')
const step            = ref<'form' | 'processing' | 'done' | 'ticket'>('form')
const orderData       = ref<any>(null)
const qrDataUrl       = ref('')
const gateways        = ref<any[]>([])
const selectedGateway = ref<any>(null)
const customer = ref({ firstname: '', lastname: '', email: '', phone: '' })
const payment  = ref({ cardNumber: '', cardName: '', expiry: '', cvv: '' })

onMounted(async () => {
  const token = getToken()
  if (!token) { router.push('/login'); return }
  if (cart.items.length === 0) { router.push('/user/dashboard'); return }
  isAuthenticated.value = true

  try {
    const data = await apiFetch('/users/me/')
    const u = data.data || data
    customer.value.firstname = u.firstname || u.first_name || ''
    customer.value.lastname  = u.lastname  || u.last_name  || ''
    customer.value.email     = u.email     || ''
    customer.value.phone     = u.mobile    || u.phone      || ''
  } catch {
    try {
      const stored = localStorage.getItem('user')
      if (stored) {
        const u = JSON.parse(stored)
        customer.value.firstname = u.firstname || u.first_name || ''
        customer.value.lastname  = u.lastname  || u.last_name  || ''
        customer.value.email     = u.email     || ''
        customer.value.phone     = u.mobile    || u.phone      || ''
      }
    } catch {}
  }

  try {
    const data = await apiFetch('/payments/gateways/')
    const list = Array.isArray(data.results || data) ? (data.results || data) : []
    gateways.value = list.filter((g: any) => g.status === 1)
    if (gateways.value.length > 0) selectedGateway.value = gateways.value[0]
  } catch { gateways.value = [] }

  isLoadingUser.value = false
})

const isFormValid = computed(() =>
  customer.value.firstname.trim() !== '' &&
  customer.value.lastname.trim()  !== '' &&
  customer.value.email.includes('@') &&
  customer.value.phone.trim()     !== '' &&
  payment.value.cardNumber.replace(/\s/g, '').length === 16 &&
  payment.value.cardName.trim()   !== '' &&
  /^\d{2}\/\d{2}$/.test(payment.value.expiry) &&
  payment.value.cvv.length >= 3
)

const cardType = computed(() => {
  const n = payment.value.cardNumber.replace(/\s/g, '')
  if (n.startsWith('4'))     return 'visa'
  if (/^5[1-5]/.test(n))     return 'mastercard'
  if (/^3[47]/.test(n))      return 'amex'
  return ''
})

const formatCardNumber = (e: any) => {
  let v = e.target.value.replace(/\D/g, '').substring(0, 16)
  payment.value.cardNumber = v.replace(/(.{4})/g, '$1 ').trim()
}
const formatExpiry = (e: any) => {
  let v = e.target.value.replace(/\D/g, '')
  if (v.length >= 3) v = v.substring(0, 2) + '/' + v.substring(2, 4)
  payment.value.expiry = v
}
const formatCvv = (e: any) => {
  payment.value.cvv = e.target.value.replace(/\D/g, '').substring(0, 4)
}
const formatTime = (d: string) => {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}
const getDateParts = (d: string) => {
  if (!d) return { day: '--', month: '---' }
  const dt = new Date(d)
  return {
    day:   dt.getDate().toString().padStart(2, '0'),
    month: dt.toLocaleDateString('fr-FR', { month: 'short' }).toUpperCase().replace('.', ''),
  }
}

const confirmPayment = async () => {
  if (!isFormValid.value) {
    apiError.value = 'Veuillez remplir tous les champs correctement.'
    return
  }
  apiError.value     = ''
  isProcessing.value = true
  step.value         = 'processing'

  const createdOrders: any[] = []

  try {
    for (const item of cart.items as CartItem[]) {
      const payload = {
        event:    item.eventId,
        quantity: item.quantity,
        details: {
          customer_name:  `${customer.value.firstname} ${customer.value.lastname}`.trim(),
          customer_email: customer.value.email,
          customer_phone: customer.value.phone,
          gateway:        selectedGateway.value?.name || 'card',
        },
      }
      const order = await apiFetch('/orders/', { method: 'POST', body: JSON.stringify(payload) })
      const orderId = order.id || order.data?.id
      if (orderId) await apiFetch(`/orders/${orderId}/mark_paid/`, { method: 'POST' })
      createdOrders.push({ orderId, eventId: item.eventId, title: item.title })
    }

    const od = {
      orderNumber:   `EVL-${Date.now().toString().slice(-8)}`,
      orders:        createdOrders,
      items:         [...cart.items],
      customer:      { ...customer.value },
      total:         cart.totalPrice,
      paymentMethod: cardType.value || 'card',
      cardLast4:     payment.value.cardNumber.slice(-4).replace(/\s/g, ''),
      gateway:       selectedGateway.value?.name || null,
      date:          new Date().toISOString(),
    }
    localStorage.setItem('last_order', JSON.stringify(od))
    orderData.value = od

    // ── Sauvegarder le billet dans Support/Tickets ──────────────
    try {
      const ticketMessage = [
        `Paiement confirme le ${new Date(od.date).toLocaleString('fr-FR')}`,
        `Commande : ${od.orderNumber}`,
        `Paiement via : ${od.gateway || od.paymentMethod || 'Carte'}`,
        `Total : ${od.total.toFixed(2)} DT`,
        ...od.items.map((item: any) =>
          `Billet: ${item.title} | ${item.quantity} billet(s) | ${(item.price * item.quantity).toFixed(2)} DT`
        ),
      ].join('\n')

      // Étape 1 : créer le ticket avec les bons champs
      const ticket = await apiFetch('/support/tickets/', {
        method: 'POST',
        body: JSON.stringify({
          subject:       `Billet - ${od.orderNumber}`,
          name:          `${od.customer.firstname} ${od.customer.lastname}`.trim(),
          email:         od.customer.email,
          status:        'open',
          priority:      '2',
          first_message: ticketMessage,
        }),
      })

      // Étape 2 : ajouter le message via reply
      const ticketId = ticket?.id || ticket?.data?.id
      if (ticketId) {
        await apiFetch(`/support/tickets/${ticketId}/reply/`, {
          method: 'POST',
          body: JSON.stringify({ message: ticketMessage }),
        })
      }

      console.log('✅ Ticket support créé avec succès, ID:', ticketId)
    } catch (e: any) {
      console.warn('⚠️ Support ticket failed:', e?.data || e)
    }

    // Générer QR code via API gratuite
    const qrText = [
      od.orderNumber,
      od.items?.[0]?.title || 'EventLab',
      `${od.customer?.firstname} ${od.customer?.lastname}`.trim(),
      od.customer?.email,
      `Total: ${od.total} DT`,
    ].join(' | ')
    qrDataUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrText)}&color=3d2c35&bgcolor=ffffff&margin=10`

    cart.clearCart()
    step.value = 'done'
    setTimeout(() => { step.value = 'ticket' }, 1400)

  } catch (err: any) {
    isProcessing.value = false
    step.value         = 'form'
    if (err?.data) {
      const msgs: string[] = []
      const d = err.data
      if (d.message) {
        msgs.push(d.message)
        if (d.errors) Object.entries(d.errors).forEach(([k, v]) =>
          msgs.push(`${k}: ${Array.isArray(v) ? v.join(', ') : JSON.stringify(v)}`)
        )
      } else if (d.detail) {
        msgs.push(String(d.detail))
      } else {
        Object.entries(d).forEach(([k, v]) =>
          msgs.push(`${k}: ${Array.isArray(v) ? v.join(', ') : JSON.stringify(v)}`)
        )
      }
      apiError.value = msgs.join(' | ')
    } else {
      apiError.value = 'Erreur de connexion. Réessayez.'
    }
  }
}

const goHome      = () => router.push('/user/dashboard')
const goToCart    = () => router.push('/cart')
const printTicket = () => window.print()
const goDashboard = () => router.push('/user/orders')
</script>

<template>
  <div class="ck">

    <!-- ── NAV ── -->
    <nav class="ck-nav">
      <div class="ck-nav__inner">
        <div class="ck-logo" @click="goHome">
          <div class="ck-logo__mark">E</div>
          <span class="ck-logo__name">EventLab</span>
        </div>
        <div class="ck-nav__secure">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          Paiement sécurisé SSL
        </div>
      </div>
    </nav>

    <!-- ── STEPPER ── -->
    <div class="ck-stepper">
      <div class="ck-steps">
        <div class="ck-step ck-step--done">
          <div class="ck-step__bubble">✓</div>
          <span class="ck-step__lbl">Panier</span>
        </div>
        <div class="ck-step__line" :class="step !== 'form' ? 'ck-step__line--done' : 'ck-step__line--active'"></div>
        <div class="ck-step" :class="step === 'form' ? 'ck-step--active' : 'ck-step--done'">
          <div class="ck-step__bubble">{{ step === 'form' ? '2' : '✓' }}</div>
          <span class="ck-step__lbl">Paiement</span>
        </div>
        <div class="ck-step__line" :class="(step === 'done' || step === 'ticket') ? 'ck-step__line--done' : ''"></div>
        <div class="ck-step" :class="(step === 'done' || step === 'ticket') ? 'ck-step--done' : 'ck-step--active'">
          <div class="ck-step__bubble">{{ (step === 'done' || step === 'ticket') ? '✓' : '3' }}</div>
          <span class="ck-step__lbl">Confirmation</span>
        </div>
      </div>
    </div>

    <!-- ── LOADER ── -->
    <div v-if="isLoadingUser" class="ck-loader">
      <div class="ck-loader__ring"></div>
      <p>Chargement de votre espace…</p>
    </div>

    <!-- ── PROCESSING / DONE ── -->
    <div v-else-if="step === 'processing' || step === 'done'" class="ck-processing">
      <div class="ck-processing__rings">
        <div class="ck-ring ck-ring--1"></div>
        <div class="ck-ring ck-ring--2"></div>
        <div class="ck-ring ck-ring--3"></div>
      </div>
      <div class="ck-processing__circle" :class="{ 'ck-processing__circle--ok': step === 'done' }">
        <span v-if="step === 'processing'" class="ck-processing__spinner"></span>
        <svg v-else width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>
      <h2 class="ck-processing__title">
        {{ step === 'done' ? 'Paiement validé !' : 'Traitement en cours…' }}
      </h2>
      <p class="ck-processing__sub">
        {{ step === 'done' ? 'Génération de votre billet…' : 'Veuillez patienter, ne fermez pas cette page.' }}
      </p>
      <div class="ck-psteps">
        <div class="ck-pstep" :class="step === 'done' ? 'ck-pstep--done' : 'ck-pstep--active'">
          <div class="ck-pstep__icon">💳</div>
          <span>Paiement</span>
        </div>
        <div class="ck-pstep__line" :class="step === 'done' ? 'ck-pstep__line--done' : ''"></div>
        <div class="ck-pstep" :class="step === 'done' ? 'ck-pstep--done' : ''">
          <div class="ck-pstep__icon">✅</div>
          <span>Confirmation</span>
        </div>
        <div class="ck-pstep__line" :class="step === 'done' ? 'ck-pstep__line--done' : ''"></div>
        <div class="ck-pstep" :class="step === 'done' ? 'ck-pstep--done' : ''">
          <div class="ck-pstep__icon">🎟️</div>
          <span>Vos billets</span>
        </div>
      </div>
    </div>


    <!-- ── TICKET SECTION ── -->
    <div v-else-if="step === 'ticket' && orderData" class="ck-ticket-page">
      <div class="ck-ticket-wrap">

        <!-- Success header -->
        <div class="ck-ticket-hero">
          <div class="ck-ticket-hero__icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>
          <div>
            <h1 class="ck-ticket-hero__title">Paiement confirmé !</h1>
            <p class="ck-ticket-hero__sub">
              Commande <strong>{{ orderData.orderNumber }}</strong> · {{ orderData.customer?.email }}
            </p>
          </div>
        </div>

        <!-- Billet(s) -->
        <div class="ck-tickets" id="ticket-print">
          <div v-for="(item, idx) in orderData.items" :key="idx" class="ck-ticket">

            <!-- Main body -->
            <div class="ck-ticket__body">
              <div class="ck-ticket__left">

                <!-- Date badge + infos événement -->
                <div class="ck-ticket__event">
                  <div class="ck-ticket__date-badge">
                    <span class="ck-ticket__date-day">{{ getDateParts(item.date).day }}</span>
                    <span class="ck-ticket__date-month">{{ getDateParts(item.date).month }}</span>
                    <span class="ck-ticket__date-year">{{ new Date(item.date).getFullYear() }}</span>
                  </div>
                  <div class="ck-ticket__event-info">
                    <div class="ck-ticket__event-label">ÉVÉNEMENT</div>
                    <div class="ck-ticket__event-name">{{ item.title }}</div>
                    <div v-if="item.location" class="ck-ticket__event-meta">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
                      </svg>
                      {{ item.location }}
                    </div>
                    <div class="ck-ticket__event-meta">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>
                      </svg>
                      {{ formatTime(item.date) }}
                    </div>
                  </div>
                </div>

                <!-- Séparateur découpé -->
                <div class="ck-ticket__tear">
                  <div class="ck-ticket__tear-notch ck-ticket__tear-notch--l"></div>
                  <div class="ck-ticket__tear-line"></div>
                  <div class="ck-ticket__tear-notch ck-ticket__tear-notch--r"></div>
                </div>

                <!-- Détails commande -->
                <div class="ck-ticket__details">
                  <div class="ck-ticket__detail">
                    <div class="ck-ticket__detail-lbl">TITULAIRE</div>
                    <div class="ck-ticket__detail-val">{{ orderData.customer?.firstname }} {{ orderData.customer?.lastname }}</div>
                  </div>
                  <div class="ck-ticket__detail">
                    <div class="ck-ticket__detail-lbl">COMMANDE</div>
                    <div class="ck-ticket__detail-val">{{ orderData.orderNumber }}</div>
                  </div>
                  <div class="ck-ticket__detail">
                    <div class="ck-ticket__detail-lbl">QUANTITÉ</div>
                    <div class="ck-ticket__detail-val">{{ item.quantity }} billet{{ item.quantity > 1 ? 's' : '' }}</div>
                  </div>
                  <div class="ck-ticket__detail">
                    <div class="ck-ticket__detail-lbl">MONTANT</div>
                    <div class="ck-ticket__detail-val ck-ticket__detail-val--pink">{{ (item.price * item.quantity).toFixed(2) }} DT</div>
                  </div>
                </div>
              </div>

              <!-- QR Code -->
              <div class="ck-ticket__qr">
                <div class="ck-ticket__qr-box">
                  <img :src="qrDataUrl" alt="QR Code" class="ck-ticket__qr-img" />
                </div>
                <div class="ck-ticket__qr-label">Scanner pour valider</div>
                <div class="ck-ticket__num">
                  <div class="ck-ticket__num-lbl">BILLET</div>
                  <div class="ck-ticket__num-val">#{{ String(Number(idx) + 1).padStart(3, '0') }}</div>
                </div>
              </div>
            </div>

            <!-- Barcode footer -->
            <div class="ck-ticket__barcode">
              <div class="ck-ticket__bars">
                <div v-for="b in 56" :key="b" class="ck-ticket__bar"
                  :style="{ height: ((b * 13 % 23) + 14) + 'px', opacity: (b * 7 % 5) * 0.1 + 0.5 }">
                </div>
              </div>
              <div class="ck-ticket__barcode-txt">
                {{ orderData.orderNumber }}-{{ String(Number(idx) + 1).padStart(2,'0') }}-EVL-{{ orderData.date?.slice(-6).replace(/[^0-9]/g,'') }}
              </div>
            </div>

          </div>
        </div>

        <!-- Actions -->
        <div class="ck-ticket-actions">
          <button class="ck-ticket-btn ck-ticket-btn--primary" @click="printTicket">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
            Télécharger mon billet
          </button>
          <button class="ck-ticket-btn ck-ticket-btn--dashboard" @click="goDashboard">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
              <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
            </svg>
            Mes réservations
          </button>
          <button class="ck-ticket-btn ck-ticket-btn--outline" @click="goHome">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
            Dashboard
          </button>
        </div>

        <!-- Notice -->
        <div class="ck-ticket-notice">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#e8405a" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
          </svg>
          Présentez ce QR code à l'entrée de l'événement pour valider votre accès.
        </div>

      </div>
    </div>

    <!-- ── MAIN FORM ── -->
    <div v-else-if="isAuthenticated" class="ck-main">
      <div class="ck-wrap">

        <!-- Error banner -->
        <div v-if="apiError" class="ck-error">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          {{ apiError }}
        </div>

        <div class="ck-grid">
          <!-- ── LEFT COLUMN ── -->
          <div class="ck-left">

            <!-- Section titre -->
            <div class="ck-page-header">
              <h1 class="ck-page-header__title">Finalisez votre commande</h1>
              <p class="ck-page-header__sub">Renseignez vos coordonnées pour recevoir votre billet par e-mail</p>
            </div>

            <!-- Coordonnées -->
            <div class="ck-section">
              <div class="ck-section__head">
                <div class="ck-section__icon">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#e8405a" stroke-width="2">
                    <circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
                  </svg>
                </div>
                <h2 class="ck-section__title">Vos coordonnées</h2>
              </div>
              <div class="ck-section__body">
                <div class="ck-row">
                  <div class="ck-field">
                    <label>Prénom <span class="ck-req">*</span></label>
                    <input v-model="customer.firstname" type="text" placeholder="Sarra" />
                  </div>
                  <div class="ck-field">
                    <label>Nom <span class="ck-req">*</span></label>
                    <input v-model="customer.lastname" type="text" placeholder="Ben Ali" />
                  </div>
                </div>
                <div class="ck-field">
                  <label>Adresse e-mail <span class="ck-req">*</span></label>
                  <div class="ck-input-icon">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#c5a8b5" stroke-width="2">
                      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>
                    </svg>
                    <input v-model="customer.email" type="email" placeholder="vous@email.com" />
                  </div>
                  <p class="ck-hint">Vos billets seront envoyés à cette adresse</p>
                </div>
                <div class="ck-field">
                  <label>Téléphone <span class="ck-req">*</span></label>
                  <div class="ck-input-icon">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#c5a8b5" stroke-width="2">
                      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 13a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 2.18h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 9.91a16 16 0 0 0 6.08 6.08l.95-.95a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21.92 17z"/>
                    </svg>
                    <input v-model="customer.phone" type="tel" placeholder="+216 XX XXX XXX" />
                  </div>
                </div>
              </div>
            </div>

            <!-- Passerelle -->
            <div v-if="gateways.length > 0" class="ck-section">
              <div class="ck-section__head">
                <div class="ck-section__icon">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#e8405a" stroke-width="2">
                    <rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>
                  </svg>
                </div>
                <h2 class="ck-section__title">Passerelle de paiement</h2>
              </div>
              <div class="ck-section__body">
                <div class="ck-gateways">
                  <div
                    v-for="gw in gateways" :key="gw.id"
                    class="ck-gw"
                    :class="{ 'ck-gw--active': selectedGateway?.id === gw.id }"
                    @click="selectedGateway = gw"
                  >
                    <img v-if="gw.logo" :src="gw.logo" :alt="gw.name" class="ck-gw__logo" />
                    <span v-else class="ck-gw__emoji">💳</span>
                    <span class="ck-gw__name">{{ gw.name }}</span>
                    <div class="ck-gw__radio">
                      <div v-if="selectedGateway?.id === gw.id" class="ck-gw__dot"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Carte bancaire -->
            <div class="ck-section">
              <div class="ck-section__head">
                <div class="ck-section__icon">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#e8405a" stroke-width="2">
                    <rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>
                  </svg>
                </div>
                <h2 class="ck-section__title">Carte bancaire</h2>
                <div class="ck-card-badges">
                  <span class="ck-cb ck-cb--visa">VISA</span>
                  <span class="ck-cb ck-cb--mc">MC</span>
                  <span class="ck-cb ck-cb--amex">AMEX</span>
                </div>
              </div>

              <!-- Visual card -->
              <div class="ck-vcard" :class="`ck-vcard--${cardType || 'default'}`">
                <div class="ck-vcard__shine"></div>
                <div class="ck-vcard__top">
                  <div class="ck-vcard__chip">
                    <div class="ck-vcard__chip-line"></div>
                    <div class="ck-vcard__chip-col"></div>
                  </div>
                  <div class="ck-vcard__network">
                    <span v-if="cardType === 'visa'" class="ck-vcard__net-visa">VISA</span>
                    <span v-else-if="cardType === 'mastercard'" class="ck-vcard__net-mc">
                      <span class="mc-c mc-c1"></span><span class="mc-c mc-c2"></span>
                    </span>
                    <span v-else-if="cardType === 'amex'" class="ck-vcard__net-amex">AMEX</span>
                    <span v-else class="ck-vcard__net-dots">• • •</span>
                  </div>
                </div>
                <div class="ck-vcard__number">
                  {{ payment.cardNumber || '•••• &nbsp; •••• &nbsp; •••• &nbsp; ••••' }}
                </div>
                <div class="ck-vcard__footer">
                  <div class="ck-vcard__col">
                    <span class="ck-vcard__label">Titulaire</span>
                    <span class="ck-vcard__value">{{ payment.cardName || 'NOM PRÉNOM' }}</span>
                  </div>
                  <div class="ck-vcard__col ck-vcard__col--right">
                    <span class="ck-vcard__label">Expire</span>
                    <span class="ck-vcard__value">{{ payment.expiry || 'MM/AA' }}</span>
                  </div>
                </div>
              </div>

              <div class="ck-section__body">
                <div class="ck-field">
                  <label>Numéro de carte <span class="ck-req">*</span></label>
                  <div class="ck-input-suffix">
                    <input
                      :value="payment.cardNumber"
                      @input="formatCardNumber"
                      type="text"
                      placeholder="1234 5678 9012 3456"
                      maxlength="19"
                      inputmode="numeric"
                      class="ck-mono"
                    />
                    <span class="ck-suffix-icon">
                      <span v-if="cardType === 'visa'" class="suf-visa">VISA</span>
                      <span v-else-if="cardType === 'mastercard'" class="suf-mc">
                        <span></span><span></span>
                      </span>
                      <span v-else-if="cardType === 'amex'" class="suf-amex">AMEX</span>
                      <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d4bfc7" stroke-width="1.5">
                        <rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>
                      </svg>
                    </span>
                  </div>
                </div>

                <div class="ck-field">
                  <label>Nom du titulaire <span class="ck-req">*</span></label>
                  <input
                    v-model="payment.cardName"
                    type="text"
                    placeholder="SARRA BEN ALI"
                    style="text-transform:uppercase"
                  />
                </div>

                <div class="ck-row">
                  <div class="ck-field">
                    <label>Date d'expiration <span class="ck-req">*</span></label>
                    <input
                      :value="payment.expiry"
                      @input="formatExpiry"
                      type="text"
                      placeholder="MM/AA"
                      maxlength="5"
                      inputmode="numeric"
                    />
                  </div>
                  <div class="ck-field">
                    <label>
                      CVV <span class="ck-req">*</span>
                      <span class="ck-cvv-tip" title="3 chiffres au dos de la carte">?</span>
                    </label>
                    <input
                      :value="payment.cvv"
                      @input="formatCvv"
                      type="password"
                      placeholder="•••"
                      maxlength="4"
                      inputmode="numeric"
                    />
                  </div>
                </div>

                <!-- Security badges -->
                <div class="ck-security">
                  <div class="ck-security__item">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                    </svg>
                    Crypté SSL 256 bits
                  </div>
                  <div class="ck-security__item">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                    3D Secure
                  </div>
                  <div class="ck-security__item">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                    PCI DSS
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── RIGHT COLUMN: SUMMARY ── -->
          <aside class="ck-right">
            <div class="ck-summary">

              <h3 class="ck-summary__title">Récapitulatif</h3>
              <p class="ck-summary__sub">Détail de votre commande</p>

              <!-- Items -->
              <div class="ck-items">
                <div v-for="item in cart.items" :key="item.id" class="ck-item">
                  <div class="ck-item__date">
                    <span class="ck-item__day">{{ getDateParts(item.date).day }}</span>
                    <span class="ck-item__month">{{ getDateParts(item.date).month }}</span>
                  </div>
                  <div class="ck-item__info">
                    <div class="ck-item__title">{{ item.title }}</div>
                    <div class="ck-item__meta">
                      {{ formatTime(item.date) }}<span v-if="item.location"> · {{ item.location }}</span>
                    </div>
                    <div class="ck-item__qty">{{ item.quantity }} × {{ Number(item.price).toFixed(2) }} DT</div>
                  </div>
                  <div class="ck-item__price">
                    {{ (item.price * item.quantity).toFixed(2) }}<small> DT</small>
                  </div>
                </div>
              </div>

              <!-- Gateway pill -->
              <div v-if="selectedGateway" class="ck-gw-pill">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/>
                </svg>
                Via <strong>{{ selectedGateway.name }}</strong>
              </div>

              <div class="ck-sep"></div>

              <!-- Totals -->
              <div class="ck-totals">
                <div class="ck-total-line">
                  <span>Sous-total</span>
                  <span>{{ cart.totalPrice.toFixed(2) }} DT</span>
                </div>
                <div class="ck-total-line">
                  <span>Frais de service</span>
                  <span class="ck-free">✓ Offerts</span>
                </div>
              </div>

              <div class="ck-grand">
                <span>Total à payer</span>
                <span class="ck-grand__amount">{{ cart.totalPrice.toFixed(2) }}<small> DT</small></span>
              </div>

              <!-- CTA -->
              <button
                class="ck-pay-btn"
                @click="confirmPayment"
                :disabled="isProcessing || !isFormValid"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
                Confirmer le paiement
              </button>

              <button
                class="ck-back-btn"
                @click="goToCart"
                :disabled="isProcessing"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
                Retour au panier
              </button>

              <p class="ck-notice">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
                </svg>
                En confirmant, vous acceptez nos
                <a href="#" class="ck-notice__link">conditions d'utilisation</a>
              </p>
            </div>
          </aside>
        </div>
      </div>
    </div>

    <!-- ── FOOTER ── -->
    <footer class="ck-footer">
      <span>© 2026 EventLab. Tous droits réservés.</span>
      <span class="ck-footer__heart">Fait avec 💖 en Tunisie</span>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Mono:wght@400;700&family=Playfair+Display:wght@700;800&display=swap');

/* ── RESET & BASE ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

.ck {
  font-family: 'DM Sans', sans-serif;
  background: #fdf6f8;
  color: #3d2c35;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ── NAV ── */
.ck-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  background: #fff;
  border-bottom: 1px solid #f5dce5;
  box-shadow: 0 1px 12px rgba(232, 64, 90, 0.05);
  padding: 0 40px;
}
.ck-nav__inner {
  max-width: 1140px;
  margin: 0 auto;
  height: 66px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ck-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  text-decoration: none;
}
.ck-logo__mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #e8405a, #c4184a);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-family: 'Playfair Display', serif;
  font-weight: 800;
  font-size: 17px;
  box-shadow: 0 4px 14px rgba(232, 64, 90, 0.3);
}
.ck-logo__name {
  font-family: 'Playfair Display', serif;
  font-weight: 800;
  font-size: 20px;
  color: #c4184a;
  letter-spacing: -0.3px;
}
.ck-nav__secure {
  display: flex;
  align-items: center;
  gap: 7px;
  background: #f0fdf6;
  color: #059669;
  padding: 7px 14px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #d1fae5;
}

/* ── STEPPER ── */
.ck-stepper {
  background: #fff;
  padding: 20px 40px;
  border-bottom: 1px solid #f5dce5;
}
.ck-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 460px;
  margin: 0 auto;
}
.ck-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.ck-step__bubble {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: #f5e8ed;
  color: #c5a8b5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  transition: all 0.3s;
}
.ck-step__lbl {
  font-size: 10px;
  font-weight: 700;
  color: #c5a8b5;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
.ck-step--active .ck-step__bubble {
  background: linear-gradient(135deg, #e8405a, #c4184a);
  color: #fff;
  box-shadow: 0 4px 14px rgba(232, 64, 90, 0.4);
  transform: scale(1.1);
}
.ck-step--active .ck-step__lbl { color: #e8405a; }
.ck-step--done .ck-step__bubble {
  background: linear-gradient(135deg, #34d399, #059669);
  color: #fff;
  box-shadow: 0 3px 10px rgba(5, 150, 105, 0.3);
}
.ck-step--done .ck-step__lbl { color: #059669; }
.ck-step__line {
  flex: 1;
  max-width: 90px;
  height: 2px;
  background: #f5dce5;
  margin: 0 10px 20px;
  border-radius: 2px;
  transition: background 0.4s;
}
.ck-step__line--active { background: linear-gradient(90deg, #e8405a, #f5a0b0); }
.ck-step__line--done { background: linear-gradient(90deg, #34d399, #059669); }

/* ── LOADER ── */
.ck-loader {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #b08090;
  font-size: 14px;
}
.ck-loader__ring {
  width: 40px;
  height: 40px;
  border: 3px solid #f5dce5;
  border-top-color: #e8405a;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ── PROCESSING ── */
.ck-processing {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  text-align: center;
  padding: 40px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(160deg, #fdf6f8 0%, #fff0f4 50%, #fde8ef 100%);
}
.ck-processing__rings {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}
.ck-ring {
  position: absolute;
  border-radius: 50%;
  border: 1.5px solid rgba(232, 64, 90, 0.12);
}
.ck-ring--1 { width: 180px; height: 180px; animation: ringPulse 2s ease-out infinite; }
.ck-ring--2 { width: 280px; height: 280px; animation: ringPulse 2s ease-out infinite 0.4s; }
.ck-ring--3 { width: 380px; height: 380px; animation: ringPulse 2s ease-out infinite 0.8s; }
@keyframes ringPulse {
  0%  { transform: scale(0.8); opacity: 0.6; }
  100%{ transform: scale(1.2); opacity: 0; }
}
.ck-processing__circle {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e8405a, #c4184a);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12px 36px rgba(232, 64, 90, 0.4);
  position: relative;
  z-index: 1;
}
.ck-processing__circle--ok {
  background: linear-gradient(135deg, #34d399, #059669);
  box-shadow: 0 12px 36px rgba(5, 150, 105, 0.4);
  animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
@keyframes popIn {
  0%  { transform: scale(0); opacity: 0; }
  70% { transform: scale(1.15); }
  100%{ transform: scale(1); opacity: 1; }
}
.ck-processing__spinner {
  width: 38px;
  height: 38px;
  border: 3px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.ck-processing__title {
  font-family: 'Playfair Display', serif;
  font-size: 28px;
  font-weight: 800;
  color: #3d2c35;
  position: relative;
  z-index: 1;
}
.ck-processing__sub {
  font-size: 14px;
  color: #b08090;
  position: relative;
  z-index: 1;
}
.ck-psteps {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1.5px solid #f5dce5;
  border-radius: 16px;
  padding: 16px 24px;
  box-shadow: 0 4px 20px rgba(232, 64, 90, 0.07);
  position: relative;
  z-index: 1;
}
.ck-pstep {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 80px;
}
.ck-pstep__icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #f5e8ed;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 19px;
  transition: all 0.3s;
}
.ck-pstep--active .ck-pstep__icon {
  background: linear-gradient(135deg, #e8405a, #c4184a);
  animation: pulsate 0.9s ease-in-out infinite alternate;
}
.ck-pstep--done .ck-pstep__icon {
  background: linear-gradient(135deg, #34d399, #059669);
}
@keyframes pulsate {
  0%  { transform: scale(1); box-shadow: 0 0 0 0 rgba(232,64,90,0.4); }
  100%{ transform: scale(1.06); box-shadow: 0 0 0 8px rgba(232,64,90,0); }
}
.ck-pstep span { font-size: 11px; font-weight: 600; color: #b08090; }
.ck-pstep--done span { color: #059669; }
.ck-pstep--active span { color: #e8405a; }
.ck-pstep__line { width: 36px; height: 2px; background: #f5dce5; margin-bottom: 22px; border-radius: 2px; }
.ck-pstep__line--done { background: linear-gradient(90deg, #34d399, #059669); }

/* ── MAIN LAYOUT ── */
.ck-main { flex: 1; padding: 36px 0 60px; }
.ck-wrap { max-width: 1140px; margin: 0 auto; padding: 0 28px; }
.ck-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 24px;
  align-items: flex-start;
}

/* ── ERROR BANNER ── */
.ck-error {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  background: #fef2f2;
  color: #b91c1c;
  border: 1.5px solid #fecaca;
  border-radius: 12px;
  padding: 13px 16px;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 20px;
}

/* ── LEFT COLUMN ── */
.ck-left { display: flex; flex-direction: column; gap: 18px; }

.ck-page-header { padding-bottom: 4px; }
.ck-page-header__title {
  font-family: 'Playfair Display', serif;
  font-size: 26px;
  font-weight: 800;
  color: #3d2c35;
  letter-spacing: -0.5px;
  margin-bottom: 5px;
}
.ck-page-header__sub { font-size: 14px; color: #b08090; }

/* ── SECTIONS ── */
.ck-section {
  background: #fff;
  border-radius: 20px;
  border: 1.5px solid #f5dce5;
  overflow: hidden;
  box-shadow: 0 2px 16px rgba(232, 64, 90, 0.05);
}
.ck-section__head {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 18px 24px;
  border-bottom: 1.5px solid #f5e8ed;
  background: linear-gradient(135deg, #fffbfc, #fef0f4);
}
.ck-section__icon {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: #fff5f7;
  border: 1px solid #ffd6de;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ck-section__title {
  flex: 1;
  font-size: 14px;
  font-weight: 700;
  color: #3d2c35;
  letter-spacing: 0.1px;
}
.ck-section__body {
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── FIELDS ── */
.ck-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.ck-field { display: flex; flex-direction: column; gap: 6px; }
.ck-field label {
  font-size: 12px;
  font-weight: 700;
  color: #b08090;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.ck-req { color: #e8405a; }
.ck-cvv-tip {
  width: 16px;
  height: 16px;
  background: #f5e8ed;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: #c4184a;
  cursor: help;
  font-weight: 800;
  border: 1px solid #ffd6de;
}

/* Base input */
.ck-field input {
  padding: 12px 15px;
  border: 1.5px solid #f0e4e9;
  border-radius: 12px;
  font-size: 14px;
  font-family: 'DM Sans', sans-serif;
  color: #3d2c35;
  background: #fdfafc;
  outline: none;
  transition: all 0.2s;
  width: 100%;
}
.ck-field input:focus {
  border-color: #e8405a;
  background: #fff;
  box-shadow: 0 0 0 4px rgba(232, 64, 90, 0.08);
}
.ck-field input::placeholder { color: #d4bfc7; }
.ck-mono { font-family: 'Space Mono', monospace !important; letter-spacing: 1.5px; }

/* Input with leading icon */
.ck-input-icon {
  position: relative;
}
.ck-input-icon svg {
  position: absolute;
  left: 13px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}
.ck-input-icon input { padding-left: 38px; }

/* Input with trailing icon */
.ck-input-suffix { position: relative; }
.ck-input-suffix input { padding-right: 44px; }
.ck-suffix-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
}
.suf-visa  { font-size: 10px; font-weight: 900; color: #1a3a8f; letter-spacing: 0.5px; }
.suf-amex  { font-size: 9px; font-weight: 900; color: #007bc1; letter-spacing: 0.5px; }
.suf-mc    { display: flex; }
.suf-mc span { width: 13px; height: 13px; border-radius: 50%; }
.suf-mc span:first-child { background: #e8405a; }
.suf-mc span:last-child  { background: #ffb347; margin-left: -5px; opacity: 0.9; }

.ck-hint { font-size: 11px; color: #c5a8b5; display: flex; align-items: center; gap: 4px; }

/* ── GATEWAYS ── */
.ck-gateways { display: flex; flex-direction: column; gap: 10px; }
.ck-gw {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 16px;
  border: 1.5px solid #f0e4e9;
  border-radius: 13px;
  cursor: pointer;
  background: #fdfafc;
  transition: all 0.2s;
}
.ck-gw:hover { border-color: #ffb3c1; background: #fff8f9; transform: translateY(-1px); }
.ck-gw--active {
  border-color: #e8405a;
  background: #fff5f7;
  box-shadow: 0 0 0 3px rgba(232, 64, 90, 0.08);
}
.ck-gw__logo  { height: 22px; object-fit: contain; }
.ck-gw__emoji { font-size: 20px; }
.ck-gw__name  { flex: 1; font-size: 14px; font-weight: 600; color: #3d2c35; }
.ck-gw__radio {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #f0d0dc;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: border-color 0.2s;
}
.ck-gw--active .ck-gw__radio { border-color: #e8405a; }
.ck-gw__dot { width: 9px; height: 9px; border-radius: 50%; background: #e8405a; }

/* ── CARD LOGOS ── */
.ck-card-badges { display: flex; gap: 5px; }
.ck-cb {
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.5px;
}
.ck-cb--visa  { background: #e8f0fe; color: #1a3a8f; border: 1px solid #c5d5f5; }
.ck-cb--mc    { background: #fef0f4; color: #c4184a; border: 1px solid #ffd6de; }
.ck-cb--amex  { background: #f0fdf6; color: #059669; border: 1px solid #bbf7d0; }

/* ── VISUAL CARD ── */
.ck-vcard {
  margin: 0 24px 4px;
  border-radius: 18px;
  padding: 24px 26px 22px;
  background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 50%, #3b0764 100%);
  position: relative;
  overflow: hidden;
  box-shadow: 0 14px 40px rgba(79, 70, 229, 0.35);
  min-height: 188px;
  transition: background 0.4s;
}
.ck-vcard--default  { background: linear-gradient(135deg, #7c3aed, #4f46e5, #3b0764); }
.ck-vcard--visa     { background: linear-gradient(135deg, #1a365d, #2563eb, #1e40af); box-shadow: 0 14px 40px rgba(37,99,235,0.35); }
.ck-vcard--mastercard { background: linear-gradient(135deg, #e8405a, #c4184a, #7f1d1d); box-shadow: 0 14px 40px rgba(232,64,90,0.35); }
.ck-vcard--amex     { background: linear-gradient(135deg, #065f46, #059669, #047857); box-shadow: 0 14px 40px rgba(5,150,105,0.35); }

.ck-vcard__shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.07) 50%, transparent 60%);
  animation: cardShine 3.5s infinite;
}
@keyframes cardShine {
  0%  { transform: translateX(-120%); }
  100%{ transform: translateX(120%); }
}
.ck-vcard::before {
  content: '';
  position: absolute;
  top: -50px; right: -50px;
  width: 200px; height: 200px;
  border-radius: 50%;
  background: rgba(255,255,255,0.07);
}
.ck-vcard::after {
  content: '';
  position: absolute;
  bottom: -40px; left: -20px;
  width: 160px; height: 160px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
}

.ck-vcard__top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
}
.ck-vcard__chip {
  width: 38px;
  height: 28px;
  background: linear-gradient(135deg, #ffe082, #f59e0b);
  border-radius: 5px;
  position: relative;
}
.ck-vcard__chip-line {
  position: absolute;
  top: 50%; left: 0; right: 0;
  height: 1px;
  background: rgba(120, 80, 0, 0.35);
  transform: translateY(-50%);
}
.ck-vcard__chip-col {
  position: absolute;
  left: 50%; top: 0; bottom: 0;
  width: 1px;
  background: rgba(120, 80, 0, 0.35);
}
.ck-vcard__network { display: flex; align-items: center; }
.ck-vcard__net-visa  { font-family: 'DM Sans', sans-serif; font-size: 17px; font-weight: 900; color: rgba(255,255,255,0.95); letter-spacing: 1px; font-style: italic; }
.ck-vcard__net-amex  { font-size: 13px; font-weight: 900; color: rgba(255,255,255,0.9); letter-spacing: 1px; }
.ck-vcard__net-mc    { display: flex; }
.mc-c { width: 26px; height: 26px; border-radius: 50%; opacity: 0.9; }
.mc-c1 { background: #fff; }
.mc-c2 { background: rgba(255,255,255,0.55); margin-left: -10px; }
.ck-vcard__net-dots  { font-size: 18px; color: rgba(255,255,255,0.4); letter-spacing: 3px; }

.ck-vcard__number {
  font-family: 'Space Mono', monospace;
  font-size: 18px;
  font-weight: 400;
  color: rgba(255,255,255,0.95);
  letter-spacing: 2px;
  margin-bottom: 18px;
  position: relative;
  z-index: 1;
}
.ck-vcard__footer {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  position: relative;
  z-index: 1;
}
.ck-vcard__col { display: flex; flex-direction: column; gap: 3px; }
.ck-vcard__col--right { text-align: right; }
.ck-vcard__label {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: rgba(255,255,255,0.5);
}
.ck-vcard__value {
  font-family: 'Space Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: rgba(255,255,255,0.95);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ── SECURITY BADGES ── */
.ck-security {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px 14px;
  background: #f0fdf6;
  border-radius: 11px;
  border: 1px solid #d1fae5;
}
.ck-security__item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 600;
  color: #059669;
}

/* ── RIGHT COLUMN: SUMMARY ── */
.ck-right { position: sticky; top: 86px; }
.ck-summary {
  background: #fff;
  border-radius: 22px;
  border: 1.5px solid #f5dce5;
  padding: 24px;
  box-shadow: 0 6px 28px rgba(232, 64, 90, 0.09);
}
.ck-summary__title {
  font-family: 'Playfair Display', serif;
  font-size: 17px;
  font-weight: 800;
  color: #3d2c35;
  margin-bottom: 2px;
}
.ck-summary__sub { font-size: 12px; color: #b08090; margin-bottom: 18px; }

/* Items */
.ck-items { display: flex; flex-direction: column; gap: 10px; margin-bottom: 14px; }
.ck-item {
  display: grid;
  grid-template-columns: 44px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 11px 12px;
  background: #fdf6f8;
  border-radius: 12px;
  border: 1px solid #f5e8ed;
}
.ck-item__date {
  background: #fff;
  border: 1px solid #ffd6de;
  border-radius: 8px;
  padding: 5px 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.ck-item__day   { font-family: 'Playfair Display', serif; font-size: 15px; font-weight: 800; color: #e8405a; line-height: 1; }
.ck-item__month { font-size: 8px; font-weight: 700; color: #c4184a; letter-spacing: 0.5px; }
.ck-item__info  { min-width: 0; }
.ck-item__title {
  font-size: 12px;
  font-weight: 700;
  color: #3d2c35;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ck-item__meta  { font-size: 10px; color: #b08090; margin-bottom: 2px; }
.ck-item__qty   { font-size: 10px; color: #e8405a; font-weight: 700; }
.ck-item__price { font-family: 'Playfair Display', serif; font-size: 14px; font-weight: 800; color: #e8405a; white-space: nowrap; }
.ck-item__price small { font-size: 10px; font-weight: 600; }

/* Gateway pill */
.ck-gw-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  padding: 4px 11px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 500;
  margin-bottom: 10px;
}

.ck-sep { height: 1px; background: #f5e8ed; margin: 10px 0; }

/* Totals */
.ck-totals { display: flex; flex-direction: column; gap: 7px; margin-bottom: 8px; }
.ck-total-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #7d5a68;
}
.ck-free {
  background: #f0fdf6;
  color: #059669;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  border-radius: 20px;
  border: 1px solid #bbf7d0;
}

/* Grand total */
.ck-grand {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 0 16px;
  border-top: 1.5px dashed #f5dce5;
  margin-top: 4px;
}
.ck-grand span:first-child { font-size: 14px; font-weight: 700; color: #3d2c35; }
.ck-grand__amount {
  font-family: 'Playfair Display', serif;
  font-size: 26px;
  font-weight: 800;
  color: #e8405a;
  letter-spacing: -0.5px;
}
.ck-grand__amount small { font-size: 13px; font-weight: 600; color: #b08090; }

/* Buttons */
.ck-pay-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  padding: 15px;
  background: linear-gradient(135deg, #e8405a, #c4184a);
  border: none;
  border-radius: 13px;
  color: #fff;
  font-family: 'DM Sans', sans-serif;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s;
  box-shadow: 0 6px 20px rgba(232, 64, 90, 0.35);
  margin-bottom: 10px;
  letter-spacing: 0.2px;
}
.ck-pay-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 28px rgba(232, 64, 90, 0.45);
}
.ck-pay-btn:active:not(:disabled) { transform: translateY(0); }
.ck-pay-btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }

.ck-back-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 11px;
  background: transparent;
  border: 1.5px solid #f0d0dc;
  border-radius: 13px;
  color: #e8405a;
  font-family: 'DM Sans', sans-serif;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 12px;
}
.ck-back-btn:hover:not(:disabled) { background: #fff5f7; border-color: #e8405a; }
.ck-back-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.ck-notice {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 11px;
  color: #b08090;
  line-height: 1.5;
}
.ck-notice__link { color: #e8405a; text-decoration: none; font-weight: 600; }
.ck-notice__link:hover { text-decoration: underline; }

/* ── FOOTER ── */
.ck-footer {
  background: #fdf0f4;
  border-top: 1px solid #f5dce5;
  padding: 18px 40px;
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #c5a8b5;
  margin-top: auto;
}
.ck-footer__heart { color: #e8405a; }

/* ── RESPONSIVE ── */
@media (max-width: 900px) {
  .ck-grid { grid-template-columns: 1fr; }
  .ck-right { position: static; }
}
@media (max-width: 600px) {
  .ck-nav  { padding: 0 16px; }
  .ck-wrap { padding: 0 14px; }
  .ck-row  { grid-template-columns: 1fr; }
  .ck-footer { flex-direction: column; gap: 4px; align-items: center; }
  .ck-stepper { padding: 16px 14px; }
}

/* ── TICKET PAGE ── */
.ck-ticket-page { flex: 1; padding: 36px 0 60px; background: #fdf6f8; }
.ck-ticket-wrap { max-width: 820px; margin: 0 auto; padding: 0 24px; }

.ck-ticket-hero {
  display: flex; align-items: center; gap: 18px;
  background: linear-gradient(135deg, #fff0f4, #fde8ef);
  border: 1.5px solid #ffd6de;
  border-radius: 20px; padding: 22px 26px;
  margin-bottom: 28px;
  box-shadow: 0 4px 20px rgba(232,64,90,0.08);
}
.ck-ticket-hero__icon {
  width: 60px; height: 60px; border-radius: 50%;
  background: linear-gradient(135deg, #34d399, #059669);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 6px 20px rgba(5,150,105,0.3);
}
.ck-ticket-hero__title {
  font-family: 'Playfair Display', serif;
  font-size: 22px; font-weight: 800; color: #3d2c35; margin-bottom: 4px;
}
.ck-ticket-hero__sub { font-size: 13px; color: #b08090; }
.ck-ticket-hero__sub strong { color: #3d2c35; }

/* Tickets list */
.ck-tickets { display: flex; flex-direction: column; gap: 24px; margin-bottom: 28px; }
.ck-ticket {
  background: #fff;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 36px rgba(232,64,90,0.13), 0 2px 8px rgba(0,0,0,0.04);
  border: 1px solid #f5dce5;
}
.ck-ticket__body {
  display: grid;
  grid-template-columns: 1fr 170px;
  min-height: 230px;
}
.ck-ticket__left {
  padding: 26px 26px 22px;
  display: flex; flex-direction: column; gap: 0;
}
.ck-ticket__event {
  display: flex; gap: 16px; align-items: flex-start;
  margin-bottom: 18px;
}
.ck-ticket__date-badge {
  background: linear-gradient(135deg, #e8405a, #c4184a);
  border-radius: 12px; padding: 10px 13px;
  display: flex; flex-direction: column; align-items: center;
  flex-shrink: 0;
  box-shadow: 0 5px 15px rgba(232,64,90,0.3);
}
.ck-ticket__date-day   { font-family:'Playfair Display',serif; font-size:26px; font-weight:800; color:#fff; line-height:1; }
.ck-ticket__date-month { font-size:10px; font-weight:700; color:rgba(255,255,255,0.85); letter-spacing:1px; margin-top:2px; }
.ck-ticket__date-year  { font-size:9px; font-weight:600; color:rgba(255,255,255,0.6); }
.ck-ticket__event-info { flex: 1; }
.ck-ticket__event-label {
  font-size: 9px; font-weight: 700; color: #e8405a;
  letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px;
}
.ck-ticket__event-name {
  font-family: 'Playfair Display', serif;
  font-size: 17px; font-weight: 800; color: #3d2c35;
  line-height: 1.25; margin-bottom: 7px;
}
.ck-ticket__event-meta {
  display: flex; align-items: center; gap: 5px;
  font-size: 11px; color: #b08090; margin-bottom: 3px;
}
/* Tear */
.ck-ticket__tear {
  display: flex; align-items: center; margin: 12px 0;
}
.ck-ticket__tear-notch {
  width: 18px; height: 18px; border-radius: 50%;
  background: #fdf6f8; border: 1px solid #f5dce5; flex-shrink: 0;
}
.ck-ticket__tear-notch--l { margin-left: -37px; }
.ck-ticket__tear-notch--r { margin-right: -37px; }
.ck-ticket__tear-line { flex: 1; border-top: 2px dashed #f5dce5; margin: 0 4px; }
/* Details */
.ck-ticket__details {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
}
.ck-ticket__detail-lbl {
  font-size: 9px; font-weight: 700; color: #c5a8b5;
  text-transform: uppercase; letter-spacing: 1px; margin-bottom: 3px;
}
.ck-ticket__detail-val { font-size: 12px; font-weight: 700; color: #3d2c35; }
.ck-ticket__detail-val--pink { color: #e8405a; }
/* QR Side */
.ck-ticket__qr {
  background: linear-gradient(160deg, #fff8fa, #fef0f4);
  border-left: 2px dashed #f5dce5;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  padding: 22px 16px; gap: 9px;
}
.ck-ticket__qr-box {
  background: #fff; border-radius: 12px; padding: 8px;
  box-shadow: 0 4px 14px rgba(232,64,90,0.1);
  border: 1px solid #f5dce5;
}
.ck-ticket__qr-img { width: 110px; height: 110px; display: block; }
.ck-ticket__qr-label {
  font-size: 9px; font-weight: 600; color: #c5a8b5;
  text-transform: uppercase; letter-spacing: 0.8px; text-align: center;
}
.ck-ticket__num { text-align: center; }
.ck-ticket__num-lbl { font-size: 8px; font-weight: 700; color: #c5a8b5; text-transform: uppercase; letter-spacing: 1px; }
.ck-ticket__num-val { font-family: 'Space Mono', monospace; font-size: 16px; font-weight: 700; color: #e8405a; }
/* Barcode */
.ck-ticket__barcode {
  background: linear-gradient(135deg, #5d3a48, #3d2c35);
  padding: 12px 24px;
  display: flex; flex-direction: column; align-items: center; gap: 5px;
}
.ck-ticket__bars { display: flex; align-items: flex-end; gap: 2px; height: 36px; }
.ck-ticket__bar  { width: 2px; background: rgba(255,255,255,0.65); border-radius: 1px; }
.ck-ticket__barcode-txt {
  font-family: 'Space Mono', monospace;
  font-size: 9px; color: rgba(255,255,255,0.45);
  letter-spacing: 2px; text-transform: uppercase;
}
/* Actions */
.ck-ticket-actions {
  display: flex; gap: 12px; justify-content: center;
  margin-bottom: 20px; flex-wrap: wrap;
}
.ck-ticket-btn {
  display: flex; align-items: center; gap: 9px;
  padding: 13px 24px; border-radius: 13px;
  font-family: 'DM Sans', sans-serif;
  font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.25s; border: none;
}
.ck-ticket-btn--primary {
  background: linear-gradient(135deg, #e8405a, #c4184a);
  color: #fff; box-shadow: 0 6px 20px rgba(232,64,90,0.3);
}
.ck-ticket-btn--primary:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(232,64,90,0.4); }
.ck-ticket-btn--dashboard {
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
  color: #fff;
  box-shadow: 0 6px 20px rgba(79,70,229,0.3);
}
.ck-ticket-btn--dashboard:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(79,70,229,0.4); }
.ck-ticket-btn--outline {
  background: #fff; color: #e8405a;
  border: 1.5px solid #f0d0dc !important;
}
.ck-ticket-btn--outline:hover { background: #fff5f7; border-color: #e8405a !important; }
.ck-ticket-notice {
  display: flex; align-items: center; gap: 8px; justify-content: center;
  font-size: 12px; color: #b08090; text-align: center;
}
@media print {
  .ck-nav, .ck-stepper, .ck-ticket-hero, .ck-ticket-actions, .ck-ticket-notice, .ck-footer { display: none !important; }
  .ck-ticket { box-shadow: none; border: 1px solid #ddd; }
}
@media (max-width: 600px) {
  .ck-ticket__body { grid-template-columns: 1fr; }
  .ck-ticket__qr { border-left: none; border-top: 2px dashed #f5dce5; flex-direction: row; justify-content: space-around; }
  .ck-ticket__details { grid-template-columns: repeat(2,1fr); }
}

</style>