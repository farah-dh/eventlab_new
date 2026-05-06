<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ─── User Data ───
const user = ref<any>({})

onMounted(() => {
  try {
    const stored = localStorage.getItem('user')
    if (stored) {
      user.value = JSON.parse(stored)
    }
  } catch {
    user.value = {}
  }
})

const userName = computed(() => {
  if (user.value.full_name) return user.value.full_name
  if (user.value.firstname || user.value.lastname) return `${user.value.firstname || ''} ${user.value.lastname || ''}`.trim()
  return user.value.username || user.value.email || 'Utilisateur'
})

const userEmail = computed(() => user.value.email || '')

const userInitials = computed(() => {
  const name = userName.value
  const parts = name.split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name[0]?.toUpperCase() || 'U'
})

const userRole = computed(() => {
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.is_staff) return 'Administrateur'
    }
  } catch {}
  return 'Utilisateur'
})

const userImage = computed(() => user.value.profile_image || null)

// ─── Logout ───
const logout = () => {
  localStorage.clear()
  router.push('/login')
}
</script>

<template>
  <VBadge
    dot
    location="bottom right"
    offset-x="3"
    offset-y="3"
    bordered
    color="success"
  >
    <VAvatar
      class="cursor-pointer"
      color="primary"
      variant="tonal"
    >
      <VImg v-if="userImage" :src="userImage" />
      <span v-else class="text-body-1 font-weight-medium">{{ userInitials }}</span>

      <!-- SECTION Menu -->
      <VMenu
        activator="parent"
        width="230"
        location="bottom end"
        offset="14px"
      >
        <VList>
          <!-- 👉 User Avatar & Name -->
          <VListItem>
            <template #prepend>
              <VListItemAction start>
                <VBadge
                  dot
                  location="bottom right"
                  offset-x="3"
                  offset-y="3"
                  color="success"
                >
                  <VAvatar
                    color="primary"
                    variant="tonal"
                  >
                    <VImg v-if="userImage" :src="userImage" />
                    <span v-else class="text-body-1 font-weight-medium">{{ userInitials }}</span>
                  </VAvatar>
                </VBadge>
              </VListItemAction>
            </template>

            <VListItemTitle class="font-weight-semibold">
              {{ userName }}
            </VListItemTitle>
            <VListItemSubtitle>{{ userRole }}</VListItemSubtitle>
          </VListItem>

          <VDivider class="my-2" />

          <!-- 👉 Profile -->
          <VListItem link to="/admin/profile">
            <template #prepend>
              <VIcon class="me-2" icon="tabler-user" size="22" />
            </template>
            <VListItemTitle>Profil</VListItemTitle>
          </VListItem>

          <!-- 👉 Settings -->
          <VListItem link to="/admin/settings">
            <template #prepend>
              <VIcon class="me-2" icon="tabler-settings" size="22" />
            </template>
            <VListItemTitle>Paramètres</VListItemTitle>
          </VListItem>

          <!-- Divider -->
          <VDivider class="my-2" />

          <!-- 👉 Logout -->
          <VListItem @click="logout">
            <template #prepend>
              <VIcon class="me-2" icon="tabler-logout" size="22" />
            </template>
            <VListItemTitle>Déconnexion</VListItemTitle>
          </VListItem>
        </VList>
      </VMenu>
      <!-- !SECTION -->
    </VAvatar>
  </VBadge>
</template>