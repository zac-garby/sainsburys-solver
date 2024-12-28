<script setup>
import { useFetch } from "../composable/fetch.js";
import { useRoute } from "vue-router";

const route = useRoute();

const {
    loading: loading,
    data: data,
    error: error,
} = useFetch(() => `http://localhost:8000/scratch/${route.params.id}`);
</script>

<template>
    <div v-if="loading">Loading...</div>
    <div v-else-if="error">{{ error }}</div>
    <template v-else>
        <h2>{{ data["name"] }}</h2>
        <table>
            <thead>
                <tr>
                    <td>Product</td>
                    <td>Amount</td>
                    <td>Cost</td>
                </tr>
            </thead>
            <tbody>
                <tr v-for="item in data['items']">
                    <td>
                        <a :href="`/product/${item['product']['id']}`">
                            {{ item["product"]["name"] }}
                        </a>
                    </td>
                    <td>
                        {{ item["num_units"] * item["product"]["unit_amount"] }}
                        {{ item["product"]["unit_measure"] }}
                    </td>
                    <td>
                        £{{ (item["num_units"] * item["product"]["unit_price"]).toFixed(2) }}
                    </td>
                </tr>
            </tbody>
        </table>
    </template>
</template>
