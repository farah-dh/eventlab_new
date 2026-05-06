<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, computed } from 'vue'
import AppNavbar from '@/components/AppNavbar.vue'
import AppFooter from '@/components/AppFooter.vue'

const router = useRouter()
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

const form = ref({
  firstname: '', lastname: '', username: '',
  email: '', password: '', password_confirm: '',
})
const showPassword  = ref(false)
const showPassword2 = ref(false)
const acceptTerms   = ref(false)
const error         = ref('')
const success       = ref('')
const isLoading     = ref(false)

const passwordStrength = computed(() => {
  const p = form.value.password
  if (!p) return { score: 0, label: '', color: '' }
  let s = 0
  if (p.length >= 8)           s++
  if (/[A-Z]/.test(p))         s++
  if (/[0-9]/.test(p))         s++
  if (/[^A-Za-z0-9]/.test(p))  s++
  return {
    score: s,
    label: ['', 'Faible', 'Moyen', 'Bon', 'Excellent'][s],
    color: ['', '#C0135A', '#F59E0B', '#3B82F6', '#10B981'][s],
  }
})

const handleRegister = async () => {
  error.value = ''
  success.value = ''
  if (!form.value.firstname || !form.value.email || !form.value.password) {
    error.value = 'Veuillez remplir tous les champs obligatoires'; return
  }
  if (!form.value.username) { error.value = "Le nom d'utilisateur est requis"; return }
  if (form.value.password.length < 6) { error.value = 'Minimum 6 caractères'; return }
  if (form.value.password !== form.value.password_confirm) { error.value = 'Les mots de passe ne correspondent pas'; return }
  if (!acceptTerms.value) { error.value = "Acceptez les conditions d'utilisation"; return }
  isLoading.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/auth/register/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    const data = await res.json()
    if (!res.ok) {
      const errs = data.errors || data
      const k = Object.keys(errs)[0]
      error.value = String(Array.isArray(errs[k]) ? errs[k][0] : errs[k] || 'Erreur'); return
    }
    success.value = 'Compte créé avec succès ! Redirection...'
    setTimeout(() => router.push('/login'), 1800)
  } catch { error.value = 'Impossible de se connecter au serveur' }
  finally { isLoading.value = false }
}
</script>

