<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppNavbar from '@/components/AppNavbar.vue'
import AppFooter from '@/components/AppFooter.vue'

const router      = useRouter()
const route       = useRoute<any>()
const authStore   = useAuthStore()

const organizerId = computed(() => Number(route.query.oid))

const digits    = ref<string[]>(['','','','','',''])
const inputRefs = ref<HTMLInputElement[]>([])
const error     = ref('')
const success   = ref('')
const loading   = ref(false)
const countdown = ref(0)
let countInterval: ReturnType<typeof setInterval> | null = null

const sparks = ref<{x:number,y:number,size:number,dur:number,delay:number,op:number}[]>([])

onMounted(() => {
  if (!organizerId.value) { router.push('/login'); return }
  sparks.value = Array.from({length:55},()=>({
    x:Math.random()*100, y:Math.random()*30,
    size:1.5+Math.random()*3, dur:3+Math.random()*6,
    delay:Math.random()*8, op:.3+Math.random()*.7
  }))
  startCountdown(60)
  setTimeout(() => inputRefs.value[0]?.focus(), 400)
})

onUnmounted(() => { if (countInterval) clearInterval(countInterval) })

function startCountdown(seconds: number) {
  countdown.value = seconds
  if (countInterval) clearInterval(countInterval)
  countInterval = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0 && countInterval) clearInterval(countInterval)
  }, 1000)
}

const otp       = computed(() => digits.value.join(''))
const otpFilled = computed(() => otp.value.length === 6 && digits.value.every(d => d !== ''))

function onDigitInput(index: number, e: Event) {
  const val = (e.target as HTMLInputElement).value
  const clean = val.replace(/\D/g, '').slice(-1)
  digits.value[index] = clean
  if (clean && index < 5) setTimeout(() => inputRefs.value[index + 1]?.focus(), 10)
}

function onKeyDown(index: number, e: KeyboardEvent) {
  if (e.key === 'Backspace') {
    if (digits.value[index]) { digits.value[index] = '' }
    else if (index > 0) { digits.value[index-1] = ''; inputRefs.value[index-1]?.focus() }
  }
  if (e.key === 'ArrowLeft' && index > 0) inputRefs.value[index-1]?.focus()
  if (e.key === 'ArrowRight' && index < 5) inputRefs.value[index+1]?.focus()
  if (e.key === 'Enter' && otpFilled.value) handleVerify()
}

function onPaste(e: ClipboardEvent) {
  const text = e.clipboardData?.getData('text')?.replace(/\D/g,'').slice(0,6) ?? ''
  if (text.length === 6) {
    e.preventDefault()
    digits.value = text.split('')
    inputRefs.value[5]?.focus()
  }
}

async function handleVerify() {
  if (!otpFilled.value) { error.value = 'Veuillez entrer les 6 chiffres du code.'; return }
  error.value = ''; loading.value = true
  const result = await authStore.verifyOrganizer2FA(organizerId.value, otp.value)
  loading.value = false
  if (result.success) {
    success.value = 'Connexion réussie !'
    setTimeout(() => router.push('/organizer/dashboard'), 800)
  } else {
    error.value = result.message || 'Code incorrect.'
    digits.value = ['','','','','','']
    setTimeout(() => inputRefs.value[0]?.focus(), 50)
  }
}

async function handleResend() {
  if (countdown.value > 0) return
  error.value = ''; success.value = ''
  const result = await authStore.resendOrganizer2FA(organizerId.value)
  if (result.success) {
    success.value = 'Nouveau code envoyé !'
    startCountdown(60)
    setTimeout(() => { success.value = '' }, 3000)
  } else {
    error.value = result.message || "Erreur lors de l'envoi."
  }
}
</script>

