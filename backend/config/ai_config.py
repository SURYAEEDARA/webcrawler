from dotenv import load_dotenv

load_dotenv()

class AIConfig:
    HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"
    MAX_CONTENT_LENGTH = 3000

class ImageConfig:
    REGULAR_LARGE_THRESHOLD_KB = 400 
    REGULAR_LARGE_THRESHOLD_BYTES = 400 * 1024
    
    BANNER_MAX_THRESHOLD_KB = 2048 
    BANNER_MAX_THRESHOLD_BYTES = 2048 * 1024
    
    OPTIMAL_TARGET_KB = 100 
    OPTIMAL_TARGET_BYTES = 100 * 1024