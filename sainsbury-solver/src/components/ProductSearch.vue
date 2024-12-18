<script setup>
import { ref } from "vue";

function debounce(f, delay) {
    var timer = null

    return function(...args) {
        if (timer === null) {
            f(...args)
            timer = window.setTimeout(() => {}, delay)
        } else {
            window.clearTimeout(timer)
            timer = window.setTimeout(() => f(...args), delay)
        }
    }
}

function search(query) {
    var url = new URL("http://localhost:8000/product/search")
    url.searchParams.append("name", query)

    fetch(url)
        .then((res) => res.json())
        .then((json) => {
            results.value = json
        })
        .catch((err) => {
            console.error(err)
        })
}

var debouncedSearch = debounce(search, 250)

var searchHideTimeout = null

function showSearch() {
    window.clearTimeout(searchHideTimeout)
    isActive.value = true
}

function hideSearch() {
    searchHideTimeout = window.setTimeout(() => {
        isActive.value = false
    }, 100)
}

var query = ref("")
var isActive = ref(false)
var results = ref([])
</script>

<template>
<div class="search-area">
    <input
        type="search"
        placeholder="Search for a product..."
        v-model="query"
        @input="debouncedSearch(query)"
        @focus="showSearch()"
        @blur="hideSearch()" />
    <ul :hidden="!isActive || results.length == 0 || query.trim().length == 0">
        <li v-for="item in results">
            <a :href="`/product/${item['id']}`">{{ item["name"] }}</a>
        </li>
        <li class="see-all">
            <a href="">&rarr; See all results</a>
        </li>
    </ul>
</div>
</template>

<style scoped>
div.search-area {
    position: relative;
}

input {
    display: block;
    width: 100%;
    border: 1px solid grey;
    padding-inline: 5px;
}

ul {
    position: absolute;
    background-color: white;
    border: 1px solid gray;
    border-top: 0;
    width: 100%;
    margin-top: 0;
    padding: 5px;
    list-style: none;
}

li {
    overflow-x: hidden;
    text-wrap: nowrap;
}

li.see-all {
    margin-top: 15px;
}
</style>
