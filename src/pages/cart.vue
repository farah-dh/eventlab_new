<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { computed } from 'vue'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const cart = useCartStore()

const formatTime = (d: string) => {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
}
const getDateParts = (d: string) => {
  if (!d) return { day: '--', month: '---' }
  const date = new Date(d)
  return {
    day: date.getDate().toString().padStart(2, '0'),
    month: date.toLocaleDateString('fr-FR', { month: 'short' }).toUpperCase().replace('.', ''),
  }
}

const itemSubtotal = (item: any) => (item.price * item.quantity).toFixed(2)
const finalTotal = computed(() => cart.totalPrice)

const goHome     = () => router.push('/')
const goToEvent  = (id: number) => router.push(`/events/${id}`)
const goToLogin  = () => router.push('/login')
const goToRegister = () => router.push('/register')

// ✅ CORRIGÉ : toujours passer par le dashboard
const proceedToCheckout = () => {
  if (cart.items.length === 0) {
    alert('Votre panier est vide')
    return
  }

  const token = localStorage.getItem('access_token')
  if (!token) {
    // Pas connecté → login (pas de setItem, login redirige vers dashboard)
    router.push('/login')
    return
  }

  // Connecté → dashboard où le panier est visible avec le bouton paiement
  router.push('/user/dashboard')
}

const removeItem = (id: number) => {
  if (confirm('Retirer ce billet du panier ?')) cart.removeItem(id)
}
const clearAll = () => {
  if (confirm('Vider complètement le panier ?')) cart.clearCart()
}
</script>

<template>
  <div class="cart">
    <nav class="cart-nav">
      <div class="cart-nav__inner">
        <div class="cart-logo" @click="goHome()">
          <div class="cart-logo__mark">E</div>
          <span class="cart-logo__name">EventLab</span>
        </div>
        <div class="cart-nav__crumb">
          <button class="cart-crumb-btn" @click="goHome()">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
            Accueil
          </button>
          <span class="cart-crumb-sep">/</span>
          <span class="cart-crumb-cur">Mon panier</span>
        </div>
        <div class="cart-nav__actions">
          <button class="cart-btn cart-ghost" @click="goToLogin()">Connexion</button>
          <button class="cart-btn cart-primary" @click="goToRegister()">S'inscrire</button>
        </div>
      </div>
    </nav>

    <header class="cart-header">
      <div class="cart-wrap">
        <div class="cart-header__content">
          <div class="cart-header__icon">🛒</div>
          <h1 class="cart-header__title">Mon panier</h1>
          <p class="cart-header__sub" v-if="cart.totalItems > 0">
            {{ cart.totalItems }} billet{{ cart.totalItems > 1 ? 's' : '' }} dans votre panier
          </p>
          <p class="cart-header__sub" v-else>Votre panier est vide</p>
        </div>
      </div>
    </header>

    <div class="cart-main">
      <div class="cart-wrap">

        <div v-if="cart.items.length === 0" class="cart-empty">
          <div class="cart-empty__icon">🛍️</div>
          <h2 class="cart-empty__title">Votre panier est vide</h2>
          <p class="cart-empty__sub">Découvrez nos événements et ajoutez vos billets préférés !</p>
          <button class="cart-btn cart-primary cart-btn--lg" @click="goHome()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
            Découvrir les événements
          </button>
        </div>

        <div v-else class="cart-grid">
          <div class="cart-items">
            <div class="cart-items__head">
              <h2 class="cart-items__title">Vos billets ({{ cart.items.length }})</h2>
              <button class="cart-clear" @click="clearAll">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                Vider le panier
              </button>
            </div>

            <div class="cart-item" v-for="item in cart.items" :key="item.id">
              <div class="cart-item__date">
                <span class="cart-item__date-day">{{ getDateParts(item.date).day }}</span>
                <span class="cart-item__date-month">{{ getDateParts(item.date).month }}</span>
              </div>
              <div class="cart-item__img" @click="goToEvent(item.eventId)">
                <img v-if="item.image" :src="item.image" :alt="item.title" />
                <div v-else class="cart-item__ph">🎪</div>
              </div>
              <div class="cart-item__info">
                <div class="cart-item__cat">{{ item.category }}</div>
                <h3 class="cart-item__title" @click="goToEvent(item.eventId)">{{ item.title }}</h3>
                <div class="cart-item__metas">
                  <span class="cart-item__meta">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12,6 12,12 16,14"/></svg>
                    {{ formatTime(item.date) }}
                  </span>
                  <span class="cart-item__meta">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                    {{ item.location }}
                  </span>
                </div>
                <div class="cart-item__price">
                  {{ Number(item.price).toFixed(2) }} <small>DT / billet</small>
                </div>
              </div>
              <div class="cart-item__actions">
                <div class="cart-item__qty">
                  <button @click="cart.decrement(item.id)" :disabled="item.quantity <= 1">−</button>
                  <span>{{ item.quantity }}</span>
                  <button @click="cart.increment(item.id)">+</button>
                </div>
                <div class="cart-item__subtotal">{{ itemSubtotal(item) }} <small>DT</small></div>
                <button class="cart-item__rm" @click="removeItem(item.id)">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </div>
            </div>
          </div>

          <aside class="cart-summary">
            <div class="cart-summary__card">
              <h3 class="cart-summary__title">Récapitulatif</h3>
              <div class="cart-summary__line">
                <span>Sous-total ({{ cart.totalItems }} billet{{ cart.totalItems > 1 ? 's' : '' }})</span>
                <span class="cart-summary__val">{{ cart.totalPrice.toFixed(2) }} DT</span>
              </div>
              <div class="cart-summary__line cart-summary__line--free">
                <span>Frais de service</span>
                <span class="cart-summary__val cart-summary__val--free">✓ Offerts</span>
              </div>
              <div class="cart-summary__total">
                <span>Total</span>
                <span class="cart-summary__total-amount">{{ finalTotal.toFixed(2) }} <small>DT</small></span>
              </div>

              <!-- ✅ Bouton corrigé -->
              <button class="cart-checkout" @click="proceedToCheckout">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                Valider la commande
              </button>

              <button class="cart-continue" @click="goHome()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
                Continuer mes achats
              </button>
              <div class="cart-summary__secure">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                Paiement 100% sécurisé
              </div>
            </div>
            <div class="cart-promo">
              <div class="cart-promo__head"><span>🎁</span> Code promo</div>
              <div class="cart-promo__form">
                <input type="text" placeholder="Entrez votre code…" />
                <button>Appliquer</button>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>

    <footer class="cart-footer">
      <div class="cart-wrap">
        <div class="cart-footer__bot">
          <span>© 2026 EventLab. Tous droits réservés.</span>
          <span class="cart-footer__made">Fait avec 💖 en Tunisie</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,700&family=Outfit:wght@300;400;500;600;700;800&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
