#!/usr/bin/env python3
"""
Interactive script to work with deployed Railway app
Use this like you were using the local app
"""
import requests
import json
import os
from pathlib import Path

# Your Railway app URL
BASE_URL = "https://projectquestionpaper-production.up.railway.app"

class DeployedAppClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def test_connection(self):
        """Test if the app is running"""
        try:
            response = self.session.get(f"{self.base_url}/ping")
            if response.status_code == 200:
                print("✅ App is running!")
                return True
            else:
                print(f"❌ App returned status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def get_status(self):
        """Get detailed app status"""
        try:
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                status = response.json()
                print("📊 App Status:")
                print(json.dumps(status, indent=2))
                return status
            else:
                print(f"❌ Status check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return None
    
    def get_health(self):
        """Get health check information"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                health = response.json()
                print("🏥 Health Check:")
                print(json.dumps(health, indent=2))
                return health
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting health: {e}")
            return None
    
    def upload_pdf(self, file_path, doc_type="textbook"):
        """Upload a PDF file to the deployed app"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file, 'application/pdf')}
                data = {'doc_type': doc_type}
                
                print(f"📤 Uploading {file_path}...")
                response = self.session.post(f"{self.base_url}/upload", files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Upload successful!")
                    print(f"File ID: {result.get('file_id')}")
                    print(f"Task ID: {result.get('task_id', 'None')}")
                    return result
                else:
                    print(f"❌ Upload failed: {response.status_code}")
                    print(response.text)
                    return None
        except Exception as e:
            print(f"❌ Upload error: {e}")
            return None
    
    def list_documents(self):
        """List all uploaded documents"""
        try:
            response = self.session.get(f"{self.base_url}/documents")
            if response.status_code == 200:
                docs = response.json()
                print("📚 Documents:")
                if docs.get('documents'):
                    for doc in docs['documents']:
                        print(f"  • {doc['filename']} (ID: {doc['doc_id']}) - {doc['status']}")
                else:
                    print("  No documents found")
                return docs
            else:
                print(f"❌ Failed to get documents: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
            return None
    
    def generate_paper(self, textbook_ids, sample_paper_id, subject="General", 
                      exam_type="midterm", difficulty="medium"):
        """Generate a question paper"""
        try:
            data = {
                "textbook_ids": textbook_ids,
                "sample_paper_id": sample_paper_id,
                "subject": subject,
                "exam_type": exam_type,
                "difficulty": difficulty
            }
            
            print(f"🤖 Generating question paper...")
            response = self.session.post(f"{self.base_url}/generate", json=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Generation started!")
                print(f"Task ID: {result.get('task_id')}")
                return result
            else:
                print(f"❌ Generation failed: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Generation error: {e}")
            return None
    
    def check_job(self, job_id):
        """Check job status"""
        try:
            response = self.session.get(f"{self.base_url}/jobs/{job_id}")
            if response.status_code == 200:
                job = response.json()
                print(f"🔍 Job {job_id} Status:")
                print(json.dumps(job, indent=2))
                return job
            else:
                print(f"❌ Job check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Job check error: {e}")
            return None
    
    def download_file(self, filename, save_path=None):
        """Download a generated file"""
        try:
            response = self.session.get(f"{self.base_url}/download/{filename}")
            if response.status_code == 200:
                if not save_path:
                    save_path = filename
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ Downloaded: {save_path}")
                return save_path
            else:
                print(f"❌ Download failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

def interactive_menu(client):
    """Interactive menu for working with deployed app"""
    while True:
        print("\n" + "="*50)
        print("🚀 DEPLOYED APP CONTROLLER")
        print("="*50)
        print("1. Test Connection")
        print("2. Get App Status")
        print("3. Get Health Check")
        print("4. Upload PDF")
        print("5. List Documents")
        print("6. Generate Question Paper")
        print("7. Check Job Status")
        print("8. Download File")
        print("9. Exit")
        
        choice = input("\nChoose option (1-9): ").strip()
        
        if choice == "1":
            client.test_connection()
        elif choice == "2":
            client.get_status()
        elif choice == "3":
            client.get_health()
        elif choice == "4":
            file_path = input("Enter PDF file path: ").strip()
            doc_type = input("Document type (textbook/sample_paper) [textbook]: ").strip() or "textbook"
            client.upload_pdf(file_path, doc_type)
        elif choice == "5":
            client.list_documents()
        elif choice == "6":
            textbook_ids = input("Enter textbook IDs (comma-separated): ").strip().split(',')
            textbook_ids = [id.strip() for id in textbook_ids if id.strip()]
            sample_id = input("Enter sample paper ID: ").strip()
            subject = input("Subject [General]: ").strip() or "General"
            exam_type = input("Exam type [midterm]: ").strip() or "midterm"
            difficulty = input("Difficulty [medium]: ").strip() or "medium"
            client.generate_paper(textbook_ids, sample_id, subject, exam_type, difficulty)
        elif choice == "7":
            job_id = input("Enter job ID: ").strip()
            client.check_job(job_id)
        elif choice == "8":
            filename = input("Enter filename to download: ").strip()
            save_path = input("Save as (press Enter for same name): ").strip() or None
            client.download_file(filename, save_path)
        elif choice == "9":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")

def main():
    print("🚀 Starting Deployed App Client...")
    
    client = DeployedAppClient()
    
    # Test connection first
    if client.test_connection():
        print("🎉 Ready to interact with your deployed app!")
        interactive_menu(client)
    else:
        print("❌ Could not connect to deployed app. Check if it's running.")

if __name__ == "__main__":
    main() 