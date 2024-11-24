import "./assets/main.css";

import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";

import Home from "./views/Home.vue";
import TaxonomyDetail from "./views/TaxonomyDetail.vue";
import ProductDetail from "./views/ProductDetail.vue";
import App from "./App.vue";

const routes = [
    { path: "/", name: "Home", component: Home },
    {
        path: "/taxonomy/:id",
        name: "TaxonomyDetail",
        component: TaxonomyDetail,
    },
    {
        path: "/product/:id",
        name: "ProductDetail",
        component: ProductDetail,
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

createApp(App).use(router).mount("#app");
