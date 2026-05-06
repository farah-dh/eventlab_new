<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const router    = useRouter()
const authStore = useAuthStore()

const email   = ref('')
const error   = ref('')
const success = ref(false)
const loading = ref(false)

// Particules flottantes
const particles = ref<{x:number,y:number,s:number,d:number,delay:number,tx:number,ty:number}[]>([])
// Étoiles scintillantes
const stars = ref<{x:number,y:number,s:number,d:number,delay:number}[]>([])

onMounted(() => {
  particles.value = Array.from({ length: 18 }, () => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
    s: Math.random() * 8 + 4,
    d: Math.random() * 8 + 5,
    delay: Math.random() * 5,
    tx: (Math.random() - 0.5) * 60,
    ty: -(Math.random() * 80 + 40),
  }))
  stars.value = Array.from({ length: 50 }, () => ({
    x: Math.random() * 100,
    y: Math.random() * 100,
    s: Math.random() * 3 + 1,
    d: Math.random() * 3 + 2,
    delay: Math.random() * 4,
  }))
})

const handleSubmit = async () => {
  if (!email.value) { error.value = 'Veuillez entrer votre adresse email'; return }
  error.value = ''
  loading.value = true
  try {
    await authStore.forgotPassword(email.value)
    success.value = true
  } catch (e: any) {
    error.value = e?.message || 'Une erreur est survenue. Veuillez réessayer.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">

    <!-- Fond framboise -->
    <div class="bg-mesh"></div>

    <!-- Orbes animés -->
    <div class="orb o1"></div>
    <div class="orb o2"></div>
    <div class="orb o3"></div>
    <div class="orb o4"></div>
    <div class="orb o5"></div>

    <!-- Cercles qui tournent -->
    <div class="ring r1"></div>
    <div class="ring r2"></div>
    <div class="ring r3"></div>
    <div class="ring r4"></div>

    <!-- Grille points -->
    <div class="dots-bg"></div>

    <!-- Étoiles scintillantes -->
    <div class="stars">
      <div
        v-for="(s, i) in stars" :key="'s'+i"
        class="star"
        :style="{
          left: s.x+'%', top: s.y+'%',
          width: s.s+'px', height: s.s+'px',
          animationDuration: s.d+'s',
          animationDelay: s.delay+'s'
        }"
      ></div>
    </div>

    <!-- Particules flottantes -->
    <div class="particles">
      <div
        v-for="(p, i) in particles" :key="'p'+i"
        class="particle"
        :style="{
          left: p.x+'%', top: p.y+'%',
          width: p.s+'px', height: p.s+'px',
          animationDuration: p.d+'s',
          animationDelay: p.delay+'s',
          '--tx': p.tx+'px',
          '--ty': p.ty+'px',
        }"
      ></div>
    </div>

    <!-- Header animé -->
    <div class="topbar">
      <div class="brand" @click="router.push('/')">
        <div class="brand-mark">E</div>
        <span>Event <strong>Lab</strong></span>
      </div>
      <RouterLink to="/login" class="login-link">
        Retour à la connexion <strong>→</strong>
      </RouterLink>
    </div>

    <!-- Carte centrée -->
    <div class="center">

      <!-- Halo derrière la carte -->
      <div class="card-halo"></div>

      <div class="card">
        <Transition name="fade" mode="out-in">

          <!-- ── Succès ── -->
          <div v-if="success" key="ok" class="success">
            <div class="success-rings">
              <div class="sr sr1"></div>
              <div class="sr sr2"></div>
              <div class="sr sr3"></div>
              <div class="sr sr4"></div>
              <div class="success-check">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20,6 9,17 4,12"/>
                </svg>
              </div>
            </div>
            <h2 class="success-title">Email envoyé ! 🎉</h2>
            <p class="success-sub">Nous avons envoyé un lien à<br><strong>{{ email }}</strong></p>
            <p class="success-hint">Vérifiez aussi vos spams.</p>
            <button class="btn" @click="router.push('/login')">
              <span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
                Retour à la connexion
              </span>
            </button>
            <button class="ghost-btn" @click="success=false;email=''">Renvoyer l'email</button>
          </div>

          <!-- ── Formulaire ── -->
          <div v-else key="form">

            <div class="card-top">
              <div class="card-ico">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </div>
              <div>
                <p class="eyebrow">Mot de passe oublié</p>
                <h2 class="card-title">Réinitialisation 🔑</h2>
              </div>
              <div class="card-badge">
                <span class="badge-dot"></span>
                Sécurisé
              </div>
            </div>

            <p class="card-sub">Entrez votre email pour recevoir un lien de réinitialisation instantané.</p>

            <!-- Steps animés -->
            <div class="mini-steps">
              <div class="mstep mstep-on">
                <div class="mstep-num">1</div>
                <span>Email</span>
              </div>
              <div class="mstep-line"><div class="mstep-progress"></div></div>
              <div class="mstep">
                <div class="mstep-num">2</div>
                <span>Lien reçu</span>
              </div>
              <div class="mstep-line"></div>
              <div class="mstep">
                <div class="mstep-num">3</div>
                <span>Nouveau MDP</span>
              </div>
            </div>

            <Transition name="shake">
              <div v-if="error" class="err-box">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                {{ error }}
              </div>
            </Transition>

            <div class="field">
              <label>Adresse email</label>
              <div class="inp-wrap">
                <span class="inp-ico">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                </span>
                <input v-model="email" type="email" placeholder="vous@email.com" @keyup.enter="handleSubmit" autocomplete="email" />
                <div class="inp-pulse" v-if="email"></div>
              </div>
            </div>

            <button class="btn" @click="handleSubmit" :disabled="loading">
              <span v-if="!loading">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M22 2L11 13"/><path d="M22 2L15 22 11 13 2 9l20-7z"/></svg>
                Envoyer le lien de réinitialisation
              </span>
              <span v-else class="dots"><i></i><i></i><i></i></span>
            </button>

            <div class="sep"><span>ou</span></div>
            <p class="sw">Vous vous souvenez ? <RouterLink to="/login">Se connecter</RouterLink></p>

          </div>
        </Transition>
      </div>
    </div>

  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700;12..96,800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --r1:#C0135A; --r2:#9E0F4A; --r3:#6B0830; --r4:#E8457A; --r5:#F4A0BF;
  --fh:'Bricolage Grotesque',sans-serif; --fb:'Plus Jakarta Sans',sans-serif;
}

