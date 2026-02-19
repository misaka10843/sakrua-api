<template>
  <div class="h-100 d-flex flex-column">
    <v-toolbar color="transparent" density="compact" class="mb-2">
      <v-toolbar-title class="text-h6 font-weight-bold">Contributors Config Editor</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn prepend-icon="mdi-download" variant="tonal" class="mr-2" @click="triggerImport">import</v-btn>
      <v-btn prepend-icon="mdi-upload" variant="flat" color="primary" @click="exportJson">export</v-btn>
      <input type="file" ref="fileInput" style="display: none" @change="handleImport" accept=".json"/>
    </v-toolbar>

    <v-row class="flex-grow-1">
      <v-col cols="12" md="5" lg="4" class="d-flex flex-column">
        <v-card title="Teams List" subtitle="Configure role group binding"
                class="flex-grow-1 d-flex flex-column">
          <template v-slot:append>
            <v-btn icon="mdi-plus" color="primary" variant="tonal" @click="addTeam"></v-btn>
          </template>

          <v-card-text class="pa-2 flex-grow-1 overflow-y-auto" style="max-height: calc(100vh - 200px);">
            <v-expansion-panels variant="popout" multiple flat>
              <v-expansion-panel class="v-card" style="border-width: 1px" v-for="(team, index) in config" :key="index">
                <v-expansion-panel-title>
                  <v-avatar size="24" :color="getTeamColor(team.color)" class="mr-3 text-caption text-white">
                    {{ team.name ? team.name.charAt(0) : '#' }}
                  </v-avatar>
                  <div class="text-truncate">{{ team.name || 'Unnamed Group' }}</div>
                </v-expansion-panel-title>

                <v-expansion-panel-text>
                  <v-autocomplete
                      v-model="team.role_ids"
                      :items="discordRoles"
                      item-title="name"
                      item-value="id"
                      label="Bind Discord Role Group"
                      multiple
                      chips
                      closable-chips
                      density="compact"
                      variant="outlined"
                      class="mb-1"
                      @update:model-value="(val) => onRolesChange(val, index)"
                  >
                    <template v-slot:item="{ props, item }">
                      <v-list-item v-bind="props" :title="item.raw.name">
                        <template v-slot:prepend>
                          <v-avatar size="12" :color="item.raw.color_hex" class="mr-2"></v-avatar>
                        </template>
                      </v-list-item>
                    </template>
                  </v-autocomplete>

                  <v-text-field
                      v-model="team.name"
                      label="Display group name"
                      density="compact"
                      variant="outlined"
                      hide-details="auto"
                      class="mb-3"
                  ></v-text-field>

                  <div class="d-flex align-center mb-3">
                    <v-text-field
                        v-model="team.color"
                        label="Color (Hex, support gradient hex arrays)"
                        density="compact"
                        variant="outlined"
                        hide-details
                        class="flex-grow-1 mr-2"
                    >
                      <template v-slot:prepend-inner>
                        <div class="rounded-circle border"
                             :style="{background: getCssGradient(team.color), width: '16px', height: '16px'}"></div>
                      </template>
                    </v-text-field>

                    <v-menu>
                      <template v-slot:activator="{ props }">
                        <v-btn v-bind="props" icon="mdi-eyedropper" size="small" variant="text" color="secondary">
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
                            <v-avatar size="16" :color="getRoleColorHex(rid)" class="mr-2"></v-avatar>
                          </template>
                          <v-list-item-title>{{ getRoleName(rid) }}</v-list-item-title>
                        </v-list-item>
                        <v-divider class="my-1"></v-divider>
                        <v-list-item @click="team.color = '#000000'" title="Reset to black"></v-list-item>
                      </v-list>
                    </v-menu>
                  </div>

                  <v-combobox
                      v-model="team.include_user_ids"
                      label="Mandatory included user ID"
                      multiple
                      chips
                      closable-chips
                      density="compact"
                      variant="outlined"
                      hide-no-data
                      placeholder="Enter the ID and press Enter."
                      hide-details="auto"
                      class="mb-3"
                  ></v-combobox>

                  <v-text-field v-model="team.image" label="Icon path" density="compact" variant="outlined"
                                hide-details></v-text-field>

                  <div class="d-flex justify-space-between mt-4 pt-2 border-t">
                    <div>
                      <v-btn icon="mdi-arrow-up" size="small" variant="text" :disabled="index === 0"
                             @click="moveTeam(index, -1)"></v-btn>
                      <v-btn icon="mdi-arrow-down" size="small" variant="text" :disabled="index === config.length - 1"
                             @click="moveTeam(index, 1)"></v-btn>
                    </div>
                    <v-btn color="error" size="small" variant="text" prepend-icon="mdi-delete"
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
            <v-btn block color="secondary" variant="text" @click="fetchRoles" :loading="loadingRoles"
                   prepend-icon="mdi-sync">
              Refresh the list of role groups
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="7" lg="8" class="d-flex flex-column">
        <v-card class="fill-height d-flex flex-column">
          <v-toolbar color="surface" density="compact" class="border-b px-2">
            <v-toolbar-title class="text-subtitle-1 font-weight-bold">Preview</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn color="primary" prepend-icon="mdi-refresh" @click="fetchPreview" :loading="loadingPreview">
              Generate/Refresh Preview
            </v-btn>
          </v-toolbar>

          <v-card-text class="pa-4 flex-grow-1 overflow-y-auto" style="max-height: calc(100vh - 200px);">
            <div v-if="!previewData.length" class="d-flex flex-column align-center justify-center text-medium-emphasis">
              <v-icon size="64" class="mb-4 text-grey-lighten-1">mdi-account-group-outline</v-icon>
              <div class="text-h6">No preview data available.</div>
              <div class="text-body-2">Please configure the team and click the "Generate Preview" button on the top right.</div>
            </div>

            <div v-for="group in previewData" :key="group.name" class="mb-8">
              <div class="d-flex align-center mb-4 px-2">
                <v-avatar size="36" :color="getTeamColor(group.color)" class="mr-3 elevation-2">
                  <v-img v-if="group.image" :src="group.image"></v-img>
                  <span v-else class="text-caption text-white font-weight-bold">{{ group.name.charAt(0) }}</span>
                </v-avatar>
                <div>
                  <h3 class="text-h6 font-weight-bold line-height-1">{{ group.name }}</h3>
                  <div class="text-caption text-grey">Number of members: {{ group.list.length }}</div>
                </div>
              </div>

              <v-row dense>
                <v-col v-for="member in group.list" :key="member.id" cols="12" sm="6" md="4" xl="3">
                  <v-card
                      @click="openEditDialog(member, group.name)"
                      hover
                      :class="{'border-primary border-md': hasOverride(member.id)}"
                      class="transition-swing rounded-lg"
                      elevation="0"
                      flat
                  >
                    <v-card-item class="pa-3">
                      <template v-slot:prepend>
                        <v-avatar size="42" :image="member.avatar" class="border"></v-avatar>
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
        <v-toolbar title="Edit member" color="surface" density="compact" class="border-b">
          <v-btn icon="mdi-close" @click="dialog = false" variant="text"></v-btn>
        </v-toolbar>

        <v-card-text class="pt-4">
          <div class="d-flex align-center mb-4">
            <v-avatar size="64" :image="editingMember?.avatar" class="mr-4 border"></v-avatar>
            <div>
              <div class="text-h6">{{ editingMember?.name }}</div>
              <div class="text-caption text-grey">ID: {{ editingMember?.id }}</div>
            </div>
          </div>

          <v-select
              v-model="tempTeamIndex"
              :items="config"
              item-title="name"
              :item-value="(item) => config.indexOf(item)"
              label="Team Affiliation (Move to Group)"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-account-switch"
              class="mb-4"
              hint="Force Add User ID to Target Group"
              persistent-hint
          ></v-select>

          <v-divider class="mb-4"></v-divider>
          <div class="text-subtitle-2 font-weight-bold mb-2 text-primary">Metadata Overrides</div>

          <v-row dense>
            <v-col cols="12">
              <v-text-field v-model="tempOverride.name" label="Display Name" placeholder="Default to Discord Nickname"
                            density="compact" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="tempOverride.position" label="Position" placeholder="Default to Group Name"
                            density="compact" variant="outlined"></v-text-field>
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="tempOverride.avatar" label="Custom Avatar URL" density="compact" placeholder="URL/github username/discord user id"
                            variant="outlined"></v-text-field>
            </v-col>
          </v-row>

          <v-switch v-model="tempOverride.avatarUseGithub" label="Use GitHub Avatar" color="primary" density="compact"
                    hide-details class="mb-2"></v-switch>

          <div class="text-subtitle-2 font-weight-bold mb-2 mt-2 text-primary">Social Links</div>
          <v-text-field v-model="tempOverride.contact.github" label="GitHub Username" density="compact"
                        variant="outlined" prepend-inner-icon="mdi-github"></v-text-field>
          <v-text-field v-model="tempOverride.contact.twitter" label="Twitter / X" density="compact" variant="outlined"
                        prepend-inner-icon="mdi-twitter"></v-text-field>
          <v-text-field v-model="tempOverride.contact.other" label="Other Links (URL)" density="compact" variant="outlined"
                        prepend-inner-icon="mdi-link"></v-text-field>
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

const API_BASE = 'http://127.0.0.1:8000'
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
    const res = await axios.get(`${API_BASE}/api/gensokyo/roles`)
    discordRoles.value = res.data
    showMsg('身份组已更新')
  } catch (e) {
    showMsg('获取身份组失败', 'error')
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
    const res = await axios.post(`${API_BASE}/api/gensokyo/contributors`, payload)
    previewData.value = res.data
    showMsg('预览已生成')
  } catch (e) {
    showMsg('生成预览失败', 'error')
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

    showMsg(`已将用户移动到 "${targetTeam.name}"`)
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
  showMsg('配置已导出')
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
      showMsg('配置导入成功')
      fetchPreview()
    } catch (e) {
      showMsg('文件格式错误', 'error')
    }
  }
  reader.readAsText(file)
}

onMounted(fetchRoles)
</script>