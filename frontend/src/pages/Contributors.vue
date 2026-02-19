<template>
  <div class="h-100 d-flex flex-column">
    <v-toolbar class="mb-2" color="transparent" density="compact">
      <v-toolbar-title class="text-h6 font-weight-bold">Contributors Config Editor</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn class="mr-2" prepend-icon="mdi-download" variant="tonal" @click="triggerImport">import</v-btn>
      <v-btn color="primary" prepend-icon="mdi-upload" variant="flat" @click="exportJson">export</v-btn>
      <input ref="fileInput" accept=".json" style="display: none" type="file" @change="handleImport"/>
    </v-toolbar>

    <v-row class="flex-grow-1">
      <v-col class="d-flex flex-column" cols="12" lg="4" md="5">
        <v-card class="flex-grow-1 d-flex flex-column" subtitle="Configure role group binding"
                title="Teams List">
          <template v-slot:append>
            <v-btn color="primary" icon="mdi-plus" variant="tonal" @click="addTeam"></v-btn>
          </template>

          <v-card-text class="pa-2 flex-grow-1 overflow-y-auto" style="max-height: calc(100vh - 200px);">
            <v-expansion-panels flat multiple variant="popout">
              <v-expansion-panel v-for="(team, index) in config" :key="index" class="v-card" style="border-width: 1px">
                <v-expansion-panel-title>
                  <v-avatar :color="getTeamColor(team.color)" class="mr-3 text-caption text-white" size="24">
                    {{ team.name ? team.name.charAt(0) : '#' }}
                  </v-avatar>
                  <div class="text-truncate">{{ team.name || 'Unnamed Group' }}</div>
                </v-expansion-panel-title>

                <v-expansion-panel-text>
                  <v-autocomplete
                      v-model="team.role_ids"
                      :items="discordRoles"
                      chips
                      class="mb-1"
                      closable-chips
                      density="compact"
                      item-title="name"
                      item-value="id"
                      label="Bind Discord Role Group"
                      multiple
                      variant="outlined"
                      @update:model-value="(val) => onRolesChange(val, index)"
                  >
                    <template v-slot:item="{ props, item }">
                      <v-list-item :title="item.raw.name" v-bind="props">
                        <template v-slot:prepend>
                          <v-avatar :color="item.raw.color_hex" class="mr-2" size="12"></v-avatar>
                        </template>
                      </v-list-item>
                    </template>
                  </v-autocomplete>

                  <v-text-field
                      v-model="team.name"
                      class="mb-3"
                      density="compact"
                      hide-details="auto"
                      label="Display group name"
                      variant="outlined"
                  ></v-text-field>

                  <div class="d-flex align-center mb-3">
                    <v-text-field
                        v-model="team.color"
                        class="flex-grow-1 mr-2"
                        density="compact"
                        hide-details
                        label="Color (Hex, support gradient hex arrays)"
                        variant="outlined"
                    >
                      <template v-slot:prepend-inner>
                        <div :style="{background: getCssGradient(team.color), width: '16px', height: '16px'}"
                             class="rounded-circle border"></div>
                      </template>
                    </v-text-field>

                    <v-menu>
                      <template v-slot:activator="{ props }">
                        <v-btn color="secondary" icon="mdi-eyedropper" size="small" v-bind="props" variant="text">
                          <v-tooltip activator="parent" location="top">Extract the color from the selected role group
                          </v-tooltip>
                        </v-btn>
                      </template>
                      <v-list density="compact">
                        <v-list-subheader>From the bound role group selection</v-list-subheader>
                        <v-list-item
                            v-for="rid in team.role_ids"
                            :key="rid"
                            :value="rid"
                            @click="team.color = getRoleColorHex(rid)"
                        >
                          <template v-slot:prepend>
                            <v-avatar :color="getRoleColorHex(rid)" class="mr-2" size="16"></v-avatar>
                          </template>
                          <v-list-item-title>{{ getRoleName(rid) }}</v-list-item-title>
                        </v-list-item>
                        <v-divider class="my-1"></v-divider>
                        <v-list-item title="Reset to black" @click="team.color = '#000000'"></v-list-item>
                      </v-list>
                    </v-menu>
                  </div>

                  <v-combobox
                      v-model="team.include_user_ids"
                      chips
                      class="mb-3"
                      closable-chips
                      density="compact"
                      hide-details="auto"
                      hide-no-data
                      label="Mandatory included user ID"
                      multiple
                      placeholder="Enter the ID and press Enter."
                      variant="outlined"
                  ></v-combobox>

                  <v-text-field v-model="team.image" density="compact" hide-details label="Icon path"
                                variant="outlined"></v-text-field>

                  <div class="d-flex justify-space-between mt-4 pt-2 border-t">
                    <div>
                      <v-btn :disabled="index === 0" icon="mdi-arrow-up" size="small" variant="text"
                             @click="moveTeam(index, -1)"></v-btn>
                      <v-btn :disabled="index === config.length - 1" icon="mdi-arrow-down" size="small" variant="text"
                             @click="moveTeam(index, 1)"></v-btn>
                    </div>
                    <v-btn color="error" prepend-icon="mdi-delete" size="small" variant="text"
                           @click="removeTeam(index)">
                      Delete
                    </v-btn>
                  </div>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>

          <v-divider></v-divider>
          <v-card-actions>
            <v-btn :loading="loadingRoles" block color="secondary" prepend-icon="mdi-sync" variant="text"
                   @click="fetchRoles">
              Refresh the list of role groups
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col class="d-flex flex-column" cols="12" lg="8" md="7">
        <v-card class="fill-height d-flex flex-column">
          <v-toolbar class="border-b px-2" color="surface" density="compact">
            <v-toolbar-title class="text-subtitle-1 font-weight-bold">Preview</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn :loading="loadingPreview" color="primary" prepend-icon="mdi-refresh" @click="fetchPreview">
              Generate/Refresh Preview
            </v-btn>
          </v-toolbar>

          <v-card-text class="pa-4 flex-grow-1 overflow-y-auto" style="max-height: calc(100vh - 200px);">
            <div v-if="!previewData.length" class="d-flex flex-column align-center justify-center text-medium-emphasis">
              <v-icon class="mb-4 text-grey-lighten-1" size="64">mdi-account-group-outline</v-icon>
              <div class="text-h6">No preview data available.</div>
              <div class="text-body-2">Please configure the team and click the "Generate Preview" button on the top
                right.
              </div>
            </div>

            <div v-for="group in previewData" :key="group.name" class="mb-8">
              <div class="d-flex align-center mb-4 px-2">
                <v-avatar :color="getTeamColor(group.color)" class="mr-3 elevation-2" size="36">
                  <v-img v-if="group.image" :src="group.image"></v-img>
                  <span v-else class="text-caption text-white font-weight-bold">{{ group.name.charAt(0) }}</span>
                </v-avatar>
                <div>
                  <h3 class="text-h6 font-weight-bold line-height-1">{{ group.name }}</h3>
                  <div class="text-caption text-grey">Number of members: {{ group.list.length }}</div>
                </div>
              </div>

              <v-row dense>
                <v-col v-for="member in group.list" :key="member.id" cols="12" md="4" sm="6" xl="3">
                  <v-card
                      :class="{'border-primary border-md': hasOverride(member.id)}"
                      class="transition-swing rounded-lg"
                      elevation="0"
                      flat
                      hover
                      @click="openEditDialog(member, group.name)"
                  >
                    <v-card-item class="pa-3">
                      <template v-slot:prepend>
                        <v-avatar :image="member.avatar" class="border" size="42"></v-avatar>
                      </template>
                      <v-card-title class="text-body-2 font-weight-bold mb-1">{{ member.name }}</v-card-title>
                      <v-card-subtitle class="d-flex flex-column">
                        <span class="text-caption text-primary mb-1">{{ member.position }}</span>
                        <span class="text-caption text-grey-lighten-1"
                              style="font-size: 0.7rem !important;">ID: {{ member.id }}</span>
                      </v-card-subtitle>
                      <template v-slot:append>
                        <v-icon v-if="hasOverride(member.id)" color="primary" size="small">mdi-pencil</v-icon>
                      </template>
                    </v-card-item>
                  </v-card>
                </v-col>
              </v-row>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="dialog" max-width="500" scrollable>
      <v-card class="rounded-xl">
        <v-toolbar class="border-b" color="surface" density="compact" title="Edit member">
          <v-btn icon="mdi-close" variant="text" @click="dialog = false"></v-btn>
        </v-toolbar>

        <v-card-text class="pt-4">
          <div class="d-flex align-center mb-4">
            <v-avatar :image="editingMember?.avatar" class="mr-4 border" size="64"></v-avatar>
            <div>
              <div class="text-h6">{{ editingMember?.name }}</div>
              <div class="text-caption text-grey">ID: {{ editingMember?.id }}</div>
            </div>
          </div>

          <v-select
              v-model="tempTeamIndex"
              :item-value="(item) => config.indexOf(item)"
              :items="config"
              class="mb-4"
              density="comfortable"
              hint="Force Add User ID to Target Group"
              item-title="name"
              label="Team Affiliation (Move to Group)"
              persistent-hint
              prepend-inner-icon="mdi-account-switch"
              variant="outlined"
          ></v-select>

          <v-divider class="mb-4"></v-divider>
          <div class="text-subtitle-2 font-weight-bold mb-2 text-primary">Metadata Overrides</div>

          <v-row dense>
            <v-col cols="12">
              <v-text-field v-model="tempOverride.name" density="compact" label="Display Name"
                            placeholder="Default to Discord Nickname" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="tempOverride.position" density="compact" label="Position"
                            placeholder="Default to Group Name" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="tempOverride.avatar" density="compact" label="Custom Avatar URL"
                            placeholder="URL/github username/discord user id"
                            variant="outlined"></v-text-field>
            </v-col>
          </v-row>

          <v-switch v-model="tempOverride.avatarUseGithub" class="mb-2" color="primary" density="compact"
                    hide-details label="Use GitHub Avatar"></v-switch>

          <div class="text-subtitle-2 font-weight-bold mb-2 mt-2 text-primary">Social Links</div>
          <v-text-field v-model="tempOverride.contact.github" density="compact" label="GitHub Username"
                        prepend-inner-icon="mdi-github" variant="outlined"></v-text-field>
          <v-text-field v-model="tempOverride.contact.twitter" density="compact" label="Twitter / X" prepend-inner-icon="mdi-twitter"
                        variant="outlined"></v-text-field>
          <v-text-field v-model="tempOverride.contact.other" density="compact" label="Other Links (URL)"
                        prepend-inner-icon="mdi-link"
                        variant="outlined"></v-text-field>
        </v-card-text>

        <v-card-actions class="pa-4 bg-surface">
          <v-btn color="error" variant="text" @click="clearOverride">Clear All Overrides</v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="flat" @click="saveChanges">Save Changes</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import {inject, onMounted, ref} from 'vue'
