import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 分类相关接口
export const categoryApi = {
  getAll: () => api.get("/categories"),
};

// 难度相关接口
export const difficultyApi = {
  getAll: () => api.get("/difficulties"),
};

// 单位相关接口
export const unitApi = {
  getAll: () => api.get("/units"),
};

// 食谱相关接口
export const recipeApi = {
  getList: (params: any) => api.get("/recipes", { params }),
  getById: (id: number) => api.get(`/recipes/${id}`),
  create: (data: any) => api.post("/recipes", data),
  update: (id: number, data: any) => api.put(`/recipes/${id}`, data),
  delete: (id: number) => api.delete(`/recipes/${id}`),
};

// 本周菜单相关接口
export const weeklyMenuApi = {
  getAll: () => api.get("/weekly-menu"),
  add: (recipeId: number) => api.post("/weekly-menu", { recipe_id: recipeId }),
  remove: (recipeId: number) => api.delete(`/weekly-menu/${recipeId}`),
  getShoppingList: () => api.get("/weekly-menu/shopping-list"),
};

// 购物清单相关接口（新版）
export const shoppingListApi = {
  getList: (isPurchased?: boolean) => {
    const params: any = {};
    if (isPurchased !== undefined) {
      params.is_purchased = isPurchased;
    }
    return api.get("/shopping-list", { params });
  },
  addFromRecipe: (recipeId: number) =>
    api.post(`/shopping-list/from-recipe/${recipeId}`),
  addCustom: (data: { name: string; amount: number; unit_name: string }) =>
    api.post("/shopping-list/add", data),
  togglePurchased: (itemId: number) =>
    api.put(`/shopping-items/${itemId}/toggle`),
  delete: (itemId: number) => api.delete(`/shopping-items/${itemId}`),
  clearPurchased: () => api.delete("/shopping-list/purchased"),
};

export default api;
