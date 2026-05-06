<script setup lang="ts">
const router = useRouter()

const currentYear = new Date().getFullYear()

const categories = [
  { name: '🎵 Concerts & Musique', key: 'musique' },
  { name: '🎭 Théâtre & Spectacles', key: 'theatre' },
  { name: '⚽ Sport & Fitness', key: 'sport' },
  { name: '💻 Tech & Business', key: 'tech' },
  { name: '🎨 Art & Culture', key: 'art' },
  { name: '🎪 Festivals', key: 'festival' },
]

const cities = [
  { name: 'Tunis', emoji: '🏙️' },
  { name: 'Sousse', emoji: '🌊' },
  { name: 'Sfax', emoji: '🏛️' },
  { name: 'Hammamet', emoji: '🌴' },
  { name: 'Djerba', emoji: '🏝️' },
  { name: 'Monastir', emoji: '⛵' },
]

const socials = [
  { name: 'Facebook', href: '#', icon: 'f' },
  { name: 'Instagram', href: '#', icon: 'ig' },
  { name: 'Twitter', href: '#', icon: 'X' },
  { name: 'LinkedIn', href: '#', icon: 'in' },
  { name: 'TikTok', href: '#', icon: 'tk' },
]

const newsletter = ref('')
const newsletterMsg = ref('')
const subscribeNewsletter = () => {
  if (!newsletter.value || !newsletter.value.includes('@')) {
    newsletterMsg.value = '⚠️ Email invalide'
    setTimeout(() => newsletterMsg.value = '', 3000)
    return
  }
  newsletterMsg.value = '✨ Merci ! Vous êtes inscrit(e)'
  newsletter.value = ''
  setTimeout(() => newsletterMsg.value = '', 4000)
}
</script>