import axios from 'axios'

const showMsg = inject('showMsg')

const config = ref([])
const overrides = ref({})
const discordRoles = ref([])
const previewData = ref([])

const loadingRoles = ref(false)
const loadingPreview = ref(false)

const dialog = ref(false)
const editingMember = ref(null)
const tempOverride = ref({contact: {}})
const tempTeamIndex = ref(-1)
const initialTeamIndex = ref(-1)

const fileInput = ref(null)

const getTeamColor = (color) => {
  if (Array.isArray(color)) return color[0]
  if (typeof color === 'string' && color.includes(',')) return color.split(',')[0].trim()
  return color || '#999'
}

const getCssGradient = (color) => {
  if (Array.isArray(color)) return `linear-gradient(to right, ${color.join(', ')})`
  if (typeof color === 'string' && color.includes(',')) return `linear-gradient(to right, ${color})`
  return color || '#000000'
}

const getRoleName = (id) => discordRoles.value.find(r => r.id === id)?.name || id
const getRoleColorHex = (id) => discordRoles.value.find(r => r.id === id)?.color_hex || '#000000'

const onRolesChange = (selectedRoleIds, teamIndex) => {
  if (selectedRoleIds && selectedRoleIds.length > 0) {
    const team = config.value[teamIndex]
    const firstRoleId = selectedRoleIds[0]
    const role = discordRoles.value.find(r => r.id === firstRoleId)

    if (role) {
      if (!team.name || team.name === 'New Team') team.name = role.name
      if (!team.color || team.color === '#000000') team.color = role.color_hex
    }
  }
}