.cart{font-family:'Outfit',sans-serif;background:#FFF5F7;color:#1a0a12;min-height:100vh}
.cart-nav{position:sticky;top:0;z-index:999;padding:0 40px;background:rgba(255,255,255,.96);backdrop-filter:blur(20px);box-shadow:0 1px 0 rgba(233,30,140,.1)}
.cart-nav__inner{max-width:1280px;margin:0 auto;height:70px;display:flex;align-items:center;justify-content:space-between;gap:30px}
.cart-nav__crumb{display:flex;align-items:center;gap:8px;font-size:14px;flex:1}
.cart-crumb-btn{display:flex;align-items:center;gap:5px;background:#FCE4EC;color:#E91E8C;border:none;border-radius:8px;padding:6px 14px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Outfit',sans-serif;transition:all .2s}
.cart-crumb-btn:hover{background:#F8BBD0}
.cart-crumb-sep{color:#F48FB1}
.cart-crumb-cur{font-weight:700;color:#E91E8C;font-size:13px}
.cart-nav__actions{display:flex;gap:10px}
.cart-logo{display:flex;align-items:center;gap:10px;cursor:pointer}
.cart-logo__mark{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,#E91E8C,#AD1457);display:flex;align-items:center;justify-content:center;color:#fff;font-family:'Playfair Display',serif;font-weight:700;font-size:18px;flex-shrink:0;box-shadow:0 4px 14px rgba(233,30,140,.35)}
.cart-logo__name{font-family:'Playfair Display',serif;font-weight:700;font-size:21px;color:#880E4F}
.cart-btn{display:inline-flex;align-items:center;gap:6px;border:none;cursor:pointer;border-radius:10px;font-size:14px;font-weight:600;padding:10px 22px;transition:all .25s;font-family:'Outfit',sans-serif;line-height:1;white-space:nowrap}
.cart-btn--lg{padding:14px 28px;font-size:15px}
.cart-primary{background:linear-gradient(135deg,#E91E8C,#AD1457);color:#fff;box-shadow:0 4px 16px rgba(233,30,140,.35)}
.cart-primary:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(233,30,140,.45)}
.cart-ghost{background:transparent;color:#E91E8C;border:1.5px solid #F8BBD0}
.cart-ghost:hover{background:#FFF5F7;border-color:#F48FB1}
.cart-header{background:linear-gradient(135deg,#E91E8C 0%,#AD1457 50%,#880E4F 100%);padding:50px 40px;position:relative;overflow:hidden}
.cart-header::before{content:'';position:absolute;inset:0;background-image:radial-gradient(circle at 20% 50%,rgba(255,255,255,.15),transparent 50%),radial-gradient(circle at 80% 50%,rgba(255,255,255,.1),transparent 50%)}
.cart-wrap{max-width:1280px;margin:0 auto;padding:0 40px;position:relative;z-index:1}
.cart-header__content{color:#fff;text-align:center}
.cart-header__icon{font-size:50px;margin-bottom:12px}
.cart-header__title{font-family:'Playfair Display',serif;font-size:clamp(32px,4vw,44px);font-weight:800;margin-bottom:8px}
.cart-header__sub{font-size:15px;color:rgba(255,255,255,.85)}
.cart-main{padding:50px 40px 60px}
.cart-empty{text-align:center;padding:80px 20px}
.cart-empty__icon{font-size:72px;margin-bottom:20px}
.cart-empty__title{font-family:'Playfair Display',serif;font-size:28px;color:#880E4F;margin-bottom:12px}
.cart-empty__sub{font-size:15px;color:#9e6878;margin-bottom:28px}
.cart-grid{display:grid;grid-template-columns:1fr 380px;gap:28px;align-items:flex-start}
.cart-items{display:flex;flex-direction:column;gap:16px}
.cart-items__head{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.cart-items__title{font-family:'Playfair Display',serif;font-size:20px;font-weight:700;color:#1a0a12}
.cart-clear{display:flex;align-items:center;gap:6px;background:transparent;border:none;color:#b91c1c;cursor:pointer;font-family:'Outfit',sans-serif;font-size:13px;font-weight:600;padding:6px 12px;border-radius:8px;transition:all .2s}
.cart-clear:hover{background:#fef2f2}
.cart-item{display:grid;grid-template-columns:70px 120px 1fr auto;gap:18px;background:#fff;border:1.5px solid #FCE4EC;border-radius:16px;padding:18px;transition:all .25s;align-items:center}
.cart-item:hover{border-color:#F48FB1;box-shadow:0 8px 24px rgba(233,30,140,.1)}
.cart-item__date{background:linear-gradient(135deg,#FFF5F7,#FCE4EC);border:1.5px solid #F8BBD0;border-radius:12px;padding:10px 8px;text-align:center;display:flex;flex-direction:column;align-items:center}
.cart-item__date-day{font-family:'Playfair Display',serif;font-size:24px;font-weight:800;color:#E91E8C;line-height:1}
.cart-item__date-month{font-size:10px;font-weight:700;color:#880E4F;letter-spacing:1.5px;margin-top:2px}
.cart-item__img{width:120px;height:100px;border-radius:10px;overflow:hidden;cursor:pointer;transition:all .2s}
.cart-item__img:hover{transform:scale(1.03)}
.cart-item__img img{width:100%;height:100%;object-fit:cover}
.cart-item__ph{width:100%;height:100%;background:linear-gradient(135deg,#FCE4EC,#F48FB1);display:flex;align-items:center;justify-content:center;font-size:32px}
.cart-item__info{min-width:0}
.cart-item__cat{display:inline-block;background:#FCE4EC;color:#E91E8C;padding:3px 10px;border-radius:100px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.cart-item__title{font-family:'Playfair Display',serif;font-size:17px;font-weight:700;color:#1a0a12;cursor:pointer;transition:color .2s;margin-bottom:6px;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
.cart-item__title:hover{color:#E91E8C}
.cart-item__metas{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:8px}
.cart-item__meta{display:flex;align-items:center;gap:4px;font-size:12px;color:#9e6878}
.cart-item__price{font-size:13px;font-weight:700;color:#AD1457}
.cart-item__price small{color:#9e6878;font-weight:500}
.cart-item__actions{display:flex;flex-direction:column;gap:10px;align-items:flex-end;min-width:130px}
.cart-item__qty{display:flex;align-items:center;gap:4px;background:#FFF5F7;border:1.5px solid #FCE4EC;border-radius:10px;padding:3px}
.cart-item__qty button{width:28px;height:28px;border:none;background:transparent;color:#E91E8C;font-size:18px;font-weight:700;cursor:pointer;border-radius:7px;transition:all .2s}
.cart-item__qty button:hover:not(:disabled){background:#FCE4EC}
.cart-item__qty button:disabled{opacity:.3;cursor:not-allowed}
.cart-item__qty span{min-width:24px;text-align:center;font-size:14px;font-weight:700;color:#1a0a12}
.cart-item__subtotal{font-family:'Playfair Display',serif;font-size:20px;font-weight:800;color:#E91E8C}
.cart-item__subtotal small{font-size:13px;font-weight:600}
.cart-item__rm{width:32px;height:32px;border-radius:8px;border:none;background:#fef2f2;color:#b91c1c;cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center}
.cart-item__rm:hover{background:#b91c1c;color:#fff}
.cart-summary{display:flex;flex-direction:column;gap:16px;position:sticky;top:90px}
.cart-summary__card{background:#fff;border:1.5px solid #FCE4EC;border-radius:18px;padding:26px;box-shadow:0 8px 28px rgba(233,30,140,.1)}
.cart-summary__title{font-family:'Playfair Display',serif;font-size:20px;font-weight:800;color:#1a0a12;margin-bottom:18px;padding-bottom:14px;border-bottom:1.5px solid #FCE4EC}
.cart-summary__line{display:flex;justify-content:space-between;align-items:center;padding:8px 0;font-size:14px;color:#4a0a2e}
.cart-summary__val{font-weight:700;color:#1a0a12}
.cart-summary__val--free{color:#047857;font-weight:700}
.cart-summary__line--free{color:#047857}
.cart-summary__total{display:flex;justify-content:space-between;align-items:center;padding:16px 0;margin:8px 0 18px;border-top:1.5px dashed #FCE4EC;font-size:15px;font-weight:700;color:#1a0a12}
.cart-summary__total-amount{font-family:'Playfair Display',serif;font-size:28px;font-weight:800;color:#E91E8C}
.cart-summary__total-amount small{font-size:14px;font-weight:600}
.cart-checkout{width:100%;display:flex;align-items:center;justify-content:center;gap:8px;padding:14px;background:linear-gradient(135deg,#E91E8C,#AD1457);border:none;border-radius:12px;color:#fff;font-family:'Outfit',sans-serif;font-size:15px;font-weight:700;cursor:pointer;transition:all .25s;box-shadow:0 6px 20px rgba(233,30,140,.35);margin-bottom:10px}
.cart-checkout:hover{transform:translateY(-2px);box-shadow:0 10px 28px rgba(233,30,140,.5)}
.cart-continue{width:100%;display:flex;align-items:center;justify-content:center;gap:6px;padding:12px;background:transparent;border:1.5px solid #F8BBD0;border-radius:12px;color:#E91E8C;font-family:'Outfit',sans-serif;font-size:14px;font-weight:600;cursor:pointer;transition:all .2s}
.cart-continue:hover{background:#FFF5F7;border-color:#E91E8C}
.cart-summary__secure{display:flex;align-items:center;justify-content:center;gap:6px;margin-top:16px;font-size:11px;color:#9e6878}
.cart-promo{background:#fff;border:1.5px solid #FCE4EC;border-radius:14px;padding:18px}
.cart-promo__head{font-size:13px;font-weight:700;color:#1a0a12;margin-bottom:12px}
.cart-promo__head span{font-size:16px;margin-right:6px}
.cart-promo__form{display:flex;gap:8px}
.cart-promo__form input{flex:1;border:1.5px solid #FCE4EC;border-radius:9px;padding:9px 12px;font-family:'Outfit',sans-serif;font-size:13px;color:#1a0a12;outline:none}
.cart-promo__form input:focus{border-color:#E91E8C}
.cart-promo__form button{padding:0 14px;background:linear-gradient(135deg,#E91E8C,#AD1457);border:none;border-radius:9px;color:#fff;font-family:'Outfit',sans-serif;font-size:13px;font-weight:700;cursor:pointer;transition:all .2s}
.cart-promo__form button:hover{opacity:.9}
.cart-footer{background:#1a0a12;padding:24px 0}
.cart-footer__bot{display:flex;justify-content:space-between;align-items:center;font-size:13px;color:#5e2b3d}
.cart-footer__made{color:#F48FB1}
@media(max-width:1024px){.cart-grid{grid-template-columns:1fr}.cart-summary{position:static}}
@media(max-width:768px){
  .cart-nav{padding:0 16px}
  .cart-nav__crumb{display:none}
  .cart-wrap{padding:0 20px}
  .cart-header{padding:36px 20px}
  .cart-main{padding:36px 20px}
  .cart-item{grid-template-columns:60px 1fr;grid-template-areas:"date info" "img img" "actions actions";gap:14px}
  .cart-item__date{grid-area:date}
  .cart-item__img{grid-area:img;width:100%;height:140px}
  .cart-item__info{grid-area:info}
  .cart-item__actions{grid-area:actions;flex-direction:row;justify-content:space-between;align-items:center;width:100%;padding-top:12px;border-top:1px solid #FCE4EC}
  .cart-footer__bot{flex-direction:column;gap:6px;text-align:center}
}
</style>