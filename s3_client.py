import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
from urllib.parse import quote

class S3ClientManager:
    def __init__(self, access_key, secret_key, endpoint_url, region='us-east-1'):
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self.region = region
        self.client = self._create_client()

    def _create_client(self):
        """创建S3客户端"""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url,
                region_name=self.region
            )
        except Exception as e:
            raise Exception(f"创建S3客户端失败: {str(e)}")

    def list_buckets(self):
        """列出所有存储桶"""
        try:
            response = self.client.list_buckets()
            buckets = []
            for bucket in response.get('Buckets', []):
                buckets.append({
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'].strftime('%Y-%m-%d %H:%M:%S')
                })
            return buckets
        except ClientError as e:
            raise Exception(f"列出存储桶失败: {str(e)}")

    def list_objects(self, bucket_name, prefix='', delimiter='/'):
        """列出存储桶中的对象"""
        try:
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter=delimiter)

            folders = []
            files = []

            for page in pages:
                # 文件夹（CommonPrefixes）
                for folder in page.get('CommonPrefixes', []):
                    folder_name = folder['Prefix'].rstrip('/')
                    if folder_name != prefix.rstrip('/'):
                        folders.append({
                            'name': os.path.basename(folder_name),
                            'key': folder['Prefix'],
                            'prefix': folder['Prefix'],
                            'type': 'folder'
                        })

                # 文件
                for obj in page.get('Contents', []):
                    if obj['Key'] != prefix and not obj['Key'].endswith('/'):
                        files.append({
                            'name': os.path.basename(obj['Key']),
                            'key': obj['Key'],
                            'size': self._format_size(obj['Size']),
                            'last_modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S'),
                            'type': 'file'
                        })

            return sorted(folders, key=lambda x: x['name']) + sorted(files, key=lambda x: x['name'])
        except ClientError as e:
            raise Exception(f"列出对象失败: {str(e)}")

    def upload_file(self, bucket_name, file_path, object_name=None):
        """上传文件"""
        if object_name is None:
            object_name = os.path.basename(file_path)

        try:
            self.client.upload_file(file_path, bucket_name, object_name)
            return True
        except ClientError as e:
            raise Exception(f"上传文件失败: {str(e)}")

    def download_file(self, bucket_name, object_name, download_path):
        """下载文件"""
        try:
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            self.client.download_file(bucket_name, object_name, download_path)
            return True
        except ClientError as e:
            raise Exception(f"下载文件失败: {str(e)}")

    def delete_object(self, bucket_name, object_name):
        """删除对象"""
        try:
            self.client.delete_object(Bucket=bucket_name, Key=object_name)
            return True
        except ClientError as e:
            raise Exception(f"删除对象失败: {str(e)}")

    def create_folder(self, bucket_name, folder_name):
        """创建文件夹"""
        try:
            # S3中文件夹实际上是空对象，以/结尾
            if not folder_name.endswith('/'):
                folder_name += '/'

            self.client.put_object(Bucket=bucket_name, Key=folder_name)
            return True
        except ClientError as e:
            raise Exception(f"创建文件夹失败: {str(e)}")

    def delete_folder(self, bucket_name, folder_prefix):
        """删除文件夹及其内容"""
        try:
            # 列出文件夹中的所有对象
            objects_to_delete = []
            paginator = self.client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix=folder_prefix)

            for page in pages:
                for obj in page.get('Contents', []):
                    objects_to_delete.append({'Key': obj['Key']})

            # 批量删除
            if objects_to_delete:
                self.client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects_to_delete}
                )

            return True
        except ClientError as e:
            raise Exception(f"删除文件夹失败: {str(e)}")

    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"