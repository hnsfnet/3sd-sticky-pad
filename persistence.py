import json
import os

import config


class NoteStore:
    def __init__(self, file_path=None):
        self.file_path = file_path or config.DATA_FILE

    def load(self):
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"加载失败: {e}")
            return []
        if not isinstance(data, list):
            return []
        return data

    def save(self, data):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存失败: {e}")
