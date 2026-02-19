<template>
  <v-app class="bg-background">
    <v-navigation-drawer
        v-model="drawer"
        :location="$vuetify.display.mobile ? 'bottom' : undefined"
        :permanent="!$vuetify.display.mobile"
        :rail="!$vuetify.display.mobile && rail"
        :temporary="$vuetify.display.mobile"
        color="primary"
        expand-on-hover
        @mouseenter="rail = false"
        @mouseleave="rail = true"
    >
      <v-list density="compact" nav>
        <v-list-item
            class="mb-4"
            prepend-icon="mdi-api"
            subtitle="v1.0.0"
            title="Gensokyo API"
        ></v-list-item>
        <v-divider class="mb-2 opacity-20"></v-divider>

        <v-list-item
            v-for="item in menuItems"
            :key="item.path"
            :prepend-icon="item.meta.icon"
            :title="item.meta.title"
            :to="item.path"
            active-class="bg-surface text-primary"
            rounded="xl"
        ></v-list-item>
      </v-list>

      <template v-slot:append>
        <v-list-item
            class="mb-2"
            href="#"
            prepend-icon="mdi-github"
            rounded="xl"
            target="_blank"
            title="Project Repo"
        ></v-list-item>
      </template>
    </v-navigation-drawer>

    <v-app-bar class="px-2 border-b" color="background" flat>
      <v-app-bar-nav-icon v-if="$vuetify.display.mobile" @click="drawer = !drawer"></v-app-bar-nav-icon>

      <v-app-bar-title class="text-h6 font-weight-bold text-primary pl-2">
        {{ currentRouteName }}
      </v-app-bar-title>

      <v-spacer></v-spacer>

    </v-app-bar>

    <v-main>
      <v-container class="pa-4 pa-md-6" fluid style="max-width: 1600px;">
        <router-view v-slot="{ Component }">
          <v-fade-transition mode="out-in">
            <component :is="Component"/>
          </v-fade-transition>
        </router-view>
      </v-container>
    </v-main>

    <v-snackbar
        v-model="snackbar.show"
        :color="snackbar.color"
        elevation="4"
        location="top center"
        rounded="pill"
        timeout="3000"
    >
      <div class="d-flex align-center justify-center">
        <v-icon :icon="snackbar.color === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle'" class="mr-2"></v-icon>
        <span class="font-weight-medium">{{ snackbar.text }}</span>
      </div>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import {computed, provide, reactive, ref} from 'vue'
import {useDisplay} from 'vuetify'
import {useRouter} from 'vue-router'

const {mobile} = useDisplay()
const router = useRouter()

const drawer = ref(!mobile.value)
const rail = ref(true)
const snackbar = reactive({show: false, text: '', color: 'success'})

const menuItems = computed(() => {
  return router.options.routes.filter(r => r.meta && !r.redirect)
})

const currentRouteName = computed(() => {
  return router.currentRoute.value.meta.title || 'Dashboard'
})

const showMsg = (text, color = 'success') => {
  snackbar.text = text
  snackbar.color = color
  snackbar.show = true
}
provide('showMsg', showMsg)
</script>

<style>
html {
  overflow-y: auto;
}
</style>