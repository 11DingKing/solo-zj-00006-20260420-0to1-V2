<template>
  <div class="create-recipe">
    <el-card class="form-card">
      <template #header>
        <h2>{{ isEdit ? '编辑食谱' : '创建食谱' }}</h2>
      </template>
      
      <el-form
        ref="formRef"
        :model="recipeForm"
        :rules="rules"
        label-width="100px"
        class="recipe-form"
      >
        <el-form-item label="菜名" prop="name">
          <el-input
            v-model="recipeForm.name"
            placeholder="请输入菜名"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="分类" prop="category_id">
              <el-select
                v-model="recipeForm.category_id"
                placeholder="请选择分类"
                style="width: 100%"
              >
                <el-option
                  v-for="category in categories"
                  :key="category.id"
                  :label="category.name"
                  :value="category.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="难度" prop="difficulty_id">
              <el-select
                v-model="recipeForm.difficulty_id"
                placeholder="请选择难度"
                style="width: 100%"
              >
                <el-option
                  v-for="difficulty in difficulties"
                  :key="difficulty.id"
                  :label="difficulty.name"
                  :value="difficulty.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="烹饪时间" prop="cooking_time">
              <el-input-number
                v-model="recipeForm.cooking_time"
                :min="1"
                :max="999"
                placeholder="分钟"
                style="width: 100%"
              />
              <span style="margin-left: 10px; color: #606266;">分钟</span>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="封面图URL" prop="cover_url">
          <el-input
            v-model="recipeForm.cover_url"
            placeholder="请输入封面图URL（可选）"
            maxlength="500"
          />
        </el-form-item>
        
        <el-form-item label="食材" prop="ingredients">
          <div class="ingredients-list">
            <div
              v-for="(ingredient, index) in recipeForm.ingredients"
              :key="index"
              class="ingredient-row"
            >
              <el-form-item
                :prop="`ingredients.${index}.name`"
                :rules="{ required: true, message: '请输入食材名称', trigger: 'blur' }"
              >
                <el-input
                  v-model="ingredient.name"
                  placeholder="食材名称"
                  style="width: 150px"
                />
              </el-form-item>
              
              <el-form-item
                :prop="`ingredients.${index}.amount`"
                :rules="{ required: true, message: '请输入用量', trigger: 'blur' }"
              >
                <el-input-number
                  v-model="ingredient.amount"
                  :min="0"
                  :precision="2"
                  placeholder="用量"
                  style="width: 120px"
                />
              </el-form-item>
              
              <el-form-item
                :prop="`ingredients.${index}.unit_id`"
                :rules="{ required: true, message: '请选择单位', trigger: 'change' }"
              >
                <el-select
                  v-model="ingredient.unit_id"
                  placeholder="单位"
                  style="width: 100px"
                >
                  <el-option
                    v-for="unit in units"
                    :key="unit.id"
                    :label="unit.name"
                    :value="unit.id"
                  />
                </el-select>
              </el-form-item>
              
              <el-button
                type="danger"
                :icon="Delete"
                circle
                @click="removeIngredient(index)"
                :disabled="recipeForm.ingredients.length <= 1"
              />
            </div>
            
            <el-button type="primary" :icon="Plus" @click="addIngredient">
              添加食材
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="烹饪步骤" prop="steps">
          <div class="steps-list">
            <div
              v-for="(step, index) in recipeForm.steps"
              :key="index"
              class="step-row"
            >
              <span class="step-number">步骤 {{ index + 1 }}</span>
              <el-input
                v-model="recipeForm.steps[index]"
                type="textarea"
                :rows="2"
                placeholder="请输入烹饪步骤"
                style="flex: 1"
              />
              <el-button
                type="danger"
                :icon="Delete"
                circle
                @click="removeStep(index)"
                :disabled="recipeForm.steps.length <= 1"
              />
            </div>
            
            <el-button type="primary" :icon="Plus" @click="addStep">
              添加步骤
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" size="large" @click="submitForm">
            {{ isEdit ? '保存修改' : '创建食谱' }}
          </el-button>
          <el-button size="large" @click="resetForm">重置</el-button>
          <el-button size="large" @click="goBack">返回</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import { categoryApi, difficultyApi, unitApi, recipeApi } from '@/api'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()

const isEdit = computed(() => !!route.params.id)

const categories = ref<any[]>([])
const difficulties = ref<any[]>([])
const units = ref<any[]>([])

