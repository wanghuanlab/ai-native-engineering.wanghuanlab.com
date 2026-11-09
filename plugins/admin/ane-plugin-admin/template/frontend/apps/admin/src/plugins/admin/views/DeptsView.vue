<template>
  <el-card>
    <div class="toolbar">
      <el-button v-perm="'system:dept:update'" type="primary" @click="openCreate()">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="tree" row-key="id" default-expand-all>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="sortOrder" label="排序" width="100" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <el-button v-perm="'system:dept:update'" link type="primary" @click="openCreate(row.id)">
            添加下级
          </el-button>
          <el-button v-perm="'system:dept:update'" link type="primary" @click="openEdit(row)">
            修改
          </el-button>
          <el-button v-perm="'system:dept:update'" link type="danger" @click="remove(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '修改部门' : '新建部门'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
        <el-form-item label="上级">
          <el-select v-model="form.parentId" clearable filterable placeholder="无">
            <el-option v-for="dept in parents" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="64" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sortOrder" :min="0" :max="9999" />
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
import { createDept, deleteDept, listDepts, updateDept, type Dept, type DeptWrite } from '../api'
import { confirmed } from '../feedback'

interface DeptRow extends Dept {
  children?: DeptRow[]
}

const items = ref<Dept[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref<string | null>(null)
const formRef = ref<FormInstance>()
const form = reactive<DeptWrite>({ parentId: undefined, name: '', sortOrder: 0 })
const rules: FormRules<DeptWrite> = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

const tree = computed(() => toTree(items.value))
const parents = computed(() => items.value.filter((dept) => dept.id !== editing.value))

function toTree(depts: Dept[]): DeptRow[] {
  const nodes = new Map<string, DeptRow>()
  for (const dept of depts) nodes.set(dept.id, { ...dept })
  const roots: DeptRow[] = []
  for (const node of nodes.values()) {
    const parent = node.parentId ? nodes.get(node.parentId) : undefined
    if (parent && parent.id !== node.id) {
      parent.children = parent.children ?? []
      parent.children.push(node)
    } else {
      roots.push(node)
    }
  }
  return roots
}

async function reload(): Promise<void> {
  loading.value = true
  try {
    items.value = await listDepts()
  } finally {
    loading.value = false
  }
}

function openCreate(parentId?: string): void {
  editing.value = null
  form.parentId = parentId
  form.name = ''
  form.sortOrder = 0
  dialogVisible.value = true
}

function openEdit(row: Dept): void {
  editing.value = row.id
  form.parentId = row.parentId
  form.name = row.name
  form.sortOrder = row.sortOrder
  dialogVisible.value = true
}

async function submit(): Promise<void> {
  if (!(await formRef.value?.validate().catch(() => false))) return
  saving.value = true
  try {
    const body: DeptWrite = {
      parentId: form.parentId || undefined,
      name: form.name,
      sortOrder: form.sortOrder,
    }
    if (editing.value) await updateDept(editing.value, body)
    else await createDept(body)
    ElMessage.success('已保存')
    dialogVisible.value = false
    await reload()
  } finally {
    saving.value = false
  }
}

async function remove(id: string): Promise<void> {
  if (!(await confirmed('确定删除这个部门吗？'))) return
  await deleteDept(id)
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
