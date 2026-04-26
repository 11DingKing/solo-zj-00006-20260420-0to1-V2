<template>
  <div class="shopping-list">
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <h2>购物清单</h2>
          <div class="header-actions">
            <el-button 
              type="danger" 
              @click="handleClearPurchased" 
              :disabled="purchasedCount === 0"
            >
              <el-icon><Delete /></el-icon>
              清空已购 ({{ purchasedCount }})
            </el-button>
          </div>
        </div>
      </template>
      
      <el-form :inline="true" :model="addForm" class="add-form" @submit.prevent="handleAddCustom">
        <el-form-item label="食材名称">
          <el-input
            v-model="addForm.name"
            placeholder="请输入食材名称"
            clearable
            style="width: 180px"
          />
        </el-form-item>
        <el-form-item label="用量">
          <el-input-number
            v-model="addForm.amount"
            :min="0.1"
            :step="1"
            :precision="2"
            style="width: 120px"
          />
        </el-form-item>
        <el-form-item label="单位">
          <el-input
            v-model="addForm.unit_name"
            placeholder="如：个、克、毫升"
            clearable
            style="width: 120px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAddCustom">
            <el-icon><Plus /></el-icon>
            添加
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="list-content">
        <div v-if="shoppingItems.length === 0" class="empty-state">
          <el-empty description="购物清单为空">
            <template #image>
              <el-icon :size="60" color="#909399"><ShoppingCart /></el-icon>
            </template>
            <el-button type="primary" @click="goToRecipes">
              去添加食谱
            </el-button>
          </el-empty>
        </div>
        
        <div v-else>
          <div v-if="unpurchasedItems.length > 0" class="items-section">
            <h3 class="section-title">未购买 ({{ unpurchasedItems.length }})</h3>
            <div class="items-list">
              <div 
                v-for="item in unpurchasedItems" 
                :key="item.id" 
                class="item-card"
              >
                <div class="item-content">
                  <el-checkbox 
                    v-model="item.is_purchased" 
                    @change="handleTogglePurchased(item)"
                  />
                  <span class="item-info">
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-amount">{{ item.amount }} {{ item.unit_name }}</span>
                  </span>
                </div>
                <el-button 
                  type="danger" 
                  :icon="Delete" 
                  circle 
                  size="small"
                  @click="handleDeleteItem(item.id)"
                />
              </div>
            </div>
          </div>
          
          <div v-if="purchasedItems.length > 0" class="items-section">
            <h3 class="section-title purchased-title">已购买 ({{ purchasedItems.length }})</h3>
            <div class="items-list">
              <div 
                v-for="item in purchasedItems" 
                :key="item.id" 
                class="item-card purchased-item"
              >
                <div class="item-content">
                  <el-checkbox 
                    v-model="item.is_purchased" 
                    @change="handleTogglePurchased(item)"
                  />
                  <span class="item-info">
                    <span class="item-name">{{ item.name }}</span>
                    <span class="item-amount">{{ item.amount }} {{ item.unit_name }}</span>
                  </span>
                </div>
                <el-button 
                  type="danger" 
                  :icon="Delete" 
                  circle 
                  size="small"
                  @click="handleDeleteItem(item.id)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ShoppingCart, Plus, Delete } from '@element-plus/icons-vue'
import { shoppingListApi } from '@/api'

const router = useRouter()

const shoppingItems = ref<any[]>([])

const addForm = ref({
  name: '',
  amount: 1,
  unit_name: ''
})

const unpurchasedItems = computed(() => {
  return shoppingItems.value.filter(item => !item.is_purchased)
})

const purchasedItems = computed(() => {
  return shoppingItems.value.filter(item => item.is_purchased)
})

const purchasedCount = computed(() => purchasedItems.value.length)

const getShoppingList = async () => {
  try {
    const res = await shoppingListApi.getList()
    shoppingItems.value = res.data
  } catch (error) {
    console.error('获取购物清单失败', error)
    ElMessage.error('获取购物清单失败')
  }
}

const handleTogglePurchased = async (item: any) => {
  try {
    const res = await shoppingListApi.togglePurchased(item.id)
    item.is_purchased = res.data.is_purchased
    shoppingItems.value.sort((a, b) => {
      if (a.is_purchased === b.is_purchased) return 0
      return a.is_purchased ? 1 : -1
    })
  } catch (error) {
    console.error('更新状态失败', error)
    ElMessage.error('更新状态失败')
    item.is_purchased = !item.is_purchased
  }
}

const handleDeleteItem = async (itemId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此项吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await shoppingListApi.delete(itemId)
    shoppingItems.value = shoppingItems.value.filter(item => item.id !== itemId)
    ElMessage.success('已删除')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleClearPurchased = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有已购买的项目吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    const res = await shoppingListApi.clearPurchased()
    shoppingItems.value = shoppingItems.value.filter(item => !item.is_purchased)
    ElMessage.success(res.data.message)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('清空失败')
    }
  }
}

const handleAddCustom = async () => {
  if (!addForm.value.name.trim()) {
    ElMessage.warning('请输入食材名称')
    return
  }
  if (!addForm.value.unit_name.trim()) {
    ElMessage.warning('请输入单位')
    return
  }
  
  try {
    await shoppingListApi.addCustom({
      name: addForm.value.name.trim(),
      amount: addForm.value.amount,
      unit_name: addForm.value.unit_name.trim()
    })
    ElMessage.success('已添加到购物清单')
    addForm.value.name = ''
    addForm.value.amount = 1
    addForm.value.unit_name = ''
    getShoppingList()
  } catch (error) {
    console.error('添加失败', error)
    ElMessage.error('添加失败')
  }
}

const goToRecipes = () => {
  router.push('/')
}

onMounted(() => {
  getShoppingList()
})
</script>

<style scoped>
.shopping-list {
  max-width: 1000px;
  margin: 0 auto;
}

.list-card {
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

.add-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.add-form .el-form-item {
  margin-bottom: 0;
}

.list-content {
  min-height: 200px;
}

.empty-state {
  padding: 40px 0;
}

.items-section {
  margin-bottom: 30px;
}

.section-title {
  margin-bottom: 15px;
  color: #303133;
  border-left: 4px solid #409EFF;
  padding-left: 10px;
  font-size: 16px;
}

.purchased-title {
  border-left-color: #909399;
  color: #909399;
}

.items-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.item-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.item-card:hover {
  background-color: #ecf5ff;
}

.purchased-item {
  background-color: #fafafa;
  opacity: 0.7;
}

.purchased-item:hover {
  background-color: #f0f0f0;
}

.item-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-name {
  font-size: 15px;
  color: #303133;
  font-weight: 500;
}

.purchased-item .item-name {
  text-decoration: line-through;
  color: #909399;
}

.item-amount {
  font-size: 14px;
  color: #606266;
  background-color: #e6e6e6;
  padding: 2px 8px;
  border-radius: 4px;
}

.purchased-item .item-amount {
  text-decoration: line-through;
  color: #909399;
}
</style>
