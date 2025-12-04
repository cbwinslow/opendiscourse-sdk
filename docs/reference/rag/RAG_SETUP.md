# RAG Database Setup for OpenDiscourse

## 🎯 **OBJECTIVE**
Vectorize all documentation and code for intelligent search and context retrieval.

---

## 🏆 **CHOSEN SOLUTION: PGVector**

### **Why PGVector Over Alternatives**

| Database | Pros | Cons | Decision |
|----------|------|------|----------|
| **PGVector** | ✅ Native PostgreSQL extension<br>✅ No additional infrastructure<br>✅ Same database as data<br>✅ Easy setup | ❌ Limited to PostgreSQL | **CHOSEN** |
| ChromaDB | ✅ Easy to use<br>✅ Good documentation | ❌ Separate service<br>❌ More complexity | Rejected |
| Weaviate | ✅ Powerful features | ❌ Heavy infrastructure<br>❌ Complex setup | Rejected |
| Cloudflare Vectorizer | ✅ Managed service | ❌ External dependency<br>❌ Not free tier | Rejected |

---

## 📋 **SETUP INSTRUCTIONS**

### **Step 1: Install PGVector**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15-pgvector

# Or compile from source
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### **Step 2: Enable Extension in Database**
```sql
-- Connect to opendiscourse database
psql -d opendiscourse

-- Enable extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
\dx vector
```

### **Step 3: Create Vector Tables**
```sql
-- Documents table for markdown files
CREATE TABLE IF NOT EXISTS rag.documents (
    id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    content TEXT NOT NULL,
    file_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    embedding vector(1536)  -- OpenAI embedding size
);

-- Code snippets table for code files
CREATE TABLE IF NOT EXISTS rag.code_snippets (
    id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,
    function_name TEXT,
    class_name TEXT,
    code_content TEXT NOT NULL,
    language TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    embedding vector(1536)
);

-- Create indexes for similarity search
CREATE INDEX ON rag.documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON rag.code_snippets USING ivfflat (embedding vector_cosine_ops);
```

---

## 🐍 **PYTHON SETUP**

### **Step 4: Install Python Dependencies**
```bash
pip install pgvector psycopg2-binary openai tiktoken python-dotenv
```

