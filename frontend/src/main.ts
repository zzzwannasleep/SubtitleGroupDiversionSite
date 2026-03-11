import { createApp } from "vue";

import App from "./App.vue";
import { router } from "./router";
import { pinia } from "./stores";
import { useAuthStore } from "./stores/auth";
import { useSiteStore } from "./stores/site";
import "./styles/app.css";


const app = createApp(App);

app.use(pinia);
app.use(router);

const authStore = useAuthStore();
const siteStore = useSiteStore();

authStore.restoreSession();
void siteStore.loadSiteSettings();
void authStore.ensureUser();

router.isReady().then(() => {
  app.mount("#app");
});
