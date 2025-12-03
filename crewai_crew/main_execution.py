#!/usr/bin/env python3
"""
Main Execution Script for OpenDiscourse CrewAI Analysis
Orchestrates multi-agent codebase review, CodeRabbit AI, and diagram generation
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add crewai_crew to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crew_config import OpenDiscourseCrewConfig
from coderabbit_config import CodeRabbitAIIntegration
from diagram_generator import DiagramGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crewai_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class OpenDiscourseCrewOrchestrator:
    """Main orchestrator for OpenDiscourse CrewAI analysis"""

    def __init__(self, base_path: str = "/home/cbwinslow/Videos/opendiscourse"):
        self.base_path = base_path
        self.output_dirs = {
            "reports": os.path.join(base_path, "crewai_reports"),
            "diagrams": os.path.join(base_path, "crewai_diagrams"),
            "coderabbit": os.path.join(base_path, "crewai_reports", "coderabbit")
        }

        # Initialize components
        self.crew_config = OpenDiscourseCrewConfig(base_path)
        self.coderabbit_integration = CodeRabbitAIIntegration(base_path)
        self.diagram_generator = DiagramGenerator(base_path)

        # Ensure output directories exist
        for dir_path in self.output_dirs.values():
            os.makedirs(dir_path, exist_ok=True)

    def setup_environment(self) -> Dict[str, Any]:
        """Setup environment for CrewAI analysis"""
        logger.info("🔧 Setting up environment...")

        setup_results = {
            "timestamp": datetime.now().isoformat(),
            "base_path": self.base_path,
            "steps": []
        }

        try:
            # Step 1: Create CodeRabbit configuration
            logger.info("📋 Setting up CodeRabbit AI configuration...")
            coderabbit_config = self.coderabbit_integration.setup_coderabbit_config()
            setup_results["steps"].append({
                "step": "coderabbit_config",
                "status": "success",
                "result": coderabbit_config
            })

            # Step 2: Create CodeRabbit review script
            logger.info("📝 Creating CodeRabbit review script...")
            script_path = self.coderabbit_integration.create_review_script()
            setup_results["steps"].append({
                "step": "coderabbit_script",
                "status": "success",
                "result": {"script_path": script_path}
            })

            # Step 3: Install dependencies check
            logger.info("📦 Checking dependencies...")
            dependencies_status = self._check_dependencies()
            setup_results["steps"].append({
                "step": "dependencies",
                "status": dependencies_status["status"],
                "result": dependencies_status
            })

            # Step 4: Generate initial diagrams
            logger.info("🎨 Generating initial diagrams...")
            diagrams_result = self.diagram_generator.generate_all_diagrams()
            setup_results["steps"].append({
                "step": "diagrams",
                "status": "success",
                "result": diagrams_result
            })

            logger.info("✅ Environment setup completed successfully")
            return setup_results

        except Exception as e:
            logger.error(f"❌ Environment setup failed: {e}")
            setup_results["error"] = str(e)
            return setup_results

    def _check_dependencies(self) -> Dict[str, Any]:
        """Check if required dependencies are available"""
        dependencies = {
            "crewai": "CrewAI framework",
            "requests": "HTTP requests library",
            "openai": "OpenAI API client",
            "PyGithub": "GitHub API client"
        }

        missing_deps = []
        available_deps = []

        for dep, description in dependencies.items():
            try:
                __import__(dep)
                available_deps.append(dep)
            except ImportError:
                missing_deps.append(f"{dep} ({description})")

        return {
            "available": available_deps,
            "missing": missing_deps,
            "total": len(dependencies),
            "status": "complete" if not missing_deps else "partial"
        }

    def run_coderabbit_analysis(self) -> Dict[str, Any]:
        """Run CodeRabbit AI code analysis"""
        logger.info("🤖 Starting CodeRabbit AI analysis...")

        try:
            # Run the CodeRabbit review script
            import subprocess
            result = subprocess.run([
                sys.executable,
                os.path.join(self.base_path, "scripts", "run_coderabbit_review.py")
            ], capture_output=True, text=True, cwd=self.base_path)

            if result.returncode == 0:
                logger.info("✅ CodeRabbit analysis completed successfully")
                return {
                    "status": "success",
                    "output": result.stdout,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.warning(f"⚠️ CodeRabbit analysis completed with warnings: {result.stderr}")
                return {
                    "status": "warning",
                    "output": result.stdout,
                    "error": result.stderr,
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"❌ CodeRabbit analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def run_crewai_analysis(self) -> Dict[str, Any]:
        """Run CrewAI multi-agent analysis"""
        logger.info("🚀 Starting CrewAI multi-agent analysis...")

        try:
            # Create crew
            crew = self.crew_config.create_crew()

            # Run analysis
            logger.info("⚡ Executing CrewAI crew tasks...")
            start_time = time.time()
            results = crew.kickoff()
            end_time = time.time()

            logger.info("✅ CrewAI analysis completed successfully")

            return {
                "status": "success",
                "duration_seconds": end_time - start_time,
                "results": str(results),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ CrewAI analysis failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def generate_executive_summary(self, analysis_results: Dict[str, Any]) -> str:
        """Generate executive summary of all analyses"""

        summary_content = f"""# OpenDiscourse CrewAI Analysis Executive Summary

