<script setup>
import { useRoute } from "vue-router";
import { useFetch } from "../composable/fetch.js";

import TaxonomySublist from "../components/TaxonomySublist.vue";
import NutritionTable from "../components/NutritionTable.vue";

const route = useRoute();

const {
    loading,
    data: product,
    error: error,
} = useFetch(() => `http://localhost:8000/product/${route.params.id}`);
</script>

<template>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <template v-else>
        <img :src="product['image_url']" />
        <h2>{{ product["name"] }}</h2>
        <p>
            <b>£{{ product["unit_price"].toFixed(2) }}</b> per
            {{ product["unit_amount"] }} {{ product["unit_measure"] }}
            (£{{ product["retail_price"].toFixed(2) }} retail)
        </p>
        <p>{{ product["description"] }} <a :href="product['url']">[View on Sainsbury's]</a></p>
        <h2>Nutrition Information</h2>
        <NutritionTable
            :nutr="product['total_nutrition']"
            :weight="`${product['unit_amount']} ${product['unit_measure']}`" />
        <p>
            Total nutrition information collated from Sainsbury's website,
            and by matching against several nutrient databases for micronutrients.
            Data from Sainsbury's is prioritised.
        </p>
        <p>
            Below is a listing of all of the data sources from which the above is
            derived.
        </p>

        <h2>All Nutrition Sources</h2>
        <div v-for="nutr in product['nutritions']">
            <NutritionTable
                :nutr="nutr['nutrition']"
                :weight="`${nutr['amount']} ${nutr['measure']}`">
                <tr>
                    <td colspan="2" class="source">source: {{ nutr["source"] }}</td>
                </tr>
                <tr>
                    <td colspan="2" class="source">sureness: {{ nutr["sureness"] }}</td>
                </tr>
            </NutritionTable>
        </div>
    </template>
</template>

<style>
table.nutrition {
    border-spacing: 0;
    margin-bottom: 20px;
}

table.nutrition thead {
    font-weight: bold;
    background-color: rgb(130, 30, 80);
    color: white;
}

table.nutrition td {
    padding-left: 5px;
    padding-right: 25px;
}

table.nutrition td:last-child {
    padding-right: 5px;
}

table.nutrition td.source {
    color: grey;
    font-style: italic;
}
</style>
