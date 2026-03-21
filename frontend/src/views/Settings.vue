<template>
  <div class="settings">
    <el-card>
      <template #header>
        <span>系统设置</span>
      </template>

      <el-form
        :model="form"
        :rules="rules"
        ref="formRef"
        label-width="180px"
        v-loading="loading"
        style="max-width: 600px"
      >
        <el-divider content-position="left">监控调度设置</el-divider>

        <el-form-item label="默认监控间隔" prop="default_interval">
          <el-input-number
            v-model="form.default_interval"
            :min="5"
            :max="1440"
            :step="5"
          />
          <span class="hint">分钟（新建账号时的默认值）</span>
        </el-form-item>

        <el-form-item label="最大并发检查数" prop="max_concurrent_checks">
          <el-input-number
            v-model="form.max_concurrent_checks"
            :min="1"
            :max="50"
          />
          <span class="hint">同时执行的检查任务数量上限</span>
        </el-form-item>

        <el-form-item label="请求超时时间" prop="request_timeout">
          <el-input-number
            v-model="form.request_timeout"
            :min="10"
            :max="120"
          />
          <span class="hint">秒（单次请求的超时时间）</span>
        </el-form-item>

        <el-form-item label="默认监控视频数" prop="default_video_count">
          <el-input-number
            v-model="form.default_video_count"
            :min="5"
            :max="100"
            :step="5"
          />
          <span class="hint">个（每次检查时获取的最新视频数量）</span>
        </el-form-item>

        <el-divider content-position="left">界面设置</el-divider>

        <el-form-item label="网站名称" prop="site_name">
          <el-input
            v-model="form.site_name"
            placeholder="请输入网站名称"
            maxlength="50"
            show-word-limit
          />
          <span class="hint">显示在浏览器标签和侧边栏顶部</span>
        </el-form-item>

        <el-form-item label="网站Logo" prop="logo_image">
          <div class="logo-upload">
            <el-upload
              class="logo-uploader"
              :show-file-list="false"
              :before-upload="handleLogoUpload"
              accept="image/*"
            >
              <img v-if="form.logo_image" :src="form.logo_image" class="logo-preview" />
              <el-icon v-else class="logo-uploader-icon"><Plus /></el-icon>
            </el-upload>
            <div class="logo-actions">
              <el-button v-if="form.logo_image" size="small" @click="clearLogo">
                清除Logo
              </el-button>
              <span class="hint">建议尺寸：200x50px，支持PNG/JPG格式</span>
            </div>
          </div>
        </el-form-item>

        <el-divider />

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            保存设置
          </el-button>
          <el-button @click="loadSettings">
            重置
          </el-button>
        </el-form-item>

        <el-alert
          title="提示"
          type="info"
          :closable="false"
          show-icon
        >
          <p>设置更改后将在下一个调度周期生效。</p>
          <p>已创建的账号不会自动更新监控间隔，需要手动编辑。</p>
        </el-alert>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getSettings, updateSettings } from '@/api/settings'

const loading = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = ref({
  default_interval: 240,  // 4 hours in minutes
  max_concurrent_checks: 5,
  request_timeout: 30,
  default_video_count: 20,
  site_name: 'TikTok Monitor',
  logo_image: ''
})

const rules = {
  default_interval: [
    { required: true, message: '请输入默认监控间隔', trigger: 'blur' },
    { type: 'number', min: 5, max: 1440, message: '间隔必须在 5-1440 分钟之间', trigger: 'blur' }
  ],
  max_concurrent_checks: [
    { required: true, message: '请输入最大并发数', trigger: 'blur' },
    { type: 'number', min: 1, max: 50, message: '并发数必须在 1-50 之间', trigger: 'blur' }
  ],
  request_timeout: [
    { required: true, message: '请输入请求超时时间', trigger: 'blur' },
    { type: 'number', min: 10, max: 120, message: '超时时间必须在 10-120 秒之间', trigger: 'blur' }
  ],
  default_video_count: [
    { required: true, message: '请输入默认监控视频数', trigger: 'blur' },
    { type: 'number', min: 5, max: 100, message: '视频数必须在 5-100 之间', trigger: 'blur' }
  ],
  site_name: [
    { required: true, message: '请输入网站名称', trigger: 'blur' },
    { min: 1, max: 50, message: '网站名称长度必须在 1-50 字符之间', trigger: 'blur' }
  ]
}

const loadSettings = async () => {
  loading.value = true
  try {
    const data = await getSettings()
    // Convert seconds to minutes for display
    form.value = {
      default_interval: Math.round(data.default_interval / 60),
      max_concurrent_checks: data.max_concurrent_checks,
      request_timeout: data.request_timeout,
      default_video_count: data.default_video_count || 20,
      site_name: data.site_name || 'TikTok Monitor',
      logo_image: data.logo_image || ''
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
    ElMessage.error('加载设置失败')
  } finally {
    loading.value = false
  }
}

const handleLogoUpload = (file) => {
  // 验证文件类型
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }

  // 验证文件大小（限制2MB）
  const isLt2M = file.size / 1024 / 1024 < 2
  if (!isLt2M) {
    ElMessage.error('图片大小不能超过 2MB！')
    return false
  }

  // 读取文件并转换为base64
  const reader = new FileReader()
  reader.onload = (e) => {
    form.value.logo_image = e.target.result
  }
  reader.readAsDataURL(file)

  return false // 阻止自动上传
}

const clearLogo = () => {
  form.value.logo_image = ''
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    // Convert minutes to seconds for backend
    const payload = {
      default_interval: form.value.default_interval * 60,
      max_concurrent_checks: form.value.max_concurrent_checks,
      request_timeout: form.value.request_timeout,
      default_video_count: form.value.default_video_count,
      site_name: form.value.site_name,
      logo_image: form.value.logo_image
    }
    await updateSettings(payload)
    ElMessage.success('设置保存成功，刷新页面生效')
    
    // 更新页面标题
    document.title = form.value.site_name
    
    // 刷新页面以应用新的logo和站名
    setTimeout(() => {
      window.location.reload()
    }, 1000)
  } catch (error) {
    console.error('Failed to update settings:', error)
    ElMessage.error('设置保存失败')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings {
  padding: 20px;
}

.hint {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.el-alert {
  margin-top: 20px;
}

.el-alert p {
  margin: 5px 0;
}

.logo-upload {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.logo-uploader {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.3s;
}

.logo-uploader:hover {
  border-color: #409eff;
}

.logo-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 200px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-preview {
  width: 200px;
  height: 100px;
  object-fit: contain;
  display: block;
}

.logo-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
