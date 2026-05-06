<script setup lang="ts">
const router = useRouter()
</script>

<template>
  <nav class="app-nav">
    <div class="app-nav__inner">
      <div class="app-nav__logo" @click="router.push('/')">
        <div class="app-nav__mark">E</div>
        <div>
          <span class="app-nav__name">EventLab</span>
          <span class="app-nav__sub">Billetterie & Événements</span>
        </div>
      </div>
      <div class="app-nav__actions">
        <button class="app-nav__ghost" @click="router.push('/login')">Connexion</button>
        <button class="app-nav__primary" @click="router.push('/register')">S'inscrire</button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=Outfit:wght@400;500;600;700&display=swap');
.app-nav { position: fixed; top: 0; left: 0; right: 0; z-index: 999; background: rgba(255,255,255,.96); backdrop-filter: blur(20px); box-shadow: 0 1px 0 rgba(233,30,140,.1); font-family: 'Outfit', sans-serif; }
.app-nav__inner { max-width: 1280px; margin: 0 auto; height: 72px; display: flex; align-items: center; justify-content: space-between; padding: 0 40px; }
.app-nav__logo { display: flex; align-items: center; gap: 12px; cursor: pointer; }
.app-nav__mark { width: 38px; height: 38px; border-radius: 11px; background: linear-gradient(135deg, #E91E8C, #AD1457); display: flex; align-items: center; justify-content: center; color: #fff; font-family: 'Playfair Display', serif; font-weight: 700; font-size: 18px; flex-shrink: 0; box-shadow: 0 4px 14px rgba(233,30,140,.35); }
.app-nav__name { display: block; font-family: 'Playfair Display', serif; font-weight: 800; font-size: 20px; color: #880E4F; line-height: 1; }
.app-nav__sub { display: block; font-size: 10px; color: #9e6878; letter-spacing: 1.5px; text-transform: uppercase; margin-top: 2px; }
.app-nav__actions { display: flex; gap: 10px; }
.app-nav__ghost { background: transparent; border: 1.5px solid #F8BBD0; color: #E91E8C; padding: 9px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; font-family: 'Outfit', sans-serif; transition: all .2s; }
.app-nav__ghost:hover { background: #FFF5F7; }
.app-nav__primary { background: linear-gradient(135deg, #E91E8C, #AD1457); border: none; color: #fff; padding: 9px 20px; border-radius: 10px; font-size: 14px; font-weight: 600; cursor: pointer; font-family: 'Outfit', sans-serif; box-shadow: 0 4px 16px rgba(233,30,140,.35); transition: all .2s; }
.app-nav__primary:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(233,30,140,.45); }
@media (max-width: 768px) { .app-nav__inner { padding: 0 20px; } .app-nav__ghost { display: none; } }
</style>