/* ════ PAGE ════ */
.page { min-height:100vh;width:100%;position:relative;overflow:hidden;display:flex;flex-direction:column;font-family:var(--fb); }

/* Fond framboise */
.bg-mesh { position:absolute;inset:0;z-index:0;background:linear-gradient(135deg,#F2A0C0 0%,#D4608A 25%,#C0135A 55%,#9E0F4A 78%,#6B0830 100%); }

/* ── Orbes ── */
.orb { position:absolute;border-radius:50%;filter:blur(80px);pointer-events:none;z-index:1; }
.o1{width:700px;height:700px;background:radial-gradient(circle,rgba(255,255,255,.2),transparent 70%);top:-250px;left:-200px;animation:drift1 16s ease-in-out infinite alternate;}
.o2{width:600px;height:600px;background:radial-gradient(circle,rgba(107,8,48,.5),transparent 70%);bottom:-200px;right:-150px;animation:drift2 20s ease-in-out infinite alternate;}
.o3{width:400px;height:400px;background:radial-gradient(circle,rgba(255,255,255,.15),transparent 70%);top:20%;right:5%;animation:drift1 14s ease-in-out infinite alternate-reverse;}
.o4{width:350px;height:350px;background:radial-gradient(circle,rgba(232,69,122,.35),transparent 70%);bottom:5%;left:10%;animation:drift2 18s ease-in-out infinite alternate;}
.o5{width:250px;height:250px;background:radial-gradient(circle,rgba(255,255,255,.1),transparent 70%);top:50%;left:50%;animation:drift1 10s ease-in-out infinite alternate-reverse;}
@keyframes drift1{from{transform:translate(0,0) scale(1)}to{transform:translate(40px,50px) scale(1.1)}}
@keyframes drift2{from{transform:translate(0,0) scale(1.1)}to{transform:translate(-35px,-45px) scale(1)}}

/* ── Cercles tournants ── */
.ring{position:absolute;border-radius:50%;pointer-events:none;z-index:1;}
.r1{width:700px;height:700px;top:-200px;right:-200px;border:1px solid rgba(255,255,255,.12);animation:spin 35s linear infinite;}
.r2{width:500px;height:500px;bottom:-150px;left:-150px;border:1px solid rgba(255,255,255,.1);animation:spin 25s linear infinite reverse;}
.r3{width:300px;height:300px;top:15%;left:3%;border:1px solid rgba(255,255,255,.07);animation:spin 18s linear infinite;}
.r4{width:180px;height:180px;bottom:20%;right:8%;border:1px solid rgba(255,255,255,.08);animation:spin 12s linear infinite reverse;}
@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}

/* Points */
.dots-bg{position:absolute;inset:0;z-index:1;background-image:radial-gradient(circle,rgba(255,255,255,.18) 1.5px,transparent 1.5px);background-size:36px 36px;}

/* ── Étoiles ── */
.stars{position:absolute;inset:0;z-index:2;pointer-events:none;}
.star{position:absolute;border-radius:50%;background:white;animation:twinkle var(--d,3s) ease-in-out infinite alternate;}
@keyframes twinkle{from{opacity:.05;transform:scale(.8)}to{opacity:.8;transform:scale(1.2)}}

/* ── Particules flottantes ── */
.particles{position:absolute;inset:0;z-index:2;pointer-events:none;overflow:hidden;}
.particle{
  position:absolute;border-radius:50%;
  background:rgba(255,255,255,.25);
  animation:floatUp var(--d,7s) ease-in infinite;
}
@keyframes floatUp{
  0%{transform:translate(0,0) scale(1);opacity:.6}
  100%{transform:translate(var(--tx,0px),var(--ty,-100px)) scale(0);opacity:0}
}

/* ── Topbar ── */
.topbar{position:relative;z-index:10;display:flex;align-items:center;justify-content:space-between;padding:24px 48px;animation:slideDown .7s ease both;}
@keyframes slideDown{from{opacity:0;transform:translateY(-20px)}to{opacity:1;transform:none}}

.brand{display:inline-flex;align-items:center;gap:10px;cursor:pointer;}
.brand-mark{
  width:38px;height:38px;border-radius:12px;
  background:rgba(255,255,255,.2);border:1.5px solid rgba(255,255,255,.4);
  backdrop-filter:blur(10px);display:grid;place-items:center;
  font-family:var(--fh);font-size:18px;font-weight:800;color:white;
  animation:pulse-mark 3s ease-in-out infinite;
}
@keyframes pulse-mark{0%,100%{box-shadow:0 0 0 0 rgba(255,255,255,.3)}50%{box-shadow:0 0 0 8px rgba(255,255,255,0)}}
.brand span{font-family:var(--fh);font-size:18px;font-weight:400;color:white;letter-spacing:-.02em;}
.brand span strong{font-weight:800;}
.login-link{font-size:13.5px;color:rgba(255,255,255,.75);text-decoration:none;transition:all .2s;padding:8px 16px;border-radius:100px;border:1px solid rgba(255,255,255,.2);backdrop-filter:blur(8px);}
.login-link:hover{background:rgba(255,255,255,.15);color:white;border-color:rgba(255,255,255,.4);}
.login-link strong{color:white;font-weight:700;}

/* ── Centre ── */
.center{flex:1;display:flex;align-items:center;justify-content:center;padding:16px 20px 48px;position:relative;z-index:10;}

/* Halo derrière la carte */
.card-halo{
  position:absolute;
  width:500px;height:500px;
  border-radius:50%;
  background:radial-gradient(circle,rgba(255,255,255,.12) 0%,transparent 70%);
  pointer-events:none;
  animation:halo 4s ease-in-out infinite alternate;
}
@keyframes halo{from{transform:scale(.9);opacity:.6}to{transform:scale(1.1);opacity:1}}

/* ── Carte ── */
.card{
  background:white;border-radius:28px;padding:38px 40px;
  width:100%;max-width:460px;
  box-shadow:
    0 0 0 1px rgba(0,0,0,.05),
    0 8px 16px rgba(0,0,0,.08),
    0 32px 80px rgba(107,8,48,.4),
    0 0 150px rgba(192,19,90,.25);
  animation:cardIn .9s cubic-bezier(.22,.68,0,1.2) .2s both, float 7s ease-in-out 1.5s infinite;
  position:relative;
}
@keyframes cardIn{from{opacity:0;transform:translateY(40px) scale(.93) rotateX(8deg)}to{opacity:1;transform:translateY(0) scale(1) rotateX(0)}}
@keyframes float{0%,100%{transform:translateY(0) rotate(0deg)}25%{transform:translateY(-8px) rotate(.3deg)}75%{transform:translateY(-4px) rotate(-.3deg)}}

/* Barre animée en haut */
.card::before{content:'';position:absolute;top:0;left:20px;right:20px;height:3px;background:linear-gradient(90deg,var(--r3),var(--r1),var(--r4),var(--r5),var(--r4),var(--r1),var(--r3));background-size:200% auto;animation:bar 2.5s linear infinite;border-radius:0 0 4px 4px;}
@keyframes bar{0%{background-position:0%}100%{background-position:200%}}

/* Reflet interne */
.card::after{content:'';position:absolute;top:0;left:0;right:0;height:60%;background:linear-gradient(180deg,rgba(255,255,255,.04) 0%,transparent 100%);border-radius:28px 28px 0 0;pointer-events:none;}

/* Card top */
.card-top{display:flex;align-items:center;gap:14px;margin-bottom:10px;padding-top:10px;animation:fadeUp .6s ease .4s both;}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}