const fetchRoles = async () => {
  loadingRoles.value = true
  try {
    const res = await axios.get(`/api/gensokyo/roles`)
    discordRoles.value = res.data
    showMsg('Role group has been updated')
  } catch (e) {
    showMsg('Failed to get role group', 'error')
  } finally {
    loadingRoles.value = false
  }
}

const fetchPreview = async () => {
  loadingPreview.value = true
  try {
    const payload = {
      config: config.value.map(c => ({
        ...c,
        color: typeof c.color === 'string' && c.color.includes(',') ? c.color.split(',').map(s => s.trim()) : c.color,
        role_ids: Array.isArray(c.role_ids) ? c.role_ids : (c.role_id ? [c.role_id] : []),
        include_user_ids: c.include_user_ids || []
      })),
      overrides: overrides.value
    }
    const res = await axios.post(`/api/gensokyo/contributors`, payload)
    previewData.value = res.data
    showMsg('Preview has been generated')
  } catch (e) {
    showMsg('Failed to generate preview', 'error')
  } finally {
    loadingPreview.value = false
  }
}

const addTeam = () => config.value.push({role_ids: [], include_user_ids: [], name: 'New Team', color: '#000000'})
const removeTeam = (idx) => config.value.splice(idx, 1)
const moveTeam = (idx, dir) => {
  const temp = config.value[idx]
  config.value[idx] = config.value[idx + dir]
  config.value[idx + dir] = temp
}

