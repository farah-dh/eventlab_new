<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { $fetch } from 'ofetch'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

type Step = 'idle' | 'sending' | 'otp' | 'done'

const enabled  = ref(false)
const step     = ref<Step>('idle')
const loading  = ref(false)
const digits   = ref<string[]>(['', '', '', '', '', ''])
const inputs   = ref<HTMLInputElement[]>([])
const message  = ref('')
const isError  = ref(false)
const resendCd = ref(0)
let cdTimer: ReturnType<typeof setInterval> | null = null

const otp = () => digits.value.join('')

const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

function authHeaders() {
  return { Authorization: `Bearer ${authStore.token}` }
}

onMounted(async () => {
  try {
    const data = await $fetch(`${apiBase}/auth/2fa/status/`, { headers: authHeaders() })
    enabled.value = (data as any).data['2fa_enabled']
  } catch { /* silent */ }
})

function showMsg(msg: string, err = false) {
  message.value = msg
  isError.value = err
}

function startCountdown(sec: number) {
  resendCd.value = sec
  if (cdTimer) clearInterval(cdTimer)
  cdTimer = setInterval(() => {
    resendCd.value--
    if (resendCd.value <= 0 && cdTimer) { clearInterval(cdTimer); cdTimer = null }
  }, 1000)
}

function resetOtp() {
  digits.value = ['', '', '', '', '', '']
  setTimeout(() => inputs.value[0]?.focus(), 50)
}

function onInput(i: number, e: Event) {
  const val = (e.target as HTMLInputElement).value.replace(/\D/g, '')
  if (val.length > 1) {
    val.slice(0, 6).split('').forEach((c, idx) => { if (idx < 6) digits.value[idx] = c })
    inputs.value[Math.min(val.length, 5)]?.focus()
    return
  }
  digits.value[i] = val.slice(-1)
  if (val && i < 5) inputs.value[i + 1]?.focus()
}

function onKeydown(i: number, e: KeyboardEvent) {
  if (e.key === 'Backspace' && !digits.value[i] && i > 0) {
    digits.value[i - 1] = ''
    inputs.value[i - 1]?.focus()
  }
}

async function requestEnable() {
  loading.value = true
  showMsg('')
  try {
    await $fetch(`${apiBase}/auth/2fa/enable/`, {
      method: 'POST', headers: authHeaders(),
    })
    step.value = 'otp'
    showMsg('Code envoyé à votre email. Entrez-le pour activer la 2FA.')
    startCountdown(60)
    setTimeout(() => inputs.value[0]?.focus(), 100)
  } catch (err: any) {
    showMsg(err?.data?.message || 'Erreur lors de l\'envoi du code.', true)
  } finally {
    loading.value = false
  }
}

async function confirmEnable() {
  if (otp().length < 6) { showMsg('Entrez les 6 chiffres.', true); return }
  loading.value = true
  showMsg('')
  try {
    await $fetch(`${apiBase}/auth/2fa/enable/confirm/`, {
      method: 'POST',
      headers: authHeaders(),
      body: { otp: otp() },
    })
    enabled.value = true
    step.value = 'done'
    showMsg('La double authentification est maintenant activée. ✅')
  } catch (err: any) {
    showMsg(err?.data?.message || 'Code invalide. Réessayez.', true)
    resetOtp()
  } finally {
    loading.value = false
  }
}

async function requestDisable() {
  loading.value = true
  showMsg('')
  try {
    await $fetch(`${apiBase}/auth/2fa/disable/`, {
      method: 'POST', headers: authHeaders(),
    })
    step.value = 'otp'
    showMsg('Code envoyé à votre email. Entrez-le pour désactiver la 2FA.')
    startCountdown(60)
    setTimeout(() => inputs.value[0]?.focus(), 100)
  } catch (err: any) {
    showMsg(err?.data?.message || 'Erreur lors de l\'envoi du code.', true)
  } finally {
    loading.value = false
  }
}

async function confirmDisable() {
  if (otp().length < 6) { showMsg('Entrez les 6 chiffres.', true); return }
  loading.value = true
  showMsg('')
  try {
    await $fetch(`${apiBase}/auth/2fa/disable/`, {
      method: 'POST',
      headers: authHeaders(),
      body: { otp: otp() },
    })
    enabled.value = false
    step.value = 'done'
    showMsg('La double authentification a été désactivée.')
  } catch (err: any) {
    showMsg(err?.data?.message || 'Code invalide. Réessayez.', true)
    resetOtp()
  } finally {
    loading.value = false
  }
}