<template>
  <div>
    <AppNavbar />

    <div class="page">
      <div class="bg-mesh"></div>
      <div class="orb o1"></div>
      <div class="orb o2"></div>
      <div class="orb o3"></div>
      <div class="orb o4"></div>
      <div class="ring r1"></div>
      <div class="ring r2"></div>
      <div class="ring r3"></div>
      <div class="dots-bg"></div>

      <div class="center">
        <div class="card">
          <div class="card-top">
            <div class="card-ico">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <div>
              <p class="eyebrow">Créer un compte</p>
              <h2 class="card-title">Bienvenue ! ✨</h2>
            </div>
            <div class="card-badge">
              <span class="badge-dot"></span>
              Gratuit
            </div>
          </div>

          <p class="card-sub">Inscrivez-vous en quelques secondes pour accéder à tous les événements</p>

          <Transition name="shake">
            <div v-if="error" class="err-box">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              {{ error }}
            </div>
          </Transition>
          <div v-if="success" class="ok-box">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20,6 9,17 4,12"/></svg>
            {{ success }}
          </div>

          <div class="mini-stats">
            <div class="ms"><strong>200+</strong><span>Événements</span></div>
            <div class="ms-div"></div>
            <div class="ms"><strong>50K+</strong><span>Membres</span></div>
            <div class="ms-div"></div>
            <div class="ms"><strong>4.9★</strong><span>Note</span></div>
          </div>

          <div class="row">
            <div class="field">
              <label>Prénom <span class="req">*</span></label>
              <div class="inp-wrap">
                <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span>
                <input v-model="form.firstname" type="text" placeholder="Farah" />
              </div>
            </div>
            <div class="field">
              <label>Nom</label>
              <div class="inp-wrap">
                <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span>
                <input v-model="form.lastname" type="text" placeholder="Ben Ali" />
              </div>
            </div>
          </div>

          <div class="field">
            <label>Nom d'utilisateur <span class="req">*</span></label>
            <div class="inp-wrap">
              <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5.52 19c.64-2.2 1.84-3 3.22-3h6.52c1.38 0 2.58.8 3.22 3"/><circle cx="12" cy="10" r="3"/><circle cx="12" cy="12" r="10"/></svg></span>
              <input v-model="form.username" type="text" placeholder="farah_ba" />
            </div>
          </div>

          <div class="field">
            <label>Adresse email <span class="req">*</span></label>
            <div class="inp-wrap">
              <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></span>
              <input v-model="form.email" type="email" placeholder="vous@email.com" />
            </div>
          </div>

          <div class="row">
            <div class="field">
              <label>Mot de passe <span class="req">*</span></label>
              <div class="inp-wrap">
                <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></span>
                <input :type="showPassword ? 'text' : 'password'" v-model="form.password" placeholder="••••••••" />
                <button type="button" class="eye" @click="showPassword = !showPassword">
                  <svg v-if="!showPassword" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <div v-if="form.password" class="sbar">
                <div v-for="i in 4" :key="i" class="sseg" :style="{ background: i <= passwordStrength.score ? passwordStrength.color : '#F8C0D5' }"></div>
                <span :style="{ color: passwordStrength.color, fontSize:'11px', fontWeight:'700', minWidth:'50px' }">{{ passwordStrength.label }}</span>
              </div>
            </div>
            <div class="field">
              <label>Confirmer <span class="req">*</span></label>
              <div class="inp-wrap" :class="{ 'ok': form.password_confirm && form.password === form.password_confirm, 'bad': form.password_confirm && form.password !== form.password_confirm }">
                <span class="ico"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></span>
                <input :type="showPassword2 ? 'text' : 'password'" v-model="form.password_confirm" placeholder="••••••••" @keyup.enter="handleRegister" />
                <button type="button" class="eye" @click="showPassword2 = !showPassword2">
                  <svg v-if="!showPassword2" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                </button>
              </div>
              <p v-if="form.password_confirm && form.password === form.password_confirm" style="font-size:11px;color:#10B981;font-weight:600;margin-top:5px;display:flex;align-items:center;gap:4px">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20,6 9,17 4,12"/></svg> OK
              </p>
            </div>
          </div>

          <label class="check">
            <input type="checkbox" v-model="acceptTerms" />
            <span class="cbox"></span>
            <span class="clbl">J'accepte les <a href="#" @click.prevent>conditions d'utilisation</a> et la <a href="#" @click.prevent>politique de confidentialité</a></span>
          </label>

          <button class="btn" @click="handleRegister" :disabled="isLoading">
            <span v-if="!isLoading">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              Créer mon compte
            </span>
            <span v-else class="dots"><i></i><i></i><i></i></span>
          </button>

          <div class="sep"><span>ou</span></div>
          <p class="sw">Déjà un compte ? <RouterLink to="/login">Se connecter</RouterLink></p>
        </div>
      </div>
    </div>

    <AppFooter />
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700;12..96,800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
:root { --r1:#C0135A; --r2:#9E0F4A; --r3:#6B0830; --r4:#E8457A; --r5:#F4A0BF; --fh:'Bricolage Grotesque',sans-serif; --fb:'Plus Jakarta Sans',sans-serif; }
.page { min-height: 100vh; width: 100%; position: relative; overflow: hidden; display: flex; flex-direction: column; font-family: var(--fb); padding-top: 72px; }
.bg-mesh { position: absolute; inset: 0; z-index: 0; background: linear-gradient(135deg, #F2A0C0 0%, #D4608A 25%, #C0135A 55%, #9E0F4A 78%, #6B0830 100%); }
.orb { position:absolute;border-radius:50%;filter:blur(80px);pointer-events:none;z-index:1; }
.o1{width:700px;height:700px;background:radial-gradient(circle,rgba(255,255,255,.18),transparent 70%);top:-250px;left:-200px;animation:drift 16s ease-in-out infinite alternate;}
.o2{width:500px;height:500px;background:radial-gradient(circle,rgba(140,15,46,.4),transparent 70%);bottom:-150px;right:-100px;animation:drift 20s ease-in-out infinite alternate-reverse;}
.o3{width:400px;height:400px;background:radial-gradient(circle,rgba(255,255,255,.12),transparent 70%);top:30%;right:10%;animation:drift 12s ease-in-out infinite alternate;}
.o4{width:300px;height:300px;background:radial-gradient(circle,rgba(255,112,150,.25),transparent 70%);bottom:10%;left:20%;animation:drift 14s ease-in-out infinite alternate-reverse;}
@keyframes drift{from{transform:translate(0,0)}to{transform:translate(30px,40px)}}
.ring{position:absolute;border-radius:50%;border:1.5px solid rgba(255,255,255,.15);pointer-events:none;z-index:1;}
.r1{width:600px;height:600px;top:-150px;right:-150px;animation:spin 30s linear infinite;}
.r2{width:400px;height:400px;bottom:-100px;left:-100px;animation:spin 20s linear infinite reverse;}
.r3{width:200px;height:200px;top:20%;left:5%;animation:spin 15s linear infinite;border-color:rgba(255,255,255,.08);}
@keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
.dots-bg{position:absolute;inset:0;z-index:1;background-image:radial-gradient(circle,rgba(255,255,255,.15) 1.5px,transparent 1.5px);background-size:36px 36px;}
.center { flex: 1; display: flex; align-items: center; justify-content: center; padding: 20px 20px 48px; position: relative; z-index: 10; }
.card { background: white; border-radius: 28px; padding: 36px 38px; width: 100%; max-width: 600px; box-shadow: 0 0 0 1px rgba(0,0,0,.06), 0 8px 16px rgba(0,0,0,.08), 0 32px 80px rgba(140,15,46,.3), 0 0 120px rgba(232,48,90,.2); animation: cardIn .8s cubic-bezier(.22,.68,0,1.1) .1s both; position: relative; }
@keyframes cardIn{from{opacity:0;transform:translateY(32px) scale(.95)}to{opacity:1;transform:none}}
.card::before{content:'';position:absolute;top:0;left:24px;right:24px;height:3px;background:linear-gradient(90deg,var(--r3),var(--r1),var(--r4),var(--r5),var(--r4),var(--r1),var(--r3));background-size:200% auto;animation:bar 3s linear infinite;border-radius:0 0 3px 3px;}
@keyframes bar{0%{background-position:0%}100%{background-position:200%}}
.card-top{display:flex;align-items:center;gap:14px;margin-bottom:8px;padding-top:8px;}
.card-ico{width:50px;height:50px;border-radius:16px;background:linear-gradient(135deg,#FFF0F5,#F8C0D5);border:1.5px solid rgba(232,48,90,.13);display:grid;place-items:center;color:var(--r1);flex-shrink:0;}
.eyebrow{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--r1);margin-bottom:4px;}
.card-title{font-family:var(--fh);font-size:26px;font-weight:800;color:#150A10;letter-spacing:-.03em;line-height:1;}
.card-badge{margin-left:auto;display:inline-flex;align-items:center;gap:7px;background:rgba(16,185,129,.08);border:1px solid rgba(16,185,129,.2);border-radius:100px;padding:5px 12px;font-size:11px;font-weight:700;color:#059669;}
.badge-dot{width:6px;height:6px;border-radius:50%;background:#10B981;animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.card-sub{font-size:13.5px;color:#9E4D65;margin-bottom:16px;}
.err-box{display:flex;align-items:center;gap:10px;background:#FFF0F3;border:1px solid #F4B0CA;color:#B01540;border-radius:12px;padding:11px 14px;font-size:13px;font-weight:500;margin-bottom:14px;}
.ok-box{display:flex;align-items:center;gap:10px;background:#F0FDF4;border:1px solid #BBF7D0;color:#166534;border-radius:12px;padding:11px 14px;font-size:13px;font-weight:500;margin-bottom:14px;}
.mini-stats{display:flex;align-items:center;background:linear-gradient(135deg,#FFF0F5,#F8D0E4);border:1px solid rgba(232,48,90,.1);border-radius:14px;padding:12px 20px;margin-bottom:20px;gap:0;}
.ms{flex:1;text-align:center;}
.ms strong{display:block;font-family:var(--fh);font-size:18px;font-weight:800;color:var(--r1);}
.ms span{font-size:10px;font-weight:700;color:#C4909E;letter-spacing:.06em;text-transform:uppercase;}
.ms-div{width:1px;height:32px;background:rgba(232,48,90,.12);}
.row{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.field{margin-bottom:14px;}
.field label{display:block;font-size:11px;font-weight:700;color:#2D0A18;letter-spacing:.06em;text-transform:uppercase;margin-bottom:7px;}
.req{color:var(--r1);}
.inp-wrap{position:relative;display:flex;align-items:center;}
.ico{position:absolute;left:13px;color:#F4A0BF;display:flex;align-items:center;pointer-events:none;transition:color .2s;}
.inp-wrap input{width:100%;padding:12px 36px 12px 40px;border:2px solid #F5C0D5;border-radius:12px;font-family:var(--fb);font-size:14px;color:#150A10;background:#FFF5F8;outline:none;transition:all .2s;}
.inp-wrap input::placeholder{color:#E090B0;}
.inp-wrap input:focus{border-color:var(--r1);background:white;box-shadow:0 0 0 4px rgba(232,48,90,.1);}
.inp-wrap:has(input:focus) .ico{color:var(--r1);}
.inp-wrap.ok input{border-color:#10B981 !important;box-shadow:0 0 0 3px rgba(16,185,129,.1) !important;}
.inp-wrap.bad input{border-color:#F59E0B !important;}
.eye{position:absolute;right:10px;background:transparent;border:none;cursor:pointer;color:#D4A0AE;display:flex;align-items:center;padding:4px;transition:color .2s;}
.eye:hover{color:var(--r1);}
.sbar{display:flex;align-items:center;gap:4px;margin-top:7px;}
.sseg{flex:1;height:3px;border-radius:3px;transition:background .3s;}
.check{display:flex;align-items:flex-start;gap:10px;cursor:pointer;margin-bottom:20px;user-select:none;}
.check input{display:none;}
.cbox{width:17px;height:17px;border:2px solid #F5C0D5;border-radius:5px;background:white;position:relative;transition:all .2s;flex-shrink:0;margin-top:1px;}
.check input:checked + .cbox{background:linear-gradient(135deg,var(--r1),var(--r3));border-color:var(--r1);}
.check input:checked + .cbox::after{content:'';position:absolute;left:4px;top:1px;width:5px;height:9px;border:solid white;border-width:0 2px 2px 0;transform:rotate(45deg);}
.clbl{font-size:12px;color:#9E4D65;font-weight:500;line-height:1.5;}
.clbl a{color:var(--r1);font-weight:700;text-decoration:none;}
.clbl a:hover{text-decoration:underline;}
.btn{width:100%;padding:0;border:none;border-radius:15px;cursor:pointer;position:relative;overflow:hidden;background:linear-gradient(160deg,#D4346A 0%,#C0135A 45%,#9E0F4A 100%);box-shadow:0 5px 0 #6B0830,0 8px 28px rgba(232,48,90,.5),0 2px 6px rgba(200,20,60,.3);transition:all .18s ease;min-height:58px;}
.btn::before{content:'';position:absolute;top:0;left:0;right:0;height:52%;background:linear-gradient(180deg,rgba(255,255,255,.2) 0%,transparent 100%);border-radius:15px 15px 0 0;pointer-events:none;}
.btn span{display:flex;align-items:center;justify-content:center;gap:10px;color:white;font-family:var(--fh);font-size:16px;font-weight:700;letter-spacing:.01em;padding:17px 20px;position:relative;z-index:1;text-shadow:0 1px 3px rgba(0,0,0,.2);}
.btn:hover:not(:disabled){transform:translateY(-3px);box-shadow:0 8px 0 #6B0830,0 16px 36px rgba(232,48,90,.6);}
.btn:active:not(:disabled){transform:translateY(3px);box-shadow:0 2px 0 #6B0830,0 4px 12px rgba(232,48,90,.35);}
.btn:disabled{opacity:.55;cursor:not-allowed;}
.dots{display:inline-flex;gap:6px;padding:17px;justify-content:center;width:100%;position:relative;z-index:1;}
.dots i{display:block;width:7px;height:7px;border-radius:50%;background:white;font-style:normal;animation:dot .9s ease-in-out infinite;}
.dots i:nth-child(2){animation-delay:.15s}.dots i:nth-child(3){animation-delay:.3s}
@keyframes dot{0%,100%{transform:translateY(0);opacity:1}50%{transform:translateY(-7px);opacity:.4}}
.sep{display:flex;align-items:center;gap:12px;margin:16px 0 12px;font-size:10px;font-weight:700;color:#D4A0AE;letter-spacing:.1em;text-transform:uppercase;}
.sep::before,.sep::after{content:'';flex:1;height:1.5px;background:#F8C0D5;}
.sw{text-align:center;font-size:13px;color:#9E4D65;}
.sw a{color:var(--r1);font-weight:700;text-decoration:none;transition:color .2s;}
.sw a:hover{color:var(--r2);}
.shake-enter-active{animation:shake .4s ease;}
@keyframes shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-7px)}40%{transform:translateX(7px)}60%{transform:translateX(-4px)}80%{transform:translateX(4px)}}
@media(max-width:640px){.card{padding:28px 20px;border-radius:20px;}.row{grid-template-columns:1fr;}.card-title{font-size:22px;}.mini-stats{display:none;}.card-badge{display:none;}}
</style>