import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { pinia } from './stores';
import { useAuthStore } from './stores/auth';
import './styles/tokens.css';
import './styles/base.css';

const app = createApp(App);

app.use(pinia);
app.use(router);

async function bootstrap() {
  const authStore = useAuthStore(pinia);
  try {
    await authStore.bootstrap();
  } catch (error) {
    console.error('Frontend bootstrap failed:', error);
  } finally {
    app.mount('#app');
  }
}

bootstrap();