### **Step 5: Create Vectorization Script**
```python
#!/usr/bin/env python3
"""
OpenDiscourse RAG Vectorizer
Index all documentation and code for intelligent search
"""

import os
import sys
import psycopg2
from pathlib import Path
from typing import List, Dict, Any
import openai
from dotenv import load_dotenv
import tiktoken

# Load environment
load_dotenv()

class RAGVectorizer:
    """Vectorize OpenDiscourse documentation and code"""

    def __init__(self):
        self.conn = psycopg2.connect(
            database='opendiscourse',
            user='cbwinslow',
            host='/var/run/postgresql'
        )
        self.openai_client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def get_files_to_vectorize(self, root_dir: str) -> List[Dict[str, Any]]:
        """Get all files to vectorize"""
        files = []
        root_path = Path(root_dir)

        # Markdown files
        for md_file in root_path.rglob("*.md"):
            if '.git' not in str(md_file):
                files.append({
                    'path': str(md_file),
                    'type': 'markdown',
                    'name': md_file.name
                })

        # Python files
        for py_file in root_path.rglob("*.py"):
            if '.git' not in str(py_file):
                files.append({
                    'path': str(py_file),
                    'type': 'python',
                    'name': py_file.name
                })

        return files

    def chunk_content(self, content: str, max_tokens: int = 800) -> List[str]:
        """Split content into chunks"""
        chunks = []
        current_chunk = ""
        current_tokens = 0

        for line in content.split('\n'):
            line_tokens = len(self.tokenizer.encode(line))

            if current_tokens + line_tokens > max_tokens:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = line
                current_tokens = line_tokens
            else:
                current_chunk += '\n' + line
                current_tokens += line_tokens

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding from OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []

    def vectorize_markdown(self, file_info: Dict[str, Any]):
        """Vectorize markdown file"""
        try:
            with open(file_info['path'], 'r', encoding='utf-8') as f:
                content = f.read()

            # Split into chunks
            chunks = self.chunk_content(content)

            cursor = self.conn.cursor()

            for i, chunk in enumerate(chunks):
                embedding = self.get_embedding(chunk)
                if embedding:
                    cursor.execute("""
                        INSERT INTO rag.documents
                        (file_path, file_name, content, file_type, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (file_path) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            updated_at = NOW()
                    """, (
                        file_info['path'],
                        file_info['name'],
                        chunk,
                        file_info['type'],
                        embedding
                    ))

            self.conn.commit()
            cursor.close()
            print(f"✅ Vectorized {len(chunks)} chunks from {file_info['name']}")

        except Exception as e:
            print(f"❌ Error vectorizing {file_info['path']}: {e}")

    def vectorize_python(self, file_info: Dict[str, Any]):
        """Vectorize Python file with function-level granularity"""
        try:
            with open(file_info['path'], 'r', encoding='utf-8') as f:
                lines = f.readlines()

            cursor = self.conn.cursor()

            # Simple function detection
            current_function = None
            function_lines = []
            function_start = 0

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Detect function definition
                if stripped.startswith('def ') or stripped.startswith('class '):
                    # Save previous function
                    if current_function and function_lines:
                        code_content = ''.join(function_lines)
                        embedding = self.get_embedding(code_content)
                        if embedding:
                            cursor.execute("""
                                INSERT INTO rag.code_snippets
                                (file_path, function_name, code_content, language, line_start, line_end, embedding)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (file_path, function_name) DO UPDATE SET
                                    code_content = EXCLUDED.code_content,
                                    embedding = EXCLUDED.embedding
                            """, (
                                file_info['path'],
                                current_function,
                                code_content,
                                'python',
                                function_start,
                                i - 1,
                                embedding
                            ))

                    # Start new function
                    if stripped.startswith('def '):
                        current_function = stripped.split('(')[0].replace('def ', '').strip()
                    else:
                        current_function = stripped.split('(')[0].replace('class ', '').strip()

                    function_lines = [line]
                    function_start = i
                elif current_function:
                    function_lines.append(line)

            # Save last function
            if current_function and function_lines:
                code_content = ''.join(function_lines)
                embedding = self.get_embedding(code_content)
                if embedding:
                    cursor.execute("""
                        INSERT INTO rag.code_snippets
                        (file_path, function_name, code_content, language, line_start, line_end, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (file_path, function_name) DO UPDATE SET
                            code_content = EXCLUDED.code_content,
                            embedding = EXCLUDED.embedding
                    """, (
                        file_info['path'],
                        current_function,
                        code_content,
                        'python',
                        function_start,
                        len(lines) - 1,
                        embedding
                    ))

            self.conn.commit()
            cursor.close()
            print(f"✅ Vectorized functions from {file_info['name']}")

        except Exception as e:
            print(f"❌ Error vectorizing {file_info['path']}: {e}")

    def vectorize_all(self, root_dir: str = "."):
        """Vectorize all files in directory"""
        files = self.get_files_to_vectorize(root_dir)

        print(f"🚀 Found {len(files)} files to vectorize")

        for file_info in files:
            if file_info['type'] == 'markdown':
                self.vectorize_markdown(file_info)
            elif file_info['type'] == 'python':
                self.vectorize_python(file_info)

        print(f"🎉 Vectorization complete!")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar content"""
        query_embedding = self.get_embedding(query)

        cursor = self.conn.cursor()

        # Search documents
        cursor.execute("""
            SELECT file_path, file_name, content, file_type,
                   1 - (embedding <=> %s::vector) as similarity
            FROM rag.documents
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, limit))

        docs = cursor.fetchall()

        # Search code snippets
        cursor.execute("""
            SELECT file_path, function_name, code_content,
                   1 - (embedding <=> %s::vector) as similarity
            FROM rag.code_snippets
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (query_embedding, query_embedding, limit))

        code = cursor.fetchall()
        cursor.close()

        return {
            'documents': docs,
            'code': code
        }

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    vectorizer = RAGVectorizer()

    # Vectorize all files
    vectorizer.vectorize_all("/home/cbwinslow/Videos/opendiscourse")

    # Test search
    results = vectorizer.search("database connection standards")
    print("\n🔍 Search Results:")
    for doc in results['documents'][:3]:
        print(f"📄 {doc[1]} (similarity: {doc[4]:.3f})")

    vectorizer.close()
```