async function resend() {
  if (resendCd.value > 0) return
  const url = enabled.value
    ? `${apiBase}/auth/2fa/disable/`
    : `${apiBase}/auth/2fa/enable/`
  try {
    await $fetch(url, { method: 'POST', headers: authHeaders() })
    startCountdown(60)
    showMsg('Nouveau code envoyé.')
  } catch {
    showMsg('Erreur lors du renvoi.', true)
  }
}

function cancel() {
  step.value = 'idle'
  message.value = ''
  resetOtp()
}
</script>

<template>
  <div class="tfa">
    <div class="tfa-head">
      <div class="tfa-icon" :class="{ on: enabled }">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <polyline v-if="enabled" points="9,12 11,14 15,10"/>
        </svg>
      </div>
      <div class="tfa-info">
        <h3 class="tfa-title">Double authentification</h3>
        <p class="tfa-desc">Protégez votre compte avec un code envoyé par email à chaque connexion.</p>
      </div>
      <div class="tfa-badge" :class="enabled ? 'badge-on' : 'badge-off'">
        {{ enabled ? 'Activée' : 'Désactivée' }}
      </div>
    </div>

    <transition name="msg">
      <div v-if="message" class="msg-box" :class="isError ? 'msg-err' : 'msg-ok'">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <template v-if="isError"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></template>
          <template v-else><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22,4 12,14.01 9,11.01"/></template>
        </svg>
        {{ message }}
      </div>
    </transition>

    <template v-if="step === 'idle' || step === 'done'">
      <div class="tfa-row">
        <div class="tfa-explain">
          <template v-if="!enabled">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            Votre compte n'est pas protégé par la 2FA.
          </template>
          <template v-else>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22,4 12,14.01 9,11.01"/></svg>
            Votre compte est protégé. Un code vous est demandé à chaque connexion.
          </template>
        </div>
        <button
          class="tfa-btn"
          :class="enabled ? 'btn-disable' : 'btn-enable'"
          :disabled="loading"
          @click="enabled ? requestDisable() : requestEnable()"
        >
          <span v-if="!loading">{{ enabled ? 'Désactiver la 2FA' : 'Activer la 2FA' }}</span>
          <span v-else class="dots"><i/><i/><i/></span>
        </button>
      </div>
    </template>

    <template v-if="step === 'otp'">
      <div class="otp-section">
        <p class="otp-hint">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
          Entrez le code à 6 chiffres reçu par email
        </p>
        <div class="otp-wrap">
          <input
            v-for="(_, i) in digits" :key="i"
            :ref="el => { if (el) inputs[i] = el as HTMLInputElement }"
            v-model="digits[i]"
            class="otp-box" :class="{ filled: digits[i] }"
            type="text" inputmode="numeric" maxlength="6"
            autocomplete="one-time-code"
            @input="onInput(i, $event)"
            @keydown="onKeydown(i, $event)"
          />
        </div>
        <div class="otp-actions">
          <button class="tfa-btn btn-enable" :disabled="loading || otp().length < 6"
            @click="enabled ? confirmDisable() : confirmEnable()">
            <span v-if="!loading">Confirmer</span>
            <span v-else class="dots"><i/><i/><i/></span>
          </button>
          <button class="tfa-btn btn-ghost" @click="cancel">Annuler</button>
        </div>
        <div class="resend">
          <span>Pas reçu le code ?</span>
          <button class="resend-btn" :disabled="resendCd > 0" @click="resend">
            <template v-if="resendCd > 0">Renvoyer dans {{ resendCd }}s</template>
            <template v-else>Renvoyer</template>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
