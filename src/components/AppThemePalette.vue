<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const themes = [
  { id: 'rose',    label: 'Rose',    p: '#D4215A', pl: '#FF4D7A', pd: '#9B1040', pale: '#FFF0F3', pmuted: '#FCE4EC', rgb: '212,33,90',  drgb: '155,16,64'  },
  { id: 'violet',  label: 'Violet',  p: '#7C3AED', pl: '#9F67FA', pd: '#5B21B6', pale: '#F5F3FF', pmuted: '#EDE9FE', rgb: '124,58,237', drgb: '91,33,182'  },
  { id: 'ocean',   label: 'Océan',   p: '#0369A1', pl: '#0EA5E9', pd: '#075985', pale: '#F0F9FF', pmuted: '#E0F2FE', rgb: '3,105,161',  drgb: '7,89,133'   },
  { id: 'emerald', label: 'Nature',  p: '#059669', pl: '#10B981', pd: '#047857', pale: '#ECFDF5', pmuted: '#D1FAE5', rgb: '5,150,105',  drgb: '4,120,87'   },
  { id: 'sunset',  label: 'Sunset',  p: '#EA580C', pl: '#F97316', pd: '#C2410C', pale: '#FFF7ED', pmuted: '#FFEDD5', rgb: '234,88,12',  drgb: '194,65,12'  },
  { id: 'gold',    label: 'Gold',    p: '#D97706', pl: '#F59E0B', pd: '#B45309', pale: '#FFFBEB', pmuted: '#FEF3C7', rgb: '217,119,6',  drgb: '180,83,9'   },
]

const isDark       = ref(false)
const showPalette  = ref(false)
const currentTheme = ref(themes[0])

// Applique thème + dark sur <html> → global pour toutes les pages
const applyToDOM = () => {
  const root = document.documentElement
  const t = currentTheme.value
  root.style.setProperty('--accent',      t.p)
  root.style.setProperty('--accent-lt',   t.pl)
  root.style.setProperty('--accent-dk',   t.pd)
  root.style.setProperty('--accent-pale', t.pale)
  root.style.setProperty('--accent-mute', t.pmuted)
  root.style.setProperty('--accent-rgb',  t.rgb)
  root.style.setProperty('--accent-drg',  t.drgb)
  isDark.value ? root.classList.add('dark') : root.classList.remove('dark')
}

const setTheme = (t: typeof themes[0]) => {
  currentTheme.value = t
  localStorage.setItem('el-theme', t.id)
  applyToDOM()
}

const toggleDark = () => {
  isDark.value = !isDark.value
  localStorage.setItem('el-dark', isDark.value ? '1' : '0')
  applyToDOM()
}

const onClickOutside = (e: MouseEvent) => {
  const el = document.querySelector('.atp-wrap')
  if (el && !el.contains(e.target as Node)) showPalette.value = false
}