const recipeForm = reactive({
  name: '',
  category_id: null as number | null,
  difficulty_id: null as number | null,
  cooking_time: 30,
  cover_url: '',
  ingredients: [
    { name: '', amount: 0, unit_id: null }
  ],
  steps: ['']
})

const rules: FormRules = {
  name: [
    { required: true, message: '请输入菜名', trigger: 'blur' },
    { min: 1, max: 100, message: '菜名长度为1-100个字符', trigger: 'blur' }
  ],
  category_id: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ],
  difficulty_id: [
    { required: true, message: '请选择难度', trigger: 'change' }
  ],
  cooking_time: [
    { required: true, message: '请输入烹饪时间', trigger: 'blur' },
    { type: 'number', min: 1, message: '烹饪时间必须大于0', trigger: 'blur' }
  ]
}

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

const getUnits = async () => {
  try {
    const res = await unitApi.getAll()
    units.value = res.data
  } catch (error) {
    console.error('获取单位失败', error)
  }
}

const getRecipeDetail = async () => {
  const id = route.params.id
  if (!id) return
  
  try {
    const res = await recipeApi.getById(Number(id))
    const data = res.data
    
    recipeForm.name = data.name
    recipeForm.category_id = data.category_id
    recipeForm.difficulty_id = data.difficulty_id
    recipeForm.cooking_time = data.cooking_time
    recipeForm.cover_url = data.cover_url || ''
    
    // 设置食材
    if (data.ingredients && data.ingredients.length > 0) {
      recipeForm.ingredients = data.ingredients.map((ing: any) => ({
        name: ing.name,
        amount: ing.amount,
        unit_id: ing.unit_id
      }))
    }
    
    // 设置步骤
    if (data.steps) {
      try {
        const steps = JSON.parse(data.steps)
        if (Array.isArray(steps) && steps.length > 0) {
          recipeForm.steps = steps
        }
      } catch {
        // 解析失败保持默认
      }
    }
  } catch (error) {
    console.error('获取食谱详情失败', error)
    ElMessage.error('获取食谱详情失败')
  }
}

const addIngredient = () => {
  recipeForm.ingredients.push({ name: '', amount: 0, unit_id: null })
}

const removeIngredient = (index: number) => {
  recipeForm.ingredients.splice(index, 1)
}

const addStep = () => {
  recipeForm.steps.push('')
}

const removeStep = (index: number) => {
  recipeForm.steps.splice(index, 1)
}

const submitForm = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      // 验证食材
      const validIngredients = recipeForm.ingredients.filter(
        ing => ing.name && ing.amount > 0 && ing.unit_id
      )
      
      if (validIngredients.length === 0) {
        ElMessage.error('请至少添加一个有效的食材')
        return
      }
      
      // 准备提交数据
      const submitData = {
        name: recipeForm.name,
        category_id: recipeForm.category_id,
        difficulty_id: recipeForm.difficulty_id,
        cooking_time: recipeForm.cooking_time,
        cover_url: recipeForm.cover_url || null,
        ingredients: validIngredients,
        steps: recipeForm.steps.filter(s => s.trim())
      }
      
      try {
        if (isEdit.value) {
          await recipeApi.update(Number(route.params.id), submitData)
          ElMessage.success('食谱修改成功')
        } else {
          await recipeApi.create(submitData)
          ElMessage.success('食谱创建成功')
        }
        router.push('/')
      } catch (error: any) {
        const errorMsg = error.response?.data?.message || '操作失败'
        ElMessage.error(errorMsg)
      }
    }
  })
}

const resetForm = () => {
  formRef.value?.resetFields()
  recipeForm.ingredients = [{ name: '', amount: 0, unit_id: null }]
  recipeForm.steps = ['']
}

const goBack = () => {
  router.push('/')
}

onMounted(() => {
  getCategories()
  getDifficulties()
  getUnits()
  
  if (isEdit.value) {
    getRecipeDetail()
  }
})
</script>

<style scoped>
.create-recipe {
  max-width: 1000px;
  margin: 0 auto;
}

.form-card {
  border-radius: 8px;
}

.recipe-form {
  max-width: 900px;
}

.ingredients-list,
.steps-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.ingredient-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.ingredient-row .el-form-item {
  margin-bottom: 0;
}

.step-row {
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.step-number {
  font-weight: 600;
  color: #409EFF;
  min-width: 60px;
  padding-top: 8px;
}
</style>
