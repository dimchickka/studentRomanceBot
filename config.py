BOT_TOKEN = ''
WELCOME_TEXT_PATH = 'storage/welcomeMessage.txt'
MALE = 1
FEMALE = 0

ERROR_EMAIL = 11
ERROR_FIND_EMAIL = 12
SUCCESS = 00
ERROR_REQUEST = 111
USER_CHOSE_MAIN_MENU = 000

#верификация
EMAIL_TO_SENDING_EMAILS = "studentRomance@yandex.ru"
PASSWORD_FOR_EMAIL_TO_SEND_EMAILS = ""

#поддержка
SUPPORT = '@StudentRomanceSupport'
admin = 123

#Запросы к GPT
API_URL_FOR_OPEN_ROUTER = "https://openrouter.ai/api/v1/chat/completions"
API_URL_FOR_IO_NET = "https://api.intelligence.io.solutions/api/v1/chat/completions"
API_KEY_FOR_OPEN_ROUTER = ""  # внутри скобок свой апи ключ отсюда https://openrouter.ai/settings/keys
API_KEY_FOR_IO_NET = "" # https://ai.io.net/ai/api-keys
MODEL_FOR_OPEN_ROUTER = "deepseek/deepseek-chat:free"
MODELS_FOR_IO_NET = [
    "deepseek-ai/DeepSeek-R1-0528",
    "private-meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
    "Qwen/Qwen3-235B-A22B-FP8",
    "meta-llama/Llama-3.2-90B-Vision-Instruct",
    "Qwen/Qwen2.5-VL-32B-Instruct",
    "google/gemma-3-27b-it",
    "meta-llama/Llama-3.3-70B-Instruct",
    "mistralai/Devstral-Small-2505",
    "mistralai/Magistral-Small-2506",
    "Qwen/Qwen2-VL-7B-Instruct",
    "deepseek-ai/DeepSeek-R1",
    "databricks/dbrx-instruct",
    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
    "Qwen/QwQ-32B",
    "netease-youdao/Confucius-o1-14B",
    "nvidia/AceMath-7B-Instruct",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    "neuralmagic/Llama-3.1-Nemotron-70B-Instruct-HF-FP8-dynamic",
    "mistralai/Mistral-Large-Instruct-2411",
    "microsoft/phi-4",
    "SentientAGI/Dobby-Mini-Unhinged-Llama-3.1-8B",
    "watt-ai/watt-tool-70B",
    "bespokelabs/Bespoke-Stratos-32B",
    "NovaSky-AI/Sky-T1-32B-Preview",
    "tiiuae/Falcon3-10B-Instruct",
    "THUDM/glm-4-9b-chat",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "CohereForAI/aya-expanse-32b",
    "jinaai/ReaderLM-v2",
    "openbmb/MiniCPM3-4B",
    "mistralai/Ministral-8B-Instruct-2410",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "ozone-ai/0x-lite",
    "microsoft/Phi-3.5-mini-instruct",
    "ibm-granite/granite-3.1-8b-instruct"
]

RAFFLE_TEXT_PATH = 'storage/raffle_text.txt'
RAFFLE_PHOTO_PATH = 'storage/raffle_photo.png'

def update_openrouter_key(new_key):
    global API_KEY_FOR_IO_NET
    API_KEY_FOR_IO_NET = new_key