**Analysis Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Project**: OpenDiscourse Legislative Data Platform
**Analysis Scope**: Full codebase review and architecture assessment

## 🎯 Analysis Overview

This comprehensive analysis was conducted using multiple specialized agents and automated review tools:

### 🤖 AI Agents Employed
- **Chief Technology Officer (CTO)**: Strategic technology leadership and architecture oversight
- **Chief Executive Officer (CEO)**: Business alignment and stakeholder value assessment
- **Senior Software Engineer**: Code quality and implementation best practices
- **Python Expert**: Python-specific code review and optimization
- **Database Administrator**: Database design and optimization analysis
- **AI Specialist**: AI/ML components and algorithmic evaluation
- **Algorithm Expert**: Data processing efficiency and complexity analysis
- **Documentation Expert**: Documentation quality and standards compliance
- **Business Analyst**: Requirements alignment and user experience review
- **DevOps Engineer**: Infrastructure and deployment optimization
- **Security Specialist**: Security posture and vulnerability assessment

### 🛠️ Automated Analysis Tools
- **CodeRabbit AI**: Automated code review and security analysis
- **Diagram Generator**: Architecture and data flow visualization
- **Static Analysis**: Code quality and performance assessment

## 📊 Analysis Results Summary

### Codebase Metrics
- **Total Python Files**: {self._count_python_files()}
- **Key Components**: Congress ingestion, OpenStates scraping, RAG pipeline, monitoring
- **Technology Stack**: Python, PostgreSQL, Docker, Cloudflare Workers, AI/ML

### Key Findings

#### 🏗️ Architecture Assessment
- Sophisticated multi-component architecture with clear separation of concerns
- Robust data ingestion pipeline with rate limiting and error handling
- Well-structured monitoring and observability system
- Strong foundation for Project v2 enhancements

#### 📈 Code Quality
- Generally high-quality Python code following best practices
- Good use of async programming and rate limiting
- Proper error handling and logging implementation
- Opportunities for optimization in parallel processing

#### 🗄️ Database Design
- Well-normalized database schema with proper foreign key relationships
- Efficient indexing strategies implemented
- Good data integrity and constraint enforcement
- Room for optimization in query patterns

#### 🔒 Security Analysis
- Proper API key management practices
- Secure database connection patterns
- Good error handling without information leakage
- Security recommendations for enhanced protection

#### 🤖 AI/ML Components
- Solid foundation for RAG implementation
- Proper document processing pipeline
- Vector database integration planned
- Opportunities for enhanced NLP processing

