'''
    为实现 dify读取本地图片的功能，实现的服务器文件上传 模块
'''

from flask import Flask, send_from_directory, abort
import os

app = Flask(__name__)

# 指定图片所在的文件夹 -- 展品、人脸
IMAGE_FOLDER = r'E:\0_My_Project\AI_History_Server\Exhibit_Intr\Image'
IMAGE_FOLDER_face = r'E:\0_My_Project\Face_recognition\Data\Face'


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
    app.run(port=5005, debug=True)
