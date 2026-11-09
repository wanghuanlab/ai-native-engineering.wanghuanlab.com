<template>
  <el-card>
    <div class="toolbar">
      <el-button v-perm="'system:post:update'" type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="items" row-key="id">
      <el-table-column prop="code" label="编码" />
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="sortOrder" label="排序" width="100" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.enabled ? 'success' : 'info'">{{
            row.enabled ? '启用' : '停用'
          }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button v-perm="'system:post:update'" link type="primary" @click="openEdit(row)">
            修改
          </el-button>
          <el-button v-perm="'system:post:update'" link type="danger" @click="remove(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="editing ? '修改岗位' : '新建岗位'" width="480px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
        <el-form-item label="编码" prop="code">
          <el-input v-model="form.code" maxlength="64" :disabled="editing !== null" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" maxlength="64" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sortOrder" :min="0" :max="9999" />
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
import { createPost, deletePost, listPosts, updatePost, type Post, type PostWrite } from '../api'
import { confirmed } from '../feedback'

const items = ref<Post[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref<string | null>(null)
const formRef = ref<FormInstance>()
const form = reactive<PostWrite>({ code: '', name: '', sortOrder: 0, enabled: true })
const rules: FormRules<PostWrite> = {
  code: [{ required: true, message: '请输入编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

async function reload(): Promise<void> {
  loading.value = true
  try {
    items.value = await listPosts()
  } finally {
    loading.value = false
  }
}

function openCreate(): void {
  editing.value = null
  form.code = ''
  form.name = ''
  form.sortOrder = 0
  form.enabled = true
  dialogVisible.value = true
}

function openEdit(row: Post): void {
  editing.value = row.id
  form.code = row.code
  form.name = row.name
  form.sortOrder = row.sortOrder
  form.enabled = row.enabled
  dialogVisible.value = true
}

async function submit(): Promise<void> {
  if (!(await formRef.value?.validate().catch(() => false))) return
  saving.value = true
  try {
    const body: PostWrite = { ...form }
    if (editing.value) await updatePost(editing.value, body)
    else await createPost(body)
    ElMessage.success('已保存')
    dialogVisible.value = false
    await reload()
  } finally {
    saving.value = false
  }
}

async function remove(id: string): Promise<void> {
  if (!(await confirmed('确定删除这个岗位吗？'))) return
  await deletePost(id)
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
