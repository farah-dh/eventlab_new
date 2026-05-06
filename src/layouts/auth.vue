<template>
  <div class="auth-layout">

    <!-- ═══ SCÈNE ANIMÉE ═══ -->
    <div class="auth-scene">
      <div class="blob b1"></div>
      <div class="blob b2"></div>
      <div class="blob b3"></div>
      <div class="blob b4"></div>
      <div class="sparks">
        <div
          v-for="(s, i) in sparks" :key="i"
          class="spark"
          :style="{
            left: s.x + '%',
            bottom: s.y + '%',
            width: s.size + 'px',
            height: s.size + 'px',
            animationDuration: s.dur + 's',
            animationDelay: s.delay + 's',
            opacity: s.op
          }"
        ></div>
      </div>
      <div class="ring r1"></div>
      <div class="ring r2"></div>
    </div>

    <!-- ═══ HEADER ═══ -->
    <header class="auth-header">
      <div class="auth-header__inner">

        <div class="auth-logo" @click="router.push('/')">
          <div class="auth-logo__mark">E</div>
          <div>
            <span class="auth-logo__name">EventLab</span>
            <span class="auth-logo__sub">Billetterie &amp; Événements</span>
          </div>
        </div>

        <nav class="auth-nav">
          <RouterLink class="auth-nav__link" to="/login"    active-class="active">Connexion</RouterLink>
          <RouterLink class="auth-nav__link" to="/register" active-class="active">Créer un compte</RouterLink>
        </nav>

        <button class="auth-btn-back" @click="router.push('/')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <polyline points="15,18 9,12 15,6"/>
          </svg>
          Retour à l'accueil
        </button>

      </div>

      <div class="auth-progress">
        <div class="auth-progress__bar" :style="{ width: progressWidth }"></div>
      </div>
    </header>

    <!-- ═══ CONTENU ═══ -->
    <main class="auth-content">
      <RouterView />
    </main>

    <!-- ═══ FOOTER ═══ -->
    <footer class="auth-footer">
      <div class="auth-footer__inner">

        <div class="auth-footer__brand">
          <div class="auth-footer__logo" @click="router.push('/')">
            <div class="auth-footer__mark">E</div>
            <span>EventLab</span>
          </div>
          <p>La plateforme #1 de billetterie en Tunisie</p>
        </div>

        <div class="auth-footer__links">
          <a href="#">À propos</a>
          <span class="dot"></span>
          <a href="#">Aide</a>
          <span class="dot"></span>
          <a href="#">Confidentialité</a>
          <span class="dot"></span>
          <a href="#">Conditions</a>
        </div>

        <p class="auth-footer__copy">
          © {{ new Date().getFullYear() }} EventLab. Tous droits réservés.
        </p>

      </div>
    </footer>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const router = useRouter()
const route  = useRoute()

const sparks = ref<{ x: number; y: number; size: number; dur: number; delay: number; op: number }[]>([])

onMounted(() => {
  sparks.value = Array.from({ length: 40 }, () => ({
    x:     Math.random() * 100,
    y:     Math.random() * 40,
    size:  1.5 + Math.random() * 3,
    dur:   4 + Math.random() * 6,
    delay: Math.random() * 8,
    op:    0.2 + Math.random() * 0.5,
  }))
})

