import os
import json
import functools
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

# 确保 JSON 响应使用 UTF-8 编码，不转义中文字符
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'database': os.getenv('MYSQL_DATABASE', 'recipe_db'),
    'user': os.getenv('MYSQL_USER', 'recipe_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'recipe_password'),
    'charset': 'utf8mb4',
    'use_unicode': True
}


def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"数据库连接错误: {e}")
        return None


# 错误处理装饰器
def validate_request(required_fields=None, field_types=None):
    """请求参数校验装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if request.method in ['POST', 'PUT']:
                data = request.get_json()
                if not data:
                    return jsonify({'message': '请求体不能为空'}), 400
                
                # 校验必填字段
                if required_fields:
                    for field in required_fields:
                        if field not in data or data[field] is None:
                            return jsonify({'message': f'缺少必填字段: {field}'}), 400
                
                # 校验字段类型
                if field_types:
                    for field, field_type in field_types.items():
                        if field in data and data[field] is not None:
                            if not isinstance(data[field], field_type):
                                type_name = field_type.__name__
                                return jsonify({'message': f'字段 {field} 类型错误，应为 {type_name}'}), 400
                
                # 将校验后的数据传递给视图函数
                kwargs['validated_data'] = data
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 分类相关接口
@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name FROM categories ORDER BY id')
        categories = cursor.fetchall()
        return jsonify(categories)
    finally:
        conn.close()


# 难度相关接口
@app.route('/api/difficulties', methods=['GET'])
def get_difficulties():
    """获取所有难度"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name, level FROM difficulties ORDER BY level')
        difficulties = cursor.fetchall()
        return jsonify(difficulties)
    finally:
        conn.close()


# 单位相关接口
@app.route('/api/units', methods=['GET'])
def get_units():
    """获取所有单位"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name FROM units ORDER BY id')
        units = cursor.fetchall()
        return jsonify(units)
    finally:
        conn.close()


# 食谱相关接口
@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """获取食谱列表（分页+筛选）"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 12, type=int)
        name = request.args.get('name', '')
        category_id = request.args.get('category_id', None, type=int)
        difficulty_id = request.args.get('difficulty_id', None, type=int)
        max_cooking_time = request.args.get('max_cooking_time', None, type=int)
        
        # 构建查询条件
        conditions = []
        params = []
        
        if name:
            conditions.append('r.name LIKE %s')
            params.append(f'%{name}%')
        if category_id:
            conditions.append('r.category_id = %s')
            params.append(category_id)
        if difficulty_id:
            conditions.append('r.difficulty_id = %s')
            params.append(difficulty_id)
        if max_cooking_time:
            conditions.append('r.cooking_time <= %s')
            params.append(max_cooking_time)
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        
        # 查询总数
        count_query = f'''
            SELECT COUNT(*) as total 
            FROM recipes r 
            WHERE {where_clause}
        '''
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # 分页查询
        offset = (page - 1) * page_size
        query = f'''
            SELECT r.*, 
                   c.name as category_name,
                   d.name as difficulty_name,
                   d.level as difficulty_level
            FROM recipes r
            JOIN categories c ON r.category_id = c.id
            JOIN difficulties d ON r.difficulty_id = d.id
            WHERE {where_clause}
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        '''
        cursor.execute(query, params + [page_size, offset])
        recipes = cursor.fetchall()
        
        return jsonify({
            'recipes': recipes,
            'total': total,
            'page': page,
            'page_size': page_size
        })
    finally:
        conn.close()


