from flask import Flask, render_template, request, jsonify, send_file, session
from flask_session import Session
import os
import uuid
import base64
from werkzeug.utils import secure_filename
from config import ConfigManager
from s3_client import S3ClientManager
import tempfile
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# 配置
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('flask_session', exist_ok=True)

# 初始化会话
Session(app)

# 初始化配置管理器
config_manager = ConfigManager()

# S3客户端缓存
s3_clients = {}

def get_s3_client(server_id):
    """获取S3客户端实例"""
    if server_id not in s3_clients:
        server_config = config_manager.get_server(server_id)
        if not server_config:
            raise Exception(f"服务器配置不存在: {server_id}")

        s3_clients[server_id] = S3ClientManager(
            server_config['access_key'],
            server_config['secret_key'],
            server_config['endpoint_url'],
            server_config['region']
        )

    return s3_clients[server_id]

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

# API 路由

@app.route('/api/servers', methods=['GET'])
def get_servers():
    """获取所有S3服务器配置"""
    try:
        servers = config_manager.get_servers()
        return jsonify({'servers': servers})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers', methods=['POST'])
def add_server():
    """添加新的S3服务器配置"""
    try:
        data = request.get_json()

        # 验证必填字段
        required_fields = ['name', 'access_key', 'secret_key', 'endpoint_url']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'缺少必填字段: {field}'}), 400

        # 添加服务器配置
        server = config_manager.add_server(
            data['name'],
            data['access_key'],
            data['secret_key'],
            data['endpoint_url'],
            data.get('region', 'us-east-1')
        )

        return jsonify({'server': server})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>', methods=['DELETE'])
