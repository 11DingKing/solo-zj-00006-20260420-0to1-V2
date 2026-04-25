<template>
  <div class="recipe-list">
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="菜名">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入菜名"
            clearable
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="分类">
          <el-select
            v-model="searchForm.category_id"
            placeholder="请选择分类"
            clearable
          >
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select
            v-model="searchForm.difficulty_id"
            placeholder="请选择难度"
            clearable
          >
            <el-option
              v-for="difficulty in difficulties"
              :key="difficulty.id"
              :label="difficulty.name"
              :value="difficulty.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="烹饪时间">
          <el-select
            v-model="searchForm.cooking_time_range"
            placeholder="请选择时间范围"
            clearable
          >
            <el-option label="30分钟以内" :value="30" />
            <el-option label="60分钟以内" :value="60" />
            <el-option label="90分钟以内" :value="90" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-row :gutter="20" class="recipe-grid">
      <el-col :xs="12" :sm="8" :md="6" v-for="recipe in recipes" :key="recipe.id">
        <el-card
          class="recipe-card"
          :body-style="{ padding: 0 }"
          shadow="hover"
        >
          <div class="recipe-cover">
            <img
              :src="recipe.cover_url || 'https://picsum.photos/400/300?random=' + recipe.id"
              :alt="recipe.name"
            />
            <div class="recipe-overlay">
              <div class="recipe-time">
                <el-icon><Clock /></el-icon>
                <span>{{ recipe.cooking_time }}分钟</span>
              </div>
            </div>
          </div>
          <div class="recipe-info">
            <h3 class="recipe-name">{{ recipe.name }}</h3>
            <div class="recipe-tags">
              <el-tag size="small" type="primary">{{ recipe.category_name }}</el-tag>
              <el-tag
                size="small"
                :type="getDifficultyTagType(recipe.difficulty_level)"
              >{{ recipe.difficulty_name }}</el-tag>
            </div>
            <div class="recipe-actions">
              <el-button type="primary" link @click="viewRecipe(recipe.id)">
                查看详情
              </el-button>
              <el-button type="success" link @click="addToMenu(recipe.id)">
                加入菜单
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[12, 24, 48]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'
import { categoryApi, difficultyApi, recipeApi, weeklyMenuApi } from '@/api'

const router = useRouter()

const categories = ref<any[]>([])
const difficulties = ref<any[]>([])
const recipes = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)

const searchForm = reactive({
  name: '',
  category_id: null as number | null,
  difficulty_id: null as number | null,
  cooking_time_range: null as number | null
})

const getCategories = async () => {
  try {
    const res = await categoryApi.getAll()
    categories.value = res.data
  } catch (error) {
    console.error('获取分类失败', error)
  }
}

const getDifficulties = async () => {
  try {
    const res = await difficultyApi.getAll()
    difficulties.value = res.data
  } catch (error) {
    console.error('获取难度失败', error)
  }
}

const getRecipes = async () => {
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (searchForm.name) {
      params.name = searchForm.name
    }
    if (searchForm.category_id) {
      params.category_id = searchForm.category_id
    }
    if (searchForm.difficulty_id) {
      params.difficulty_id = searchForm.difficulty_id
    }
    if (searchForm.cooking_time_range) {
      params.max_cooking_time = searchForm.cooking_time_range
    }
    
    const res = await recipeApi.getList(params)
    recipes.value = res.data.recipes
    total.value = res.data.total
  } catch (error) {
    console.error('获取食谱列表失败', error)
    ElMessage.error('获取食谱列表失败')
  }
}

const handleSearch = () => {
  currentPage.value = 1
  getRecipes()
}

const handleReset = () => {
  searchForm.name = ''
  searchForm.category_id = null
  searchForm.difficulty_id = null
  searchForm.cooking_time_range = null
  currentPage.value = 1
  getRecipes()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  getRecipes()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  getRecipes()
}

const viewRecipe = (id: number) => {
  router.push(`/recipe/${id}`)
}

const addToMenu = async (recipeId: number) => {
  try {
    await weeklyMenuApi.add(recipeId)
    ElMessage.success('已加入本周菜单')
  } catch (error: any) {
    if (error.response?.data?.message === '食谱已在菜单中') {
      ElMessage.warning('该食谱已在菜单中')
    } else {
      ElMessage.error('加入菜单失败')
    }
  }
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
  getCategories()
  getDifficulties()
  getRecipes()
})
</script>

<style scoped>
.recipe-list {
  max-width: 1400px;
  margin: 0 auto;
}

.search-card {
  margin-bottom: 20px;
}

.search-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.recipe-grid {
  margin-bottom: 20px;
}

.recipe-card {
  margin-bottom: 20px;
  cursor: pointer;
  transition: transform 0.3s;
}

.recipe-card:hover {
  transform: translateY(-5px);
}

.recipe-cover {
  position: relative;
  width: 100%;
  height: 180px;
  overflow: hidden;
}

.recipe-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recipe-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  padding: 10px;
}

.recipe-time {
  display: flex;
  align-items: center;
  gap: 5px;
  color: white;
  font-size: 14px;
}

.recipe-info {
  padding: 15px;
}

.recipe-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 10px;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.recipe-tags {
  display: flex;
  gap: 5px;
  margin-bottom: 10px;
}

.recipe-actions {
  display: flex;
  justify-content: space-between;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
