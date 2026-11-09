<template>
  <el-card>
    <div class="toolbar">
      <el-button v-perm="'system:role:update'" type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="items" row-key="id">
      <el-table-column prop="code" label="编码" />
      <el-table-column prop="name" label="名称" />
      <el-table-column label="数据范围">
        <template #default="{ row }">{{ scopeLabel(row.dataScope) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">{{
            row.enabled ? '启用' : '停用'
          }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button v-perm="'system:role:update'" link type="primary" @click="openEdit(row)">
            修改
          </el-button>
          <el-button v-perm="'system:role:update'" link type="danger" @click="remove(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '修改角色' : '新建角色'" width="640px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="form.code" maxlength="64" :disabled="editing !== null" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="64" />
        </el-form-item>
        <el-form-item label="数据范围" prop="dataScope">
          <el-select v-model="form.dataScope">
            <el-option
              v-for="item in scopeOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.dataScope === DataScope.CUSTOM" label="指定部门">
          <el-checkbox-group v-model="form.deptIds">
            <el-checkbox v-for="dept in depts" :key="dept.id" :value="dept.id">
              {{ dept.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="菜单">
          <el-checkbox-group v-model="form.menuIds" class="roles__menus">
            <el-checkbox v-for="menu in menuOptions" :key="menu.id" :value="menu.id">
              {{ menu.label }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
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
import { onMounted, reactive, ref } from 'vue'
import {
  DataScope,
  createRole,
  deleteRole,
  listDepts,
  listMenus,
  listRoles,
  updateRole,
  type Dept,
  type MenuNode,
  type Role,
  type RoleWrite,
} from '../api'
import { confirmed } from '../feedback'

const scopeOptions = [
  { value: DataScope.ALL, label: '全部数据' },
  { value: DataScope.DEPT_AND_CHILD, label: '本部门及下级' },
  { value: DataScope.CUSTOM, label: '指定部门' },
  { value: DataScope.DEPT, label: '本部门' },
  { value: DataScope.SELF, label: '仅本人' },
]

const items = ref<Role[]>([])
const depts = ref<Dept[]>([])
const menuOptions = ref<{ id: string; label: string }[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref<string | null>(null)
const formRef = ref<FormInstance>()
const form = reactive<RoleWrite>({
  code: '',
  name: '',
  dataScope: DataScope.DEPT,
  enabled: true,
  menuIds: [],
  deptIds: [],
})
const rules: FormRules<RoleWrite> = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  dataScope: [{ required: true, message: '请选择数据范围', trigger: 'change' }],
}

function scopeLabel(value: string): string {
  return scopeOptions.find((item) => item.value === value)?.label ?? value
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
    items.value = await listRoles()
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editing.value = null
  form.code = ''
  form.name = ''
  form.dataScope = DataScope.DEPT
  form.enabled = true
  form.menuIds = []
  form.deptIds = []
  dialogVisible.value = true
}

function openEdit(row: Role): void {
  editing.value = row.id
  form.code = row.code
  form.name = row.name
  form.dataScope = row.dataScope
  form.enabled = row.enabled
  form.menuIds = [...row.menuIds]
  form.deptIds = [...row.deptIds]
  dialogVisible.value = true
}

async function submit(): Promise<void> {
  if (!(await formRef.value?.validate().catch(() => false))) return
  saving.value = true
  try {
    const body: RoleWrite = {
      code: form.code,
      name: form.name,
      dataScope: form.dataScope,
      enabled: form.enabled,
      menuIds: [...form.menuIds],
      deptIds: form.dataScope === DataScope.CUSTOM ? [...form.deptIds] : [],
    }
    if (editing.value) await updateRole(editing.value, body)
    else await createRole(body)
    ElMessage.success('已保存')
    dialogVisible.value = false
    await reload()
  } finally {
    saving.value = false
  }
}

async function remove(id: string): Promise<void> {
  if (!(await confirmed('确定删除这个角色吗？'))) return
  await deleteRole(id)
  ElMessage.success('已删除')
  await reload()
}

onMounted(async () => {
  const [deptRows, menus] = await Promise.all([listDepts(), listMenus()])
  depts.value = deptRows
  menuOptions.value = flatten(menus)
  await reload()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.roles__menus {
  display: flex;
  flex-direction: column;
  max-height: 240px;
  overflow: auto;
}
</style>
