# Railway Environment Variables Setup

## Copy-Paste these variables into Railway Dashboard:

### Core Variables (Required):
```
ENVIRONMENT = production
FORCE_FULL_MODE = true
API_DEBUG = false
```

### Redis Variables (Add after Redis service is deployed):
```
REDIS_URL = ${{Redis.REDIS_URL}}
REDIS_MAX_CONNECTIONS = 100
CELERY_BROKER_URL = ${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND = ${{Redis.REDIS_URL}}
```

### ML/AI Variables:
```
HF_HOME = /tmp/huggingface
TRANSFORMERS_CACHE = /tmp/transformers
SENTENCE_TRANSFORMERS_HOME = /tmp/sentence_transformers
EMBEDDING_MODEL = all-MiniLM-L6-v2
VECTOR_DIMENSION = 384
```

### Storage Variables:
```
UPLOAD_PATH = data/uploads
OUTPUT_PATH = data/output
DB_PATH = data/documents.db
FAISS_INDEX_PATH = data/faiss_index
```

### Performance Variables:
```
ALLOWED_ORIGINS = ["*"]
CORS_ENABLED = true
MAX_FILE_SIZE = 50MB
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MAX_CONCURRENT_JOBS = 5
```

## How to Add:
1. Go to Railway Dashboard → Your Project → Backend Service
2. Click "Variables" tab
3. Click "New Variable" for each one above
4. Copy name and value exactly
5. Save each variable

## After Adding Variables:
Your app will automatically redeploy with full functionality! 