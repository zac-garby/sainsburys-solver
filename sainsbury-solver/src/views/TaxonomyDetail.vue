<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";
import { useFetch } from "../composable/fetch.js";

import TaxonomySublist from "../components/TaxonomySublist.vue";

const route = useRoute();

const {
    loading: taxonLoading,
    data: taxon,
    error: taxonError,
} = useFetch(() => `http://localhost:8000/taxonomy/${route.params.id}`);

const {
    loading: itemsLoading,
    data: items,
    error: itemsError,
} = useFetch(
    () =>
        `http://localhost:8000/product/search?taxon=${route.params.id}&limit=80`,
);
</script>

<template>
    <div v-if="itemsLoading || taxonLoading">Loading...</div>
    <div v-else-if="taxonError">{{ taxonError }}</div>
    <div v-else-if="itemsError">{{ itemsError }}</div>
    <template v-else>
        <template v-if="taxon['parent_id'] !== null">
            <router-link :to="`/taxonomy/${taxon['parent_id']}`">
                &uarr; Up to {{ taxon["parent_name"] }}
            </router-link>
            <br />
        </template>
        <TaxonomySublist :taxonomy="taxon" />
        <ul class="item-gallery">
            <li v-for="item in items">
                <router-link :to="`/product/${item['id']}`">
                    <img :src="item['image_url']" />
                </router-link>
            </li>
        </ul>
    </template>
</template>

<style>
ul.item-gallery {
    margin-top: 20px;
    list-style: none;
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    gap: 10px;
    width: 100%;
    padding: 0;
}
</style>
