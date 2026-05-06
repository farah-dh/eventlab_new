const getNavItems = () => {
  let isAdmin = false
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]))
      isAdmin = payload.is_staff === true
    }
  } catch {}

  if (isAdmin) {
    return [
      { heading: '🏠 Administration' },
      { title: 'Dashboard', to: { path: '/admin/dashboard' }, icon: { icon: 'tabler-layout-dashboard' } },
      { heading: '👥 Gestion' },
      { title: 'Utilisateurs', icon: { icon: 'tabler-users' }, children: [
        { title: 'Liste', to: { path: '/admin/users' }, icon: { icon: 'tabler-list' } },
        { title: 'Ajouter', to: { path: '/admin/users/add' }, icon: { icon: 'tabler-user-plus' } },
      ]},
      { title: 'Organisateurs', icon: { icon: 'tabler-user-star' }, children: [
        { title: 'Liste', to: { path: '/admin/organizers' }, icon: { icon: 'tabler-list' } },
        { title: 'Ajouter', to: { path: '/admin/organizers/add' }, icon: { icon: 'tabler-user-plus' } },
      ]},
      { heading: '🎪 Événements' },
      { title: 'Événements', icon: { icon: 'tabler-calendar-event' }, children: [
        { title: 'Tous les événements', to: { path: '/admin/events' }, icon: { icon: 'tabler-list' } },
        { title: 'Ajouter', to: { path: '/admin/events/add' }, icon: { icon: 'tabler-calendar-plus' } },
        { title: 'Catégories', to: { path: '/admin/events/categories' }, icon: { icon: 'tabler-tag' } },
        { title: 'Lieux', to: { path: '/admin/events/locations' }, icon: { icon: 'tabler-map-pin' } },
      ]},
      { heading: '💰 Finance' },
      { title: 'Transactions', icon: { icon: 'tabler-credit-card' }, children: [
        { title: 'Toutes les transactions', to: { path: '/admin/transactions' }, icon: { icon: 'tabler-list' } },
        { title: 'Retraits', to: { path: '/admin/transactions/withdrawals' }, icon: { icon: 'tabler-cash' } },
        { title: 'Dépôts', to: { path: '/admin/transactions/deposits' }, icon: { icon: 'tabler-coins' } },
      ]},
      { heading: '⚙️ Système' },
      { title: 'Paramètres', icon: { icon: 'tabler-settings' }, children: [
        { title: 'Général', to: { path: '/admin/settings/general' }, icon: { icon: 'tabler-adjustments' } },
        { title: 'Passerelles paiement', to: { path: '/admin/settings/gateways' }, icon: { icon: 'tabler-credit-card' } },
        { title: 'Notifications', to: { path: '/admin/settings/notifications' }, icon: { icon: 'tabler-bell' } },
        { title: 'Sécurité', to: { path: '/admin/settings/security' }, icon: { icon: 'tabler-shield-lock' } },
        { title: 'Système', to: { path: '/admin/settings/system' }, icon: { icon: 'tabler-server' } },
      ]},
    ]
  }

  return [
    { heading: 'Mon espace' },
    { title: 'Dashboard', to: { path: '/user/dashboard' }, icon: { icon: 'tabler-layout-dashboard' } },
    { title: 'Mes réservations', to: { path: '/user/orders' }, icon: { icon: 'tabler-ticket' } },
    { title: 'Sauvegardés', to: { path: '/user/saved' }, icon: { icon: 'tabler-heart' } },
    { title: 'Notifications', to: { path: '/user/notifications' }, icon: { icon: 'tabler-bell' } },
    { title: 'Support', to: { path: '/user/support' }, icon: { icon: 'tabler-headset' } },
    { heading: 'Compte' },
    { title: 'Mon profil', to: { path: '/user/profile' }, icon: { icon: 'tabler-user' } },
  ]
}

export default getNavItems()
