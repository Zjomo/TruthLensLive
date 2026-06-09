from flask import render_template, Flask, send_from_directory, abort
import mysql.connector
import os

app = Flask(__name__)

# 数据库配置
config = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'port': 3306,
    'database': 'RAG',
    'raise_on_warnings': True,
    'charset': 'utf8mb4'
}

# 指定图片所在的文件夹 -- 展品、人脸
IMAGE_FOLDER = r'E:\0_My_Project\AI_History_Server\Exhibit_Intr\Image'
IMAGE_FOLDER_face = r'E:\0_My_Project\Face_recognition\Data\Face'


def get_exhibits():
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, exhibit_name, description, image_url FROM exhibits_1")
        exhibits = cursor.fetchall()
        return exhibits
    except mysql.connector.Error as err:
        print(f"数据库错误: {err}")
        return []
    finally:
        cursor.close()
        conn.close()


@app.route('/')
def index():
    exhibits = get_exhibits()
    return render_template('index.html', exhibits=exhibits)


@app.route('/download/<filename>', methods=['GET'])
def download_image(filename):
    # 确保文件夹存在
    if not os.path.exists(IMAGE_FOLDER):
        abort(404, description="Image folder not found.")

    # 检查文件是否存在
    file_path = os.path.join(IMAGE_FOLDER, filename)
    if not os.path.isfile(file_path):
        abort(404, description="Image not found.")

    # 返回文件给用户下载
    return send_from_directory(IMAGE_FOLDER, filename)


@app.route('/downloadface/<filename>', methods=['GET'])
def download_image2(filename):
    # 确保文件夹存在
    if not os.path.exists(IMAGE_FOLDER_face):
        abort(404, description="Image folder not found.")

    # 检查文件是否存在
    file_path = os.path.join(IMAGE_FOLDER_face, filename)
    if not os.path.isfile(file_path):
        abort(404, description="Image not found.")

    # 返回文件给用户下载
    return send_from_directory(IMAGE_FOLDER_face, filename)


if __name__ == '__main__':
    app.run(port=5004, debug=True)
