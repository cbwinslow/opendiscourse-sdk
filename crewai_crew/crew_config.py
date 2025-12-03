"""
CrewAI Configuration for OpenDiscourse Project Analysis
Comprehensive multi-agent codebase review and documentation system
"""

import os
from crewai import Agent, Task, Crew, Process
from crewai.memory import LongTermMemory
from crewai.tools import BaseTool
from crewai.cache import SimpleCache
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenDiscourseCrewConfig:
    """Main configuration class for OpenDiscourse CrewAI crew"""

    def __init__(self, base_path: str = "/home/cbwinslow/Videos/opendiscourse"):
        self.base_path = base_path
        self.memory = LongTermMemory()
        self.cache = SimpleCache()

    def get_specialized_agents(self) -> Dict[str, Agent]:
        """Initialize and return all specialized agents"""

        agents = {}

        # Chief Technology Officer (CTO) - Strategic oversight and architecture
        agents['cto'] = Agent(
            role="Chief Technology Officer",
            goal="Provide strategic technology leadership and architectural oversight for the OpenDiscourse platform",
            backstory="""You are an experienced CTO with 15+ years in software architecture and
            technology strategy. You have expertise in legislative technology platforms, data
            ingestion systems, and large-scale web applications. Your role is to ensure
            technical excellence, scalable architecture, and alignment with business objectives.""",
            verbose=True,
            allow_delegation=True,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=300
        )

        # CEO - Business strategy and stakeholder alignment
        agents['ceo'] = Agent(
            role="Chief Executive Officer",
            goal="Align technical decisions with business strategy and ensure stakeholder value delivery",
            backstory="""You are a strategic business leader focused on value delivery, stakeholder
            management, and ensuring the OpenDiscourse platform serves its mission of improving
            legislative transparency and civic engagement. You understand the political and
            social impact of the platform.""",
            verbose=True,
            allow_delegation=True,
            max_iter=2,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=240
        )

        # Senior Software Engineer - Code quality and architecture
        agents['senior_engineer'] = Agent(
            role="Senior Software Engineer",
            goal="Ensure code quality, architectural integrity, and implementation best practices",
            backstory="""You are a senior software engineer with expertise in Python, web development,
            database design, API development, and system architecture. You have experience with
            data ingestion pipelines, PostgreSQL, and distributed systems. You focus on code
            maintainability, scalability, and performance optimization.""",
            verbose=True,
            allow_delegation=False,
            max_iter=4,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=600
        )

        # Python Expert - Python-specific code review and optimization
        agents['python_expert'] = Agent(
            role="Python Expert",
            goal="Review Python code quality, identify optimizations, and ensure best practices",
            backstory="""You are a Python expert with deep knowledge of the language, frameworks,
            and ecosystem. You specialize in Pythonic code patterns, performance optimization,
            async programming, and modern Python features. You understand the requirements.txt
            dependencies and can provide recommendations for improvement.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=480
        )

        # Database Administrator - Database design and optimization
        agents['dba'] = Agent(
            role="Database Administrator",
            goal="Analyze database design, optimize queries, and ensure data integrity",
            backstory="""You are a database administrator with expertise in PostgreSQL, database
            design, query optimization, indexing strategies, and data modeling. You understand
            the database protection rules and can analyze the schema design, foreign key
            relationships, and recommend optimizations for the OpenDiscourse platform.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=450
        )

        # AI Specialist - AI/ML components and algorithmic considerations
        agents['ai_specialist'] = Agent(
            role="AI Specialist",
            goal="Review AI/ML components, NLP processing, and algorithmic implementations",
            backstory="""You are an AI specialist with expertise in machine learning, natural
            language processing, and AI pipeline design. You understand the RAG implementation,
            document processing, and can evaluate the AI components of the OpenDiscourse platform
            including the OpenStates scrapers and Congress data processing.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=420
        )

        # Algorithm Expert - Data processing and algorithmic efficiency
        agents['algorithm_expert'] = Agent(
            role="Algorithm Expert",
            goal="Analyze algorithmic complexity, data processing efficiency, and optimization opportunities",
            backstory="""You are an algorithm expert with focus on computational complexity,
            data structures, and algorithmic optimization. You can analyze the data ingestion
            pipelines, rate limiting algorithms, parallel processing, and identify optimization
            opportunities in the codebase.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=360
        )

        # Documentation Expert - Code documentation and technical writing
        agents['doc_expert'] = Agent(
            role="Documentation Expert",
            goal="Ensure comprehensive documentation, maintain standards, and improve clarity",
            backstory="""You are a documentation expert with technical writing skills and experience
            in API documentation, code comments, and user guides. You can analyze the existing
            documentation quality, identify gaps, and recommend improvements for the OpenDiscourse
            platform documentation structure.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=300
        )

        # Business Analyst - Requirements analysis and stakeholder needs
        agents['business_analyst'] = Agent(
            role="Business Analyst",
            goal="Align technical implementation with business requirements and user needs",
            backstory="""You are a business analyst focused on requirements gathering, stakeholder
            alignment, and ensuring technical solutions meet business objectives. You understand
            the legislative data domain and can bridge technical and business perspectives.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=270
        )

        # DevOps Engineer - Infrastructure, deployment, and monitoring
        agents['devops'] = Agent(
            role="DevOps Engineer",
            goal="Review infrastructure setup, deployment processes, and monitoring capabilities",
            backstory="""You are a DevOps engineer with expertise in infrastructure as code,
            deployment automation, monitoring, and system reliability. You can analyze the
            Docker configurations, Cloudflare Workers, monitoring scripts, and recommend
            infrastructure improvements.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=330
        )

        # Security Specialist - Security analysis and recommendations
        agents['security_specialist'] = Agent(
            role="Security Specialist",
            goal="Identify security vulnerabilities and recommend security improvements",
            backstory="""You are a security specialist with expertise in application security,
            API security, database security, and compliance. You can analyze the security
            aspects of the OpenDiscourse platform including API key management, database
            connections, and overall security posture.""",
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=280
        )

        return agents

    def get_codebase_analysis_tasks(self, agents: Dict[str, Agent]) -> List[Task]:
        """Create tasks for comprehensive codebase analysis"""

        tasks = []

        # Task 1: Architecture and Strategy Review (CTO + CEO)
        tasks.append(Task(
            description=f"""
            Conduct a comprehensive architectural and strategic review of the OpenDiscourse codebase.

            Analyze the following areas:
            1. Overall system architecture and design patterns
            2. Scalability considerations and bottlenecks
            3. Technology stack alignment with business goals
            4. Integration patterns between components
            5. Strategic recommendations for Project v2 alignment

            Focus on the following directories:
            - {self.base_path}/ (root level structure)
            - {self.base_path}/opendiscourse/ (main application)
            - {self.base_path}/scripts/ (ingestion scripts)
            - {self.base_path}/docs/ (documentation)

            Provide strategic insights and high-level architectural recommendations.
            """,
            agent=agents['cto'],
            expected_output="Comprehensive architectural analysis with strategic recommendations"
        ))

        # Task 2: Code Quality and Best Practices Review (Senior Engineer + Python Expert)
        tasks.append(Task(
            description=f"""
            Perform detailed code quality analysis focusing on Python best practices and implementation quality.

            Analyze:
            1. Python code quality and adherence to PEP standards
            2. Code structure and design patterns
            3. Error handling and exception management
            4. Performance optimization opportunities
            5. Code maintainability and readability

            Focus on Python files in:
            - {self.base_path}/scripts/ (all Python scripts)
            - {self.base_path}/opendiscourse/ (main application code)
            - {self.base_path}/cli_tool.py
            - {self.base_path}/test_minimal.py

            Provide specific code improvement recommendations with examples.
            """,
            agent=agents['senior_engineer'],
            expected_output="Detailed code quality report with specific improvement recommendations"
        ))

        # Task 3: Database Design and Optimization Review (DBA + Algorithm Expert)
        tasks.append(Task(
            description=f"""
            Analyze the database design, schema, and data processing algorithms.

            Review:
            1. Database schema design and normalization
            2. Indexing strategies and query optimization
            3. Data ingestion pipeline efficiency
            4. Foreign key relationships and constraints
            5. Data integrity and consistency measures

            Examine:
            - Database connection patterns in scripts
            - Data transformation algorithms
            - Rate limiting and pagination logic
            - Parallel processing strategies

            Provide database optimization recommendations.
            """,
            agent=agents['dba'],
            expected_output="Database design analysis with optimization recommendations"
        ))

        # Task 4: AI/ML and NLP Components Review (AI Specialist + Algorithm Expert)
        tasks.append(Task(
            description=f"""
            Review AI/ML components, NLP processing, and algorithmic implementations.

            Analyze:
            1. AI pipeline design and implementation
            2. Natural language processing components
            3. Document processing and embedding strategies
            4. RAG implementation and vector database integration
            5. Algorithmic efficiency and complexity

            Focus on:
            - {self.base_path}/nlp/ directory
            - {self.base_path}/rag/ directory
            - Document processing scripts
            - Data ingestion algorithms

            Provide AI/ML improvement recommendations.
            """,
            agent=agents['ai_specialist'],
            expected_output="AI/ML components analysis with enhancement recommendations"
        ))

        # Task 5: Documentation and Standards Review (Doc Expert + Business Analyst)
        tasks.append(Task(
            description=f"""
            Conduct comprehensive documentation analysis and standards compliance review.

            Review:
            1. Documentation completeness and quality
            2. Code documentation and comments
            3. API documentation coverage
            4. User guides and technical guides
            5. Standards compliance (coding, documentation, security)

            Examine:
            - {self.base_path}/docs/ directory
            - {self.base_path}/README.md
            - {self.base_path}/CONTRIBUTING.md
            - Code comments and docstrings
            - Agent documentation standards

            Provide documentation improvement plan.
            """,
            agent=agents['doc_expert'],
            expected_output="Documentation analysis with improvement recommendations"
        ))

        # Task 6: Security and Infrastructure Review (Security Specialist + DevOps)
        tasks.append(Task(
            description=f"""
            Analyze security posture and infrastructure setup.

            Review:
            1. API key management and security
            2. Database security and access patterns
            3. Docker and deployment security
            4. Infrastructure as code and configuration
            5. Monitoring and logging security

            Examine:
            - {self.base_path}/.env.example
            - {self.base_path}/docker-compose files
            - {self.base_path}/monitoring/ directory
            - Security practices in scripts

            Provide security and infrastructure recommendations.
            """,
            agent=agents['security_specialist'],
            expected_output="Security and infrastructure analysis with recommendations"
        ))

        # Task 7: Business Requirements and User Experience Review (Business Analyst + CEO)
        tasks.append(Task(
            description=f"""
            Analyze business alignment and user experience considerations.

            Review:
            1. Business requirements alignment
            2. User journey and experience
            3. Stakeholder value delivery
            4. Mission and vision alignment
            5. Project v2 strategic planning

            Analyze:
            - Project goals and objectives
            - User documentation and guides
            - Feature completeness and roadmaps
            - Business impact assessments

            Provide business strategy recommendations.
            """,
            agent=agents['business_analyst'],
            expected_output="Business alignment analysis with strategic recommendations"
        ))

        return tasks

    def create_crew(self) -> Crew:
        """Create and configure the complete CrewAI crew"""

        agents = self.get_specialized_agents()
        tasks = self.get_codebase_analysis_tasks(agents)

        # Create crew with sequential process
        crew = Crew(
            agents=list(agents.values()),
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=self.memory,
            cache=self.cache,
            max_execution_time=3600  # 1 hour max execution
        )

        return crew

    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration for the crew"""

        return {
            "base_path": self.base_path,
            "agents": {
                "total_agents": 8,
                "specializations": [
                    "strategic_planning",
                    "code_quality",
                    "database_optimization",
                    "ai_ml_analysis",
                    "documentation_standards",
                    "security_infrastructure",
                    "business_alignment"
                ]
            },
            "tasks": {
                "total_tasks": 7,
                "estimated_duration": "2-4 hours",
                "output_formats": [
                    "architectural_analysis",
                    "code_quality_report",
                    "database_optimization_plan",
                    "ai_ml_improvement_recommendations",
                    "documentation_enhancement_plan",
                    "security_infrastructure_recommendations",
                    "business_strategy_analysis"
                ]
            },
            "outputs": {
                "reports_dir": f"{self.base_path}/crewai_reports/",
                "diagrams_dir": f"{self.base_path}/crewai_diagrams/",
                "recommendations_file": f"{self.base_path}/crewai_recommendations.md",
                "summary_report": f"{self.base_path}/crewai_executive_summary.md"
            }
        }