.card-ico{
  width:52px;height:52px;border-radius:16px;
  background:linear-gradient(135deg,#FFF0F5,#FFD8E8);
  border:1.5px solid rgba(192,19,90,.13);
  display:grid;place-items:center;color:var(--r1);flex-shrink:0;
  animation:wobble 4s ease-in-out infinite;
}
@keyframes wobble{0%,100%{transform:rotate(0deg)}25%{transform:rotate(-5deg)}75%{transform:rotate(5deg)}}

.eyebrow{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--r1);margin-bottom:4px;}
.card-title{font-family:var(--fh);font-size:26px;font-weight:800;color:#150A10;letter-spacing:-.03em;line-height:1;}
.card-badge{
  margin-left:auto;display:inline-flex;align-items:center;gap:7px;
  background:rgba(192,19,90,.08);border:1px solid rgba(192,19,90,.2);
  border-radius:100px;padding:5px 12px;font-size:11px;font-weight:700;color:var(--r1);
  animation:fadeUp .6s ease .5s both;
}
.badge-dot{width:6px;height:6px;border-radius:50%;background:var(--r1);animation:blink 1.5s infinite;}
@keyframes blink{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(192,19,90,.5)}50%{opacity:.3;box-shadow:0 0 0 6px rgba(192,19,90,0)}}