### **Step 6: Create Search Interface**
```python
#!/usr/bin/env python3
"""
RAG Search Interface for OpenDiscourse
"""

import sys
import os
sys.path.append('/home/cbwinslow/Videos/opendiscourse')

from rag_vectorizer import RAGVectorizer

def main():
    vectorizer = RAGVectorizer()

    print("🔍 OpenDiscourse RAG Search")
    print("Enter search query or 'quit' to exit:")

    while True:
        query = input("\n🔎 Search: ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            break

        if not query:
            continue

        results = vectorizer.search(query, limit=3)

        print(f"\n📄 Documents ({len(results['documents'])} results):")
        for doc in results['documents']:
            print(f"  📋 {doc[1]} (similarity: {doc[4]:.3f})")
            print(f"     📁 {doc[0]}")
            print(f"     📝 {doc[2][:200]}...")
            print()

        print(f"🐍 Code ({len(results['code'])} results):")
        for code in results['code']:
            print(f"  🔧 {code[1]} (similarity: {code[3]:.3f})")
            print(f"     📁 {code[0]}")
            print(f"     💻 {code[2][:200]}...")
            print()

    vectorizer.close()

if __name__ == "__main__":
    main()
```

---

## 🚀 **USAGE EXAMPLES**

### **Vectorize All Files**
```bash
cd /home/cbwinslow/Videos/opendiscourse
python rag_vectorizer.py
```

### **Search for Information**
```bash
python rag_search.py
🔎 Search: database connection standards
📄 Documents (3 results):
  📋 agents.md (similarity: 0.892)
     📁 /home/cbwinslow/Videos/opendiscourse/agents.md
     📝 REQUIRED DATABASE CONNECTION PATTERN conn = psycopg2.connect( database='opendiscourse', # MUST be 'opendiscourse' user='cbwinslow', host='/var/run/postgresql' # MUST use Unix socket )...
```

---

## 📊 **BENEFITS**

### **For AI Agents**
- **Context Retrieval**: Find relevant documentation instantly
- **Code Discovery**: Locate functions and examples
- **Decision History**: Understand past decisions
- **Standards Compliance**: Find required patterns

### **For Developers**
- **Quick Search**: Find any information instantly
- **Semantic Search**: Search by meaning, not keywords
- **Code Examples**: Find similar implementations
- **Documentation Access**: All docs in one place

---

## 🔄 **MAINTENANCE**

### **Regular Updates**
```bash
# Re-vectorize when files change
python rag_vectorizer.py

# Schedule daily updates
crontab -e
# Add: 0 2 * * * cd /home/cbwinslow/Videos/opendiscourse && python rag_vectorizer.py
```

### **Monitoring**
```sql
-- Check vectorization status
SELECT
    file_type,
    COUNT(*) as total_files,
    COUNT(embedding) as vectorized_files
FROM rag.documents
GROUP BY file_type;

-- Check storage usage
SELECT pg_size_pretty(pg_total_relation_size('rag.documents')) as docs_size,
       pg_size_pretty(pg_total_relation_size('rag.code_snippets')) as code_size;
```

---

## 🎯 **NEXT STEPS**

1. **Install PGVector extension**
2. **Create vector tables**
3. **Run vectorization script**
4. **Test search functionality**
5. **Integrate with AI agent workflows**

---

*Last Updated: 2025-11-26*
*Priority: Medium (after bills ingestion fixed)*
*Impact: High - improves agent efficiency and knowledge access*
