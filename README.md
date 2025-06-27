# 🚀 Question Paper Generator

AI-powered question paper generation from textbooks and sample papers. This application follows the roadmap from POC to first sellable web-app.

## ✨ Features

### MVP Features (v0.1)
- **Upload PDFs**: Support for textbooks and sample papers
- **Dashboard**: Lists uploaded books/papers with processing status
- **Generate Question Papers**: AI-powered generation with customizable parameters
- **Download Results**: Get both PDF and JSON outputs
- **Real-time Progress**: Track generation jobs with live status updates

### Technical Stack
- **Backend**: FastAPI with async support
- **Task Queue**: Celery + Redis for background processing
- **Vector DB**: FAISS + SQLite for document embeddings
- **LLM**: DeepSeek API integration
- **PDF Processing**: ReportLab for clean PDF generation
- **Frontend**: React + Material-UI
- **Deployment**: Docker Compose

## 🏗️ Architecture

```
Browser  ──►  FastAPI ──►  Redis queue ──► Celery worker
   │             │                │
   │  (React)    │ (returns 202)  │ 1. ingest PDF
   │             │                │ 2. embed chunks
   │             │◄───────────────┘ 3. generate paper
   │             │
   │ ◄── Real-time job status polling
   ▼
Download PDF / JSON
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis (or use Docker)
- DeepSeek API key

### 1. Environment Setup

```bash
# Clone the repository
git clone <your-repo>
cd question-paper-app

# Copy environment template
cp .env.example .env

# Edit .env and add your DeepSeek API key
DEEPSEEK_API_KEY=your_api_key_here
```

### 2. Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f app
```

The application will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Manual Setup (Development)

#### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (if not using Docker)
redis-server

# Start FastAPI server
uvicorn app.main:app --reload

# In another terminal, start Celery worker
celery -A app.worker worker --loglevel=info --concurrency=2
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📖 Usage Guide

### 1. Upload Documents
1. Go to "Upload Documents" tab
2. Drag & drop or select PDF files:
   - **Textbooks**: Subject content for question generation
   - **Sample Papers**: Structure and format templates

### 2. Monitor Processing
1. Check "Dashboard" tab to see upload status
2. Wait for documents to show "completed" status
3. Processing creates searchable embeddings from your PDFs

### 3. Generate Question Papers
1. Go to "Generate Papers" tab
2. Click "Generate Question Paper"
3. Configure:
   - Select subject textbooks (multiple allowed)
   - Choose sample paper for structure
   - Set grade, total marks, number of questions
   - Specify subject query (e.g., "algebra problems")
4. Monitor real-time progress
5. Download PDF and JSON when complete

## 🔧 Configuration

### Environment Variables
```bash
# Required
DEEPSEEK_API_KEY=your_deepseek_api_key

# Optional (with defaults)
REDIS_URL=redis://localhost:6379/0
MAX_FILE_SIZE=104857600  # 100MB
DEBUG=true
```

### Celery Configuration
- **Concurrency**: 2 workers by default
- **Time Limits**: 30 minutes per task
- **Retry Policy**: 3 attempts for failed tasks
- **Cleanup**: Auto-cleanup of old files (7 days)

### API Endpoints

#### Core Endpoints
- `POST /upload` - Upload PDF files
- `GET /documents` - List uploaded documents
- `POST /generate` - Start question paper generation
- `GET /jobs/{job_id}` - Check generation status
- `GET /download/{job_id}` - Download generated files

#### Utility Endpoints
- `GET /health` - System health check
- `GET /stats` - Application statistics
- `GET /search` - Search document content

## 📁 Project Structure