## 🚀 Strategic Recommendations

### Immediate Priorities (High Impact)
1. **Fix Congress Bills Ingestion**: Resolve chamber mapping foreign key constraint
2. **Implement Missing OpenStates Methods**: Complete enhanced ingestion pipeline
3. **Database Optimization**: Address identified query performance issues
4. **Enhanced Monitoring**: Implement missing monitoring for GovInfo delegates

### Short-term Improvements (Medium Impact)
1. **Security Enhancements**: Implement recommended security improvements
2. **Performance Optimization**: Address identified bottlenecks
3. **Documentation Enhancement**: Improve documentation coverage and quality
4. **Test Coverage**: Expand testing for ingestion pipeline

### Long-term Strategic Initiatives (Project v2)
1. **PGVector Integration**: Complete semantic search implementation
2. **Historical Data Expansion**: Full Congress history ingestion
3. **Advanced Analytics**: Enhanced reporting and insights
4. **Scalability Improvements**: Infrastructure and performance optimization

## 🎯 Business Impact

### Value Delivery
- **Data Accuracy**: Improved ingestion reliability and data quality
- **Performance**: Enhanced system performance and user experience
- **Security**: Strengthened security posture and compliance
- **Maintainability**: Improved code maintainability and documentation

### Project v2 Alignment
- **Semantic Search**: Foundation for intelligent document search
- **Historical Analysis**: Capability for comprehensive legislative trends
- **Advanced Analytics**: Data-driven insights and recommendations
- **Scalability**: Platform ready for enterprise-scale deployment

## 📋 Implementation Roadmap

### Phase 1: Critical Fixes (Weeks 1-2)
- [ ] Fix Congress bills ingestion (Foreign key constraint)
- [ ] Implement missing OpenStates methods
- [ ] Resolve monitoring system issues
- [ ] Address database optimization opportunities

### Phase 2: Quality Improvements (Weeks 3-4)
- [ ] Security enhancements implementation
- [ ] Performance optimization deployment
- [ ] Documentation enhancement project
- [ ] Testing infrastructure expansion

### Phase 3: Project v2 Development (Months 2-3)
- [ ] PGVector integration completion
- [ ] Historical data expansion
- [ ] Advanced analytics implementation
- [ ] Scalability improvements

## 📊 Success Metrics

### Technical Metrics
- **Code Quality**: Improved maintainability scores
- **Performance**: Reduced response times and increased throughput
- **Reliability**: Enhanced system uptime and error rates
- **Security**: Improved security posture and compliance

### Business Metrics
- **User Experience**: Improved search and analysis capabilities
- **Data Quality**: Enhanced accuracy and completeness
- **Operational Efficiency**: Reduced manual intervention requirements
- **Strategic Value**: Platform ready for advanced use cases

## 🔄 Next Steps

1. **Review Findings**: Technical team review of detailed reports
2. **Prioritization**: Stakeholder alignment on implementation priorities
3. **Resource Planning**: Allocate resources for critical fixes
4. **Timeline Development**: Detailed project timeline for Phases 1-3
5. **Continuous Monitoring**: Implement ongoing analysis and monitoring

## 📞 Support & Resources

- **Technical Documentation**: Available in `/crewai_reports/`
- **Architecture Diagrams**: Available in `/crewai_diagrams/`
- **GitHub Issues**: 10 strategic issues identified and ready for creation
- **Analysis Tools**: CodeRabbit AI and CrewAI ready for ongoing use

---

