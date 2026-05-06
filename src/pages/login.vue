<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppNavbar from '@/components/AppNavbar.vue'
import AppFooter from '@/components/AppFooter.vue'

const router    = useRouter()
const authStore = useAuthStore()

const email        = ref('')
const password     = ref('')
const showPassword = ref(false)
const error        = ref('')
const role         = ref<'user' | 'organizer'>('user')
const remember     = ref(false)
const sparks       = ref<{x:number,y:number,size:number,dur:number,delay:number,op:number}[]>([])

onMounted(() => {
  sparks.value = Array.from({length:55},()=>({
    x:    Math.random()*100,
    y:    Math.random()*30,
    size: 1.5+Math.random()*3,
    dur:  3+Math.random()*6,
    delay:Math.random()*8,
    op:   .3+Math.random()*.7
  }))
})

const handleLogin = async () => {
  if (!email.value || !password.value) { error.value='Veuillez remplir tous les champs'; return }
  error.value = ''
  let result: any
  if (role.value === 'organizer') {
    result = await authStore.loginOrganizer(email.value, password.value)
    if (result.success) return router.push('/organizer/dashboard')
  } else {
    result = await authStore.login(email.value, password.value)
    if (result.success) {
      if (authStore.isAdmin) return router.push('/admin/dashboard')
      return router.push('/user/dashboard')
    }
  }
  if (result.requires2FA) { error.value='Entrez votre code 2FA pour continuer'; return }
  error.value = result.message || 'Email ou mot de passe incorrect'
}
</script>