// ✅ CORRIGÉ : String(route.path) + imports explicites vue-router
const progressWidth = computed(() => {
  const path = String(route.path)
  const map: Record<string, string> = {
    '/login':           '33%',
    '/register':        '66%',
    '/forgot-password': '50%',
    '/reset-password':  '85%',
  }
  return map[path] ?? '20%'
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;0,700;1,700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── SHELL ── */
.auth-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: 'Plus Jakarta Sans', sans-serif;
  position: relative;
  overflow-x: hidden;
}

/* ── FOND ANIMÉ ── */
.auth-scene {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background: radial-gradient(ellipse 130% 110% at 50% -10%,
    #A82248 0%, #6B1230 30%, #2E0416 65%, #0D0005 100%);
}
.blob {
  position: absolute; border-radius: 50%;
  filter: blur(100px); mix-blend-mode: screen;
  animation: blobFloat linear infinite;
}
.b1 { width:650px; height:650px; background:rgba(168,34,72,.50); top:-180px; left:-120px; animation-duration:20s; }
.b2 { width:480px; height:480px; background:rgba(224,112,144,.25); top:50%; right:-80px; animation-duration:15s; animation-delay:-5s; }
.b3 { width:400px; height:400px; background:rgba(200,54,95,.32); bottom:-80px; left:35%; animation-duration:24s; animation-delay:-9s; }
.b4 { width:260px; height:260px; background:rgba(242,168,190,.15); top:25%; left:42%; animation-duration:17s; animation-delay:-3s; }
@keyframes blobFloat {
  0%   { transform: translateY(0) scale(1); }
  33%  { transform: translateY(-55px) scale(1.07); }
  66%  { transform: translateY(28px) scale(.94); }
  100% { transform: translateY(0) scale(1); }
}
.sparks { position: absolute; inset: 0; overflow: hidden; }
.spark  { position: absolute; border-radius: 50%; background: #fff; animation: sparkUp linear infinite; }
@keyframes sparkUp {
  0%   { opacity: 0; transform: translateY(0) scale(0); }
  10%  { opacity: 1; transform: translateY(-12px) scale(1); }
  90%  { opacity: .3; transform: translateY(-130px) scale(.4); }
  100% { opacity: 0; transform: translateY(-150px) scale(0); }
}
.ring {
  position: absolute; border-radius: 50%;
  border: 1px solid rgba(255,255,255,.07);
  top: 50%; left: 50%;
  animation: ringPulse ease-in-out infinite;
}
.r1 { width:900px; height:900px; transform:translate(-50%,-50%); animation-duration:7s; }
.r2 { width:560px; height:560px; transform:translate(-50%,-50%); animation-duration:7s; animation-delay:-3.5s; }
@keyframes ringPulse {
  0%,100% { opacity:.07; transform:translate(-50%,-50%) scale(1); }
  50%     { opacity:.15; transform:translate(-50%,-50%) scale(1.04); }
}

/* ── HEADER ── */
.auth-header {
  position: relative; z-index: 100;
  background: rgba(12, 1, 6, .6);
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-bottom: 1px solid rgba(255,255,255,.08);
  animation: slideDown .55s ease both;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-18px); }
  to   { opacity: 1; transform: translateY(0); }
}
.auth-header__inner {
  max-width: 1200px; margin: 0 auto;
  padding: 0 40px; height: 66px;
  display: flex; align-items: center;
  justify-content: space-between; gap: 20px;
}

/* Logo */
.auth-logo {
  display: flex; align-items: center; gap: 11px;
  cursor: pointer; flex-shrink: 0; transition: opacity .2s;
}
.auth-logo:hover { opacity: .8; }
.auth-logo__mark {
  width: 38px; height: 38px;
  background: rgba(255,255,255,.12);
  border: 1px solid rgba(255,255,255,.22);
  border-radius: 10px; backdrop-filter: blur(8px);
  display: grid; place-items: center;
  font-family: 'Cormorant Garamond', serif;
  font-size: 19px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.auth-logo__name {
  display: block; font-family: 'Cormorant Garamond', serif;
  font-size: 17px; font-weight: 600; color: #fff; line-height: 1;
}
.auth-logo__sub {
  display: block; font-size: 10px; color: rgba(255,255,255,.42);
  letter-spacing: .1em; text-transform: uppercase; margin-top: 3px;
}

/* Nav */
.auth-nav { display: flex; align-items: center; gap: 4px; }
.auth-nav__link {
  padding: 7px 18px; border-radius: 9px;
  font-size: 13px; font-weight: 600;
  color: rgba(255,255,255,.5); text-decoration: none;
  border: 1px solid transparent; transition: all .2s;
}
.auth-nav__link:hover { color: rgba(255,255,255,.88); background: rgba(255,255,255,.07); }
.auth-nav__link.active { color: #fff; background: rgba(200,54,95,.28); border-color: rgba(200,54,95,.4); }

/* Bouton retour */
.auth-btn-back {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px;
  background: rgba(255,255,255,.07);
  border: 1px solid rgba(255,255,255,.13);
  border-radius: 9px;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 12.5px; font-weight: 600; color: rgba(255,255,255,.7);
  cursor: pointer; transition: all .2s; flex-shrink: 0;
}
.auth-btn-back:hover { background: rgba(255,255,255,.13); color: #fff; border-color: rgba(255,255,255,.25); }
.auth-btn-back svg { transition: transform .2s; }
.auth-btn-back:hover svg { transform: translateX(-3px); }

/* Barre de progression */
.auth-progress { height: 2px; background: rgba(255,255,255,.05); }
.auth-progress__bar {
  height: 100%;
  background: linear-gradient(90deg, #7D1235, #C8365F, #E07090);
  border-radius: 0 2px 2px 0;
  transition: width .5s ease;
}

/* ── CONTENU ── */
.auth-content {
  position: relative; z-index: 10; flex: 1;
  display: flex; align-items: center; justify-content: center;
  padding: 40px 24px;
}

/* ── FOOTER ── */
.auth-footer {
  position: relative; z-index: 100;
  background: rgba(8, 0, 4, .75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255,255,255,.07);
  animation: slideUp .55s ease .2s both;
}
@keyframes slideUp {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}
.auth-footer__inner {
  max-width: 1200px; margin: 0 auto; padding: 22px 40px;
  display: flex; align-items: center; justify-content: space-between;
  gap: 20px; flex-wrap: wrap;
}
.auth-footer__brand { display: flex; flex-direction: column; gap: 4px; }
.auth-footer__logo  { display: flex; align-items: center; gap: 8px; cursor: pointer; transition: opacity .2s; }
.auth-footer__logo:hover { opacity: .7; }
.auth-footer__mark {
  width: 26px; height: 26px;
  background: rgba(200,54,95,.28); border: 1px solid rgba(200,54,95,.42);
  border-radius: 7px; display: grid; place-items: center;
  font-family: 'Cormorant Garamond', serif; font-size: 13px; font-weight: 700; color: #fff;
}
.auth-footer__logo span {
  font-family: 'Cormorant Garamond', serif;
  font-size: 15px; font-weight: 600; color: rgba(255,255,255,.75);
}
.auth-footer__brand p { font-size: 11px; color: rgba(255,255,255,.3); padding-left: 34px; }
.auth-footer__links   { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.auth-footer__links a {
  font-size: 12px; font-weight: 500;
  color: rgba(255,255,255,.42); text-decoration: none; transition: color .2s;
}
.auth-footer__links a:hover { color: rgba(255,255,255,.82); }
.dot { width: 3px; height: 3px; background: rgba(255,255,255,.2); border-radius: 50%; flex-shrink: 0; }
.auth-footer__copy { font-size: 11.5px; color: rgba(255,255,255,.28); }

/* ── RESPONSIVE ── */
@media (max-width: 768px) {
  .auth-header__inner { padding: 0 20px; }
  .auth-nav { display: none; }
  .auth-footer__inner { padding: 18px 20px; flex-direction: column; text-align: center; gap: 14px; }
  .auth-footer__brand p { padding-left: 0; }
  .auth-footer__logo { justify-content: center; }
  .auth-footer__links { justify-content: center; }
}
</style>