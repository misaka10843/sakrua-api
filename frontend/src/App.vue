<template>
  <v-app>
    <v-app-bar title="Gensokyo API Manager" color="primary" density="compact">
      <template v-slot:append>
        <v-btn prepend-icon="mdi-upload" @click="triggerFileInput">导入配置 JSON</v-btn>
        <v-btn prepend-icon="mdi-download" @click="exportJson">导出配置 JSON</v-btn>
        <input type="file" ref="fileInput" style="display: none" @change="importJson" accept=".json" />
      </template>
    </v-app-bar>

    <v-main class="bg-grey-darken-4">
      <v-container fluid>
        <v-row>
          <v-col cols="12" md="4">
            <v-card title="团队配置 (Teams)" subtitle="顺序决定显示优先级" class="mb-4">
              <template v-slot:append>
                <v-btn icon="mdi-plus" color="success" size="small" @click="addTeam"></v-btn>
              </template>

              <v-card-text class="pa-2">
                <v-expansion-panels variant="accordion">
                  <v-expansion-panel v-for="(team, index) in config" :key="index">
                    <v-expansion-panel-title>
                      <v-avatar size="24" :color="team.color[0] || 'grey'" class="mr-2"></v-avatar>
                      {{ team.name }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-text-field v-model="team.name" label="组名 (Name)" density="compact"></v-text-field>

                      <v-select
                        v-model="team.role_id"
                        :items="discordRoles"
                        item-title="name"
                        item-value="id"
                        label="绑定 Discord 身份组"
                        density="compact"
                        @update:model-value="autoFillTeam(index)"
                      >
                         <template v-slot:item="{ props, item }">
                            <v-list-item v-bind="props" :subtitle="item.raw.id">
                                <template v-slot:prepend>
                                   <v-avatar size="16" :color="item.raw.color_hex"></v-avatar>
                                </template>
                            </v-list-item>
                         </template>
                      </v-select>

                      <v-text-field v-model="team.image" label="图标路径 (Image)" density="compact"></v-text-field>
                      <v-text-field v-model="team.color" label="颜色 (支持数组)" density="compact" hint="单色或逗号分隔: #aaa, #bbb"></v-text-field>

                      <div class="d-flex justify-space-between mt-2">
                         <div>
                            <v-btn icon="mdi-arrow-up" size="x-small" variant="text" :disabled="index === 0" @click="moveTeam(index, -1)"></v-btn>
                            <v-btn icon="mdi-arrow-down" size="x-small" variant="text" :disabled="index === config.length - 1" @click="moveTeam(index, 1)"></v-btn>
                         </div>
                         <v-btn icon="mdi-delete" color="error" size="x-small" variant="text" @click="removeTeam(index)"></v-btn>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-card-text>
              <v-card-actions>
                  <v-btn block color="primary" @click="fetchRoles" :loading="loadingRoles">刷新身份组列表</v-btn>
              </v-card-actions>
            </v-card>
          </v-col>

          <v-col cols="12" md="8">
             <v-card class="fill-height">
                <v-toolbar color="surface" density="compact">
                   <v-toolbar-title>预览 & 编辑</v-toolbar-title>
                   <v-spacer></v-spacer>
                   <v-btn color="primary" prepend-icon="mdi-refresh" @click="fetchPreview" :loading="loadingPreview">生成预览</v-btn>
                </v-toolbar>

                <v-card-text class="pa-4">
                   <div v-if="!previewData.length" class="text-center text-grey mt-10">
                      点击“生成预览”查看结果。<br>点击头像可以编辑特定用户的详细信息（覆盖）。
                   </div>

                   <div v-for="group in previewData" :key="group.name" class="mb-6">
                      <div class="d-flex align-center mb-2">
                         <h3 class="text-h6 mr-2">{{ group.name }}</h3>
                         <v-chip size="small" variant="tonal">{{ group.list.length }} 人</v-chip>
                      </div>

                      <v-row dense>
                         <v-col v-for="member in group.list" :key="member.id" cols="12" sm="6" md="4" lg="3">
                            <v-card @click="openEditDialog(member)" hover border :class="{'border-primary': hasOverride(member.id)}">
                               <v-card-text class="d-flex align-center pa-2">
                                  <v-avatar size="40" :image="member.avatar" class="mr-3"></v-avatar>
                                  <div class="text-truncate">
                                     <div class="font-weight-bold text-body-2">{{ member.name }}</div>
                                     <div class="text-caption text-grey">{{ member.position }}</div>
                                  </div>
                                  <v-spacer></v-spacer>
                                  <v-icon v-if="hasOverride(member.id)" color="primary" size="small">mdi-pencil</v-icon>
                               </v-card-text>
                            </v-card>
                         </v-col>
                      </v-row>
                   </div>
                </v-card-text>
             </v-card>
          </v-col>
        </v-row>
      </v-container>

      <v-dialog v-model="dialog" max-width="500">
         <v-card v-if="editingMember">
            <v-card-title>编辑成员信息</v-card-title>
            <v-card-subtitle>ID: {{ editingMember.id }}</v-card-subtitle>

            <v-card-text>
               <v-alert type="info" density="compact" variant="tonal" class="mb-4">
                  在此处的修改将生成 "Overrides"，覆盖 Discord 自动获取的数据。
               </v-alert>

               <v-text-field v-model="tempOverride.name" label="显示名称 (Name)" placeholder="留空则使用 Discord 昵称"></v-text-field>
               <v-text-field v-model="tempOverride.position" label="职位 (Position)" placeholder="留空则使用组名"></v-text-field>
               <v-text-field v-model="tempOverride.avatar" label="头像链接 (Avatar)" placeholder="留空则使用 Discord 头像"></v-text-field>
               <v-switch v-model="tempOverride.avatarUseGithub" label="头像视为 GitHub 用户名" color="primary" density="compact"></v-switch>

               <v-divider class="my-3"></v-divider>
               <h4 class="text-body-2 font-weight-bold mb-2">社交链接 (Contact)</h4>

               <v-text-field v-model="tempOverride.contact.github" label="GitHub" prepend-inner-icon="mdi-github" density="compact"></v-text-field>
               <v-text-field v-model="tempOverride.contact.twitter" label="Twitter / X" prepend-inner-icon="mdi-twitter" density="compact"></v-text-field>
               <v-text-field v-model="tempOverride.contact.youtube" label="YouTube" prepend-inner-icon="mdi-youtube" density="compact"></v-text-field>
               <v-text-field v-model="tempOverride.contact.other" label="其他链接" prepend-inner-icon="mdi-link" density="compact"></v-text-field>
            </v-card-text>

            <v-card-actions>
               <v-btn color="error" variant="text" @click="clearOverride(editingMember.id)">清除覆盖</v-btn>
               <v-spacer></v-spacer>
               <v-btn variant="text" @click="dialog = false">取消</v-btn>
               <v-btn color="primary" @click="saveOverride">保存</v-btn>
            </v-card-actions>
         </v-card>
      </v-dialog>

      <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
         {{ snackbar.text }}
      </v-snackbar>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';

const config = ref([]);
const overrides = ref({});
const discordRoles = ref([]);
const previewData = ref([]);

const loadingRoles = ref(false);
const loadingPreview = ref(false);
const dialog = ref(false);
const fileInput = ref(null);

const editingMember = ref(null);
const tempOverride = ref({ contact: {} });
const snackbar = reactive({ show: false, text: '', color: 'success' });

const showMsg = (text, color = 'success') => {
   snackbar.text = text;
   snackbar.color = color;
   snackbar.show = true;
};

const fetchRoles = async () => {
   loadingRoles.value = true;
   try {
      const res = await axios.get(`${API_BASE}/api/gensokyo/roles`);
      discordRoles.value = res.data;
      showMsg('身份组列表已更新');
   } catch (e) {
      showMsg('获取身份组失败: ' + e.message, 'error');
   } finally {
      loadingRoles.value = false;
   }
};

const fetchPreview = async () => {
   loadingPreview.value = true;
   try {
      const payload = {
         config: config.value.map(c => {
             let colorData = c.color;
             if (typeof c.color === 'string' && c.color.includes(',')) {
                 colorData = c.color.split(',').map(s => s.trim());
             }
             return { ...c, color: colorData };
         }),
         overrides: overrides.value
      };

      const res = await axios.post(`${API_BASE}/api/gensokyo/contributors`, payload);
      previewData.value = res.data;
      showMsg('预览已生成');
   } catch (e) {
      showMsg('生成预览失败: ' + e.message, 'error');
      console.error(e);
   } finally {
      loadingPreview.value = false;
   }
};

const addTeam = () => {
   config.value.push({ role_id: '', name: 'New Team', image: '', color: '#000000' });
};
const removeTeam = (idx) => config.value.splice(idx, 1);
const moveTeam = (idx, dir) => {
   const temp = config.value[idx];
   config.value[idx] = config.value[idx + dir];
   config.value[idx + dir] = temp;
};
const autoFillTeam = (index) => {
   const team = config.value[index];
   const role = discordRoles.value.find(r => r.id === team.role_id);
   if (role) {
      team.name = role.name;
      team.color = role.color_hex;
   }
};

const hasOverride = (id) => !!overrides.value[id];

const openEditDialog = (member) => {
   editingMember.value = member;
   const existing = overrides.value[member.id] || {};
   tempOverride.value = JSON.parse(JSON.stringify({
      name: existing.name || '',
      position: existing.position || '',
      avatar: existing.avatar || '',
      avatarUseGithub: existing.avatarUseGithub || false,
      contact: existing.contact || { github: '', twitter: '', youtube: '', other: '' }
   }));
   dialog.value = true;
};

const saveOverride = () => {
   if (!editingMember.value) return;
   const id = editingMember.value.id;

   const cleanData = { ...tempOverride.value };
   if (!cleanData.name) delete cleanData.name;
   if (!cleanData.position) delete cleanData.position;
   if (!cleanData.avatar) delete cleanData.avatar;

   overrides.value[id] = cleanData;
   dialog.value = false;

   fetchPreview();
};

const clearOverride = (id) => {
   delete overrides.value[id];
   dialog.value = false;
   fetchPreview();
};

const exportJson = () => {
   const data = JSON.stringify({ config: config.value, overrides: overrides.value }, null, 2);
   const blob = new Blob([data], { type: 'application/json' });
   const url = URL.createObjectURL(blob);
   const a = document.createElement('a');
   a.href = url;
   a.download = 'gensokyo_contributors_config.json';
   a.click();
};

const triggerFileInput = () => fileInput.value.click();
const importJson = (event) => {
   const file = event.target.files[0];
   if (!file) return;
   const reader = new FileReader();
   reader.onload = (e) => {
      try {
         const json = JSON.parse(e.target.result);
         if (json.config) config.value = json.config;
         if (json.overrides) overrides.value = json.overrides;
         showMsg('配置导入成功');
         fetchPreview(); // 导入后自动刷新
      } catch (err) {
         showMsg('JSON 格式错误', 'error');
      }
   };
   reader.readAsText(file);
};

onMounted(() => {
   fetchRoles();
});
</script>

<style scoped>
</style>