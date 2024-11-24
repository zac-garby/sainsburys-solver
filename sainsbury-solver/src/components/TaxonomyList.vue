<script setup>
import { useFetch } from "../composable/fetch.js"
import TaxonomySublist from "./TaxonomySublist.vue"

const { loading, data: taxonomy, error } = useFetch("http://localhost:8000/taxonomy")
</script>

<template>
<div v-if="loading">Loading...</div>
<div v-else-if="error">{{ error }}</div>
<ul v-else-if="taxonomy">
    <li v-for="child in taxonomy['children']">
        <TaxonomySublist :taxonomy="child" />
    </li>
</ul>
</template>
