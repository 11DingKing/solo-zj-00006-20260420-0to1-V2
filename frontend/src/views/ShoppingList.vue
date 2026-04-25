<template>
  <div class="shopping-list">
    <el-card class="menu-card">
      <template #header>
        <div class="card-header">
          <h2>本周菜单</h2>
          <div class="header-actions">
            <el-button type="primary" @click="exportShoppingList" :disabled="shoppingList.length === 0">
              <el-icon><Download /></el-icon>
              导出购物清单
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="menuRecipes.length === 0" class="empty-state">
        <el-empty description="暂无菜单，请从食谱列表添加食谱到本周菜单">
          <template #image>
            <el-icon :size="60" color="#909399"><ShoppingCart /></el-icon>
          </template>
          <el-button type="primary" @click="goToRecipes">
            去添加食谱
          </el-button>
        </el-empty>
      </div>
      
      <div v-else>
        <el-row :gutter="20">
          <el-col :span="12">
            <h3>已选食谱</h3>
            <el-table :data="menuRecipes" border style="width: 100%">
              <el-table-column prop="name" label="食谱名称">
                <template #default="scope">
                  <el-link type="primary" @click="viewRecipe(scope.row.id)">
                    {{ scope.row.name }}
                  </el-link>
                </template>
              </el-table-column>
              <el-table-column prop="category_name" label="分类" width="100" />
              <el-table-column prop="cooking_time" label="烹饪时间" width="100">
                <template #default="scope">
                  {{ scope.row.cooking_time }} 分钟
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="scope">
                  <el-button
                    type="danger"
                    :icon="Delete"
                    circle
                    size="small"
                    @click="removeFromMenu(scope.row.recipe_id)"
                  />
                </template>
              </el-table-column>
            </el-table>
          </el-col>
          
          <el-col :span="12">
            <h3>购物清单（已合并食材用量）</h3>
            <el-table :data="shoppingList" border style="width: 100%">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="name" label="食材名称" />
              <el-table-column prop="total_amount" label="总用量" width="120">
                <template #default="scope">
                  {{ scope.row.total_amount }}
                </template>
              </el-table-column>
              <el-table-column prop="unit_name" label="单位" width="80" />
            </el-table>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ShoppingCart, Download, Delete } from '@element-plus/icons-vue'
import { weeklyMenuApi } from '@/api'

const router = useRouter()

const menuRecipes = ref<any[]>([])
const shoppingList = ref<any[]>([])

const getWeeklyMenu = async () => {
  try {
    const res = await weeklyMenuApi.getAll()
    menuRecipes.value = res.data
  } catch (error) {
    console.error('获取本周菜单失败', error)
    ElMessage.error('获取本周菜单失败')
  }
}

const getShoppingList = async () => {
  try {
    const res = await weeklyMenuApi.getShoppingList()
    shoppingList.value = res.data
  } catch (error) {
    console.error('获取购物清单失败', error)
    ElMessage.error('获取购物清单失败')
  }
}

const removeFromMenu = async (recipeId: number) => {
  try {
    await ElMessageBox.confirm('确定要从菜单中移除该食谱吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await weeklyMenuApi.remove(recipeId)
    ElMessage.success('已从菜单中移除')
    getWeeklyMenu()
    getShoppingList()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  }
}

const viewRecipe = (id: number) => {
  router.push(`/recipe/${id}`)
}

const goToRecipes = () => {
  router.push('/')
}

const exportShoppingList = () => {
  if (shoppingList.value.length === 0) return
  
  let content = '=== 购物清单 ===\n\n'
  content += '已选食谱：\n'
  menuRecipes.value.forEach((recipe, index) => {
    content += `${index + 1}. ${recipe.name}\n`
  })
  
  content += '\n食材清单：\n'
  shoppingList.value.forEach((item, index) => {
    content += `${index + 1}. ${item.name}: ${item.total_amount} ${item.unit_name}\n`
  })
  
  // 创建Blob并下载
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `购物清单_${new Date().toISOString().split('T')[0]}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('购物清单已导出')
}

onMounted(() => {
  getWeeklyMenu()
  getShoppingList()
})
</script>

<style scoped>
.shopping-list {
  max-width: 1400px;
  margin: 0 auto;
}

.menu-card {
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

.empty-state {
  padding: 40px 0;
}

h3 {
  margin-bottom: 15px;
  color: #303133;
  border-left: 4px solid #409EFF;
  padding-left: 10px;
}
</style>