@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe_detail(recipe_id):
    """获取食谱详情"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 查询食谱基本信息
        query = '''
            SELECT r.*, 
                   c.name as category_name,
                   d.name as difficulty_name,
                   d.level as difficulty_level
            FROM recipes r
            JOIN categories c ON r.category_id = c.id
            JOIN difficulties d ON r.difficulty_id = d.id
            WHERE r.id = %s
        '''
        cursor.execute(query, (recipe_id,))
        recipe = cursor.fetchone()
        
        if not recipe:
            return jsonify({'message': '食谱不存在'}), 404
        
        # 查询食材
        cursor.execute('''
            SELECT i.*, u.name as unit_name
            FROM ingredients i
            JOIN units u ON i.unit_id = u.id
            WHERE i.recipe_id = %s
            ORDER BY i.id
        ''', (recipe_id,))
        ingredients = cursor.fetchall()
        
        recipe['ingredients'] = ingredients
        
        return jsonify(recipe)
    finally:
        conn.close()


@app.route('/api/recipes', methods=['POST'])
@validate_request(
    required_fields=['name', 'category_id', 'difficulty_id', 'cooking_time', 'ingredients'],
    field_types={
        'name': str,
        'category_id': int,
        'difficulty_id': int,
        'cooking_time': int,
        'cover_url': (str, type(None)),
        'ingredients': list,
        'steps': (list, type(None))
    }
)
def create_recipe(validated_data):
    """创建食谱"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 额外的参数校验
        name = validated_data.get('name', '').strip()
        if not name or len(name) > 100:
            return jsonify({'message': '菜名不能为空且长度不能超过100个字符'}), 400
        
        cooking_time = validated_data.get('cooking_time')
        if cooking_time <= 0:
            return jsonify({'message': '烹饪时间必须为正整数'}), 400
        
        ingredients = validated_data.get('ingredients', [])
        if not ingredients or len(ingredients) == 0:
            return jsonify({'message': '食谱至少需要一个食材'}), 400
        
        # 校验分类和难度是否存在
        cursor.execute('SELECT id FROM categories WHERE id = %s', (validated_data['category_id'],))
        if not cursor.fetchone():
            return jsonify({'message': '分类不存在'}), 400
        
        cursor.execute('SELECT id FROM difficulties WHERE id = %s', (validated_data['difficulty_id'],))
        if not cursor.fetchone():
            return jsonify({'message': '难度不存在'}), 400
        
        # 校验食材
        for idx, ing in enumerate(ingredients):
            if not ing.get('name') or not ing.get('name').strip():
                return jsonify({'message': f'第 {idx + 1} 个食材名称不能为空'}), 400
            if 'amount' not in ing or float(ing['amount']) <= 0:
                return jsonify({'message': f'第 {idx + 1} 个食材用量必须大于0'}), 400
            if not ing.get('unit_id'):
                return jsonify({'message': f'第 {idx + 1} 个食材请选择单位'}), 400
            
            # 校验单位是否存在
            cursor.execute('SELECT id FROM units WHERE id = %s', (ing['unit_id'],))
            if not cursor.fetchone():
                return jsonify({'message': f'第 {idx + 1} 个食材单位不存在'}), 400
        
        # 准备步骤数据
        steps = validated_data.get('steps', [])
        steps_json = json.dumps([s.strip() for s in steps if s and s.strip()], ensure_ascii=False) if steps else None
        
        # 插入食谱
        insert_recipe_query = '''
            INSERT INTO recipes (name, category_id, difficulty_id, cooking_time, cover_url, steps)
            VALUES (%s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(insert_recipe_query, (
            name,
            validated_data['category_id'],
            validated_data['difficulty_id'],
            cooking_time,
            validated_data.get('cover_url'),
            steps_json
        ))
        
        recipe_id = cursor.lastrowid
        
        # 插入食材
        insert_ingredient_query = '''
            INSERT INTO ingredients (recipe_id, name, amount, unit_id)
            VALUES (%s, %s, %s, %s)
        '''
        for ing in ingredients:
            cursor.execute(insert_ingredient_query, (
                recipe_id,
                ing['name'].strip(),
                float(ing['amount']),
                ing['unit_id']
            ))
        
        conn.commit()
        
        return jsonify({
            'message': '食谱创建成功',
            'recipe_id': recipe_id
        }), 201
    except Error as e:
        conn.rollback()
        return jsonify({'message': f'创建食谱失败: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/recipes/<int:recipe_id>', methods=['PUT'])
@validate_request(
    required_fields=['name', 'category_id', 'difficulty_id', 'cooking_time', 'ingredients'],
    field_types={
        'name': str,
        'category_id': int,
        'difficulty_id': int,
        'cooking_time': int,
        'cover_url': (str, type(None)),
        'ingredients': list,
        'steps': (list, type(None))
    }
)
def update_recipe(recipe_id, validated_data):
    """更新食谱"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 检查食谱是否存在
        cursor.execute('SELECT id FROM recipes WHERE id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不存在'}), 404
        
        # 额外的参数校验
        name = validated_data.get('name', '').strip()
        if not name or len(name) > 100:
            return jsonify({'message': '菜名不能为空且长度不能超过100个字符'}), 400
        
        cooking_time = validated_data.get('cooking_time')
        if cooking_time <= 0:
            return jsonify({'message': '烹饪时间必须为正整数'}), 400
        
        ingredients = validated_data.get('ingredients', [])
        if not ingredients or len(ingredients) == 0:
            return jsonify({'message': '食谱至少需要一个食材'}), 400
        
        # 校验分类和难度是否存在
        cursor.execute('SELECT id FROM categories WHERE id = %s', (validated_data['category_id'],))
        if not cursor.fetchone():
            return jsonify({'message': '分类不存在'}), 400
        
        cursor.execute('SELECT id FROM difficulties WHERE id = %s', (validated_data['difficulty_id'],))
        if not cursor.fetchone():
            return jsonify({'message': '难度不存在'}), 400
        
        # 校验食材
        for idx, ing in enumerate(ingredients):
            if not ing.get('name') or not ing.get('name').strip():
                return jsonify({'message': f'第 {idx + 1} 个食材名称不能为空'}), 400
            if 'amount' not in ing or float(ing['amount']) <= 0:
                return jsonify({'message': f'第 {idx + 1} 个食材用量必须大于0'}), 400
            if not ing.get('unit_id'):
                return jsonify({'message': f'第 {idx + 1} 个食材请选择单位'}), 400
            
            # 校验单位是否存在
            cursor.execute('SELECT id FROM units WHERE id = %s', (ing['unit_id'],))
            if not cursor.fetchone():
                return jsonify({'message': f'第 {idx + 1} 个食材单位不存在'}), 400
        
        # 准备步骤数据
        steps = validated_data.get('steps', [])
        steps_json = json.dumps([s.strip() for s in steps if s and s.strip()], ensure_ascii=False) if steps else None
        
        # 更新食谱
        update_recipe_query = '''
            UPDATE recipes 
            SET name = %s, category_id = %s, difficulty_id = %s, 
                cooking_time = %s, cover_url = %s, steps = %s
            WHERE id = %s
        '''
        cursor.execute(update_recipe_query, (
            name,
            validated_data['category_id'],
            validated_data['difficulty_id'],
            cooking_time,
            validated_data.get('cover_url'),
            steps_json,
            recipe_id
        ))
        
        # 删除旧食材
        cursor.execute('DELETE FROM ingredients WHERE recipe_id = %s', (recipe_id,))
        
        # 插入新食材
        insert_ingredient_query = '''
            INSERT INTO ingredients (recipe_id, name, amount, unit_id)
            VALUES (%s, %s, %s, %s)
        '''
        for ing in ingredients:
            cursor.execute(insert_ingredient_query, (
                recipe_id,
                ing['name'].strip(),
                float(ing['amount']),
                ing['unit_id']
            ))
        
        conn.commit()
        
        return jsonify({
            'message': '食谱更新成功',
            'recipe_id': recipe_id
        })
    except Error as e:
        conn.rollback()
        return jsonify({'message': f'更新食谱失败: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """删除食谱"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor()
        
        # 检查食谱是否存在
        cursor.execute('SELECT id FROM recipes WHERE id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不存在'}), 404
        
        # 删除食谱（会级联删除食材和菜单关联）
        cursor.execute('DELETE FROM recipes WHERE id = %s', (recipe_id,))
        conn.commit()
        
        return jsonify({'message': '食谱删除成功'})
    except Error as e:
        conn.rollback()
        return jsonify({'message': f'删除食谱失败: {str(e)}'}), 500
    finally:
        conn.close()


# 本周菜单相关接口
@app.route('/api/weekly-menu', methods=['GET'])
def get_weekly_menu():
    """获取本周菜单"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        query = '''
            SELECT wm.id, wm.recipe_id, wm.created_at,
                   r.name, r.category_id, r.cooking_time, r.cover_url,
                   c.name as category_name
            FROM weekly_menu wm
            JOIN recipes r ON wm.recipe_id = r.id
            JOIN categories c ON r.category_id = c.id
            ORDER BY wm.created_at DESC
        '''
        cursor.execute(query)
        menu_items = cursor.fetchall()
        
        return jsonify(menu_items)
    finally:
        conn.close()


@app.route('/api/weekly-menu', methods=['POST'])
@validate_request(
    required_fields=['recipe_id'],
    field_types={'recipe_id': int}
)
def add_to_weekly_menu(validated_data):
    """添加食谱到本周菜单"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        recipe_id = validated_data['recipe_id']
        
        # 检查食谱是否存在
        cursor.execute('SELECT id FROM recipes WHERE id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不存在'}), 404
        
        # 检查是否已在菜单中
        cursor.execute('SELECT id FROM weekly_menu WHERE recipe_id = %s', (recipe_id,))
        if cursor.fetchone():
            return jsonify({'message': '食谱已在菜单中'}), 400
        
        # 添加到菜单
        cursor.execute('INSERT INTO weekly_menu (recipe_id) VALUES (%s)', (recipe_id,))
        conn.commit()
        
        return jsonify({'message': '已添加到本周菜单'}), 201
    except Error as e:
        conn.rollback()
        return jsonify({'message': f'添加到菜单失败: {str(e)}'}), 500
    finally:
        conn.close()


@app.route('/api/weekly-menu/shopping-list', methods=['GET'])
def get_shopping_list():
    """获取购物清单（合并同名食材用量）"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        # 查询所有菜单中的食谱食材，并按食材名称和单位分组汇总
        query = '''
            SELECT 
                i.name,
                i.unit_id,
                u.name as unit_name,
                SUM(i.amount) as total_amount
            FROM ingredients i
            JOIN units u ON i.unit_id = u.id
            JOIN weekly_menu wm ON i.recipe_id = wm.recipe_id
            GROUP BY i.name, i.unit_id, u.name
            ORDER BY i.name
        '''
        cursor.execute(query)
        shopping_list = cursor.fetchall()
        
        # 格式化total_amount
        for item in shopping_list:
            # 如果是整数，显示为整数，否则保留两位小数
            amount = item['total_amount']
            if amount == int(amount):
                item['total_amount'] = int(amount)
            else:
                item['total_amount'] = round(amount, 2)
        
        return jsonify(shopping_list)
    finally:
        conn.close()


@app.route('/api/weekly-menu/<int:recipe_id>', methods=['DELETE'])
def remove_from_weekly_menu(recipe_id):
    """从本周菜单移除食谱"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败'}), 500
    
    try:
        cursor = conn.cursor()
        
        # 检查是否在菜单中
        cursor.execute('SELECT id FROM weekly_menu WHERE recipe_id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不在菜单中'}), 404
        
        # 从菜单移除
        cursor.execute('DELETE FROM weekly_menu WHERE recipe_id = %s', (recipe_id,))
        conn.commit()
        
        return jsonify({'message': '已从菜单中移除'})
    except Error as e:
        conn.rollback()
        return jsonify({'message': f'从菜单移除失败: {str(e)}'}), 500
    finally:
        conn.close()


# 健康检查接口
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': '服务运行正常'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
