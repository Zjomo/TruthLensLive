# 访问数据库，并开放本地的3001端口，供dify的http请求，以访问本地数据库，实现本地知识库的检索功能

from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

# 数据库连接配置
config = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'port': 3306,
    'database': 'RAG',
    'raise_on_warnings': True,
    'charset': 'utf8mb4'  # 添加字符集配置
}

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 启用CORS支持
app.config['JSON_AS_ASCII'] = False  # 确保JSON响应中的中文不会被转义
app.json.ensure_ascii = False  # Flask 2.x版本使用这个配置


# 连接数据库
def connect_to_database():
    try:
        conn = mysql.connector.connect(**config)
        print("Connected to MySQL database")
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


# 执行SQL查询
def execute_query(conn, sql):
    cursor = conn.cursor(dictionary=True, buffered=True)  # 使用dictionary=True来返回字典格式的结果
    try:
        cursor.execute(sql)
        if sql.strip().lower().startswith("select"):
            # 如果是查询操作，返回结果
            result = cursor.fetchall()
            return result
        else:
            # 如果是插入、更新、删除操作，提交事务并返回受影响的行数
            conn.commit()
            return cursor.rowcount
    except mysql.connector.Error as err:
        error_msg = {
            "error_code": err.errno,
            "error_message": str(err),
            "sql_state": err.sqlstate if hasattr(err, 'sqlstate') else None
        }
        print(f"数据库错误: {error_msg}")
        raise Exception(error_msg)
    finally:
        cursor.close()


# HTTP接口：执行SQL -- 返回给dify作为数据库 -- 实现知识检索
@app.route('/execute', methods=['POST'])
def execute_sql():
    try:
        # 获取请求中的SQL语句
        data = request.get_json()
        if not data or 'sql' not in data:
            return jsonify({"error": "SQL语句是必需的"}), 400

        sql = data['sql']
        conn = connect_to_database()
        if not conn:
            return jsonify({"error": "无法连接到数据库"}), 500

        try:
            # 执行SQL
            result = execute_query(conn, sql)
            return jsonify({"result": result})
        except Exception as e:
            # 如果是数据库错误，返回详细的错误信息
            if isinstance(e.args[0], dict):
                return jsonify({"error": e.args[0]}), 500
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 启动Flask应用
if __name__ == '__main__':
    # 启动Flask应用
    app.run(host='127.0.0.1', port=3001, debug=True)