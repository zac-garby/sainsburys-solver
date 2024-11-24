<script setup>
const props = defineProps(['nutr', 'weight'])

const nutrKeys = [
    "energy",
    "protein",
    "fat",
    "sat_fat",
    "cholesterol",
    "carbohydrate",
    "total_sugar",
    "starch",
    "fibre",
    "sodium",
    "potassium",
    "calcium",
    "magnesium",
    "chromium",
    "molybdenum",
    "phosphorus",
    "iron",
    "copper",
    "zinc",
    "manganese",
    "selenium",
    "iodine",
    "vit_a",
    "vit_c",
    "vit_d",
    "vit_e",
    "vit_k",
    "vit_b1",
    "vit_b2",
    "vit_b3",
    "vit_b5",
    "vit_b6",
    "vit_b7",
    "vit_b9",
    "vit_b12",
]

function showG(key, val) {
    if (key == "energy") {
        // special case for kcal
        return `${val}kcal`
    }

    let disp;
    if (val <= 5e-4) {
        disp = `${(val * 1e6).toFixed(2)}µg`;
    } else if (val <= 0.5) {
        disp = `${(val * 1e3).toFixed(2)}mg`;
    } else if (val <= 500) {
        disp = `${val.toFixed(2)}g`;
    } else {
        disp = `${(val / 1e3).toFixed(2)}kg`;
    }

    return disp;
}
</script>

<template>
<table class="nutrition">
    <thead>
        <tr>
            <td>nutrient</td>
            <td>amount/{{ weight }}</td>
        </tr>
    </thead>
    <template v-for="k in nutrKeys" :key="k">
        <tr v-if="nutr[k]">
            <td>{{ k }}</td>
            <td>{{ showG(k, nutr[k]) }}</td>
        </tr>
    </template>
    <template v-if="$slots.default">
        <slot></slot>
    </template>
</table>
</template>