<template>
  <footer class="ft">

    <!-- ══ NEWSLETTER BAND ══ -->
    <div class="ft-news">
      <div class="ft-news__inner">
        <div class="ft-news__left">
          <span class="ft-news__icon">📨</span>
          <div>
            <h3 class="ft-news__title">Restez informé(e)</h3>
            <p class="ft-news__sub">Les meilleurs événements de Tunisie dans votre boîte mail</p>
          </div>
        </div>
        <div class="ft-news__form">
          <input
            v-model="newsletter"
            type="email"
            placeholder="votre@email.com"
            @keyup.enter="subscribeNewsletter"
          />
          <button @click="subscribeNewsletter">S'inscrire →</button>
        </div>
      </div>
      <p v-if="newsletterMsg" class="ft-news__msg">{{ newsletterMsg }}</p>
    </div>

    <!-- ══ MAIN FOOTER ══ -->
    <div class="ft-main">
      <div class="ft-wrap">

        <!-- Brand -->
        <div class="ft-brand">
          <div class="ft-logo" @click="router.push('/')">
            <div class="ft-logo__mark">E</div>
            <div>
              <span class="ft-logo__name">EventLab</span>
              <span class="ft-logo__sub">Billetterie & Événements</span>
            </div>
          </div>
          <p class="ft-brand__desc">
            La plateforme de billetterie #1 en Tunisie. Découvrez, réservez et vivez des expériences inoubliables partout en Tunisie.
          </p>

          <!-- Socials -->
          <div class="ft-socials">
            <a v-for="s in socials" :key="s.name" :href="s.href" :aria-label="s.name" class="ft-social">
              {{ s.icon }}
            </a>
          </div>

          <!-- Stats -->
          <div class="ft-stats">
            <div class="ft-stat">
              <span class="ft-stat__num">200+</span>
              <span class="ft-stat__lbl">Événements</span>
            </div>
            <div class="ft-stat__sep"></div>
            <div class="ft-stat">
              <span class="ft-stat__num">50K+</span>
              <span class="ft-stat__lbl">Participants</span>
            </div>
            <div class="ft-stat__sep"></div>
            <div class="ft-stat">
              <span class="ft-stat__num">4.9★</span>
              <span class="ft-stat__lbl">Avis</span>
            </div>
          </div>
        </div>

        <!-- Catégories -->
        <div class="ft-col">
          <h4 class="ft-col__title">
            <span class="ft-col__dot"></span>
            Catégories
          </h4>
          <ul class="ft-list">
            <li v-for="cat in categories" :key="cat.key">
              <a class="ft-link" @click="router.push('/')">{{ cat.name }}</a>
            </li>
          </ul>
        </div>

        <!-- Villes -->
        <div class="ft-col">
          <h4 class="ft-col__title">
            <span class="ft-col__dot"></span>
            Villes
          </h4>
          <ul class="ft-list">
            <li v-for="city in cities" :key="city.name">
              <a class="ft-link" @click="router.push('/')">
                {{ city.emoji }} {{ city.name }}
              </a>
            </li>
          </ul>
        </div>

        <!-- Liens utiles -->
        <div class="ft-col">
          <h4 class="ft-col__title">
            <span class="ft-col__dot"></span>
            Compte
          </h4>
          <ul class="ft-list">
            <li><a class="ft-link" @click="router.push('/login')">🔑 Se connecter</a></li>
            <li><a class="ft-link" @click="router.push('/register')">✨ S'inscrire</a></li>
            <li><a class="ft-link" @click="router.push('/register')">🏢 Espace organisateur</a></li>
            <li><a class="ft-link" @click="router.push('/login')">📊 Mon dashboard</a></li>
          </ul>

          <h4 class="ft-col__title" style="margin-top:28px">
            <span class="ft-col__dot"></span>
            Légal
          </h4>
          <ul class="ft-list">
            <li><a href="#" class="ft-link">📄 CGU</a></li>
            <li><a href="#" class="ft-link">🔒 Confidentialité</a></li>
            <li><a href="#" class="ft-link">🍪 Cookies</a></li>
            <li><a href="#" class="ft-link">📞 Contact</a></li>
          </ul>
        </div>

      </div>
    </div>

    <!-- ══ BOTTOM BAR ══ -->
    <div class="ft-bottom">
      <div class="ft-wrap ft-bottom__inner">
        <span>© {{ currentYear }} EventLab. Tous droits réservés.</span>
        <div class="ft-bottom__badges">
          <span class="ft-badge">🔒 Paiements sécurisés</span>
          <span class="ft-badge">🇹🇳 Made in Tunisia</span>
          <span class="ft-badge">💖 Fait avec passion</span>
        </div>
      </div>
    </div>

  </footer>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Outfit:wght@400;500;600;700&display=swap');

.ft { font-family: 'Outfit', sans-serif; }

