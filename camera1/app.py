from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import base64
import uuid

app = Flask(__name__)

# Configuration
BASE_UPLOAD_FOLDER = 'static/uploads'

# Ensure the base upload folder exists
if not os.path.exists(BASE_UPLOAD_FOLDER):
    os.makedirs(BASE_UPLOAD_FOLDER)

app.config['BASE_UPLOAD_FOLDER'] = BASE_UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_photo():
    data = request.get_json()
    image_data = data.get('image')
    folder_name = data.get('folder')

    if not image_data or not folder_name:
        return jsonify({'success': False, 'message': '缺少图片数据或文件夹名称。'}), 400

    # Decode base64 image
    try:
        # Remove the "data:image/png;base64," prefix
        header, encoded = image_data.split(',', 1)
        decoded_image = base64.b64decode(encoded)
    except Exception as e:
        return jsonify({'success': False, 'message': f'图片解码失败: {e}'}), 400

    folder_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path) # Create folder if it doesn't exist

    # Generate filename based on folder name and existing photo count
    existing_photos = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    next_number = len(existing_photos) + 1
    filename = f"{folder_name}_{next_number:02d}.png" # e.g., "001_螺丝_01.png"
    file_path = os.path.join(folder_path, filename)

    # Handle potential filename conflicts (though unlikely with sequential numbering)
    counter = 0
    while os.path.exists(file_path):
        counter += 1
        filename = f"{folder_name}_{next_number:02d}_{counter}.png"
        file_path = os.path.join(folder_path, filename)

    try:
        with open(file_path, 'wb') as f:
            f.write(decoded_image)
        return jsonify({'success': True, 'message': '照片上传成功。'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存照片失败: {e}'}), 500

@app.route('/create_folder', methods=['POST'])
def create_folder():
    data = request.get_json()
    folder_name = data.get('folder_name')

    if not folder_name:
        return jsonify({'success': False, 'message': '文件夹名称不能为空。'}), 400

    folder_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name)

    if os.path.exists(folder_path):
        return jsonify({'success': False, 'message': '文件夹已存在。'}), 409

    try:
        os.makedirs(folder_path)
        return jsonify({'success': True, 'message': '文件夹创建成功。'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建文件夹失败: {e}'}), 500

@app.route('/get_folders')
def get_folders():
    try:
        folders = [d for d in os.listdir(app.config['BASE_UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['BASE_UPLOAD_FOLDER'], d))]
        return jsonify({'success': True, 'folders': sorted(folders)})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取文件夹列表失败: {e}'}), 500

@app.route('/get_photos/<folder_name>')
def get_photos(folder_name):
    folder_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        return jsonify({'success': False, 'message': '文件夹不存在。'}), 404

    photos = []
    try:
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                photo_path = os.path.join(folder_path, filename)
                # Construct URL relative to static folder
                url = f"/static/uploads/{folder_name}/{filename}"
                photos.append({'name': filename, 'url': url, 'path': photo_path})
        return jsonify({'success': True, 'photos': photos})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取照片失败: {e}'}), 500

@app.route('/delete_photo', methods=['POST'])
def delete_photo():
    data = request.get_json()
    photo_path = data.get('photo_path')

    if not photo_path:
        return jsonify({'success': False, 'message': '缺少照片路径。'}), 400

    # Ensure the path is within the UPLOAD_FOLDER for security
    if not photo_path.startswith(app.config['BASE_UPLOAD_FOLDER']):
        return jsonify({'success': False, 'message': '无效的照片路径。'}), 403

    if not os.path.exists(photo_path):
        return jsonify({'success': False, 'message': '照片不存在。'}), 404

    try:
        os.remove(photo_path)
        return jsonify({'success': True, 'message': '照片删除成功。'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除照片失败: {e}'}), 500

@app.route('/delete_folder', methods=['POST'])
def delete_folder():
    data = request.get_json()
    folder_name = data.get('folder_name')

    if not folder_name:
        return jsonify({'success': False, 'message': '文件夹名称不能为空。'}), 400

    folder_path = os.path.join(app.config['BASE_UPLOAD_FOLDER'], folder_name)

    if not os.path.exists(folder_path):
        return jsonify({'success': False, 'message': '文件夹不存在。'}), 404

    try:
        # Remove the folder and its contents
        import shutil
        shutil.rmtree(folder_path)
        return jsonify({'success': True, 'message': '文件夹删除成功。'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除文件夹失败: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)