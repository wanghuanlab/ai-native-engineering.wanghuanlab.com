<template>
  <el-card>
    <div class="toolbar">
      <el-button v-perm="'system:menu:update'" type="primary" @click="openCreate()">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="items" row-key="id" default-expand-all>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="path" label="路径" />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">{{ typeLabel(row.menuType) }}</template>
      </el-table-column>
      <el-table-column prop="permission" label="权限" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button v-perm="'system:menu:update'" link type="primary" @click="openCreate(row.id)">
            添加下级
          </el-button>
          <el-button v-perm="'system:menu:update'" link type="primary" @click="openEdit(row)">
            修改
          </el-button>
          <el-button v-perm="'system:menu:update'" link type="danger" @click="remove(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '修改菜单' : '新建菜单'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <el-form-item label="上级">
          <el-select v-model="form.parentId" clearable filterable placeholder="无">
            <el-option
              v-for="menu in parents"
              :key="menu.id"
              :label="menu.label"
              :value="menu.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="64" />
        </el-form-item>
        <el-form-item label="类型" prop="menuType">
          <el-select v-model="form.menuType">
            <el-option
              v-for="item in typeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="路径" prop="path">
          <el-input v-model="form.path" maxlength="128" placeholder="例如 users" />
        </el-form-item>
        <el-form-item v-if="form.menuType === MenuType.MENU" label="页面">
          <el-input
            v-model="form.component"
            maxlength="128"
            placeholder="admin/users、admin/roles、admin/menus、admin/depts、admin/posts"
          />
        </el-form-item>
        <el-form-item label="权限">
          <el-input v-model="form.permission" maxlength="128" placeholder="例如 system:user:list" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sortOrder" :min="0" :max="9999" />
        </el-form-item>
        <el-form-item label="显示">
          <el-switch v-model="form.visible" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import {
  MenuType,
  createMenu,
  deleteMenu,
  listMenus,
  updateMenu,
  type MenuNode,
  type MenuWrite,
} from '../api'
import { confirmed } from '../feedback'

const typeOptions = [
  { value: MenuType.DIR, label: '目录' },
  { value: MenuType.MENU, label: '菜单' },
  { value: MenuType.BUTTON, label: '按钮' },
]

const items = ref<MenuNode[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref<string | null>(null)
const formRef = ref<FormInstance>()
const form = reactive<MenuWrite>({
  parentId: undefined,
  name: '',
  path: '',
  component: '',
  permission: '',
  menuType: MenuType.MENU,
  sortOrder: 0,
  visible: true,
})

const rules: FormRules<MenuWrite> = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  menuType: [{ required: true, message: '请选择类型', trigger: 'change' }],
  path: [
    {
      validator: (_rule, value: string, callback) => {
        if (form.menuType !== MenuType.BUTTON && !value) callback(new Error('请输入路径'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

const parents = computed(() => flatten(items.value).filter((item) => item.id !== editing.value))

function typeLabel(value: string): string {
  return typeOptions.find((item) => item.value === value)?.label ?? value
}

function flatten(nodes: MenuNode[], prefix = ''): { id: string; label: string }[] {
  const rows: { id: string; label: string }[] = []
  for (const node of nodes) {
    const label = prefix ? `${prefix} / ${node.name}` : node.name
    rows.push({ id: node.id, label })
    if (node.children?.length) rows.push(...flatten(node.children, label))
  }
  return rows
}

async function reload(): Promise<void> {
  loading.value = true
  try {
    items.value = await listMenus()
  } finally {
    loading.value = false
  }
}

function blank(parentId?: string): void {
  form.parentId = parentId
  form.name = ''
  form.path = ''
  form.component = ''
  form.permission = ''
  form.menuType = MenuType.MENU
  form.sortOrder = 0
  form.visible = true
}

function openCreate(parentId?: string): void {
  editing.value = null
  blank(parentId)
  dialogVisible.value = true
}

function openEdit(row: MenuNode): void {
  editing.value = row.id
  form.parentId = row.parentId
  form.name = row.name
  form.path = row.path ?? ''
  form.component = row.component ?? ''
  form.permission = row.permission ?? ''
  form.menuType = row.menuType
  form.sortOrder = row.sortOrder
  form.visible = row.visible
  dialogVisible.value = true
}

function payload(): MenuWrite {
  return {
    parentId: form.parentId || undefined,
    name: form.name,
    path: form.path || undefined,
    component: form.menuType === MenuType.MENU ? form.component || undefined : undefined,
    permission: form.permission || undefined,
    menuType: form.menuType,
    sortOrder: form.sortOrder,
    visible: form.visible,
  }
}

async function submit(): Promise<void> {
  if (!(await formRef.value?.validate().catch(() => false))) return
  saving.value = true
  try {
    if (editing.value) await updateMenu(editing.value, payload())
    else await createMenu(payload())
    ElMessage.success('已保存')
    dialogVisible.value = false
    await reload()
  } finally {
    saving.value = false
  }
}

async function remove(id: string): Promise<void> {
  if (!(await confirmed('确定删除这个菜单吗？下级会一并删除。'))) return
  await deleteMenu(id)
  ElMessage.success('已删除')
  await reload()
}

onMounted(reload)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