.card-sub{font-size:13.5px;color:#9E4D65;margin-bottom:16px;line-height:1.6;animation:fadeUp .6s ease .5s both;}

/* Mini steps animés */
.mini-steps{
  display:flex;align-items:center;
  background:linear-gradient(135deg,#FFF0F5,#FFE0EE);
  border:1px solid rgba(192,19,90,.1);border-radius:14px;
  padding:12px 16px;margin-bottom:20px;
  animation:fadeUp .6s ease .55s both;
}
.mstep{display:flex;align-items:center;gap:7px;flex:1;justify-content:center;}
.mstep-num{
  width:22px;height:22px;border-radius:50%;
  background:rgba(192,19,90,.1);border:1.5px solid rgba(192,19,90,.2);
  display:grid;place-items:center;font-size:11px;font-weight:800;color:var(--r2);flex-shrink:0;
  transition:all .3s;
}
.mstep-on .mstep-num{
  background:var(--r1);border-color:var(--r1);color:white;
  box-shadow:0 3px 10px rgba(192,19,90,.5);
  animation:step-pulse 2s ease-in-out infinite;
}
@keyframes step-pulse{0%,100%{box-shadow:0 3px 10px rgba(192,19,90,.5)}50%{box-shadow:0 3px 20px rgba(192,19,90,.8),0 0 30px rgba(192,19,90,.3)}}
.mstep span{font-size:11.5px;font-weight:600;color:#C4909E;}
.mstep-on span{color:var(--r1);font-weight:700;}
.mstep-line{flex:1;height:2px;background:rgba(192,19,90,.12);border-radius:2px;position:relative;overflow:hidden;}
.mstep-progress{position:absolute;left:0;top:0;height:100%;width:100%;background:linear-gradient(90deg,var(--r1),var(--r4));animation:progress 2s ease-in-out infinite alternate;border-radius:2px;}
@keyframes progress{from{transform:scaleX(0);transform-origin:left}to{transform:scaleX(1);transform-origin:left}}

/* Erreur */
.err-box{
  display:flex;align-items:center;gap:10px;
  background:#FFF0F3;border:1px solid #F4B0CA;color:#9E0F4A;
  border-radius:12px;padding:11px 14px;font-size:13px;font-weight:500;margin-bottom:16px;
}

/* Champ */
.field{margin-bottom:22px;animation:fadeUp .6s ease .6s both;}
.field label{display:block;font-size:11.5px;font-weight:700;color:#2D0A18;letter-spacing:.06em;text-transform:uppercase;margin-bottom:9px;}
.inp-wrap{position:relative;display:flex;align-items:center;}
.inp-ico{position:absolute;left:16px;color:var(--r5);display:flex;align-items:center;pointer-events:none;transition:all .3s;}
.inp-wrap input{
  width:100%;padding:15px 16px 15px 48px;
  border:2px solid #F5C0D5;border-radius:14px;
  font-family:var(--fb);font-size:15px;color:#150A10;
  background:#FFF8FA;outline:none;
  transition:all .3s;
}
.inp-wrap input::placeholder{color:#E090B0;}
.inp-wrap input:focus{
  border-color:var(--r1);background:white;
  box-shadow:0 0 0 4px rgba(192,19,90,.12),0 4px 20px rgba(192,19,90,.1);
}
.inp-wrap:has(input:focus) .inp-ico{color:var(--r1);transform:scale(1.15);}

/* Pulse quand email saisi */
.inp-pulse{
  position:absolute;right:14px;
  width:8px;height:8px;border-radius:50%;
  background:var(--r1);
  animation:inp-blink 1s ease-in-out infinite;
}
@keyframes inp-blink{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.3;transform:scale(.6)}}

/* ── BOUTON ── */
.btn{
  width:100%;padding:0;border:none;border-radius:15px;cursor:pointer;
  position:relative;overflow:hidden;
  background:linear-gradient(160deg,#D4346A 0%,#C0135A 45%,#9E0F4A 100%);
  box-shadow:0 5px 0 #6B0830,0 8px 28px rgba(192,19,90,.5),0 2px 6px rgba(160,10,60,.3);
  transition:all .2s ease;min-height:60px;
  animation:fadeUp .6s ease .65s both;
}
/* Reflet */
.btn::before{content:'';position:absolute;top:0;left:0;right:0;height:52%;background:linear-gradient(180deg,rgba(255,255,255,.2) 0%,transparent 100%);border-radius:15px 15px 0 0;pointer-events:none;}
/* Shimmer qui passe */
.btn::after{
  content:'';position:absolute;
  top:0;left:-100%;width:60%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.15),transparent);
  animation:shimmer 3s ease-in-out infinite;
}
@keyframes shimmer{0%{left:-100%}60%,100%{left:150%}}

.btn span{display:flex;align-items:center;justify-content:center;gap:10px;color:white;font-family:var(--fh);font-size:15.5px;font-weight:700;letter-spacing:.01em;padding:18px 20px;position:relative;z-index:1;text-shadow:0 1px 3px rgba(0,0,0,.2);}
.btn:hover:not(:disabled){transform:translateY(-4px);box-shadow:0 9px 0 #6B0830,0 18px 40px rgba(192,19,90,.65);}
.btn:active:not(:disabled){transform:translateY(3px);box-shadow:0 2px 0 #6B0830,0 4px 12px rgba(192,19,90,.35);}
.btn:disabled{opacity:.55;cursor:not-allowed;}

/* Loader dots */
.dots{display:inline-flex;gap:6px;padding:18px;justify-content:center;width:100%;position:relative;z-index:1;}
.dots i{display:block;width:7px;height:7px;border-radius:50%;background:white;font-style:normal;animation:dot .9s ease-in-out infinite;}
.dots i:nth-child(2){animation-delay:.15s}.dots i:nth-child(3){animation-delay:.3s}
@keyframes dot{0%,100%{transform:translateY(0);opacity:1}50%{transform:translateY(-8px);opacity:.3}}

.ghost-btn{
  width:100%;padding:13px;border:2px solid #F5C0D5;border-radius:14px;
  background:transparent;color:var(--r2);font-family:var(--fb);font-size:14px;font-weight:600;
  cursor:pointer;transition:all .25s;margin-top:10px;
}
.ghost-btn:hover{background:#FFF0F5;border-color:var(--r4);color:var(--r1);transform:translateY(-2px);}

.sep{display:flex;align-items:center;gap:12px;margin:20px 0 16px;font-size:10px;font-weight:700;color:#D4A0AE;letter-spacing:.1em;text-transform:uppercase;animation:fadeUp .6s ease .7s both;}
.sep::before,.sep::after{content:'';flex:1;height:1.5px;background:linear-gradient(90deg,transparent,#F5C0D5,transparent);}
.sw{text-align:center;font-size:13.5px;color:#9E4D65;animation:fadeUp .6s ease .75s both;}
.sw a{color:var(--r1);font-weight:700;text-decoration:none;transition:all .2s;}
.sw a:hover{color:var(--r2);letter-spacing:.02em;}

/* ── Succès ── */
.success{text-align:center;display:flex;flex-direction:column;align-items:center;padding:10px 0;}
.success-rings{position:relative;width:110px;height:110px;display:flex;align-items:center;justify-content:center;margin-bottom:28px;}
.sr{position:absolute;border-radius:50%;border:2px solid rgba(192,19,90,.2);animation:rpulse 2.5s ease-out infinite;}
.sr1{width:110px;height:110px;animation-delay:0s}
.sr2{width:84px;height:84px;animation-delay:.3s}
.sr3{width:58px;height:58px;animation-delay:.6s}
.sr4{width:34px;height:34px;animation-delay:.9s}
@keyframes rpulse{0%{transform:scale(.6);opacity:0}50%{opacity:1}100%{transform:scale(1.2);opacity:0}}
.success-check{
  width:66px;height:66px;border-radius:50%;
  background:linear-gradient(135deg,var(--r3),var(--r1));
  display:grid;place-items:center;
  box-shadow:0 8px 32px rgba(192,19,90,.55);
  z-index:1;
  animation:pop .6s cubic-bezier(.22,.68,0,1.5) both;
}
@keyframes pop{0%{transform:scale(.2) rotate(-20deg);opacity:0}70%{transform:scale(1.15) rotate(5deg)}100%{transform:scale(1) rotate(0deg);opacity:1}}
.success-title{font-family:var(--fh);font-size:26px;font-weight:800;color:#150A10;letter-spacing:-.03em;margin-bottom:12px;animation:fadeUp .5s ease .2s both;}
.success-sub{font-size:14.5px;line-height:1.7;color:#9E4D65;margin-bottom:6px;animation:fadeUp .5s ease .3s both;}
.success-sub strong{color:var(--r1);}
.success-hint{font-size:12px;color:#C4909E;margin-bottom:28px;animation:fadeUp .5s ease .4s both;}

/* Transitions */
.fade-enter-active,.fade-leave-active{transition:all .4s ease;}
.fade-enter-from{opacity:0;transform:translateY(20px) scale(.97)}
.fade-leave-to{opacity:0;transform:translateY(-20px) scale(.97)}
.shake-enter-active{animation:shake .4s ease;}
@keyframes shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-8px)}40%{transform:translateX(8px)}60%{transform:translateX(-5px)}80%{transform:translateX(5px)}}

@media(max-width:600px){
  .topbar{padding:18px 20px;}
  .card{padding:28px 20px;border-radius:22px;}
  .card-title{font-size:22px;}
  .card-badge,.mini-steps{display:none;}
}
</style>