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
        <button class="toggle" @click="toggle" v-if="hasChildren">
            [{{ collapsed ? "+" : "-" }}]
        </button>
        <span class="spacer" v-else>&nbsp;*&nbsp;</span>
        <router-link :to="detailLink">{{ props.taxonomy["name"] }}</router-link>
    </span>
    <ul v-if="hasChildren && !collapsed">
        <li v-for="child in props.taxonomy['children']">
            <TaxonomySublist :taxonomy="child" />
        </li>
    </ul>
</template>

<style scoped>
ul {
    padding-left: 30px;
    margin: 0;
    list-style: none;
}

button.toggle {
    font-family: monospace;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0;
    margin-right: 5px;
    font-size: 1em;
}

span.spacer {
    margin-right: 5px;
    font-size: 1em;
    font-family: monospace;
}
</style>
