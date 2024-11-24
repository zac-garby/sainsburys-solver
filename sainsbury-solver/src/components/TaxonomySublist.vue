<script setup>
import { ref, computed } from "vue";

const props = defineProps(["taxonomy"]);
const collapsed = ref(true);
const hasChildren = props.taxonomy["children"].length > 0;
const detailLink = computed(() => `/taxonomy/${props.taxonomy["id"]}`)

function toggle() {
    collapsed.value = !collapsed.value;
}
</script>

<template>
    <span>
        <router-link :to="detailLink">{{ props.taxonomy["name"] }}</router-link>
        <button class="toggle" @click="toggle" v-if="hasChildren">[{{ collapsed ? "+" : "-" }}]</button>
    </span>
    <ul v-if="hasChildren && !collapsed">
        <li v-for="child in props.taxonomy['children']">
            <TaxonomySublist :taxonomy="child" />
        </li>
    </ul>
</template>

<style>
ul {
    padding-left: 20px;
    margin: 0;
}

button.toggle {
    cursor: pointer;
    background: none;
    border: none;
    padding: 0;
    margin-left: 5px;
}
</style>
