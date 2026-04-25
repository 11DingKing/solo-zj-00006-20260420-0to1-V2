<template>
  <div class="recipe-detail" v-loading="loading">
    <el-card v-if="recipe" class="detail-card">
      <template #header>
        <div class="card-header">
          <h2>{{ recipe.name }}</h2>
          <div class="header-actions">
            <el-button type="primary" @click="addToMenu">
              <el-icon><Plus /></el-icon>
              加入本周菜单
            </el-button>
            <el-button @click="goBack">返回列表</el-button>
          </div>
        </div>
      </template>
      
      <el-row :gutter="40">
        <el-col :span="12">
          <div class="recipe-cover">
            <img
              :src="recipe.cover_url || 'https://picsum.photos/600/400?random=' + recipe.id"
              :alt="recipe.name"
            />
          </div>
        </el-col>
        
        <el-col :span="12">
          <div class="recipe-meta">
            <div class="meta-item">
              <span class="meta-label">分类：</span>
              <el-tag type="primary">{{ recipe.category_name }}</el-tag>
            </div>
            <div class="meta-item">
              <span class="meta-label">难度：</span>
              <el-tag :type="getDifficultyTagType(recipe.difficulty_level)">
                {{ recipe.difficulty_name }}
              </el-tag>
            </div>
            <div class="meta-item">
              <span class="meta-label">烹饪时间：</span>
              <span class="meta-value">{{ recipe.cooking_time }} 分钟</span>
            </div>
          </div>
          
          <div class="ingredients-section">
            <h3>食材清单</h3>
            <el-table :data="recipe.ingredients" border style="width: 100%">
              <el-table-column prop="name" label="食材名称" />
              <el-table-column prop="amount" label="用量" width="100" />
              <el-table-column prop="unit_name" label="单位" width="80" />
            </el-table>
          </div>
        </el-col>
      </el-row>
      
      <div class="steps-section" v-if="recipe.steps && recipe.steps.length > 0">
        <h3>烹饪步骤</h3>
        <div class="steps-list">
          <div
            v-for="(step, index) in recipe.steps"
            :key="index"
            class="step-item"
          >
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">{{ step }}</div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { recipeApi, weeklyMenuApi } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const recipe = ref<any>(null)

const getRecipeDetail = async () => {
  const id = route.params.id
  if (!id) return
  
  loading.value = true
  try {
    const res = await recipeApi.getById(Number(id))
    recipe.value = res.data
    // 解析步骤JSON
    if (recipe.value.steps) {
      try {
        recipe.value.steps = JSON.parse(recipe.value.steps)
      } catch {
        // 如果解析失败，保持原样
      }
    }
  } catch (error) {
    console.error('获取食谱详情失败', error)
    ElMessage.error('获取食谱详情失败')
  } finally {
    loading.value = false
  }
}

const addToMenu = async () => {
  if (!recipe.value) return
  
  try {
    await weeklyMenuApi.add(recipe.value.id)
    ElMessage.success('已加入本周菜单')
  } catch (error: any) {
    if (error.response?.data?.message === '食谱已在菜单中') {
      ElMessage.warning('该食谱已在菜单中')
    } else {
      ElMessage.error('加入菜单失败')
    }
  }
}

const goBack = () => {
  router.push('/')
}

const getDifficultyTagType = (level: number) => {
  switch (level) {
    case 1:
      return 'success'
    case 2:
      return 'warning'
    case 3:
      return 'danger'
    default:
      return 'info'
  }
}

onMounted(() => {
  getRecipeDetail()
})
</script>

<style scoped>
.recipe-detail {
  max-width: 1200px;
  margin: 0 auto;
}

.detail-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #303133;
}

.recipe-cover {
  width: 100%;
  height: 300px;
  border-radius: 8px;
  overflow: hidden;
}

.recipe-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recipe-meta {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.meta-label {
  font-weight: 600;
  color: #606266;
}

.meta-value {
  color: #303133;
}

.ingredients-section,
.steps-section {
  margin-top: 30px;
}

.ingredients-section h3,
.steps-section h3 {
  margin-bottom: 15px;
  color: #303133;
  border-left: 4px solid #409EFF;
  padding-left: 10px;
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.step-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.step-number {
  width: 30px;
  height: 30px;
  background-color: #409EFF;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
}

.step-content {
  line-height: 1.6;
  color: #303133;
}
</style>