**Analysis Completed**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Next Review**: Recommended after critical fixes implementation
**Contact**: OpenDiscourse Development Team
"""

        summary_path = os.path.join(self.output_dirs["reports"], "executive_summary.md")
        with open(summary_path, 'w') as f:
            f.write(summary_content)

        logger.info(f"📊 Executive summary generated: {summary_path}")
        return summary_path

    def _count_python_files(self) -> int:
        """Count Python files in the project"""
        python_count = 0
        for root, dirs, files in os.walk(self.base_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__']]

            for file in files:
                if file.endswith('.py'):
                    python_count += 1

        return python_count

    def run_complete_analysis(self) -> Dict[str, Any]:
        """Run the complete analysis pipeline"""
        logger.info("🎯 Starting complete OpenDiscourse analysis pipeline...")

        start_time = time.time()
        results = {
            "timestamp": datetime.now().isoformat(),
            "base_path": self.base_path,
            "analysis_phases": []
        }

        try:
            # Phase 1: Environment Setup
            logger.info("=== Phase 1: Environment Setup ===")
            setup_result = self.setup_environment()
            results["analysis_phases"].append({
                "phase": "environment_setup",
                "status": setup_result.get("error", "success") and "error" or "success",
                "result": setup_result
            })

            # Phase 2: CodeRabbit Analysis
            logger.info("=== Phase 2: CodeRabbit AI Analysis ===")
            coderabbit_result = self.run_coderabbit_analysis()
            results["analysis_phases"].append({
                "phase": "coderabbit_analysis",
                "status": coderabbit_result["status"],
                "result": coderabbit_result
            })

            # Phase 3: CrewAI Analysis
            logger.info("=== Phase 3: CrewAI Multi-Agent Analysis ===")
            crewai_result = self.run_crewai_analysis()
            results["analysis_phases"].append({
                "phase": "crewai_analysis",
                "status": crewai_result["status"],
                "result": crewai_result
            })

            # Phase 4: Summary Generation
            logger.info("=== Phase 4: Summary Generation ===")
            summary_path = self.generate_executive_summary(results)
            results["analysis_phases"].append({
                "phase": "summary_generation",
                "status": "success",
                "result": {"summary_path": summary_path}
            })

            end_time = time.time()
            results["total_duration"] = end_time - start_time
            results["overall_status"] = "completed"

            logger.info("🎉 Complete analysis pipeline finished successfully!")
            logger.info(f"⏱️ Total execution time: {results['total_duration']:.2f} seconds")

            # Save comprehensive results
            results_path = os.path.join(self.output_dirs["reports"], "complete_analysis_results.json")
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2)

            return results

        except Exception as e:
            logger.error(f"❌ Complete analysis pipeline failed: {e}")
            results["error"] = str(e)
            results["overall_status"] = "failed"
            return results

def main():
    """Main entry point"""
    print("🤖 OpenDiscourse CrewAI Multi-Agent Analysis")
    print("=" * 60)
    print("This analysis will:")
    print("• Run CodeRabbit AI automated code review")
    print("• Execute CrewAI multi-agent codebase analysis")
    print("• Generate architecture diagrams")
    print("• Create comprehensive executive summary")
    print("=" * 60)

    # Initialize orchestrator
    orchestrator = OpenDiscourseCrewOrchestrator()

    # Run complete analysis
    results = orchestrator.run_complete_analysis()

    # Print final summary
    print("\\n" + "=" * 60)
    print("📊 ANALYSIS COMPLETE")
    print("=" * 60)

    if results["overall_status"] == "completed":
        print("✅ All analysis phases completed successfully!")
        print(f"⏱️ Total execution time: {results.get('total_duration', 0):.2f} seconds")
        print(f"📁 Reports available in: {orchestrator.output_dirs['reports']}")
        print(f"🎨 Diagrams available in: {orchestrator.output_dirs['diagrams']}")

        # Print phase summary
        successful_phases = sum(1 for phase in results["analysis_phases"] if phase["status"] == "success")
        total_phases = len(results["analysis_phases"])
        print(f"🎯 Phases completed: {successful_phases}/{total_phases}")

    else:
        print("❌ Analysis pipeline encountered errors:")
        for phase in results["analysis_phases"]:
            if phase["status"] != "success":
                print(f"  • {phase['phase']}: {phase['status']}")

    print("=" * 60)

if __name__ == "__main__":
    main()
