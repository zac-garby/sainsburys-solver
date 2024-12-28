import "./assets/main.css";

import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";

import Home from "./views/Home.vue";
import TaxonomyDetail from "./views/TaxonomyDetail.vue";
import ProductDetail from "./views/ProductDetail.vue";
import Scratchpad from "./views/Scratchpad.vue";
import App from "./App.vue";

const routes = [
    {
        path: "/",
        name: "Home",
        component: Home
    },
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
    {
        path: "/scratch/:id",
        name: "Scratchpad",
        component: Scratchpad,
    },
    {
        path: "/lucky",
        name: "Lucky",
        beforeEnter: async (to, from, next) => {
            await fetch("http://localhost:8000/product/lucky")
                .then((res) => res.json())
                .then((id) => next(`/product/${id}`))
                .catch((err) => {
                    console.error(err)
                    next(false)
                })
        }
    }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

createApp(App).use(router).mount("#app");
