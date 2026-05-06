import { createApp } from 'vue'

import App from '@/App.vue'
import { registerPlugins } from '@core/utils/plugins'

// ApexCharts
import VueApexCharts from 'vue3-apexcharts'

// Styles
import '@core/scss/template/index.scss'
import '@styles/styles.scss'

// Create vue app
const app = createApp(App)

// Register plugins
registerPlugins(app)

// ApexCharts
app.use(VueApexCharts as any)

// Mount vue app
app.mount('#app')