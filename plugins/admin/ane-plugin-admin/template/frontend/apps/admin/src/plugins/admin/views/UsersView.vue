<template>
  <el-card>
    <div class="toolbar">
      <el-button v-perm="'system:user:create'" type="primary" @click="openCreate">新建</el-button>
    </div>
    <el-table v-loading="loading" :data="items" row-key="id">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="nickname" label="昵称" />
      <el-table-column label="部门">
        <template #default="{ row }">{{ deptName(row.deptId) }}</template>
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
          <el-button v-perm="'system:user:update'" link type="primary" @click="openEdit(row)">
            修改
          </el-button>
          <el-button v-perm="'system:user:delete'" link type="danger" @click="remove(row.id)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="size"
      :total="total"
      layout="total, prev, pager, next, sizes"
      class="pager"
      @change="reload"
    />

    <el-dialog v-model="dialogVisible" :title="editing ? '修改用户' : '新建用户'" width="560px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="72px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" maxlength="64" :disabled="editing !== null" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="form.nickname" maxlength="64" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            maxlength="72"
            :placeholder="editing ? '留空则不修改' : '至少 8 位'"
          />
        </el-form-item>
        <el-form-item label="部门" prop="deptId">
          <el-select v-model="form.deptId" filterable>
            <el-option v-for="dept in depts" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.roleIds" multiple collapse-tags>
            <el-option v-for="role in roles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="岗位">
          <el-select v-model="form.postIds" multiple collapse-tags>
            <el-option v-for="post in posts" :key="post.id" :label="post.name" :value="post.id" />
          </el-select>
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
  createUser,
  deleteUser,
  listDepts,
  listPosts,
  listRoles,
  listUsers,
  updateUser,
  type Dept,
  type Post,
  type Role,
  type User,
  type UserWrite,
} from '../api'
import { confirmed } from '../feedback'

const page = ref(1)
const size = ref(20)
const total = ref(0)
const items = ref<User[]>([])
const depts = ref<Dept[]>([])
const roles = ref<Role[]>([])
const posts = ref<Post[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const editing = ref<string | null>(null)
const formRef = ref<FormInstance>()
const form = reactive({
  username: '',
  nickname: '',
  password: '',
  deptId: '',
  enabled: true,
  roleIds: [] as string[],
  postIds: [] as string[],
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  deptId: [{ required: true, message: '请选择部门', trigger: 'change' }],
  password: [
    {
      validator: (_rule, value: string, callback) => {
        if (!editing.value && !value) callback(new Error('请输入密码'))
        else if (value && value.length < 8) callback(new Error('密码至少 8 位'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

function deptName(id: string): string {
  return depts.value.find((dept) => dept.id === id)?.name ?? id
}

async function reload(): Promise<void> {
  loading.value = true
  try {
    const result = await listUsers({ page: page.value, size: size.value })
    items.value = result.items
    total.value = result.total
  } finally {
    loading.value = false
  }
}

function resetForm(): void {
  form.username = ''
  form.nickname = ''
  form.password = ''
  form.deptId = depts.value[0]?.id ?? ''
  form.enabled = true
  form.roleIds = []
  form.postIds = []
}

function openCreate(): void {
  editing.value = null
  resetForm()
  dialogVisible.value = true
}

function openEdit(row: User): void {
  editing.value = row.id
  form.username = row.username
  form.nickname = row.nickname
  form.password = ''
  form.deptId = row.deptId
  form.enabled = row.enabled
  form.roleIds = [...row.roleIds]
  form.postIds = [...row.postIds]
  dialogVisible.value = true
}

function payload(): UserWrite {
  const body: UserWrite = {
    username: form.username,
    nickname: form.nickname,
    deptId: form.deptId,
    enabled: form.enabled,
    roleIds: [...form.roleIds],
    postIds: [...form.postIds],
  }
  if (form.password) body['password'] = form.password
  return body
}

async function submit(): Promise<void> {
  if (!(await formRef.value?.validate().catch(() => false))) return
  saving.value = true
  try {
    if (editing.value) await updateUser(editing.value, payload())
    else await createUser(payload())
    ElMessage.success('已保存')
    dialogVisible.value = false
    await reload()
  } finally {
    saving.value = false
  }
}

async function remove(id: string): Promise<void> {
  if (!(await confirmed('确定删除这个用户吗？'))) return
  await deleteUser(id)
  ElMessage.success('已删除')
  await reload()
}

onMounted(async () => {
  ;[depts.value, roles.value, posts.value] = await Promise.all([
    listDepts(),
    listRoles(),
    listPosts(),
  ])
  await reload()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
