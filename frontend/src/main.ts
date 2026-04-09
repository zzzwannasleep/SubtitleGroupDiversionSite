import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { pinia } from './stores';
import { useAuthStore } from './stores/auth';
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

  try {
    await themeStore.initialize();
    await authStore.bootstrap();
  } catch (error) {
    console.error('Frontend bootstrap failed:', error);
  } finally {
    app.mount('#app');
  }
}

bootstrap();
