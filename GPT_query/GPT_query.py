import requests
import config as cfg
import time
import re
class ChatGPTRequests:
    def __init__(self):
        self.api_key = cfg.API_KEY_FOR_OPEN_ROUTER
        self.model_for_open_router = cfg.MODEL_FOR_OPEN_ROUTER
        self.api_key_IO_net = cfg.API_KEY_FOR_IO_NET
        self.models_for_io_net = cfg.MODELS_FOR_IO_NET
        self.max_retries = 3

    def query_to_IO_NET(self, prompt, model):
        url = cfg.API_URL_FOR_IO_NET

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key_IO_net}",
        }

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=15)

            if response.status_code != 200:
                return None

            json_data = response.json()

            # Безопасное извлечение контента
            content = json_data.get('choices', [{}])[0].get('message', {}).get('content')
            if not content:
                return cfg.ERROR_REQUEST

            # Удалить всё до последнего </think>, если он есть
            last_think_index = content.rfind('</think>')
            content_after_think = content[last_think_index + len(
                '</think>'):].strip() if last_think_index != -1 else content.strip()
            return content_after_think


        except requests.exceptions.RequestException as e:
            return None

    def query_openrouter(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_for_open_router,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(cfg.API_URL_FOR_OPEN_ROUTER, headers=headers, json=payload, timeout=15)

            if response.status_code != 200:
                return cfg.ERROR_REQUEST

            content = response.json()["choices"][0]["message"]["content"]
            return content

        except requests.exceptions.RequestException as e:
            return cfg.ERROR_REQUEST

    def main_Request(self, prompt):
        for model in self.models_for_io_net:
            response = self.query_to_IO_NET(prompt, model)
            if response:
                return response
            else:
                return cfg.ERROR_REQUEST
        for attempt in range(self.max_retries):
            response = self.query_openrouter(prompt)
            if response != cfg.ERROR_REQUEST:
                return response
            else:
                time.sleep(2)  # задержка перед следующей попыткой

        return cfg.ERROR_REQUEST
