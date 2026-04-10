import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { pinia } from './stores';
import { useAuthStore } from './stores/auth';
import { useSiteSettingsStore } from './stores/siteSettings';
import { useThemeStore } from './stores/theme';
import './styles/tokens.css';
import './styles/base.css';
import './styles/theme.css';

const app = createApp(App);

app.use(pinia);
app.use(router);

async function bootstrap() {
  const themeStore = useThemeStore(pinia);
  const authStore = useAuthStore(pinia);
  const siteSettingsStore = useSiteSettingsStore(pinia);

  try {
    await themeStore.initialize();
    siteSettingsStore.initialize();
    await siteSettingsStore.loadPublicSettings();
    await authStore.bootstrap();
  } catch (error) {
    console.error('Frontend bootstrap failed:', error);
  } finally {
    app.mount('#app');
  }
}

bootstrap();