<template>
  <div>
    <AppNavbar />

    <div class="lp">
      <div class="scene">
        <div class="blob b1"></div>
        <div class="blob b2"></div>
        <div class="blob b3"></div>
        <div class="blob b4"></div>
        <div class="sparks">
          <div v-for="(s,i) in sparks" :key="i" class="spark" :style="{ left: s.x+'%', bottom: s.y+'%', width: s.size+'px', height: s.size+'px', animationDuration: s.dur+'s', animationDelay: s.delay+'s', opacity: s.op }"></div>
        </div>
        <div class="ring r1"></div>
        <div class="ring r2"></div>
        <div class="ring r3"></div>
      </div>

      <aside class="hero">
        <div class="hero-logo" @click="router.push('/')">
          <div class="hero-logo__mark">E</div>
          <div>
            <span class="hero-logo__name">EventLab</span>
            <span class="hero-logo__sub">Billetterie & Événements</span>
          </div>
        </div>
        <div class="hero-badge">
          <span class="badge-dot"></span>
          Plateforme #1 en Tunisie
        </div>
        <h1 class="hero-h1">Vivez des moments<br><em>inoubliables</em></h1>
        <p class="hero-p">Concerts, festivals, conférences… Retrouvez votre espace personnel et explorez votre univers.</p>
        <div class="hero-stats">
          <div class="hero-stat"><strong>200+</strong><span>Événements</span></div>
          <div class="stat-div"></div>
          <div class="hero-stat"><strong>50K+</strong><span>Participants</span></div>
          <div class="stat-div"></div>
          <div class="hero-stat"><strong>4.9 ★</strong><span>Avis clients</span></div>
        </div>
        <div class="hero-testi">
          <p>« La meilleure plateforme pour découvrir les événements en Tunisie. Interface élégante et réservation facile. »</p>
          <div class="testi-author">
            <div class="testi-av">SB</div>
            <div><b>Sarra B.</b><span>Utilisatrice depuis 2024</span></div>
          </div>
        </div>
      </aside>

      <main class="card">
        <button class="card-back" @click="router.push('/')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
          Retour à l'accueil
        </button>
        <p class="card-eyebrow">Bienvenue sur EventLab</p>
        <h2 class="card-title">{{ role==='organizer' ? 'Espace Organisateur 🏢' : 'Bon retour 👋' }}</h2>
        <p class="card-sub">{{ role==='organizer' ? 'Gérez vos événements en toute simplicité' : 'Connectez-vous à votre espace personnel' }}</p>
        <div class="tabs">
          <button :class="['tab',{on:role==='user'}]" @click="role='user'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            Utilisateur
          </button>
          <button :class="['tab',{on:role==='organizer'}]" @click="role='organizer'">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>
            Organisateur
          </button>
        </div>
        <transition name="err">
          <div v-if="error" class="err-box">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ error }}
          </div>
        </transition>
        <div class="field">
          <label class="label">Adresse email</label>
          <div class="inp-wrap">
            <span class="inp-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></span>
            <input v-model="email" class="inp" type="email" placeholder="vous@email.com" @keyup.enter="handleLogin" />
          </div>
        </div>
        <div class="field">
          <div class="field-top">
            <label class="label">Mot de passe</label>
            <a class="forgot" @click.prevent="router.push('/forgot-password')">Mot de passe oublié ?</a>
          </div>
          <div class="inp-wrap">
            <span class="inp-icon"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></span>
            <input :type="showPassword?'text':'password'" v-model="password" class="inp" placeholder="••••••••" @keyup.enter="handleLogin" />
            <button type="button" class="eye-btn" @click="showPassword=!showPassword">
              <svg v-if="showPassword" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
          </div>
        </div>
        <label class="remember">
          <input type="checkbox" v-model="remember" />
          <span class="remember__box"><svg width="10" height="8" viewBox="0 0 12 10" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="1,5 4.5,8.5 11,1"/></svg></span>
          <span>Se souvenir de moi</span>
        </label>
        <button class="btn" @click="handleLogin" :disabled="authStore.isLoading">
          <span v-if="!authStore.isLoading" class="btn__inner">
            Se connecter
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12,5 19,12 12,19"/></svg>
          </span>
          <span v-else class="dots"><i></i><i></i><i></i></span>
        </button>
        <div class="sep"><span>ou</span></div>
        <p class="reg">Pas encore de compte ? <RouterLink to="/register">Créer un compte</RouterLink></p>
      </main>
    </div>

    <!-- ✅ footer-wrap pour passer au-dessus du .scene fixed -->
    <div class="footer-wrap">
      <AppFooter />
    </div>

  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;0,700;1,700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{ --p1:#C8365F;--p2:#A82248;--p3:#7D1235;--p4:#4A0820; --g1:#F2A8BE;--g2:#E07090;--ink:#1A0510; --font-d:'Cormorant Garamond',serif; --font-b:'Plus Jakarta Sans',sans-serif; }
.lp{position:relative;z-index:10;display:grid;grid-template-columns:1fr 460px;width:100%;max-width:1160px;min-height:100vh;padding:72px 56px 0;gap:64px;align-items:center;margin:0 auto;font-family:var(--font-b);}
.scene{position:fixed;inset:0;z-index:0;background:radial-gradient(ellipse 130% 110% at 50% -10%,#A82248 0%,#6B1230 30%,#2E0416 65%,#0D0005 100%);}
.blob{position:absolute;border-radius:50%;filter:blur(100px);mix-blend-mode:screen;animation:blobFloat linear infinite;}
.b1{width:700px;height:700px;background:rgba(168,34,72,.55);top:-200px;left:-150px;animation-duration:18s;}
.b2{width:500px;height:500px;background:rgba(224,112,144,.28);top:50%;right:-100px;animation-duration:14s;animation-delay:-4s;}
.b3{width:420px;height:420px;background:rgba(200,54,95,.38);bottom:-100px;left:30%;animation-duration:22s;animation-delay:-8s;}
.b4{width:280px;height:280px;background:rgba(242,168,190,.18);top:20%;left:40%;animation-duration:16s;animation-delay:-2s;}
@keyframes blobFloat{0%{transform:translateY(0) scale(1);}33%{transform:translateY(-60px) scale(1.07);}66%{transform:translateY(30px) scale(.94);}100%{transform:translateY(0) scale(1);}}
.sparks{position:absolute;inset:0;overflow:hidden;pointer-events:none;}
.spark{position:absolute;border-radius:50%;background:#fff;animation:sparkAnim linear infinite;}
@keyframes sparkAnim{0%{opacity:0;transform:translateY(0) scale(0);}10%{opacity:1;transform:translateY(-10px) scale(1);}90%{opacity:.4;transform:translateY(-120px) scale(.5);}100%{opacity:0;transform:translateY(-140px) scale(0);}}
.ring{position:absolute;border-radius:50%;border:1px solid rgba(255,255,255,.08);animation:ringPulse ease-in-out infinite;}
.r1{width:900px;height:900px;top:50%;left:50%;transform:translate(-50%,-50%);animation-duration:6s;}
.r2{width:650px;height:650px;top:50%;left:50%;transform:translate(-50%,-50%);animation-duration:6s;animation-delay:-2s;}
.r3{width:400px;height:400px;top:50%;left:50%;transform:translate(-50%,-50%);animation-duration:6s;animation-delay:-4s;}
@keyframes ringPulse{0%,100%{opacity:.08;transform:translate(-50%,-50%) scale(1);}50%{opacity:.18;transform:translate(-50%,-50%) scale(1.03);}}
.hero{color:#fff;position:relative;z-index:2;display:flex;flex-direction:column;gap:0;}
.hero-logo{display:flex;align-items:center;gap:13px;cursor:pointer;margin-bottom:72px;animation:fadeSlide .8s ease both;}
.hero-logo__mark{width:46px;height:46px;border-radius:12px;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);backdrop-filter:blur(10px);display:grid;place-items:center;font-family:var(--font-d);font-size:22px;font-weight:700;color:#fff;flex-shrink:0;}
.hero-logo__name{display:block;font-family:var(--font-d);font-size:19px;font-weight:600;color:#fff;line-height:1;}
.hero-logo__sub{display:block;font-size:10.5px;color:rgba(255,255,255,.5);letter-spacing:.1em;text-transform:uppercase;margin-top:4px;}
.hero-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:100px;padding:6px 16px;font-size:11px;font-weight:700;color:rgba(255,255,255,.9);letter-spacing:.08em;text-transform:uppercase;margin-bottom:28px;animation:fadeSlide .8s ease .1s both;width:fit-content;}
.badge-dot{width:7px;height:7px;border-radius:50%;background:#fff;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(255,255,255,.5);}70%{box-shadow:0 0 0 7px rgba(255,255,255,0);}}
.hero-h1{font-family:var(--font-d);font-size:clamp(48px,5vw,72px);font-weight:700;line-height:1.06;margin-bottom:22px;animation:fadeSlide .8s ease .2s both;}
.hero-h1 em{font-style:italic;background:linear-gradient(90deg,#FFD6E5,#fff,#FFB3CF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;background-size:200% auto;animation:shimmer 3s ease infinite;}
@keyframes shimmer{0%{background-position:0%;}100%{background-position:200%;}}
.hero-p{font-size:15.5px;line-height:1.75;color:rgba(255,255,255,.65);max-width:380px;margin-bottom:44px;animation:fadeSlide .8s ease .3s both;}
.hero-stats{display:flex;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);backdrop-filter:blur(20px);border-radius:20px;padding:22px 28px;max-width:420px;animation:fadeSlide .8s ease .4s both;}
.hero-stat{flex:1;text-align:center;}
.hero-stat strong{display:block;font-family:var(--font-d);font-size:28px;font-weight:700;color:#fff;line-height:1;}
.hero-stat span{display:block;font-size:10.5px;color:rgba(255,255,255,.5);text-transform:uppercase;letter-spacing:.07em;margin-top:5px;}
.stat-div{width:1px;background:rgba(255,255,255,.15);flex-shrink:0;}
.hero-testi{margin-top:28px;padding:22px 26px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:18px;backdrop-filter:blur(12px);max-width:420px;animation:fadeSlide .8s ease .5s both;}
.hero-testi p{font-size:14px;font-style:italic;color:rgba(255,255,255,.75);line-height:1.65;margin-bottom:14px;}
.testi-author{display:flex;align-items:center;gap:11px;}
.testi-av{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,rgba(255,255,255,.3),rgba(255,255,255,.1));border:1px solid rgba(255,255,255,.3);display:grid;place-items:center;font-size:11.5px;font-weight:700;color:#fff;flex-shrink:0;}
.testi-author b{display:block;font-size:13px;color:#fff;}
.testi-author span{display:block;font-size:11px;color:rgba(255,255,255,.45);margin-top:2px;}
@keyframes fadeSlide{from{opacity:0;transform:translateY(30px);}to{opacity:1;transform:translateY(0);}}
.card{position:relative;z-index:2;background:rgba(255,255,255,.97);border:1px solid rgba(255,255,255,.6);border-radius:28px;padding:44px 40px;backdrop-filter:blur(30px);box-shadow:0 30px 80px rgba(0,0,0,.25),0 0 0 1px rgba(255,255,255,.15) inset,0 1px 0 rgba(255,255,255,.6) inset;animation:cardIn .9s cubic-bezier(.22,.68,0,1.1) .1s both;}
@keyframes cardIn{from{opacity:0;transform:translateX(40px) scale(.97);}to{opacity:1;transform:translateX(0) scale(1);}}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--p4),var(--p1),var(--g2),var(--p1),var(--p4));background-size:200% auto;animation:barSlide 3s linear infinite;border-radius:28px 28px 0 0;}
@keyframes barSlide{0%{background-position:0%;}100%{background-position:200%;}}
.card-back{position:absolute;top:22px;right:22px;display:flex;align-items:center;gap:5px;background:rgba(255,31,113,.06);border:1px solid rgba(255,31,113,.15);border-radius:8px;padding:6px 12px;font-family:var(--font-b);font-size:12px;font-weight:600;color:var(--p3);cursor:pointer;transition:all .2s;}
.card-back:hover{background:rgba(255,31,113,.12);border-color:rgba(255,31,113,.3);}
.card-back svg{transition:transform .2s;}
.card-back:hover svg{transform:translateX(-3px);}
.card-eyebrow{font-size:10.5px;font-weight:700;color:var(--p1);letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px;margin-top:8px;}
.card-title{font-family:var(--font-d);font-size:36px;font-weight:700;color:var(--ink);line-height:1.1;margin-bottom:6px;}
.card-sub{font-size:14px;color:#7A4A5A;margin-bottom:28px;}
.tabs{display:flex;background:#FFF0F5;border:1.5px solid rgba(255,31,113,.12);border-radius:14px;padding:4px;margin-bottom:26px;gap:3px;}
.tab{flex:1;display:flex;align-items:center;justify-content:center;gap:7px;padding:11px 8px;border:none;background:transparent;border-radius:11px;font-family:var(--font-b);font-size:13px;font-weight:600;color:#B06080;cursor:pointer;transition:all .25s cubic-bezier(.22,.68,0,1.2);}
.tab.on{background:#fff;color:var(--p3);box-shadow:0 3px 14px rgba(255,31,113,.15);}
.err-box{display:flex;align-items:center;gap:8px;background:#fff1f2;color:#be123c;border:1px solid #fecdd3;border-radius:10px;padding:11px 14px;font-size:13px;margin-bottom:14px;}
.err-enter-active,.err-leave-active{transition:all .3s;}
.err-enter-from,.err-leave-to{opacity:0;transform:translateY(-8px);}
.field{margin-bottom:16px;}
.field-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;}
.label{display:block;font-size:12.5px;font-weight:700;color:#2D0A18;margin-bottom:8px;}
.field-top .label{margin-bottom:0;}
.forgot{font-size:12px;color:var(--p1);font-weight:600;text-decoration:none;cursor:pointer;transition:color .2s;}
.forgot:hover{color:var(--p3);}
.inp-wrap{position:relative;display:flex;align-items:center;}
.inp-icon{position:absolute;left:14px;color:var(--g2);pointer-events:none;display:flex;align-items:center;}
.inp{width:100%;padding:14px 14px 14px 44px;border:1.5px solid rgba(255,31,113,.14);border-radius:13px;font-family:var(--font-b);font-size:14px;color:var(--ink);background:#FFF8FA;outline:none;transition:all .2s;}
.inp::placeholder{color:rgba(180,80,120,.4);}
.inp:focus{border-color:var(--p1);background:#fff;box-shadow:0 0 0 4px rgba(255,31,113,.08);}
.eye-btn{position:absolute;right:14px;background:none;border:none;cursor:pointer;color:#C06080;opacity:.5;display:flex;align-items:center;padding:4px;transition:opacity .2s;}
.eye-btn:hover{opacity:1;}
.remember{display:flex;align-items:center;gap:10px;cursor:pointer;margin-bottom:24px;user-select:none;}
.remember input{display:none;}
.remember__box{width:22px;height:22px;border:2px solid #C8365F;border-radius:7px;background:#fff;flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:all .22s ease;}
.remember__box svg{opacity:0;transition:opacity .18s;}
.remember input:checked + .remember__box{background:#C8365F;border-color:#C8365F;box-shadow:0 0 0 3px rgba(200,54,95,.2),0 3px 10px rgba(125,18,53,.4);}
.remember input:checked + .remember__box svg{opacity:1;}
.remember span:last-child{font-size:13.5px;color:#5A2030;font-weight:500;}
.btn{width:100%;padding:17px;border:none;border-radius:14px;background:#C8365F;color:#fff;font-family:var(--font-b);font-size:15.5px;font-weight:700;letter-spacing:.03em;cursor:pointer;position:relative;overflow:hidden;box-shadow:0 6px 24px rgba(125,18,53,.45),0 2px 6px rgba(0,0,0,.2);transition:all .25s ease;}
.btn::after{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(255,255,255,.18) 0%,transparent 50%);pointer-events:none;}
.btn:hover:not(:disabled){background:#A82248;transform:translateY(-2px);box-shadow:0 10px 32px rgba(125,18,53,.55),0 4px 10px rgba(0,0,0,.2);}
.btn:active:not(:disabled){transform:translateY(0);}
.btn:disabled{opacity:.65;cursor:not-allowed;}
.btn__inner{position:relative;z-index:2;display:flex;align-items:center;justify-content:center;gap:10px;color:#fff;font-weight:700;font-size:15.5px;}
.btn__inner svg{stroke:#fff;stroke-width:2.5;transition:transform .22s;flex-shrink:0;}
.btn:hover:not(:disabled) .btn__inner svg{transform:translateX(5px);}
.dots{display:inline-flex;gap:5px;position:relative;z-index:1;}
.dots i{display:block;width:7px;height:7px;border-radius:50%;background:#fff;animation:db 1s infinite;font-style:normal;}
.dots i:nth-child(2){animation-delay:.15s;}
.dots i:nth-child(3){animation-delay:.3s;}
@keyframes db{0%,100%{transform:translateY(0);opacity:1;}50%{transform:translateY(-7px);opacity:.4;}}
.sep{display:flex;align-items:center;gap:14px;margin:20px 0 16px;font-size:11px;font-weight:700;color:rgba(180,80,120,.4);text-transform:uppercase;letter-spacing:.1em;}
.sep::before,.sep::after{content:'';flex:1;height:1px;background:rgba(255,31,113,.1);}
.reg{text-align:center;font-size:13.5px;color:#8A5060;}
.reg a{color:var(--p1);font-weight:700;text-decoration:none;transition:color .2s;}
.reg a:hover{color:var(--p3);}

/* ✅ FIX FOOTER — passe au-dessus du .scene fixed */
.footer-wrap { position: relative; z-index: 10; }

@media(max-width:1100px){.lp{grid-template-columns:1fr;padding:100px 24px 40px;min-height:auto;gap:32px;}.hero{padding-top:0;}.hero-logo{margin-bottom:32px;}.hero-testi{display:none;}.hero-stats{max-width:100%;}.card{padding:36px 28px;}.hero-h1{font-size:40px;}}
@media(max-width:600px){.hero{text-align:center;}.hero-logo{justify-content:center;}.hero-badge{margin:0 auto 20px;}.hero-p{margin:0 auto 32px;}.hero-stats{padding:16px;}.hero-stat strong{font-size:22px;}.card{padding:28px 20px;border-radius:20px;}.card-title{font-size:28px;}}
</style>