```
question-paper-app/
├── app/
│   ├── main.py              # FastAPI routes
│   ├── schemas.py           # Pydantic models
│   ├── deps.py              # Database & dependencies
│   ├── worker.py            # Celery tasks
│   ├── postprocess.py       # Output cleaning
│   ├── pdf_export.py        # PDF generation
│   ├── ingest/
│   │   ├── pdf_reader.py    # PDF text extraction
│   │   ├── chunker.py       # Text chunking
│   │   └── embedder.py      # Embedding generation
│   └── rag/
│       ├── retriever.py     # Semantic search
│       ├── prompt_builder.py # LLM prompts
│       └── deepseek_client.py # API client
├── frontend/                # React application
├── data/                    # Generated at runtime
│   ├── uploads/            # Uploaded PDFs
│   ├── output/             # Generated papers
│   ├── index.faiss         # Vector embeddings
│   └── metadata.sqlite     # Document metadata
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## 🔍 How It Works

### 1. Document Ingestion
```python
# Stream PDF pages to avoid memory issues
for page_num, text in stream_pages(pdf_path):
    # Clean and chunk text
    for chunk in chunker.chunks(text):
        # Generate embeddings
        embeddings = embed_batch([chunk])
        # Store in FAISS + metadata in SQLite
        add_embeddings(embeddings, metadata)
```

### 2. Question Generation
```python
# Hybrid search across document types
structure_chunks = search_by_doc_id("format structure", sample_paper_id)
subject_chunks = search_by_doc_id(user_query, textbook_ids)

# Build contextual prompt
prompt = build_prompt(instructions, structure_chunks, subject_chunks)

# Generate with DeepSeek
raw_output = await chat_async(prompt)

# Post-process and create PDF
structured_data = clean_output(raw_output, instructions)
pdf_path = make_pdf(structured_data, output_path)
```

## 🚀 Deployment

### Production Checklist
- [ ] Set strong API keys
- [ ] Configure Redis persistence
- [ ] Set up SSL/HTTPS
- [ ] Configure file storage (S3 for scale)
- [ ] Set up monitoring (health checks)
- [ ] Configure log aggregation
- [ ] Set up backup strategy

### Scaling Considerations
- **Vector DB**: Migrate to Pinecone/Qdrant for larger datasets
- **File Storage**: Use S3 + CloudFront for file serving
- **LLM**: Consider multiple model providers
- **Workers**: Scale Celery workers horizontally
- **Caching**: Add Redis caching layer

## 🛠️ Development

### Adding New Features
1. **New Document Types**: Extend `DocType` enum in schemas
2. **Custom Models**: Modify `deepseek_client.py`
3. **PDF Formats**: Enhance `pdf_export.py`
4. **Search Methods**: Extend `retriever.py`

### Testing
```bash
# Run backend tests
pytest

# Test API endpoints
curl http://localhost:8000/health

# Test file upload
curl -X POST -F "file=@sample.pdf" http://localhost:8000/upload
```

### Debugging
- Check Celery logs: `docker-compose logs worker`
- Monitor Redis: `redis-cli monitor`
- API logs: `docker-compose logs app`
- Vector DB size: `GET /stats`

## 📈 Roadmap

### Phase 1: MVP (Current)
- ✅ Basic upload/generation workflow
- ✅ PDF processing pipeline
- ✅ React frontend

### Phase 2: Enhanced Features
- [ ] User authentication & workspaces
- [ ] Advanced question types
- [ ] Batch generation
- [ ] Question difficulty analysis

### Phase 3: Scale & Monetize
- [ ] Multi-tenant architecture
- [ ] Stripe integration
- [ ] Advanced analytics
- [ ] Mobile app

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**"No module named 'app'"**
```bash
# Make sure you're in the root directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**"DeepSeek API key not set"**
```bash
# Check your .env file
echo $DEEPSEEK_API_KEY
```

**"Redis connection failed"**
```bash
# Start Redis
redis-server
# Or use Docker
docker run -d -p 6379:6379 redis:alpine
```

**"PDF upload fails"**
- Check file size (max 100MB)
- Ensure PDF is not password protected
- Verify file is a valid PDF

### Getting Help
- Check logs: `docker-compose logs`
- API documentation: http://localhost:8000/docs
- Health status: http://localhost:8000/health

---

Built with ❤️ following the minimal viable product approach - ship fast, iterate faster! 