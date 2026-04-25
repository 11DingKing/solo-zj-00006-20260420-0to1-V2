<template>
  <div class="app-container">
    <el-container>
      <el-header class="header">
        <div class="logo">
          <el-icon :size="30"><Food /></el-icon>
          <span class="title">食谱管理平台</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          background-color="transparent"
          text-color="#606266"
          active-text-color="#409EFF"
          router
        >
          <el-menu-item index="/">
            <el-icon><List /></el-icon>
            <span>食谱列表</span>
          </el-menu-item>
          <el-menu-item index="/create">
            <el-icon><Plus /></el-icon>
            <span>创建食谱</span>
          </el-menu-item>
          <el-menu-item index="/shopping-list">
            <el-icon><ShoppingCart /></el-icon>
            <span>购物清单</span>
          </el-menu-item>
        </el-menu>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Food, List, Plus, ShoppingCart } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
  background-color: #f5f7fa;
}

.app-container {
  min-height: 100vh;
}

.header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.el-menu {
  border-bottom: none;
}

.main-content {
  padding: 20px;
}
</style>