<template>
  <div>
    <AppNavbar />
    <div class="lp">
      <div class="scene">
        <div class="blob b1"></div><div class="blob b2"></div>
        <div class="blob b3"></div><div class="blob b4"></div>
        <div class="sparks">
          <div v-for="(s,i) in sparks" :key="i" class="spark"
            :style="{left:s.x+'%',bottom:s.y+'%',width:s.size+'px',height:s.size+'px',
              animationDuration:s.dur+'s',animationDelay:s.delay+'s',opacity:s.op}"/>
        </div>
        <div class="ring r1"></div><div class="ring r2"></div><div class="ring r3"></div>
      </div>

      <aside class="hero">
        <div class="hero-logo" @click="router.push('/')">
          <div class="hero-logo__mark">E</div>
          <div>
            <span class="hero-logo__name">EventLab</span>
            <span class="hero-logo__sub">Espace Organisateur</span>
          </div>
        </div>
        <div class="hero-badge"><span class="badge-dot"></span>Vérification sécurisée</div>
        <h1 class="hero-h1">Votre espace,<br><em>sécurisé</em></h1>
        <p class="hero-p">La vérification en deux étapes protège votre compte organisateur contre les accès non autorisés.</p>
        <div class="hero-steps">
          <div class="step done">
            <div class="step-dot">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20,6 9,17 4,12"/></svg>
            </div>
            <span>Identifiants vérifiés</span>
          </div>
          <div class="step-line"></div>
          <div class="step active">
            <div class="step-dot pulse">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <span>Code de vérification</span>
          </div>
          <div class="step-line dim"></div>
          <div class="step dim">
            <div class="step-dot">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>
            </div>
            <span>Accès au tableau de bord</span>
          </div>
        </div>
        <div class="hero-tip">
          <div class="tip-icon">💡</div>
          <p>Vérifiez votre boîte mail. Le code expire dans <strong>10 minutes</strong>.</p>
        </div>
      </aside>

      <main class="card">
        <button class="card-back" @click="router.push('/login')">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
          Retour à la connexion
        </button>
        <div class="shield-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <p class="card-eyebrow">Espace Organisateur — 2FA</p>
        <h2 class="card-title">Entrez votre code 🔐</h2>
        <p class="card-sub">Un code à 6 chiffres a été envoyé à votre adresse email.</p>

        <transition name="err">
          <div v-if="error" class="err-box">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ error }}
          </div>
        </transition>
        <transition name="err">
          <div v-if="success" class="ok-box">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="9,12 11,14 15,10"/></svg>
            {{ success }}
          </div>
        </transition>

        <div class="otp-wrap" @paste.prevent="onPaste">
          <input
            v-for="(_, i) in 6" :key="i"
            :ref="el => { if (el) inputRefs[i] = el as HTMLInputElement }"
            class="otp-box" :class="{ filled: digits[i] !== '' }"
            type="text" inputmode="numeric" maxlength="1"
            :value="digits[i]"
            @input="onDigitInput(i, $event)"
            @keydown="onKeyDown(i, $event)"
            autocomplete="one-time-code"
          />
        </div>

        <button class="btn" @click="handleVerify" :disabled="loading || !otpFilled">
          <span v-if="!loading" class="btn__inner">
            Vérifier le code
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </span>
          <span v-else class="dots"><i></i><i></i><i></i></span>
        </button>

        <div class="resend-row">
          <span class="resend-label">Vous n'avez pas reçu le code ?</span>
          <button class="resend-btn" :class="{ disabled: countdown > 0 }" :disabled="countdown > 0" @click="handleResend">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1,4 1,10 7,10"/><path d="M3.51 15a9 9 0 1 0 .49-4.02"/></svg>
            <span v-if="countdown > 0">Renvoyer dans {{ countdown }}s</span>
            <span v-else>Renvoyer le code</span>
          </button>
        </div>
      </main>
    </div>
    <div class="footer-wrap"><AppFooter /></div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;0,700;1,700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
