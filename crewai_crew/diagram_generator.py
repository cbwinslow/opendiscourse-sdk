"""
Diagram Generation System for OpenDiscourse CrewAI Analysis
Creates architectural diagrams, flowcharts, and visual representations
"""

import os
import json
import subprocess
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DiagramGenerator:
    """Generate diagrams for codebase analysis and documentation"""

    def __init__(self, base_path: str = "/home/cbwinslow/Videos/opendiscourse"):
        self.base_path = base_path
        self.diagrams_dir = os.path.join(base_path, "crewai_diagrams")
        os.makedirs(self.diagrams_dir, exist_ok=True)

    def generate_system_architecture_diagram(self) -> Dict[str, Any]:
        """Generate system architecture diagram using Mermaid"""

        diagram_content = """graph TB
    subgraph "OpenDiscourse Platform Architecture"
        subgraph "Data Sources"
            A[Congress.gov API]
            B[OpenStates API]
            C[GovInfo API]
        end

        subgraph "Ingestion Layer"
            D[Congress Data Ingestion]
            E[OpenStates Scraper]
            F[GovInfo Processor]
        end

        subgraph "Data Processing"
            G[Rate Limiting System]
            H[Data Validation]
            I[Transformation Pipeline]
        end

        subgraph "Database Layer"
            J[(Congress Database)]
            K[(OpenStates Database)]
            L[(Vector Database)]
        end

        subgraph "AI/ML Components"
            M[NLP Processor]
            N[Document Embeddings]
            O[RAG Pipeline]
        end

        subgraph "API & Web Layer"
            P[REST API]
            Q[Web Interface]
            R[Monitoring System]
        end
    end

    A --> D
    B --> E
    C --> F
    D --> G
    E --> G
    F --> G
    G --> H
    H --> I
    I --> J
    I --> K
    I --> L
    L --> M
    M --> N
    N --> O
    O --> P
    P --> Q
    P --> R

    classDef source fill:#e1f5fe
    classDef process fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef ai fill:#fff3e0
    classDef api fill:#fce4ec

    class A,B,C source
    class D,E,F,G,H,I process
    class J,K,L storage
    class M,N,O ai
    class P,Q,R api"""

        diagram_path = os.path.join(self.diagrams_dir, "system_architecture.mmd")
        with open(diagram_path, 'w') as f:
            f.write(diagram_content)

        return {
            "diagram_type": "system_architecture",
            "file_path": diagram_path,
            "format": "mermaid",
            "description": "Complete OpenDiscourse system architecture diagram"
        }

    def generate_data_flow_diagram(self) -> Dict[str, Any]:
        """Generate data flow diagram"""

        diagram_content = """graph LR
    subgraph "Data Flow Pipeline"
        subgraph "Input Sources"
            A[Congress API]
            B[OpenStates API]
            C[GovInfo API]
        end

        subgraph "Rate Limiting"
            D[Congress Limiter<br/>1000 req/hour]
            E[OpenStates Limiter<br/>1000 req/hour]
            F[GovInfo Limiter<br/>500 req/hour]
        end

        subgraph "Processing Queue"
            G[Congress Queue]
            H[OpenStates Queue]
            I[GovInfo Queue]
        end

        subgraph "Validation Layer"
            J[Schema Validation]
            K[Business Rules]
            L[Data Quality Checks]
        end

        subgraph "Storage Layer"
            M[Congress DB]
            N[OpenStates DB]
            O[Vector Store]
        end

        subgraph "Search & Retrieval"
            P[Semantic Search]
            Q[Full Text Search]
            R[Hybrid Search]
        end
    end

    A --> D
    B --> E
    C --> F
    D --> G
    E --> H
    F --> I
    G --> J
    H --> K
    I --> L
    J --> M
    K --> N
    L --> O
    M --> P
    N --> Q
    O --> R

    classDef source fill:#e3f2fd
    classDef process fill:#f1f8e9
    classDef storage fill:#e8f5e8
    classDef search fill:#fce4ec

    class A,B,C source
    class D,E,F,G,H,I,J,K,L process
    class M,N,O storage
    class P,Q,R search"""

        diagram_path = os.path.join(self.diagrams_dir, "data_flow_diagram.mmd")
        with open(diagram_path, 'w') as f:
            f.write(diagram_content)

        return {
            "diagram_type": "data_flow",
            "file_path": diagram_path,
            "format": "mermaid",
            "description": "Data flow through the ingestion and processing pipeline"
        }

    def generate_database_schema_diagram(self) -> Dict[str, Any]:
        """Generate database schema diagram"""

        diagram_content = """erDiagram
    CONGRESS_MEMBERS {
        string bioguide_id PK
        string first_name
        string last_name
        string middle_name
        string suffix
        string full_name
        int congress
        string chamber
        string state
        int district
        date birth_date
        string party
        string gender
        string religion
        date term_start_date
        date term_end_date
        timestamp created_at
        timestamp updated_at
    }

    CONGRESS_BILLS {
        int bill_id PK
        int congress
        string bill_type
        int bill_number
        string origin_chamber
        date introduced_date
        date latest_action_date
        string latest_action_text
        string policy_area
        string title
        string sponsor_bioguide_id FK
        timestamp created_at
        timestamp updated_at
    }

    OPENSTATES_PEOPLE {
        string person_id PK
        string name
        string family_name
        string given_name
        string image
        string gender
        string biography
        date birth_date
        date death_date
        string primary_party
        string jurisdiction_id FK
        json current_role_data
        timestamp created_at
        timestamp updated_at
    }

    OPENSTATES_JURISDICTIONS {
        string jurisdiction_id PK
        string name
        string classification
        string url
        json feature_flags
        json divisions
        json links
        timestamp created_at
        timestamp updated_at
    }

    MONITORING_TASKS {
        int task_id PK
        string task_name
        string status
        string record_type
        int records_processed
        int records_total
        float progress_percentage
        json metrics
        timestamp started_at
        timestamp completed_at
        timestamp created_at
    }

    CONGRESS_MEMBERS ||--o{ CONGRESS_BILLS : "sponsors"
    OPENSTATES_JURISDICTIONS ||--o{ OPENSTATES_PEOPLE : "contains"
    CONGRESS_MEMBERS ||--o{ MONITORING_TASKS : "tracked_by"
    OPENSTATES_PEOPLE ||--o{ MONITORING_TASKS : "tracked_by" """

        diagram_path = os.path.join(self.diagrams_dir, "database_schema.mmd")
        with open(diagram_path, 'w') as f:
            f.write(diagram_content)

        return {
            "diagram_type": "database_schema",
            "file_path": diagram_path,
            "format": "mermaid",
            "description": "Database schema with relationships and constraints"
        }

    def generate_api_flow_diagram(self) -> Dict[str, Any]:
        """Generate API workflow diagram"""

        diagram_content = """sequenceDiagram
    participant Client
    participant API_Gateway
    participant Auth_Service
    participant Data_Service
    participant Database
    participant Cache
    participant Search_Engine

    Client->>API_Gateway: GET /api/search?q=congress+bill
    API_Gateway->>Auth_Service: Validate Token
    Auth_Service-->>API_Gateway: Token Valid

    API_Gateway->>Data_Service: Search Request
    Data_Service->>Cache: Check Cache
    alt Cache Hit
        Cache-->>Data_Service: Return Cached Results
    else Cache Miss
        Data_Service->>Database: Query Database
        Database-->>Data_Service: Raw Data
        Data_Service->>Search_Engine: Semantic Search
        Search_Engine-->>Data_Service: Processed Results
        Data_Service->>Cache: Store Results
    end

    Data_Service-->>API_Gateway: Search Results
    API_Gateway-->>Client: JSON Response

    Note over Client,Search_Engine: Real-time monitoring tracks<br/>all API calls and performance"""

        diagram_path = os.path.join(self.diagrams_dir, "api_flow_diagram.mmd")
        with open(diagram_path, 'w') as f:
            f.write(diagram_content)

        return {
            "diagram_type": "api_flow",
            "file_path": diagram_path,
            "format": "mermaid",
            "description": "API workflow and request processing sequence"
        }

    def generate_monitoring_architecture_diagram(self) -> Dict[str, Any]:
        """Generate monitoring and observability architecture"""

        diagram_content = """graph TB
    subgraph "Monitoring & Observability"
        subgraph "Application Layer"
            A[OpenDiscourse App]
            B[Ingestion Scripts]
            C[API Endpoints]
        end

        subgraph "Metrics Collection"
            D[Application Metrics]
            E[Database Metrics]
            F[API Metrics]
            G[Business Metrics]
        end

        subgraph "Logging & Events"
            H[Structured Logs]
            I[Error Tracking]
            J[Performance Logs]
            K[Audit Logs]
        end

        subgraph "Monitoring Stack"
            L[Prometheus]
            M[Grafana]
            N[Alert Manager]
        end

        subgraph "Alerting"
            O[Critical Alerts]
            P[Warning Alerts]
            Q[Info Notifications]
        end

        subgraph "Dashboard & Reporting"
            R[Real-time Dashboard]
            S[Historical Reports]
            T[Executive Summary]
        end
    end

    A --> D
    B --> D
    C --> E
    C --> F
    A --> H
    B --> H
    C --> I

    D --> L
    E --> L
    F --> L
    G --> L
    H --> M
    I --> N

    L --> N
    N --> O
    N --> P
    M --> R
    M --> S
    M --> T

    classDef app fill:#e3f2fd
    classDef metrics fill:#e8f5e8
    classDef logs fill:#fff3e0
    classDef monitoring fill:#f3e5f5
    classDef alerts fill:#ffebee
    classDef dashboard fill:#e0f2f1

    class A,B,C app
    class D,E,F,G metrics
    class H,I,J,K logs
    class L,M,N monitoring
    class O,P,Q alerts
    class R,S,T dashboard"""

        diagram_path = os.path.join(self.diagrams_dir, "monitoring_architecture.mmd")
        with open(diagram_path, 'w') as f:
            f.write(diagram_content)

        return {
            "diagram_type": "monitoring_architecture",
            "file_path": diagram_path,
            "format": "mermaid",
            "description": "Monitoring and observability architecture diagram"
        }

    def generate_all_diagrams(self) -> Dict[str, Any]:
        """Generate all diagrams for the project"""

        diagrams = {}

        print("🎨 Generating system architecture diagram...")
        diagrams["system_architecture"] = self.generate_system_architecture_diagram()

        print("📊 Generating data flow diagram...")
        diagrams["data_flow"] = self.generate_data_flow_diagram()

        print("🗄️ Generating database schema diagram...")
        diagrams["database_schema"] = self.generate_database_schema_diagram()

        print("🔄 Generating API flow diagram...")
        diagrams["api_flow"] = self.generate_api_flow_diagram()

        print("📈 Generating monitoring architecture diagram...")
        diagrams["monitoring_architecture"] = self.generate_monitoring_architecture_diagram()

        # Create summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_diagrams": len(diagrams),
            "diagrams": diagrams,
            "output_directory": self.diagrams_dir,
            "format": "mermaid",
            "next_steps": [
                "View diagrams in a Mermaid-compatible editor",
                "Convert to PNG/PDF using Mermaid CLI",
                "Include in documentation and presentations"
            ]
        }

        # Save summary
        summary_path = os.path.join(self.diagrams_dir, "diagrams_summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        return summary

    def create_diagram_viewer(self) -> str:
        """Create HTML viewer for Mermaid diagrams"""

        viewer_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenDiscourse System Architecture Diagrams</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .diagram-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        .diagram-card {
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            color: #333;
        }
        .diagram-card h3 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        .diagram-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 15px;
            min-height: 400px;
            overflow: auto;
        }
        .description {
            margin: 10px 0;
            font-style: italic;
            color: #666;
        }
        .file-path {
            background: #f8f9fa;
            padding: 8px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9em;
            margin: 10px 0;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>🏛️ OpenDiscourse System Architecture</h1>
        <p style="text-align: center; font-size: 1.1em; margin-bottom: 30px;">
            Comprehensive architectural diagrams generated by CrewAI analysis
        </p>

        <div class="diagram-grid">
            <div class="diagram-card">
                <h3>🏗️ System Architecture</h3>
                <div class="description">Complete system overview showing all major components and their interactions</div>
                <div class="file-path">File: crewai_diagrams/system_architecture.mmd</div>
                <div class="diagram-container">
                    <div class="mermaid">
graph TB
    subgraph "OpenDiscourse Platform Architecture"
        subgraph "Data Sources"
            A[Congress.gov API]
            B[OpenStates API]
            C[GovInfo API]
        end

        subgraph "Ingestion Layer"
            D[Congress Data Ingestion]
            E[OpenStates Scraper]
            F[GovInfo Processor]
        end

        subgraph "Data Processing"
            G[Rate Limiting System]
            H[Data Validation]
            I[Transformation Pipeline]
        end

        subgraph "Database Layer"
            J[(Congress Database)]
            K[(OpenStates Database)]
            L[(Vector Database)]
        end

        subgraph "AI/ML Components"
            M[NLP Processor]
            N[Document Embeddings]
            O[RAG Pipeline]
        end

        subgraph "API & Web Layer"
            P[REST API]
            Q[Web Interface]
            R[Monitoring System]
        end
    end

    A --> D
    B --> E
    C --> F
    D --> G
    E --> G
    F --> G
    G --> H
    H --> I
    I --> J
    I --> K
    I --> L
    L --> M
    M --> N
    N --> O
    O --> P
    P --> Q
    P --> R

    classDef source fill:#e1f5fe
    classDef process fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef ai fill:#fff3e0
    classDef api fill:#fce4ec

    class A,B,C source
    class D,E,F,G,H,I process
    class J,K,L storage
    class M,N,O ai
    class P,Q,R api
                    </div>
                </div>
            </div>

            <div class="diagram-card">
                <h3>📊 Data Flow</h3>
                <div class="description">Data flow through ingestion, processing, and storage pipeline</div>
                <div class="file-path">File: crewai_diagrams/data_flow_diagram.mmd</div>
                <div class="diagram-container">
                    <div class="mermaid">
graph LR
    subgraph "Data Flow Pipeline"
        subgraph "Input Sources"
            A[Congress API]
            B[OpenStates API]
            C[GovInfo API]
        end

        subgraph "Rate Limiting"
            D[Congress Limiter<br/>1000 req/hour]
            E[OpenStates Limiter<br/>1000 req/hour]
            F[GovInfo Limiter<br/>500 req/hour]
        end

        subgraph "Processing Queue"
            G[Congress Queue]
            H[OpenStates Queue]
            I[GovInfo Queue]
        end

        subgraph "Validation Layer"
            J[Schema Validation]
            K[Business Rules]
            L[Data Quality Checks]
        end

        subgraph "Storage Layer"
            M[Congress DB]
            N[OpenStates DB]
            O[Vector Store]
        end

        subgraph "Search & Retrieval"
            P[Semantic Search]
            Q[Full Text Search]
            R[Hybrid Search]
        end
    end

    A --> D
    B --> E
    C --> F
    D --> G
    E --> H
    F --> I
    G --> J
    H --> K
    I --> L
    J --> M
    K --> N
    L --> O
    M --> P
    N --> Q
    O --> R

    classDef source fill:#e3f2fd
    classDef process fill:#f1f8e9
    classDef storage fill:#e8f5e8
    classDef search fill:#fce4ec

    class A,B,C source
    class D,E,F,G,H,I,J,K,L process
    class M,N,O storage
    class P,Q,R search
                    </div>
                </div>
            </div>

            <div class="diagram-card">
                <h3>🗄️ Database Schema</h3>
                <div class="description">Database structure and relationships between entities</div>
                <div class="file-path">File: crewai_diagrams/database_schema.mmd</div>
                <div class="diagram-container">
                    <div class="mermaid">
erDiagram
    CONGRESS_MEMBERS {
        string bioguide_id PK
        string first_name
        string last_name
        string full_name
        int congress
        string chamber
        string state
        int district
        string party
        date term_start_date
        date term_end_date
    }

    CONGRESS_BILLS {
        int bill_id PK
        int congress
        string bill_type
        int bill_number
        string origin_chamber
        date introduced_date
        string title
        string sponsor_bioguide_id FK
    }

    OPENSTATES_PEOPLE {
        string person_id PK
        string name
        string family_name
        string given_name
        string primary_party
        string jurisdiction_id FK
    }

    OPENSTATES_JURISDICTIONS {
        string jurisdiction_id PK
        string name
        string classification
        string url
    }

    CONGRESS_MEMBERS ||--o{ CONGRESS_BILLS : "sponsors"
    OPENSTATES_JURISDICTIONS ||--o{ OPENSTATES_PEOPLE : "contains"
                    </div>
                </div>
            </div>

            <div class="diagram-card">
                <h3>📈 Monitoring Architecture</h3>
                <div class="description">Monitoring stack and observability architecture</div>
                <div class="file-path">File: crewai_diagrams/monitoring_architecture.mmd</div>
                <div class="diagram-container">
                    <div class="mermaid">
graph TB
    subgraph "Monitoring & Observability"
        subgraph "Application Layer"
            A[OpenDiscourse App]
            B[Ingestion Scripts]
            C[API Endpoints]
        end

        subgraph "Metrics Collection"
            D[Application Metrics]
            E[Database Metrics]
            F[API Metrics]
            G[Business Metrics]
        end

        subgraph "Monitoring Stack"
            L[Prometheus]
            M[Grafana]
            N[Alert Manager]
        end

        subgraph "Alerting"
            O[Critical Alerts]
            P[Warning Alerts]
        end

        subgraph "Dashboard & Reporting"
            R[Real-time Dashboard]
            S[Executive Summary]
        end
    end

    A --> D
    B --> D
    C --> E
    C --> F
    A --> L
    B --> L
    L --> M
    M --> R
    N --> O
    N --> P
    M --> S

    classDef app fill:#e3f2fd
    classDef metrics fill:#e8f5e8
    classDef monitoring fill:#f3e5f5
    classDef alerts fill:#ffebee
    classDef dashboard fill:#e0f2f1

    class A,B,C app
    class D,E,F,G metrics
    class L,M,N monitoring
    class O,P alerts
    class R,S dashboard
                    </div>
                </div>
            </div>
        </div>

        <div style="margin-top: 40px; text-align: center; color: rgba(255,255,255,0.8);">
            <p>Generated by <strong>CrewAI Multi-Agent Analysis</strong> on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p>OpenDiscourse Platform - Legislative Data Analysis System</p>
        </div>
    </div>

    <script>
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose'
        });
    </script>
</body>
</html>"""

        viewer_path = os.path.join(self.diagrams_dir, "diagram_viewer.html")
        with open(viewer_path, 'w') as f:
            f.write(viewer_html)

        return viewer_path