const hasOverride = (id) => !!overrides.value[id]

const openEditDialog = (member, currentTeamName) => {
  editingMember.value = member

  const existing = overrides.value[member.id] || {}
  tempOverride.value = JSON.parse(JSON.stringify({
    name: existing.name || '',
    position: existing.position || '',
    avatar: existing.avatar || '',
    avatarUseGithub: existing.avatarUseGithub || false,
    contact: existing.contact || {github: '', twitter: '', other: ''}
  }))

  const foundIndex = config.value.findIndex(c => c.name === currentTeamName)
  initialTeamIndex.value = foundIndex
  tempTeamIndex.value = foundIndex

  dialog.value = true
}

const saveChanges = () => {
  const id = editingMember.value.id

  const cleanData = {...tempOverride.value}
  Object.keys(cleanData).forEach(k => {
    if (cleanData[k] === '' || cleanData[k] === null) delete cleanData[k]
  })
  if (cleanData.contact) {
    Object.keys(cleanData.contact).forEach(k => {
      if (!cleanData.contact[k]) delete cleanData.contact[k]
    })
  }

  if (Object.keys(cleanData).length > 0 && !(Object.keys(cleanData).length === 1 && Object.keys(cleanData.contact).length === 0)) {
    overrides.value[id] = cleanData
  } else {
    delete overrides.value[id]
  }

  if (tempTeamIndex.value !== -1 && tempTeamIndex.value !== initialTeamIndex.value) {
    const targetTeam = config.value[tempTeamIndex.value]

    if (!targetTeam.include_user_ids) targetTeam.include_user_ids = []
    if (!targetTeam.include_user_ids.includes(id)) {
      targetTeam.include_user_ids.push(id)
    }

    if (initialTeamIndex.value !== -1) {
      const oldTeam = config.value[initialTeamIndex.value]
      if (oldTeam.include_user_ids) {
        oldTeam.include_user_ids = oldTeam.include_user_ids.filter(uid => uid !== id)
      }
    }

    showMsg(`User has been moved to "${targetTeam.name}"`)
  }

  dialog.value = false
  fetchPreview()
}

const clearOverride = () => {
  delete overrides.value[editingMember.value.id]
  dialog.value = false
  fetchPreview()
}

const exportJson = () => {
  const data = JSON.stringify({config: config.value, overrides: overrides.value}, null, 2)
  const blob = new Blob([data], {type: 'application/json'})
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'gensokyo_config.json'
  a.click()
  showMsg('Configuration has been exported')
}
const triggerImport = () => fileInput.value.click()
const handleImport = (e) => {
  const file = e.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (event) => {
    try {
      const json = JSON.parse(event.target.result)
      if (json.config) config.value = json.config
      if (json.overrides) overrides.value = json.overrides
      showMsg('Configuration import successful')
      fetchPreview()
    } catch (e) {
      showMsg('File format error', 'error')
    }
  }
  reader.readAsText(file)
}

onMounted(fetchRoles)
</script>