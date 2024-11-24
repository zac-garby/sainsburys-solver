import { ref, onMounted, watchEffect, toValue } from "vue";

export function useFetch(url) {
    const loading = ref(true);
    const data = ref(null);
    const error = ref(null);

    function fetchData() {
        loading.value = true;
        data.value = null;
        error.value = null;

        fetch(toValue(url))
            .then((res) => res.json())
            .then((json) => {
                data.value = json;
                loading.value = false;
            })
            .catch((err) => {
                error.value = err;
                loading.value = false;
            })
            .finally(() => (loading.value = false));
    }

    onMounted(() => watchEffect(() => fetchData()));

    return { loading, data, error };
}
