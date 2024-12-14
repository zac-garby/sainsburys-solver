<template>
    <header>
        <h1>
            <router-link to="/">Sainsbury's Solver</router-link>
        </h1>
        <nav>
            <router-link to="/">Home</router-link>
            <router-link to="/calc">Calculator</router-link>
            <router-link to="/recipes">Recipes</router-link>
            <router-link to="/lucky">I'm Feeling Lucky</router-link>
        </nav>
    </header>

    <main>
        <router-view />
    </main>
</template>

<style scoped>
nav {
    display: block;
    margin-bottom: 15px;
}

nav a {
    margin-right: 5px;
    padding-inline: 3px;
    background-color: rgba(130, 30, 80, 0.1);
}
</style>