onMounted(() => {
  isDark.value = localStorage.getItem('el-dark') === '1'
  const saved = localStorage.getItem('el-theme')
  if (saved) { const t = themes.find(x => x.id === saved); if (t) currentTheme.value = t }
  applyToDOM()
  document.addEventListener('click', onClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>

<template>
  <div class="atp-wrap">
    <!-- Panel -->
    <transition name="atp-panel">
      <div v-if="showPalette" class="atp-panel">

        <!-- Thèmes couleur -->
        <div class="atp-section">
          <div class="atp-label">🎨 Couleur du thème</div>
          <div class="atp-swatches">
            <button
              v-for="t in themes"
              :key="t.id"
              class="atp-swatch"
              :class="{ active: currentTheme.id === t.id }"
              :style="{ '--sw': t.p, '--sw2': t.pd }"
              :title="t.label"
              @click="setTheme(t)"
            >
              <span v-if="currentTheme.id === t.id">✓</span>
            </button>
          </div>
          <div class="atp-names">
            <span
              v-for="t in themes"
              :key="t.id"
              :class="{ active: currentTheme.id === t.id }"
            >{{ t.label }}</span>
          </div>
        </div>

        <div class="atp-sep"></div>

        <!-- Mode sombre/clair -->
        <div class="atp-section">
          <div class="atp-label">💡 Mode d'affichage</div>
          <div class="atp-mode" @click="toggleDark">
            <div class="atp-mode-opt" :class="{ active: !isDark }">
              <span>☀️</span> Clair
            </div>
            <div class="atp-mode-opt" :class="{ active: isDark }">
              <span>🌙</span> Sombre
            </div>
          </div>
        </div>

      </div>
    </transition>

    <!-- Bouton FAB -->
    <button
      class="atp-fab"
      @click.stop="showPalette = !showPalette"
      :title="showPalette ? 'Fermer' : 'Personnaliser le thème'"
    >
      <transition name="atp-icon" mode="out-in">
        <svg v-if="showPalette" key="x" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
        <svg v-else key="pal" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10c0 1.657-1.343 3-3 3h-1.5A1.5 1.5 0 0 0 16 16.5V16a4 4 0 1 0-4 4"/>
          <circle cx="7.5" cy="10.5" r="1" fill="currentColor"/>
          <circle cx="12" cy="7.5" r="1" fill="currentColor"/>
          <circle cx="16.5" cy="10.5" r="1" fill="currentColor"/>
        </svg>
      </transition>
    </button>
  </div>
</template>

<style scoped>
/* Wrapper fixe en bas à droite */
.atp-wrap {
  position: fixed;
  bottom: 32px;
  right: 28px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 14px;
}

/* Bouton principal */
.atp-fab {
  width: 54px;
  height: 54px;
  border-radius: 17px;
  background: linear-gradient(135deg, var(--accent-lt, #FF4D7A), var(--accent, #D4215A));
  border: none;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 32px rgba(var(--accent-rgb, 212,33,90), .45);
  transition: all .25s;
  flex-shrink: 0;
}
.atp-fab:hover {
  transform: scale(1.1) rotate(12deg);
  box-shadow: 0 12px 40px rgba(var(--accent-rgb, 212,33,90), .6);
}

/* Panel */
.atp-panel {
  background: var(--card, #fff);
  border: 1.5px solid var(--border, #F0DCE4);
  border-radius: 24px;
  padding: 22px 24px;
  width: 248px;
  box-shadow: 0 28px 64px rgba(0,0,0,.18);
  backdrop-filter: blur(20px);
}

.atp-section { }
.atp-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--muted, #7A5060);
  margin-bottom: 14px;
  font-family: 'Jost', system-ui, sans-serif;
}
.atp-sep {
  height: 1px;
  background: var(--border, #F0DCE4);
  margin: 18px 0;
}

/* Swatches */
.atp-swatches {
  display: flex;
  gap: 10px;
  justify-content: space-between;
  margin-bottom: 8px;
}
.atp-swatch {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--sw), var(--sw2));
  border: 2.5px solid transparent;
  cursor: pointer;
  transition: all .2s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #fff;
  font-weight: 900;
  outline: none;
}
.atp-swatch:hover { transform: scale(1.15); }
.atp-swatch.active {
  border-color: var(--bg, #fff);
  box-shadow: 0 0 0 3px var(--sw);
  transform: scale(1.18);
}

.atp-names {
  display: flex;
  justify-content: space-between;
}
.atp-names span {
  font-size: 9px;
  color: var(--muted, #7A5060);
  text-align: center;
  flex: 1;
  transition: color .2s;
  font-family: 'Jost', system-ui, sans-serif;
}
.atp-names span.active {
  color: var(--accent, #D4215A);
  font-weight: 700;
}

/* Mode toggle */
.atp-mode {
  display: flex;
  background: var(--bg-alt, #FDF8F5);
  border-radius: 12px;
  padding: 4px;
  border: 1.5px solid var(--border, #F0DCE4);
  cursor: pointer;
  transition: border-color .2s;
}
.atp-mode:hover { border-color: var(--accent, #D4215A); }
.atp-mode-opt {
  flex: 1;
  padding: 9px 4px;
  border-radius: 9px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  color: var(--muted, #7A5060);
  transition: all .25s;
  font-family: 'Jost', system-ui, sans-serif;
}
.atp-mode-opt.active {
  background: var(--card, #fff);
  color: var(--accent, #D4215A);
  box-shadow: 0 2px 10px rgba(var(--accent-rgb, 212,33,90), .18);
}

/* Animations */
.atp-panel-enter-active { animation: panIn .3s cubic-bezier(.34,1.56,.64,1); }
.atp-panel-leave-active { animation: panOut .2s ease; }
@keyframes panIn  { from { opacity:0; transform:translateY(12px) scale(.95) } to { opacity:1; transform:none } }
@keyframes panOut { from { opacity:1 } to { opacity:0; transform:translateY(8px) scale(.96) } }

.atp-icon-enter-active, .atp-icon-leave-active { transition: all .2s; }
.atp-icon-enter-from { opacity:0; transform: rotate(-90deg) scale(.5); }
.atp-icon-leave-to   { opacity:0; transform: rotate(90deg) scale(.5); }

@media (max-width: 768px) {
  .atp-wrap { bottom: 20px; right: 16px; }
}
</style>