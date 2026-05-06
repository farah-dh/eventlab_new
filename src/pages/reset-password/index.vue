<route lang="yaml">
meta:
  layout: blank
  public: true
</route>

<script setup lang="ts">
definePage({ meta: { layout: 'blank', public: true } })
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const router    = useRouter()
const route     = useRoute()
const authStore = useAuthStore()

const password        = ref('')
const confirmPassword = ref('')
const showPassword    = ref(false)
const showConfirm     = ref(false)
const error           = ref('')
const success         = ref(false)
const loading         = ref(false)

const token = computed(() => String((route as any).query?.token ?? ''))

const strength = computed(() => {
  const p = password.value
  if (!p) return 0
  let s = 0
  if (p.length >= 8)           s++
  if (/[A-Z]/.test(p))         s++
  if (/[0-9]/.test(p))         s++
  if (/[^A-Za-z0-9]/.test(p))  s++
  return s
})
const strengthLabel = computed(() => ['', 'Faible', 'Moyen', 'Bon', 'Excellent'][strength.value])
const strengthColor = computed(() => ['', '#E8305A', '#F59E0B', '#3B82F6', '#10B981'][strength.value])

const handleSubmit = async () => {
  if (!password.value || !confirmPassword.value) { error.value = 'Veuillez remplir tous les champs'; return }
  if (password.value !== confirmPassword.value)   { error.value = 'Les mots de passe ne correspondent pas'; return }
  if (strength.value < 2)                         { error.value = 'Votre mot de passe est trop faible'; return }
  error.value = ''
  loading.value = true
  try {
    await authStore.resetPassword(token.value, password.value)
    success.value = true
  } catch (e: any) {
    error.value = e?.message || 'Une erreur est survenue. Le lien est peut-être expiré.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">

    <div class="bg-blob b1"></div>
    <div class="bg-blob b2"></div>
    <div class="bg-blob b3"></div>
    <div class="bg-dots"></div>

    <div class="layout">

      <!-- ══ GAUCHE ══ -->
      <aside class="hero">

        <div class="logo" @click="router.push('/')">
          <div class="logo-mark">E</div>
          <span>Event <strong>Lab</strong></span>
        </div>

        <div class="hero-body">
          <div class="hero-badge">
            <span class="blink-dot"></span>
            Sécurité renforcée
          </div>

          <h1 class="hero-h1">
            Nouveau<br>
            <span class="hero-em">mot de passe</span>
          </h1>

          <p class="hero-p">
            Choisissez un mot de passe fort et unique pour protéger votre compte Event Lab.
          </p>

          <!-- Tips dynamiques -->
          <div class="tips">
            <p class="tips-title">Critères de sécurité</p>
            <div class="tip" :class="{ 'tip-ok': password.length >= 8 }">
              <div class="tip-ico">
                <svg v-if="password.length >= 8" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5"><polyline points="20,6 9,17 4,12"/></svg>
                <svg v-else width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </div>
              Au moins 8 caractères
            </div>
            <div class="tip" :class="{ 'tip-ok': /[A-Z]/.test(password) }">
              <div class="tip-ico">
                <svg v-if="/[A-Z]/.test(password)" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5"><polyline points="20,6 9,17 4,12"/></svg>
                <svg v-else width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </div>
              Une lettre majuscule (A–Z)
            </div>
            <div class="tip" :class="{ 'tip-ok': /[0-9]/.test(password) }">
              <div class="tip-ico">
                <svg v-if="/[0-9]/.test(password)" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5"><polyline points="20,6 9,17 4,12"/></svg>
                <svg v-else width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </div>
              Un chiffre (0–9)
            </div>
            <div class="tip" :class="{ 'tip-ok': /[^A-Za-z0-9]/.test(password) }">
              <div class="tip-ico">
                <svg v-if="/[^A-Za-z0-9]/.test(password)" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5"><polyline points="20,6 9,17 4,12"/></svg>
                <svg v-else width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </div>
              Un caractère spécial (!, @, #…)
            </div>
          </div>
        </div>

        <RouterLink to="/login" class="back-link">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15,18 9,12 15,6"/></svg>
          Retour à la connexion
        </RouterLink>

      </aside>

      <!-- ══ DROITE ══ -->
      <main class="panel">
        <div class="card">
          <Transition name="fade" mode="out-in">

            <!-- ── Succès ── -->
            <div v-if="success" key="ok" class="success">
              <div class="success-rings">
                <div class="sr sr1"></div>
                <div class="sr sr2"></div>
                <div class="sr sr3"></div>
                <div class="success-check">
                  <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20,6 9,17 4,12"/>
                  </svg>
                </div>
              </div>
              <h2 class="success-title">Mot de passe mis à jour ! 🎉</h2>
              <p class="success-sub">
                Votre mot de passe a été réinitialisé avec succès. Vous pouvez maintenant vous connecter.
              </p>
              <button class="send-btn" @click="router.push('/login')">
                <span>
                  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10,17 15,12 10,7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
                  Se connecter
                </span>
              </button>
            </div>

            <!-- ── Formulaire ── -->
            <div v-else key="form" class="form-body">

              <div class="card-head">
                <div class="card-ico">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <div>
                  <p class="eyebrow">Réinitialisation</p>
                  <h2 class="card-title">Nouveau mot de passe</h2>
                </div>
              </div>

              <p class="card-sub">Choisissez un mot de passe sécurisé pour protéger votre compte.</p>

              <Transition name="shake">
                <div v-if="error" class="err-box">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  {{ error }}
                </div>
              </Transition>

              <!-- Mot de passe -->
              <div class="field">
                <label>Nouveau mot de passe</label>
                <div class="inp-wrap">
                  <span class="inp-ico">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  </span>
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    placeholder="••••••••"
                    autocomplete="new-password"
                  />
                  <button type="button" class="eye-btn" @click="showPassword = !showPassword">
                    <svg v-if="!showPassword" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>

                <!-- Barre de force -->
                <div v-if="password" class="strength-row">
                  <div class="strength-bars">
                    <div v-for="i in 4" :key="i" class="strength-seg" :style="{ background: i <= strength ? strengthColor : '#FFE0EC' }"></div>
                  </div>
                  <span class="strength-lbl" :style="{ color: strengthColor }">{{ strengthLabel }}</span>
                </div>
              </div>

              <!-- Confirmer -->
              <div class="field">
                <label>Confirmer le mot de passe</label>
                <div class="inp-wrap" :class="{ 'inp-ok': confirmPassword && confirmPassword === password, 'inp-bad': confirmPassword && confirmPassword !== password }">
                  <span class="inp-ico">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                  </span>
                  <input
                    v-model="confirmPassword"
                    :type="showConfirm ? 'text' : 'password'"
                    placeholder="••••••••"
                    autocomplete="new-password"
                    @keyup.enter="handleSubmit"
                  />
                  <button type="button" class="eye-btn" @click="showConfirm = !showConfirm">
                    <svg v-if="!showConfirm" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>
                <p v-if="confirmPassword && confirmPassword === password" class="hint-ok">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20,6 9,17 4,12"/></svg>
                  Les mots de passe correspondent
                </p>
                <p v-if="confirmPassword && confirmPassword !== password" class="hint-bad">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  Les mots de passe ne correspondent pas
                </p>
              </div>

              <!-- Bouton -->
              <button class="send-btn" @click="handleSubmit" :disabled="loading">
                <span v-if="!loading">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                  Réinitialiser le mot de passe
                </span>
                <span v-else class="dots"><i></i><i></i><i></i></span>
              </button>

              <div class="sep"><span>ou</span></div>

              <p class="login-txt">
                Retourner à la
                <RouterLink to="/login">connexion</RouterLink>
              </p>
            </div>

          </Transition>
        </div>
      </main>

    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,600;12..96,700;12..96,800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --r1:#E8305A; --r2:#C91F48; --r3:#8C0F2E; --r4:#FF7096; --r5:#FFB3C6;
  --rg:#FFF0F4; --page-bg:#FEF0F4;
  --ink:#200815; --ink2:#5C2035; --ink3:#9E4D65;
  --fh:'Bricolage Grotesque',sans-serif;
  --fb:'Plus Jakarta Sans',sans-serif;
}

.page { min-height:100vh;width:100%;background:var(--page-bg);font-family:var(--fb);position:relative;overflow:hidden;display:flex;align-items:stretch; }

.bg-blob { position:absolute;border-radius:50%;filter:blur(70px);pointer-events:none;z-index:0; }
.b1{width:600px;height:600px;background:radial-gradient(circle,rgba(232,48,90,.18),transparent 70%);top:-200px;left:-150px;animation:drift 14s ease-in-out infinite alternate;}
.b2{width:500px;height:500px;background:radial-gradient(circle,rgba(255,112,150,.14),transparent 70%);bottom:-150px;right:-80px;animation:drift 18s ease-in-out infinite alternate-reverse;}
.b3{width:300px;height:300px;background:radial-gradient(circle,rgba(255,179,198,.2),transparent 70%);top:40%;left:40%;animation:drift 10s ease-in-out infinite alternate;}
@keyframes drift{from{transform:translate(0,0)}to{transform:translate(25px,35px)}}
.bg-dots{position:absolute;inset:0;z-index:0;background-image:radial-gradient(circle,rgba(232,48,90,.12) 1.5px,transparent 1.5px);background-size:32px 32px;}

.layout{position:relative;z-index:1;display:grid;grid-template-columns:1fr 500px;width:100%;min-height:100vh;}

/* ══ HERO ══ */
.hero{background:linear-gradient(160deg,#F7C5D5 0%,#F2A8BF 40%,#EE8BAA 100%);display:flex;flex-direction:column;padding:48px 56px;position:relative;overflow:hidden;}
.hero::after{content:'';position:absolute;width:340px;height:340px;border-radius:50%;border:60px solid rgba(255,255,255,.12);top:-100px;right:-100px;pointer-events:none;}
.hero::before{content:'';position:absolute;width:200px;height:200px;border-radius:50%;border:40px solid rgba(255,255,255,.08);bottom:60px;left:-60px;pointer-events:none;}

.logo{display:inline-flex;align-items:center;gap:10px;cursor:pointer;width:fit-content;animation:up .6s ease both;}
.logo-mark{width:36px;height:36px;border-radius:11px;background:linear-gradient(135deg,var(--r1),var(--r3));display:grid;place-items:center;font-family:var(--fh);font-size:18px;font-weight:800;color:white;box-shadow:0 4px 14px rgba(140,15,46,.35);}
.logo span{font-family:var(--fh);font-size:18px;font-weight:400;color:var(--ink);letter-spacing:-.02em;}
.logo span strong{font-weight:800;}

.hero-body{flex:1;display:flex;flex-direction:column;justify-content:center;padding:40px 0;}
.hero-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.35);border:1px solid rgba(255,255,255,.5);backdrop-filter:blur(10px);border-radius:100px;padding:6px 16px;font-size:11px;font-weight:700;color:var(--r3);letter-spacing:.08em;text-transform:uppercase;width:fit-content;margin-bottom:28px;animation:up .6s ease .1s both;}
.blink-dot{width:7px;height:7px;border-radius:50%;background:var(--r1);animation:blink 2s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(232,48,90,.4)}50%{opacity:.5;box-shadow:0 0 0 5px rgba(232,48,90,0)}}

.hero-h1{font-family:var(--fh);font-size:clamp(46px,4.2vw,70px);font-weight:800;line-height:1.0;letter-spacing:-.04em;color:var(--ink);margin-bottom:18px;animation:up .6s ease .15s both;}
.hero-em{display:block;background:linear-gradient(135deg,var(--r1) 0%,var(--r3) 60%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}
.hero-p{font-size:15px;line-height:1.8;color:rgba(32,8,21,.55);max-width:340px;margin-bottom:36px;animation:up .6s ease .2s both;}

/* Tips */
.tips{background:rgba(255,255,255,.4);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.65);border-radius:18px;padding:18px 20px;animation:up .6s ease .25s both;}
.tips-title{font-size:10.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--r3);margin-bottom:14px;opacity:.7;}
.tip{display:flex;align-items:center;gap:10px;font-size:13px;color:rgba(32,8,21,.4);padding:7px 0;border-bottom:1px solid rgba(255,255,255,.5);transition:color .3s;}
.tip:last-child{border-bottom:none;padding-bottom:0;}
.tip-ok{color:var(--ink);}
.tip-ico{width:20px;height:20px;border-radius:50%;background:rgba(255,255,255,.5);border:1.5px solid rgba(232,48,90,.15);display:grid;place-items:center;flex-shrink:0;color:rgba(32,8,21,.25);transition:all .3s;}
.tip-ok .tip-ico{background:var(--r1);border-color:var(--r1);color:white;box-shadow:0 2px 8px rgba(232,48,90,.35);}