/* ══ NEWSLETTER BAND ══ */
.ft-news {
  background: linear-gradient(135deg, #E91E8C, #AD1457);
  padding: 32px 40px;
}
.ft-news__inner {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  flex-wrap: wrap;
}
.ft-news__left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.ft-news__icon { font-size: 36px; }
.ft-news__title {
  font-family: 'Playfair Display', serif;
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 4px;
}
.ft-news__sub { font-size: 13px; color: rgba(255,255,255,.8); }
.ft-news__form {
  display: flex;
  gap: 8px;
  background: rgba(255,255,255,.15);
  border: 1px solid rgba(255,255,255,.3);
  border-radius: 14px;
  padding: 6px;
  backdrop-filter: blur(10px);
  min-width: 380px;
}
.ft-news__form input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  padding: 10px 14px;
  font-size: 14px;
  color: #fff;
  font-family: 'Outfit', sans-serif;
}
.ft-news__form input::placeholder { color: rgba(255,255,255,.6); }
.ft-news__form button {
  background: #fff;
  color: #E91E8C;
  border: none;
  border-radius: 10px;
  padding: 10px 20px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  font-family: 'Outfit', sans-serif;
  white-space: nowrap;
  transition: all .2s;
}
.ft-news__form button:hover { background: #FCE4EC; transform: translateY(-1px); }
.ft-news__msg {
  text-align: center;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  margin-top: 12px;
  max-width: 1280px;
  margin-left: auto;
  margin-right: auto;
}

/* ══ MAIN ══ */
.ft-main {
  background: linear-gradient(135deg, #2a0619 0%, #1a0a12 50%, #0d0308 100%);
  padding: 64px 0 40px;
}
.ft-wrap {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 40px;
}
.ft-main .ft-wrap {
  display: grid;
  grid-template-columns: 1.8fr 1fr 1fr 1fr;
  gap: 48px;
}

/* Brand */
.ft-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  margin-bottom: 20px;
}
.ft-logo__mark {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #E91E8C, #AD1457);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(233,30,140,.4);
}
.ft-logo__name {
  display: block;
  font-family: 'Playfair Display', serif;
  font-size: 20px;
  font-weight: 800;
  color: #fff;
  line-height: 1;
}
.ft-logo__sub {
  display: block;
  font-size: 10px;
  color: rgba(255,255,255,.4);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-top: 3px;
}
.ft-brand__desc {
  font-size: 14px;
  color: rgba(255,255,255,.5);
  line-height: 1.7;
  margin-bottom: 24px;
  max-width: 300px;
}
.ft-socials {
  display: flex;
  gap: 8px;
  margin-bottom: 28px;
}
.ft-social {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,.5);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  transition: all .25s;
}
.ft-social:hover {
  background: linear-gradient(135deg, #E91E8C, #AD1457);
  border-color: transparent;
  color: #fff;
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(233,30,140,.4);
}
.ft-stats {
  display: flex;
  align-items: center;
  background: rgba(233,30,140,.08);
  border: 1px solid rgba(233,30,140,.2);
  border-radius: 14px;
  padding: 14px 20px;
  gap: 0;
}
.ft-stat { flex: 1; text-align: center; }
.ft-stat__num {
  display: block;
  font-family: 'Playfair Display', serif;
  font-size: 22px;
  font-weight: 800;
  background: linear-gradient(135deg, #E91E8C, #F48FB1);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.ft-stat__lbl {
  display: block;
  font-size: 10px;
  color: rgba(255,255,255,.4);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 3px;
}
.ft-stat__sep { width: 1px; height: 36px; background: rgba(233,30,140,.2); }

/* Colonnes -->
.ft-col__title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: #E91E8C;
  margin-bottom: 18px;
}
.ft-col__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #E91E8C;
  flex-shrink: 0;
}
.ft-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ft-link {
  font-size: 14px;
  color: rgba(255,255,255,.45);
  cursor: pointer;
  text-decoration: none;
  padding: 6px 10px;
  border-radius: 8px;
  display: block;
  transition: all .2s;
  background: transparent;
  border: none;
  font-family: 'Outfit', sans-serif;
  text-align: left;
  width: 100%;
}
.ft-link:hover {
  color: #F48FB1;
  background: rgba(233,30,140,.08);
  padding-left: 14px;
}

/* ══ BOTTOM ══ */
.ft-bottom {
  background: #0d0308;
  padding: 18px 40px;
  border-top: 1px solid rgba(233,30,140,.1);
}
.ft-bottom__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: rgba(255,255,255,.3);
}
.ft-bottom__badges { display: flex; gap: 12px; flex-wrap: wrap; }
.ft-badge {
  background: rgba(233,30,140,.08);
  border: 1px solid rgba(233,30,140,.15);
  border-radius: 100px;
  padding: 5px 12px;
  font-size: 11px;
  color: rgba(255,255,255,.5);
  font-weight: 600;
}

/* ══ RESPONSIVE ══ */
@media (max-width: 1024px) {
  .ft-main .ft-wrap { grid-template-columns: 1fr 1fr; gap: 36px; }
  .ft-news__form { min-width: auto; }
}
@media (max-width: 768px) {
  .ft-news { padding: 24px 20px; }
  .ft-news__inner { flex-direction: column; align-items: flex-start; }
  .ft-news__form { width: 100%; min-width: auto; flex-direction: column; }
  .ft-news__form button { width: 100%; }
  .ft-main .ft-wrap { grid-template-columns: 1fr; padding: 0 20px; }
  .ft-bottom { padding: 18px 20px; }
  .ft-bottom__inner { flex-direction: column; text-align: center; }
  .ft-bottom__badges { justify-content: center; }
}
</style>