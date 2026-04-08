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
  await authStore.bootstrap();
  app.mount('#app');
}

bootstrap();
