import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { pinia } from "./stores";
import { useAuthStore } from "./stores/auth";
import "./styles/app.css";


const app = createApp(App);

app.use(pinia);
app.use(router);

const authStore = useAuthStore();
authStore.restoreSession();
void authStore.ensureUser();

router.isReady().then(() => {
  app.mount("#app");
});