:root{--p1:#C8365F;--p2:#A82248;--p3:#7D1235;--font-b:'Plus Jakarta Sans',sans-serif;}
.tfa{background:#fff;border:1.5px solid rgba(200,54,95,.12);border-radius:20px;padding:26px 28px;font-family:var(--font-b);display:flex;flex-direction:column;gap:16px;}
.tfa-head{display:flex;align-items:flex-start;gap:14px;}
.tfa-icon{width:44px;height:44px;border-radius:13px;display:grid;place-items:center;flex-shrink:0;background:rgba(200,54,95,.07);border:1.5px solid rgba(200,54,95,.15);color:#C8365F;transition:all .3s;}
.tfa-icon.on{background:rgba(200,54,95,.12);border-color:rgba(200,54,95,.3);}
.tfa-info{flex:1;}
.tfa-title{font-size:15px;font-weight:700;color:#1A0510;margin-bottom:4px;}
.tfa-desc{font-size:13px;color:#8A5060;line-height:1.5;}
.tfa-badge{padding:5px 12px;border-radius:100px;font-size:11.5px;font-weight:700;white-space:nowrap;flex-shrink:0;}
.badge-on{background:rgba(16,185,129,.1);color:#059669;border:1px solid rgba(16,185,129,.2);}
.badge-off{background:rgba(200,54,95,.07);color:#C8365F;border:1px solid rgba(200,54,95,.15);}
.msg-box{display:flex;align-items:center;gap:8px;padding:11px 14px;border-radius:10px;font-size:13px;}
.msg-ok{background:#f0fdf4;color:#15803d;border:1px solid #bbf7d0;}
.msg-err{background:#fff1f2;color:#be123c;border:1px solid #fecdd3;}
.msg-enter-active,.msg-leave-active{transition:all .3s;}
.msg-enter-from,.msg-leave-to{opacity:0;transform:translateY(-6px);}
.tfa-row{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;}
.tfa-explain{display:flex;align-items:center;gap:7px;font-size:13px;color:#7A4A5A;}
.tfa-btn{padding:11px 22px;border-radius:11px;font-family:var(--font-b);font-size:13.5px;font-weight:700;cursor:pointer;border:none;transition:all .22s;white-space:nowrap;}
.btn-enable{background:#C8365F;color:#fff;box-shadow:0 4px 16px rgba(200,54,95,.3);}
.btn-enable:hover:not(:disabled){background:#A82248;transform:translateY(-1px);}
.btn-disable{background:rgba(200,54,95,.08);color:#C8365F;border:1.5px solid rgba(200,54,95,.2);}
.btn-disable:hover:not(:disabled){background:rgba(200,54,95,.14);}
.btn-ghost{background:rgba(0,0,0,.04);color:#7A4A5A;border:1.5px solid rgba(0,0,0,.08);}
.btn-ghost:hover{background:rgba(0,0,0,.07);}
.tfa-btn:disabled{opacity:.5;cursor:not-allowed;transform:none;}
.otp-section{display:flex;flex-direction:column;gap:14px;}
.otp-hint{display:flex;align-items:center;gap:7px;font-size:13px;color:#7A4A5A;}
.otp-wrap{display:flex;gap:8px;}
.otp-box{width:48px;height:58px;border:1.5px solid rgba(200,54,95,.18);border-radius:12px;background:#FFF8FA;font-size:24px;font-weight:700;color:#1A0510;text-align:center;outline:none;transition:all .2s;font-family:'Cormorant Garamond',serif;}
.otp-box:focus{border-color:#C8365F;background:#fff;box-shadow:0 0 0 3px rgba(200,54,95,.1);transform:translateY(-2px);}
.otp-box.filled{border-color:#A82248;color:#C8365F;}
.otp-actions{display:flex;gap:10px;}
.otp-actions .tfa-btn{flex:1;}
.resend{display:flex;align-items:center;gap:6px;font-size:12.5px;color:#8A5060;}
.resend-btn{background:none;border:none;color:#C8365F;font-family:var(--font-b);font-size:12.5px;font-weight:700;cursor:pointer;padding:0;transition:color .2s;}
.resend-btn:hover:not(:disabled){color:#7D1235;}
.resend-btn:disabled{color:#C8A0B0;cursor:not-allowed;}
.dots{display:inline-flex;gap:4px;}
.dots i{display:block;width:6px;height:6px;border-radius:50%;background:currentColor;animation:db 1s infinite;font-style:normal;}
.dots i:nth-child(2){animation-delay:.15s;}
.dots i:nth-child(3){animation-delay:.3s;}
@keyframes db{0%,100%{transform:translateY(0);opacity:1;}50%{transform:translateY(-5px);opacity:.4;}}
@media(max-width:600px){.tfa{padding:20px;}.otp-box{width:40px;height:50px;font-size:20px;}.tfa-row{flex-direction:column;align-items:flex-start;}.tfa-btn{width:100%;text-align:center;}}
</style>