<template>
  <div class="login">
    <el-card class="login__card">
      <h1>{{ projectName }}</h1>
      <p class="login__hint">请使用管理员账号登录</p>
      <el-form :model="form" label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" maxlength="32" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            autocomplete="current-password"
            show-password
            maxlength="72"
          />
        </el-form-item>
        <el-form-item label="验证码">
          <div class="login__captcha">
            <el-input v-model="form.captchaCode" maxlength="8" />
            <button type="button" class="login__image" @click="loadCaptcha">
              <img v-if="image" :src="image" alt="验证码，点击刷新" />
              <span v-else>获取验证码</span>
            </button>
          </div>
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="submitting" class="login__submit">
          登录
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { issueCaptcha, login, projectName } from './api'
import { writeSession } from './session'

const route = useRoute()
const router = useRouter()
const image = ref('')
const submitting = ref(false)
const form = reactive({
  username: '',
  password: '',
  captchaId: '',
  captchaCode: '',
})

function captchaSrc(value: string): string {
  return value.startsWith('data:') ? value : `data:image/png;base64,${value}`
}

async function loadCaptcha(): Promise<void> {
  const captcha = await issueCaptcha()
  form.captchaId = captcha.captchaId
  form.captchaCode = ''
  image.value = captchaSrc(captcha.image)
}

function nextPath(): string {
  const redirect = route.query.redirect
  if (typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('/login')) {
    return redirect
  }
  return '/'
}

async function submit(): Promise<void> {
  if (!form.username || !form.password || !form.captchaCode) {
    ElMessage.warning('请填写用户名、密码和验证码')
    return
  }
  submitting.value = true
  try {
    const tokens = await login({
      username: form.username,
      ['password']: form.password,
      captchaId: form.captchaId,
      captchaCode: form.captchaCode,
    })
    writeSession(tokens.accessToken, tokens.refreshToken)
    await router.push(nextPath())
  } catch {
    await loadCaptcha()
  } finally {
    submitting.value = false
  }
}

onMounted(loadCaptcha)
</script>

<style scoped>
.login {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--el-bg-color-page);
}
.login__card {
  width: 400px;
}
.login__card h1 {
  margin: 0;
  font-size: 22px;
}
.login__hint {
  margin: 8px 0 20px;
  color: var(--el-text-color-secondary);
}
.login__captcha {
  display: flex;
  gap: 8px;
  width: 100%;
}
.login__image {
  width: 120px;
  height: 40px;
  padding: 0;
  border: 1px solid var(--el-border-color);
  background: #fff;
  cursor: pointer;
}
.login__image img {
  display: block;
  width: 120px;
  height: 40px;
}
.login__submit {
  width: 100%;
}
</style>