def delete_server(server_id):
    """删除S3服务器配置"""
    try:
        success = config_manager.delete_server(server_id)
        if not success:
            return jsonify({'error': '服务器不存在'}), 404

        # 清理客户端缓存
        if server_id in s3_clients:
            del s3_clients[server_id]

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/buckets', methods=['GET'])
def list_buckets(server_id):
    """列出S3存储桶"""
    try:
        client = get_s3_client(server_id)
        buckets = client.list_buckets()
        return jsonify({'buckets': buckets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/objects', methods=['GET'])
def list_objects(server_id):
    """列出S3对象"""
    try:
        bucket = request.args.get('bucket')
        prefix = request.args.get('prefix', '')

        if not bucket:
            return jsonify({'error': '缺少存储桶名称'}), 400

        client = get_s3_client(server_id)
        objects = client.list_objects(bucket, prefix)
        return jsonify({'objects': objects})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/upload', methods=['POST'])
def upload_file(server_id):
    """上传文件到S3"""
    try:
        bucket = request.form.get('bucket')
        prefix = request.form.get('prefix', '')

        if not bucket:
            return jsonify({'error': '缺少存储桶名称'}), 400

        if 'file' not in request.files:
            return jsonify({'error': '没有文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400

        # 安全处理文件名
        filename = secure_filename(file.filename)
        object_name = prefix + filename if prefix else filename

        # 保存临时文件
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{filename}")
        file.save(temp_path)

        try:
            # 上传到S3
            client = get_s3_client(server_id)
            success = client.upload_file(bucket, temp_path, object_name)

            if success:
                return jsonify({'success': True, 'object_name': object_name})
            else:
                return jsonify({'error': '上传失败'}), 500

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/download', methods=['GET'])
def download_file(server_id):
    """从S3下载文件"""
    try:
        bucket = request.args.get('bucket')
        key = request.args.get('key')

        if not bucket or not key:
            return jsonify({'error': '缺少存储桶名称或对象键'}), 400

        client = get_s3_client(server_id)

        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        filename = key.split('/')[-1]
        temp_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{filename}")

        try:
            # 下载文件
            success = client.download_file(bucket, key, temp_path)

            if success and os.path.exists(temp_path):
                return send_file(
                    temp_path,
                    as_attachment=True,
                    download_name=filename
                )
            else:
                return jsonify({'error': '下载失败'}), 500

        finally:
            # 清理临时文件（延迟清理，确保文件传输完成）
            import threading
            def cleanup():
                import time
                time.sleep(5)  # 等待5秒后清理
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            cleanup_thread = threading.Thread(target=cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/delete', methods=['DELETE'])
def delete_objects(server_id):
    """删除S3对象"""
    try:
        data = request.get_json()
        bucket = data.get('bucket')
        keys = data.get('keys', [])

        if not bucket or not keys:
            return jsonify({'error': '缺少存储桶名称或对象键'}), 400

        client = get_s3_client(server_id)
        errors = []

        for key in keys:
            try:
                if key.endswith('/'):
                    # 删除文件夹
                    client.delete_folder(bucket, key)
                else:
                    # 删除文件
                    client.delete_object(bucket, key)
            except Exception as e:
                errors.append(f"删除 {key} 失败: {str(e)}")

        if errors:
            return jsonify({'error': '; '.join(errors)}), 500
        else:
            return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/folders', methods=['POST'])
def create_folder(server_id):
    """创建文件夹"""
    try:
        data = request.get_json()
        bucket = data.get('bucket')
        folder_path = data.get('folder_path')

        if not bucket or not folder_path:
            return jsonify({'error': '缺少存储桶名称或文件夹路径'}), 400

        client = get_s3_client(server_id)
        success = client.create_folder(bucket, folder_path)

        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': '创建文件夹失败'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/preview', methods=['GET'])
def preview_file(server_id):
    """获取文件预览内容"""
    try:
        bucket = request.args.get('bucket')
        key = request.args.get('key')

        if not bucket or not key:
            return jsonify({'error': '缺少存储桶名称或对象键'}), 400

        client = get_s3_client(server_id)

        # 创建临时文件
        temp_dir = tempfile.gettempdir()
        filename = key.split('/')[-1]
        temp_path = os.path.join(temp_dir, f"preview_{uuid.uuid4()}_{filename}")

        try:
            # 下载文件
            success = client.download_file(bucket, key, temp_path)

            if not success or not os.path.exists(temp_path):
                return jsonify({'error': '文件不存在或下载失败'}), 404

            # 获取文件信息
            file_size = os.path.getsize(temp_path)
            file_ext = os.path.splitext(filename)[1].lower()

            # 限制预览文件大小 (10MB)
            if file_size > 10 * 1024 * 1024:
                os.remove(temp_path)
                return jsonify({
                    'error': '文件太大，无法预览',
                    'download_url': f"/api/servers/{server_id}/download?bucket={bucket}&key={key}"
                }), 413

            # 根据文件类型处理
            content_type = get_content_type(file_ext)
            preview_data = process_file_preview(temp_path, file_ext, content_type, server_id, bucket, key)

            # 处理PDF预览的字典返回
            if isinstance(preview_data, dict) and preview_data.get('type') == 'pdf_embed':
                return jsonify({
                    'filename': filename,
                    'size': file_size,
                    'content_type': content_type,
                    'preview_type': 'pdf_embed',
                    'preview_url': preview_data.get('url'),
                    'download_url': preview_data.get('download_url')
                })

            return jsonify({
                'filename': filename,
                'size': file_size,
                'content_type': content_type,
                'preview': preview_data,
                'download_url': f"/api/servers/{server_id}/download?bucket={bucket}&key={key}"
            })

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_content_type(file_ext):
    """根据文件扩展名获取MIME类型"""
    content_types = {
        # 图片
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.gif': 'image/gif', '.bmp': 'image/bmp', '.webp': 'image/webp',
        '.svg': 'image/svg+xml', '.ico': 'image/x-icon',

        # 文档
        '.pdf': 'application/pdf',
        '.doc': 'application/msword', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.xls': 'application/vnd.ms-excel', '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.ppt': 'application/vnd.ms-powerpoint', '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        '.txt': 'text/plain', '.md': 'text/markdown', '.rtf': 'application/rtf',

        # 代码
        '.js': 'application/javascript', '.json': 'application/json',
        '.xml': 'text/xml', '.html': 'text/html', '.htm': 'text/html',
        '.css': 'text/css', '.scss': 'text/x-scss', '.less': 'text/x-less',
        '.py': 'text/x-python', '.java': 'text/x-java', '.cpp': 'text/x-c++',
        '.c': 'text/x-c', '.h': 'text/x-c', '.php': 'text/x-php',
        '.rb': 'text/x-ruby', '.go': 'text/x-go', '.rs': 'text/x-rust',
        '.sql': 'text/x-sql', '.sh': 'text/x-shellscript',

        # 数据
        '.csv': 'text/csv', '.tsv': 'text/tab-separated-values',
        '.jsonl': 'application/jsonl', '.xml': 'text/xml',

        # 音频
        '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4', '.flac': 'audio/flac',

        # 视频
        '.mp4': 'video/mp4', '.avi': 'video/x-msvideo', '.mov': 'video/quicktime',
        '.wmv': 'video/x-ms-wmv', '.flv': 'video/x-flv', '.webm': 'video/webm',

        # 压缩包
        '.zip': 'application/zip', '.rar': 'application/x-rar-compressed',
        '.7z': 'application/x-7z-compressed', '.tar': 'application/x-tar',
        '.gz': 'application/gzip', '.tar.gz': 'application/gzip',

        # 数据库
        '.db': 'application/x-sqlite3', '.sqlite': 'application/x-sqlite3',
        '.sqlite3': 'application/x-sqlite3'
    }
    return content_types.get(file_ext, 'application/octet-stream')

def process_file_preview(file_path, file_ext, content_type, server_id=None, bucket=None, key=None):
    """处理文件预览内容"""
    try:
        if content_type.startswith('image/'):
            # 图片文件 - 返回base64
            with open(file_path, 'rb') as f:
                image_data = f.read()
                return f"data:{content_type};base64,{base64.b64encode(image_data).decode()}"

        elif content_type.startswith('text/') or content_type in ['application/json', 'application/javascript', 'application/xml']:
            # 文本文件 - 读取内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 限制预览长度
                    if len(content) > 50000:  # 50KB限制
                        return content[:50000] + "\n\n... (内容过长，仅显示前50KB)"
                    return content
            except UnicodeDecodeError:
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                        if len(content) > 50000:
                            return content[:50000] + "\n\n... (内容过长，仅显示前50KB)"
                        return content
                except:
                    return "二进制文件，无法预览内容"

        elif content_type == 'application/pdf':
            # PDF文件 - 构建MinIO预览URL
            if server_id and bucket and key:
                server_config = None
                for server in config_manager.get_servers():
                    if server['id'] == server_id:
                        server_config = server
                        break

                if server_config:
                    # 构建预览URL，使用MinIO的内置预览功能
                    preview_url = f"{server_config['endpoint_url']}/{bucket}/{key}?response-content-disposition=inline"
                    return {
                        'type': 'pdf_embed',
                        'url': preview_url,
                        'download_url': f"/api/servers/{server_id}/download?bucket={bucket}&key={key}"
                    }
                else:
                    return "PDF文档预览不可用"
            else:
                return "PDF文档预览不可用"

        elif file_ext in ['.db', '.sqlite', '.sqlite3']:
            # 数据库文件
            return get_database_info(file_path)

        elif file_ext in ['.csv', '.tsv']:
            # CSV文件
            return get_csv_preview(file_path)

        elif content_type.startswith('audio/'):
            # 音频文件
            return "音频文件，无法在线预览"

        elif content_type.startswith('video/'):
            # 视频文件
            return "视频文件，无法在线预览"

        else:
            return "此文件类型不支持预览"

    except Exception as e:
        return f"预览处理失败: {str(e)}"

def get_database_info(db_path):
    """获取数据库文件基本信息"""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 获取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        info = f"SQLite数据库\n\n表列表:\n"
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            info += f"- {table_name} ({count} 条记录)\n"

        conn.close()
        return info

    except Exception as e:
        return f"数据库文件，读取失败: {str(e)}"

def get_csv_preview(csv_path):
    """获取CSV文件预览"""
    try:
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = []
            for i, row in enumerate(reader):
                if i >= 10:  # 只显示前10行
                    break
                rows.append(row)

        # 转换为表格格式
        if not rows:
            return "空CSV文件"

        # 简单的文本表格
        result = "CSV文件预览 (前10行):\n\n"
        for i, row in enumerate(rows):
            result += " | ".join(str(cell) for cell in row) + "\n"
            if i == 0:  # 标题行后加分割线
                result += "-" * 50 + "\n"

        return result

    except Exception as e:
        return f"CSV文件，读取失败: {str(e)}"

# 错误处理

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '文件太大，最大支持100MB'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': '服务器内部错误'}), 500

# 应用上下文处理器

@app.context_processor
def inject_current_time():
    return {'current_time': datetime.now()}

# 清理函数

@app.teardown_appcontext
def cleanup_clients(error):
    """清理S3客户端连接"""
    pass  # S3客户端会自动清理连接

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)