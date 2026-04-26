import os
import json
import functools
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)

app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'database': os.getenv('MYSQL_DATABASE', 'recipe_db'),
    'user': os.getenv('MYSQL_USER', 'recipe_user'),
    'password': os.getenv('MYSQL_PASSWORD', 'recipe_password'),
    'charset': 'utf8mb4',
    'use_unicode': True
}

MAX_RETRIES = 30
RETRY_INTERVAL = 2


def get_db_connection():
    """获取数据库连接（带重试机制）"""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if attempt > 0:
                print(f"[DB] 数据库连接成功（第 {attempt + 1} 次尝试）")
            return connection
        except Error as e:
            last_error = e
            if attempt == 0:
                print(f"[DB] 首次连接失败: {str(e)}")
                print(f"[DB] 数据库配置: host={DB_CONFIG['host']}, port={DB_CONFIG['port']}, database={DB_CONFIG['database']}")
            print(f"[DB] 等待 {RETRY_INTERVAL} 秒后重试...（第 {attempt + 1}/{MAX_RETRIES} 次）")
            time.sleep(RETRY_INTERVAL)
    
    print(f"[DB] 数据库连接失败，已重试 {MAX_RETRIES} 次。最后错误: {str(last_error)}")
    return None


def validate_request(required_fields=None, field_types=None):
    """请求参数校验装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if request.method in ['POST', 'PUT']:
                data = request.get_json()
                if not data:
                    return jsonify({'message': '请求体不能为空'}), 400
                
                if required_fields:
                    for field in required_fields:
                        if field not in data or data[field] is None:
                            return jsonify({'message': f'缺少必填字段: {field}'}), 400
                
                if field_types:
                    for field, field_type in field_types.items():
                        if field in data and data[field] is not None:
                            if not isinstance(data[field], field_type):
                                type_name = field_type.__name__
                                return jsonify({'message': f'字段 {field} 类型错误，应为 {type_name}'}), 400
                
                kwargs['validated_data'] = data
            return func(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """获取所有分类"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name FROM categories ORDER BY id')
        categories = cursor.fetchall()
        return jsonify(categories)
    except Error as e:
        print(f"[ERROR] get_categories SQL错误: {str(e)}")
        return jsonify({'message': f'查询分类失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/difficulties', methods=['GET'])
def get_difficulties():
    """获取所有难度"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name, level FROM difficulties ORDER BY level')
        difficulties = cursor.fetchall()
        return jsonify(difficulties)
    except Error as e:
        print(f"[ERROR] get_difficulties SQL错误: {str(e)}")
        return jsonify({'message': f'查询难度失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/units', methods=['GET'])
def get_units():
    """获取所有单位"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, name FROM units ORDER BY id')
        units = cursor.fetchall()
        return jsonify(units)
    except Error as e:
        print(f"[ERROR] get_units SQL错误: {str(e)}")
        return jsonify({'message': f'查询单位失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/recipes', methods=['GET'])
def get_recipes():
    """获取食谱列表（分页+筛选）"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 12, type=int)
        name = request.args.get('name', '')
        category_id = request.args.get('category_id', None, type=int)
        difficulty_id = request.args.get('difficulty_id', None, type=int)
        max_cooking_time = request.args.get('max_cooking_time', None, type=int)
        
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
        
        count_query = f'''
            SELECT COUNT(*) as total 
            FROM recipes r 
            WHERE {where_clause}
        '''
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
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
    except Error as e:
        print(f"[ERROR] get_recipes SQL错误: {str(e)}")
        return jsonify({'message': f'查询食谱列表失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe_detail(recipe_id):
    """获取食谱详情"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
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
    except Error as e:
        print(f"[ERROR] get_recipe_detail SQL错误: {str(e)}")
        return jsonify({'message': f'查询食谱详情失败: {str(e)}'}), 500
    finally:
        if conn:
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
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        name = validated_data.get('name', '').strip()
        if not name or len(name) > 100:
            return jsonify({'message': '菜名不能为空且长度不能超过100个字符'}), 400
        
        cooking_time = validated_data.get('cooking_time')
        if cooking_time <= 0:
            return jsonify({'message': '烹饪时间必须为正整数'}), 400
        
        ingredients = validated_data.get('ingredients', [])
        if not ingredients or len(ingredients) == 0:
            return jsonify({'message': '食谱至少需要一个食材'}), 400
        
        cursor.execute('SELECT id FROM categories WHERE id = %s', (validated_data['category_id'],))
        if not cursor.fetchone():
            return jsonify({'message': '分类不存在'}), 400
        
        cursor.execute('SELECT id FROM difficulties WHERE id = %s', (validated_data['difficulty_id'],))
        if not cursor.fetchone():
            return jsonify({'message': '难度不存在'}), 400
        
        for idx, ing in enumerate(ingredients):
            if not ing.get('name') or not ing.get('name').strip():
                return jsonify({'message': f'第 {idx + 1} 个食材名称不能为空'}), 400
            if 'amount' not in ing or float(ing['amount']) <= 0:
                return jsonify({'message': f'第 {idx + 1} 个食材用量必须大于0'}), 400
            if not ing.get('unit_id'):
                return jsonify({'message': f'第 {idx + 1} 个食材请选择单位'}), 400
            
            cursor.execute('SELECT id FROM units WHERE id = %s', (ing['unit_id'],))
            if not cursor.fetchone():
                return jsonify({'message': f'第 {idx + 1} 个食材单位不存在'}), 400
        
        steps = validated_data.get('steps', [])
        steps_json = json.dumps([s.strip() for s in steps if s and s.strip()], ensure_ascii=False) if steps else None
        
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
        print(f"[ERROR] create_recipe SQL错误: {str(e)}")
        return jsonify({'message': f'创建食谱失败: {str(e)}'}), 500
    finally:
        if conn:
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
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT id FROM recipes WHERE id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不存在'}), 404
        
        name = validated_data.get('name', '').strip()
        if not name or len(name) > 100:
            return jsonify({'message': '菜名不能为空且长度不能超过100个字符'}), 400
        
        cooking_time = validated_data.get('cooking_time')
        if cooking_time <= 0:
            return jsonify({'message': '烹饪时间必须为正整数'}), 400
        
        ingredients = validated_data.get('ingredients', [])
        if not ingredients or len(ingredients) == 0:
            return jsonify({'message': '食谱至少需要一个食材'}), 400
        
        cursor.execute('SELECT id FROM categories WHERE id = %s', (validated_data['category_id'],))
        if not cursor.fetchone():
            return jsonify({'message': '分类不存在'}), 400
        
        cursor.execute('SELECT id FROM difficulties WHERE id = %s', (validated_data['difficulty_id'],))
        if not cursor.fetchone():
            return jsonify({'message': '难度不存在'}), 400
        
        for idx, ing in enumerate(ingredients):
            if not ing.get('name') or not ing.get('name').strip():
                return jsonify({'message': f'第 {idx + 1} 个食材名称不能为空'}), 400
            if 'amount' not in ing or float(ing['amount']) <= 0:
                return jsonify({'message': f'第 {idx + 1} 个食材用量必须大于0'}), 400
            if not ing.get('unit_id'):
                return jsonify({'message': f'第 {idx + 1} 个食材请选择单位'}), 400
            
            cursor.execute('SELECT id FROM units WHERE id = %s', (ing['unit_id'],))
            if not cursor.fetchone():
                return jsonify({'message': f'第 {idx + 1} 个食材单位不存在'}), 400
        
        steps = validated_data.get('steps', [])
        steps_json = json.dumps([s.strip() for s in steps if s and s.strip()], ensure_ascii=False) if steps else None
        
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
        
        cursor.execute('DELETE FROM ingredients WHERE recipe_id = %s', (recipe_id,))
        
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
        print(f"[ERROR] update_recipe SQL错误: {str(e)}")
        return jsonify({'message': f'更新食谱失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
def delete_recipe(recipe_id):
    """删除食谱"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM recipes WHERE id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不存在'}), 404
        
        cursor.execute('DELETE FROM recipes WHERE id = %s', (recipe_id,))
        conn.commit()
        
        return jsonify({'message': '食谱删除成功'})
    except Error as e:
        conn.rollback()
        print(f"[ERROR] delete_recipe SQL错误: {str(e)}")
        return jsonify({'message': f'删除食谱失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/weekly-menu', methods=['GET'])
def get_weekly_menu():
    """获取本周菜单"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
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
    except Error as e:
        print(f"[ERROR] get_weekly_menu SQL错误: {str(e)}")
        return jsonify({'message': f'查询本周菜单失败: {str(e)}'}), 500
    finally:
        if conn:
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
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        recipe_id = validated_data['recipe_id']
        
        cursor.execute('SELECT id FROM recipes WHERE id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不存在'}), 404
        
        cursor.execute('SELECT id FROM weekly_menu WHERE recipe_id = %s', (recipe_id,))
        if cursor.fetchone():
            return jsonify({'message': '食谱已在菜单中'}), 400
        
        cursor.execute('INSERT INTO weekly_menu (recipe_id) VALUES (%s)', (recipe_id,))
        conn.commit()
        
        return jsonify({'message': '已添加到本周菜单'}), 201
    except Error as e:
        conn.rollback()
        print(f"[ERROR] add_to_weekly_menu SQL错误: {str(e)}")
        return jsonify({'message': f'添加到菜单失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/weekly-menu/shopping-list', methods=['GET'])
def get_shopping_list():
    """获取购物清单（合并同名食材用量）"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
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
        
        for item in shopping_list:
            amount = item['total_amount']
            if amount == int(amount):
                item['total_amount'] = int(amount)
            else:
                item['total_amount'] = round(amount, 2)
        
        return jsonify(shopping_list)
    except Error as e:
        print(f"[ERROR] get_shopping_list SQL错误: {str(e)}")
        return jsonify({'message': f'查询购物清单失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


CURRENT_USER_ID = 1


@app.route('/api/shopping-list', methods=['GET'])
def get_shopping_list_v2():
    """获取当前用户的购物清单（支持按已购/未购筛选）"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        is_purchased = request.args.get('is_purchased', None)
        
        conditions = ['user_id = %s']
        params = [CURRENT_USER_ID]
        
        if is_purchased is not None:
            conditions.append('is_purchased = %s')
            params.append(1 if is_purchased in ['1', 'true', 'True', True] else 0)
        
        where_clause = ' AND '.join(conditions)
        
        query = f'''
            SELECT id, name, amount, unit_name, is_purchased, recipe_id, created_at
            FROM shopping_items
            WHERE {where_clause}
            ORDER BY is_purchased ASC, created_at DESC
        '''
        cursor.execute(query, params)
        items = cursor.fetchall()
        
        for item in items:
            amount = item['amount']
            if amount == int(amount):
                item['amount'] = int(amount)
            else:
                item['amount'] = round(amount, 2)
        
        return jsonify(items)
    except Error as e:
        print(f"[ERROR] get_shopping_list_v2 SQL错误: {str(e)}")
        return jsonify({'message': f'查询购物清单失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/shopping-list/from-recipe/<int:recipe_id>', methods=['POST'])
def add_recipe_to_shopping_list(recipe_id):
    """从食谱一键生成购物清单"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('SELECT id FROM recipes WHERE id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不存在'}), 404
        
        cursor.execute('''
            SELECT i.name, i.amount, u.name as unit_name
            FROM ingredients i
            JOIN units u ON i.unit_id = u.id
            WHERE i.recipe_id = %s
        ''', (recipe_id,))
        ingredients = cursor.fetchall()
        
        if not ingredients:
            return jsonify({'message': '该食谱没有食材'}), 400
        
        added_count = 0
        merged_count = 0
        
        for ing in ingredients:
            cursor.execute('''
                SELECT id, amount FROM shopping_items
                WHERE user_id = %s AND name = %s AND unit_name = %s AND is_purchased = 0
            ''', (CURRENT_USER_ID, ing['name'], ing['unit_name']))
            existing_item = cursor.fetchone()
            
            if existing_item:
                new_amount = existing_item['amount'] + ing['amount']
                cursor.execute('''
                    UPDATE shopping_items SET amount = %s WHERE id = %s
                ''', (new_amount, existing_item['id']))
                merged_count += 1
            else:
                cursor.execute('''
                    INSERT INTO shopping_items (user_id, name, amount, unit_name, recipe_id, is_purchased)
                    VALUES (%s, %s, %s, %s, %s, 0)
                ''', (CURRENT_USER_ID, ing['name'], ing['amount'], ing['unit_name'], recipe_id))
                added_count += 1
        
        conn.commit()
        
        return jsonify({
            'message': '已加入购物清单',
            'added_count': added_count,
            'merged_count': merged_count
        }), 201
    except Error as e:
        conn.rollback()
        print(f"[ERROR] add_recipe_to_shopping_list SQL错误: {str(e)}")
        return jsonify({'message': f'加入购物清单失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/shopping-list/add', methods=['POST'])
@validate_request(
    required_fields=['name', 'amount', 'unit_name'],
    field_types={
        'name': str,
        'amount': (int, float),
        'unit_name': str
    }
)
def add_custom_item(validated_data):
    """手动添加自定义清单项"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        name = validated_data.get('name', '').strip()
        amount = validated_data.get('amount')
        unit_name = validated_data.get('unit_name', '').strip()
        
        if not name:
            return jsonify({'message': '食材名称不能为空'}), 400
        if amount <= 0:
            return jsonify({'message': '用量必须大于0'}), 400
        if not unit_name:
            return jsonify({'message': '单位不能为空'}), 400
        
        cursor.execute('''
            SELECT id, amount FROM shopping_items
            WHERE user_id = %s AND name = %s AND unit_name = %s AND is_purchased = 0
        ''', (CURRENT_USER_ID, name, unit_name))
        existing_item = cursor.fetchone()
        
        if existing_item:
            new_amount = existing_item['amount'] + amount
            cursor.execute('''
                UPDATE shopping_items SET amount = %s WHERE id = %s
            ''', (new_amount, existing_item['id']))
            conn.commit()
            return jsonify({
                'message': '已添加到购物清单（合并数量）',
                'id': existing_item['id']
            })
        else:
            cursor.execute('''
                INSERT INTO shopping_items (user_id, name, amount, unit_name, is_purchased)
                VALUES (%s, %s, %s, %s, 0)
            ''', (CURRENT_USER_ID, name, amount, unit_name))
            conn.commit()
            return jsonify({
                'message': '已添加到购物清单',
                'id': cursor.lastrowid
            }), 201
    except Error as e:
        conn.rollback()
        print(f"[ERROR] add_custom_item SQL错误: {str(e)}")
        return jsonify({'message': f'添加失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/shopping-items/<int:item_id>/toggle', methods=['PUT'])
def toggle_item_purchased(item_id):
    """勾选/取消勾选已购买状态"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT id, is_purchased FROM shopping_items
            WHERE id = %s AND user_id = %s
        ''', (item_id, CURRENT_USER_ID))
        item = cursor.fetchone()
        
        if not item:
            return jsonify({'message': '清单项不存在'}), 404
        
        new_status = 0 if item['is_purchased'] else 1
        cursor.execute('''
            UPDATE shopping_items SET is_purchased = %s WHERE id = %s
        ''', (new_status, item_id))
        conn.commit()
        
        return jsonify({
            'message': '状态已更新',
            'is_purchased': bool(new_status)
        })
    except Error as e:
        conn.rollback()
        print(f"[ERROR] toggle_item_purchased SQL错误: {str(e)}")
        return jsonify({'message': f'更新失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/shopping-items/<int:item_id>', methods=['DELETE'])
def delete_shopping_item(item_id):
    """删除清单项"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            SELECT id FROM shopping_items
            WHERE id = %s AND user_id = %s
        ''', (item_id, CURRENT_USER_ID))
        if not cursor.fetchone():
            return jsonify({'message': '清单项不存在'}), 404
        
        cursor.execute('DELETE FROM shopping_items WHERE id = %s', (item_id,))
        conn.commit()
        
        return jsonify({'message': '已删除'})
    except Error as e:
        conn.rollback()
        print(f"[ERROR] delete_shopping_item SQL错误: {str(e)}")
        return jsonify({'message': f'删除失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/shopping-list/purchased', methods=['DELETE'])
def clear_purchased_items():
    """清空已购买项"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute('''
            DELETE FROM shopping_items
            WHERE user_id = %s AND is_purchased = 1
        ''', (CURRENT_USER_ID,))
        deleted_count = cursor.rowcount
        conn.commit()
        
        return jsonify({
            'message': f'已清空 {deleted_count} 项已购商品',
            'deleted_count': deleted_count
        })
    except Error as e:
        conn.rollback()
        print(f"[ERROR] clear_purchased_items SQL错误: {str(e)}")
        return jsonify({'message': f'清空失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/weekly-menu/<int:recipe_id>', methods=['DELETE'])
def remove_from_weekly_menu(recipe_id):
    """从本周菜单移除食谱"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': '数据库连接失败，请稍后重试'}), 500
    
    try:
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM weekly_menu WHERE recipe_id = %s', (recipe_id,))
        if not cursor.fetchone():
            return jsonify({'message': '食谱不在菜单中'}), 404
        
        cursor.execute('DELETE FROM weekly_menu WHERE recipe_id = %s', (recipe_id,))
        conn.commit()
        
        return jsonify({'message': '已从菜单中移除'})
    except Error as e:
        conn.rollback()
        print(f"[ERROR] remove_from_weekly_menu SQL错误: {str(e)}")
        return jsonify({'message': f'从菜单移除失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'status': 'error', 'message': '数据库连接失败'}), 500
    conn.close()
    return jsonify({'status': 'ok', 'message': '服务运行正常'})


if __name__ == '__main__':
    print(f"[INIT] 启动 Flask 应用，数据库配置:")
    print(f"  host: {DB_CONFIG['host']}")
    print(f"  port: {DB_CONFIG['port']}")
    print(f"  database: {DB_CONFIG['database']}")
    print(f"  user: {DB_CONFIG['user']}")
    app.run(host='0.0.0.0', port=5000, debug=True)
