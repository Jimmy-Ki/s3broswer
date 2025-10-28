import json
import os
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file='s3_config.json'):
        self.config_file = Path(config_file)
        self.config_data = self.load_config()

    def load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {'servers': []}
        return {'servers': []}

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError:
            return False

    def get_servers(self):
        """获取所有S3服务器配置"""
        return self.config_data.get('servers', [])

    def add_server(self, name, access_key, secret_key, endpoint_url, region='us-east-1'):
        """添加新的S3服务器配置"""
        server = {
            'id': len(self.config_data['servers']) + 1,
            'name': name,
            'access_key': access_key,
            'secret_key': secret_key,
            'endpoint_url': endpoint_url,
            'region': region,
            'bucket_cdn_configs': {}
        }
        self.config_data['servers'].append(server)
        self.save_config()
        return server

    def update_server(self, server_id, **kwargs):
        """更新S3服务器配置"""
        for server in self.config_data['servers']:
            if server['id'] == server_id:
                server.update(kwargs)
                self.save_config()
                return True
        return False

    def delete_server(self, server_id):
        """删除S3服务器配置"""
        self.config_data['servers'] = [
            server for server in self.config_data['servers']
            if server['id'] != server_id
        ]
        self.save_config()
        return True

    def get_server(self, server_id):
        """获取指定S3服务器配置"""
        for server in self.config_data['servers']:
            if server['id'] == server_id:
                return server
        return None

    def get_bucket_cdn_config(self, server_id, bucket_name):
        """获取指定桶的CDN配置"""
        server = self.get_server(server_id)
        if not server:
            return None

        # 初始化桶CDN配置（如果不存在）
        if 'bucket_cdn_configs' not in server:
            server['bucket_cdn_configs'] = {}

        return server['bucket_cdn_configs'].get(bucket_name)

    def set_bucket_cdn_config(self, server_id, bucket_name, cdn_url):
        """设置指定桶的CDN配置"""
        server = self.get_server(server_id)
        if not server:
            return False

        # 初始化桶CDN配置（如果不存在）
        if 'bucket_cdn_configs' not in server:
            server['bucket_cdn_configs'] = {}

        if cdn_url:
            server['bucket_cdn_configs'][bucket_name] = cdn_url
        else:
            # 如果CDN URL为空，则删除配置
            server['bucket_cdn_configs'].pop(bucket_name, None)

        return self.save_config()

    def delete_bucket_cdn_config(self, server_id, bucket_name):
        """删除指定桶的CDN配置"""
        return self.set_bucket_cdn_config(server_id, bucket_name, None)

    def get_server_bucket_cdn_configs(self, server_id):
        """获取服务器所有桶的CDN配置"""
        server = self.get_server(server_id)
        if not server:
            return {}

        return server.get('bucket_cdn_configs', {})