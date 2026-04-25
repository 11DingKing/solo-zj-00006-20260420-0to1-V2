import { createRouter, createWebHistory } from 'vue-router'
import RecipeList from '../views/RecipeList.vue'
import RecipeDetail from '../views/RecipeDetail.vue'
import CreateRecipe from '../views/CreateRecipe.vue'
import ShoppingList from '../views/ShoppingList.vue'

const routes = [
  {
    path: '/',
    name: 'RecipeList',
    component: RecipeList
  },
  {
    path: '/recipe/:id',
    name: 'RecipeDetail',
    component: RecipeDetail
  },
  {
    path: '/create',
    name: 'CreateRecipe',
    component: CreateRecipe
  },
  {
    path: '/edit/:id',
    name: 'EditRecipe',
    component: CreateRecipe
  },
  {
    path: '/shopping-list',
    name: 'ShoppingList',
    component: ShoppingList
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