.lp{position:relative;z-index:10;display:grid;grid-template-columns:1fr 460px;width:100%;max-width:1160px;min-height:100vh;padding:72px 56px 0;gap:64px;align-items:center;margin:0 auto;font-family:'Plus Jakarta Sans',sans-serif;}
.scene{position:fixed;inset:0;z-index:0;background:radial-gradient(ellipse 130% 110% at 50% -10%,#A82248 0%,#6B1230 30%,#2E0416 65%,#0D0005 100%);}
.blob{position:absolute;border-radius:50%;filter:blur(100px);mix-blend-mode:screen;animation:blobFloat linear infinite;}
.b1{width:700px;height:700px;background:rgba(168,34,72,.55);top:-200px;left:-150px;animation-duration:18s;}
.b2{width:500px;height:500px;background:rgba(224,112,144,.28);top:50%;right:-100px;animation-duration:14s;animation-delay:-4s;}
.b3{width:420px;height:420px;background:rgba(200,54,95,.38);bottom:-100px;left:30%;animation-duration:22s;animation-delay:-8s;}
.b4{width:280px;height:280px;background:rgba(242,168,190,.18);top:20%;left:40%;animation-duration:16s;animation-delay:-2s;}
@keyframes blobFloat{0%{transform:translateY(0) scale(1);}33%{transform:translateY(-60px) scale(1.07);}66%{transform:translateY(30px) scale(.94);}100%{transform:translateY(0) scale(1);}}
.sparks{position:absolute;inset:0;overflow:hidden;pointer-events:none;}
.spark{position:absolute;border-radius:50%;background:#fff;animation:sparkAnim linear infinite;}
@keyframes sparkAnim{0%{opacity:0;transform:translateY(0) scale(0);}10%{opacity:1;}90%{opacity:.4;transform:translateY(-120px) scale(.5);}100%{opacity:0;transform:translateY(-140px) scale(0);}}
.ring{position:absolute;border-radius:50%;border:1px solid rgba(255,255,255,.08);animation:ringPulse ease-in-out infinite;}
.r1{width:900px;height:900px;top:50%;left:50%;transform:translate(-50%,-50%);animation-duration:6s;}
.r2{width:650px;height:650px;top:50%;left:50%;transform:translate(-50%,-50%);animation-duration:6s;animation-delay:-2s;}
.r3{width:400px;height:400px;top:50%;left:50%;transform:translate(-50%,-50%);animation-duration:6s;animation-delay:-4s;}
@keyframes ringPulse{0%,100%{opacity:.08;transform:translate(-50%,-50%) scale(1);}50%{opacity:.18;transform:translate(-50%,-50%) scale(1.03);}}
.hero{color:#fff;position:relative;z-index:2;display:flex;flex-direction:column;gap:0;}
.hero-logo{display:flex;align-items:center;gap:13px;cursor:pointer;margin-bottom:64px;animation:fadeSlide .8s ease both;}
.hero-logo__mark{width:46px;height:46px;border-radius:12px;background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);backdrop-filter:blur(10px);display:grid;place-items:center;font-family:'Cormorant Garamond',serif;font-size:22px;font-weight:700;color:#fff;}
.hero-logo__name{display:block;font-family:'Cormorant Garamond',serif;font-size:19px;font-weight:600;color:#fff;line-height:1;}
.hero-logo__sub{display:block;font-size:10.5px;color:rgba(255,255,255,.5);letter-spacing:.1em;text-transform:uppercase;margin-top:4px;}
.hero-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:100px;padding:6px 16px;font-size:11px;font-weight:700;color:rgba(255,255,255,.9);letter-spacing:.08em;text-transform:uppercase;margin-bottom:28px;width:fit-content;animation:fadeSlide .8s ease .1s both;}
.badge-dot{width:7px;height:7px;border-radius:50%;background:#fff;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(255,255,255,.5);}70%{box-shadow:0 0 0 7px rgba(255,255,255,0);}}
.hero-h1{font-family:'Cormorant Garamond',serif;font-size:clamp(48px,5vw,68px);font-weight:700;line-height:1.06;margin-bottom:20px;animation:fadeSlide .8s ease .2s both;}
.hero-h1 em{font-style:italic;background:linear-gradient(90deg,#FFD6E5,#fff,#FFB3CF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero-p{font-size:15px;line-height:1.75;color:rgba(255,255,255,.65);max-width:380px;margin-bottom:40px;animation:fadeSlide .8s ease .3s both;}
.hero-steps{display:flex;flex-direction:column;gap:0;margin-bottom:36px;animation:fadeSlide .8s ease .4s both;}
.step{display:flex;align-items:center;gap:14px;padding:10px 0;}
.step span{font-size:14px;font-weight:600;color:rgba(255,255,255,.9);}
.step.dim span{color:rgba(255,255,255,.35);}
.step-dot{width:34px;height:34px;border-radius:50%;background:rgba(255,255,255,.15);border:1.5px solid rgba(255,255,255,.3);display:grid;place-items:center;color:#fff;flex-shrink:0;}
.step.done .step-dot{background:rgba(255,255,255,.25);border-color:rgba(255,255,255,.5);}
.step.active .step-dot{background:rgba(200,54,95,.5);border-color:rgba(200,54,95,.8);box-shadow:0 0 0 6px rgba(200,54,95,.2);}
.step.active .step-dot.pulse{animation:stepPulse 2s ease infinite;}
@keyframes stepPulse{0%,100%{box-shadow:0 0 0 4px rgba(200,54,95,.2);}50%{box-shadow:0 0 0 10px rgba(200,54,95,.05);}}
.step.dim .step-dot{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.12);}
.step-line{width:2px;height:24px;background:rgba(255,255,255,.2);margin-left:16px;}
.step-line.dim{background:rgba(255,255,255,.08);}
.hero-tip{display:flex;gap:14px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:18px 20px;max-width:400px;animation:fadeSlide .8s ease .5s both;}
.tip-icon{font-size:20px;flex-shrink:0;}
.hero-tip p{font-size:13.5px;color:rgba(255,255,255,.6);line-height:1.65;}
.hero-tip strong{color:rgba(255,255,255,.9);}
@keyframes fadeSlide{from{opacity:0;transform:translateY(30px);}to{opacity:1;transform:translateY(0);}}
.card{position:relative;z-index:2;background:rgba(255,255,255,.97);border:1px solid rgba(255,255,255,.6);border-radius:28px;padding:44px 40px;backdrop-filter:blur(30px);box-shadow:0 30px 80px rgba(0,0,0,.25);animation:cardIn .9s cubic-bezier(.22,.68,0,1.1) .1s both;}
@keyframes cardIn{from{opacity:0;transform:translateX(40px) scale(.97);}to{opacity:1;transform:translateX(0) scale(1);}}
.card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#4A0820,#C8365F,#E07090,#C8365F,#4A0820);background-size:200% auto;animation:barSlide 3s linear infinite;border-radius:28px 28px 0 0;}
@keyframes barSlide{0%{background-position:0%;}100%{background-position:200%;}}
.card-back{position:absolute;top:22px;right:22px;display:flex;align-items:center;gap:5px;background:rgba(255,31,113,.06);border:1px solid rgba(255,31,113,.15);border-radius:8px;padding:6px 12px;font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;font-weight:600;color:#7D1235;cursor:pointer;transition:all .2s;}
.card-back:hover{background:rgba(255,31,113,.12);}
.shield-icon{width:64px;height:64px;border-radius:20px;background:linear-gradient(135deg,rgba(200,54,95,.1),rgba(200,54,95,.05));border:1.5px solid rgba(200,54,95,.2);display:grid;place-items:center;color:#C8365F;margin-bottom:20px;margin-top:12px;}
.card-eyebrow{font-size:10.5px;font-weight:700;color:#C8365F;letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px;}
.card-title{font-family:'Cormorant Garamond',serif;font-size:36px;font-weight:700;color:#1A0510;line-height:1.1;margin-bottom:6px;}
.card-sub{font-size:14px;color:#7A4A5A;margin-bottom:28px;}
.err-box{display:flex;align-items:center;gap:8px;background:#fff1f2;color:#be123c;border:1px solid #fecdd3;border-radius:10px;padding:11px 14px;font-size:13px;margin-bottom:18px;}
.ok-box{display:flex;align-items:center;gap:8px;background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0;border-radius:10px;padding:11px 14px;font-size:13px;margin-bottom:18px;}
.err-enter-active,.err-leave-active{transition:all .3s;}
.err-enter-from,.err-leave-to{opacity:0;transform:translateY(-8px);}
.otp-wrap{display:flex;gap:10px;justify-content:center;margin-bottom:32px;}
.otp-box{width:52px;height:62px;border:2px solid rgba(255,31,113,.14);border-radius:14px;background:#FFF8FA;font-family:'Cormorant Garamond',serif;font-size:28px;font-weight:700;color:#1A0510;text-align:center;outline:none;transition:all .2s;caret-color:transparent;}
.otp-box:focus{border-color:#C8365F;background:#fff;box-shadow:0 0 0 4px rgba(255,31,113,.1);transform:translateY(-2px);}
.otp-box.filled{border-color:#A82248;background:#FFF0F5;color:#A82248;}
.btn{width:100%;padding:17px;border:none;border-radius:14px;background:#C8365F;color:#fff;font-family:'Plus Jakarta Sans',sans-serif;font-size:15.5px;font-weight:700;cursor:pointer;position:relative;overflow:hidden;box-shadow:0 6px 24px rgba(125,18,53,.45);transition:all .25s;margin-bottom:24px;}
.btn:hover:not(:disabled){background:#A82248;transform:translateY(-2px);}
.btn:disabled{opacity:.5;cursor:not-allowed;}
.btn__inner{display:flex;align-items:center;justify-content:center;gap:10px;color:#fff;font-weight:700;}
.dots{display:inline-flex;gap:5px;}
.dots i{display:block;width:7px;height:7px;border-radius:50%;background:#fff;animation:db 1s infinite;font-style:normal;}
.dots i:nth-child(2){animation-delay:.15s;}
.dots i:nth-child(3){animation-delay:.3s;}
@keyframes db{0%,100%{transform:translateY(0);opacity:1;}50%{transform:translateY(-7px);opacity:.4;}}
.resend-row{display:flex;flex-direction:column;align-items:center;gap:8px;}
.resend-label{font-size:13px;color:#8A5060;}
.resend-btn{display:flex;align-items:center;gap:7px;background:none;border:1.5px solid rgba(200,54,95,.25);border-radius:10px;padding:9px 18px;font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;font-weight:600;color:#C8365F;cursor:pointer;transition:all .2s;}
.resend-btn:hover:not(.disabled){background:rgba(200,54,95,.06);}
.resend-btn.disabled{color:#C0909A;cursor:not-allowed;}
.footer-wrap{position:relative;z-index:10;}
@media(max-width:1100px){.lp{grid-template-columns:1fr;padding:100px 24px 40px;gap:32px;}.hero-logo{margin-bottom:32px;}.hero-tip{display:none;}.card{padding:36px 28px;}}
@media(max-width:600px){.otp-box{width:42px;height:52px;font-size:22px;}.card{padding:28px 20px;border-radius:20px;}.card-title{font-size:28px;}}
</style>