.back-link{display:inline-flex;align-items:center;gap:7px;color:rgba(32,8,21,.45);font-size:13.5px;font-weight:500;text-decoration:none;transition:color .2s,gap .2s;animation:up .6s ease .3s both;}
.back-link:hover{color:var(--r1);gap:12px;}
@keyframes up{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}

/* ══ PANEL ══ */
.panel{display:flex;align-items:center;justify-content:center;padding:48px 44px;background:rgba(255,240,244,.6);}
.card{background:white;border-radius:28px;padding:44px 40px;width:100%;max-width:420px;box-shadow:0 0 0 1px rgba(232,48,90,.07),0 4px 6px rgba(0,0,0,.02),0 16px 40px rgba(232,48,90,.12),0 40px 80px rgba(0,0,0,.05);animation:cardIn .7s cubic-bezier(.22,.68,0,1.1) both;}
@keyframes cardIn{from{opacity:0;transform:translateY(20px) scale(.97)}to{opacity:1;transform:none}}
.card::before{content:'';display:block;height:4px;background:linear-gradient(90deg,var(--r1),var(--r4),var(--r5));border-radius:4px;margin-bottom:32px;}

.card-head{display:flex;align-items:center;gap:16px;margin-bottom:14px;}
.card-ico{width:52px;height:52px;border-radius:16px;background:linear-gradient(135deg,var(--rg),#FFE0EC);border:1.5px solid rgba(232,48,90,.13);display:grid;place-items:center;color:var(--r1);flex-shrink:0;}
.eyebrow{font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--r1);margin-bottom:5px;}
.card-title{font-family:var(--fh);font-size:26px;font-weight:800;color:var(--ink);letter-spacing:-.03em;line-height:1;}
.card-sub{font-size:14px;line-height:1.7;color:var(--ink3);margin-bottom:22px;}

.err-box{display:flex;align-items:center;gap:10px;background:#FFF0F3;border:1px solid #FFCCD6;color:#B01540;border-radius:12px;padding:12px 14px;font-size:13px;font-weight:500;margin-bottom:18px;}

/* Champs */
.field{margin-bottom:18px;}
.field label{display:block;font-size:12px;font-weight:700;color:var(--ink);letter-spacing:.05em;text-transform:uppercase;margin-bottom:9px;}
.inp-wrap{position:relative;display:flex;align-items:center;}
.inp-ico{position:absolute;left:16px;color:var(--r5);display:flex;align-items:center;pointer-events:none;transition:color .2s;}
.inp-wrap input{width:100%;padding:14px 44px 14px 48px;border:2px solid #FFD6E4;border-radius:14px;font-family:var(--fb);font-size:15px;color:var(--ink);background:#FFF8FA;outline:none;transition:all .2s;}
.inp-wrap input::placeholder{color:#EAACBE;}
.inp-wrap input:focus{border-color:var(--r1);background:white;box-shadow:0 0 0 4px rgba(232,48,90,.1);}
.inp-wrap:has(input:focus) .inp-ico{color:var(--r1);}
.inp-ok input{border-color:#10B981 !important;box-shadow:0 0 0 3px rgba(16,185,129,.1) !important;}
.inp-bad input{border-color:#F59E0B !important;box-shadow:0 0 0 3px rgba(245,158,11,.1) !important;}

.eye-btn{position:absolute;right:14px;background:transparent;border:none;cursor:pointer;color:#D4A0AE;display:flex;align-items:center;padding:4px;transition:color .2s;}
.eye-btn:hover{color:var(--r1);}

/* Barre de force — 4 segments */
.strength-row{display:flex;align-items:center;gap:10px;margin-top:9px;}
.strength-bars{display:flex;gap:4px;flex:1;}
.strength-seg{flex:1;height:4px;border-radius:4px;transition:background .35s ease;}
.strength-lbl{font-size:11.5px;font-weight:700;min-width:52px;text-align:right;transition:color .35s;}

.hint-ok{display:flex;align-items:center;gap:5px;font-size:12px;color:#10B981;font-weight:600;margin-top:7px;}
.hint-bad{display:flex;align-items:center;gap:5px;font-size:12px;color:#F59E0B;font-weight:600;margin-top:7px;}

/* Bouton */
.send-btn{width:100%;padding:0;border:none;border-radius:16px;cursor:pointer;position:relative;overflow:hidden;background:linear-gradient(160deg,#F0547A 0%,#E8305A 45%,#C01F45 100%);box-shadow:0 5px 0px #8C0F2E,0 8px 24px rgba(232,48,90,.45),0 2px 6px rgba(200,20,60,.25);transition:all .18s ease;min-height:60px;margin-top:4px;}
.send-btn::before{content:'';position:absolute;top:0;left:0;right:0;height:52%;background:linear-gradient(180deg,rgba(255,255,255,.18) 0%,transparent 100%);border-radius:16px 16px 0 0;pointer-events:none;}
.send-btn span{display:flex;align-items:center;justify-content:center;gap:10px;color:white;font-family:var(--fh);font-size:15.5px;font-weight:700;letter-spacing:.01em;padding:18px 20px;position:relative;z-index:1;text-shadow:0 1px 3px rgba(0,0,0,.2);}
.send-btn:hover:not(:disabled){transform:translateY(-3px);box-shadow:0 8px 0px #8C0F2E,0 14px 32px rgba(232,48,90,.55);}
.send-btn:active:not(:disabled){transform:translateY(3px);box-shadow:0 2px 0px #8C0F2E,0 4px 12px rgba(232,48,90,.35);}
.send-btn:disabled{opacity:.55;cursor:not-allowed;}

.dots{display:inline-flex;gap:6px;padding:18px;justify-content:center;width:100%;position:relative;z-index:1;}
.dots i{display:block;width:7px;height:7px;border-radius:50%;background:white;font-style:normal;animation:dot .9s ease-in-out infinite;}
.dots i:nth-child(2){animation-delay:.15s}.dots i:nth-child(3){animation-delay:.3s}
@keyframes dot{0%,100%{transform:translateY(0);opacity:1}50%{transform:translateY(-7px);opacity:.4}}

.sep{display:flex;align-items:center;gap:14px;margin:20px 0 16px;font-size:11px;font-weight:700;color:#E5B0BF;letter-spacing:.1em;text-transform:uppercase;}
.sep::before,.sep::after{content:'';flex:1;height:1.5px;background:#FFE0EC;}
.login-txt{text-align:center;font-size:13.5px;color:var(--ink3);}
.login-txt a{color:var(--r1);font-weight:700;text-decoration:none;transition:color .2s;}
.login-txt a:hover{color:var(--r2);}

/* Succès */
.success{text-align:center;display:flex;flex-direction:column;align-items:center;padding:8px 0;}
.success-rings{position:relative;width:100px;height:100px;display:flex;align-items:center;justify-content:center;margin-bottom:26px;}
.sr{position:absolute;border-radius:50%;border:2px solid rgba(232,48,90,.2);animation:rpulse 2s ease-out infinite;}
.sr1{width:100px;height:100px;animation-delay:0s}.sr2{width:76px;height:76px;animation-delay:.2s}.sr3{width:52px;height:52px;animation-delay:.4s}
@keyframes rpulse{0%{transform:scale(.7);opacity:0}55%{opacity:1}100%{transform:scale(1.15);opacity:0}}
.success-check{width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,var(--r3),var(--r1));display:grid;place-items:center;box-shadow:0 8px 28px rgba(232,48,90,.45);z-index:1;animation:pop .5s cubic-bezier(.22,.68,0,1.4) both;}
@keyframes pop{from{transform:scale(.3);opacity:0}to{transform:scale(1);opacity:1}}
.success-title{font-family:var(--fh);font-size:24px;font-weight:800;color:var(--ink);letter-spacing:-.03em;margin-bottom:12px;}
.success-sub{font-size:14px;line-height:1.7;color:var(--ink3);margin-bottom:28px;}

.fade-enter-active,.fade-leave-active{transition:all .3s ease;}
.fade-enter-from{opacity:0;transform:translateY(14px)}
.fade-leave-to{opacity:0;transform:translateY(-14px)}
.shake-enter-active{animation:shake .4s ease;}
@keyframes shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-7px)}40%{transform:translateX(7px)}60%{transform:translateX(-4px)}80%{transform:translateX(4px)}}

@media(max-width:900px){
  .layout{grid-template-columns:1fr;min-height:auto}
  .hero{padding:36px 28px 28px;min-height:auto}
  .hero-h1{font-size:40px}
  .hero-p,.tips{display:none}
  .panel{padding:28px 20px 48px}
}
@media(max-width:480px){
  .card{padding:30px 20px;border-radius:20px}
  .card-title{font-size:22px}
  .send-btn span{font-size:14px}
}
</style>