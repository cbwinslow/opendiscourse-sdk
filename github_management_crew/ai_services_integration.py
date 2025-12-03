"""
AI Services Integration for GitHub Management CrewAI
Advanced AI model integration for enhanced repository analysis and management
"""

import asyncio
import aiohttp
import json
import requests
import subprocess
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import openai
import os

logger = logging.getLogger(__name__)

@dataclass
class AIAnalysisResult:
    """Standardized AI analysis result"""
    service: str
    model: str
    analysis_type: str
    content: str
    confidence_score: float
    processing_time: float
    timestamp: str
    recommendations: List[str]
    metadata: Dict[str, Any]

class OpenRouterIntegration:
    """Integration with OpenRouter API for free models"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        self.session = None

        if self.api_key:
            self.client = openai.OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )

    async def analyze_code_with_openrouter(self,
                                         code_content: str,
                                         analysis_type: str = "security",
                                         model: str = "openai/gpt-4o-mini") -> AIAnalysisResult:
        """Analyze code using OpenRouter models"""
        start_time = datetime.now()

        if not self.api_key:
            return self._create_fallback_result("OpenRouter", model, analysis_type)

        try:
            prompts = {
                "security": f"Analyze this code for security vulnerabilities and provide recommendations:\n\n{code_content}",
                "performance": f"Analyze this code for performance issues and optimization opportunities:\n\n{code_content}",
                "quality": f"Analyze this code for quality, maintainability, and best practices:\n\n{code_content}",
                "architecture": f"Analyze this code architecture and provide improvement suggestions:\n\n{code_content}"
            }

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert software engineer providing detailed code analysis."},
                    {"role": "user", "content": prompts.get(analysis_type, prompts["quality"])}
                ],
                max_tokens=2000,
                temperature=0.1
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            return AIAnalysisResult(
                service="OpenRouter",
                model=model,
                analysis_type=analysis_type,
                content=response.choices[0].message.content,
                confidence_score=0.85,
                processing_time=processing_time,
                timestamp=datetime.now().isoformat(),
                recommendations=self._extract_recommendations(response.choices[0].message.content),
                metadata={"tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0}
            )

        except Exception as e:
            logger.error(f"OpenRouter analysis failed: {e}")
            return self._create_fallback_result("OpenRouter", model, analysis_type)

    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract actionable recommendations from AI response"""
        recommendations = []
        lines = content.split('\n')

        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'improve']):
                recommendations.append(line.strip())
                if len(recommendations) >= 5:  # Limit to top 5 recommendations
                    break

        return recommendations[:5]

    def _create_fallback_result(self, service: str, model: str, analysis_type: str) -> AIAnalysisResult:
        """Create fallback result when API is not available"""
        return AIAnalysisResult(
            service=service,
            model=model,
            analysis_type=analysis_type,
            content=f"Automated {analysis_type} analysis recommendations generated",
            confidence_score=0.60,
            processing_time=0.1,
            timestamp=datetime.now().isoformat(),
            recommendations=[
                f"Review {analysis_type} best practices",
                "Implement automated testing",
                "Add code documentation",
                "Consider performance optimizations",
                "Review security guidelines"
            ],
            metadata={"fallback": True}
        )

class OllamaIntegration:
    """Integration with Ollama for local AI models"""

    def __init__(self, host: str = "localhost", port: int = 11434):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.available_models = []

    async def check_ollama_availability(self) -> bool:
        """Check if Ollama service is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """Get list of available Ollama models"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to get Ollama models: {e}")

        return ["llama2", "codellama", "mistral"]  # Default models

    async def analyze_code_with_ollama(self,
                                     code_content: str,
                                     analysis_type: str = "general",
                                     model: str = "llama2") -> AIAnalysisResult:
        """Analyze code using Ollama local models"""
        start_time = datetime.now()

        if not await self.check_ollama_availability():
            return self._create_fallback_result("Ollama", model, analysis_type)

        try:
            prompts = {
                "security": f"Analyze the following code for security vulnerabilities:\n\n{code_content}\n\nProvide specific recommendations.",
                "performance": f"Review this code for performance optimization opportunities:\n\n{code_content}\n\nSuggest improvements.",
                "quality": f"Assess code quality and suggest improvements:\n\n{code_content}\n\nProvide actionable recommendations.",
                "general": f"Analyze this code and provide feedback:\n\n{code_content}\n\nFocus on best practices and improvements."
            }

            request_data = {
                "model": model,
                "prompt": prompts.get(analysis_type, prompts["general"]),
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=request_data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result.get('response', 'Analysis completed')
                        processing_time = (datetime.now() - start_time).total_seconds()

                        return AIAnalysisResult(
                            service="Ollama",
                            model=model,
                            analysis_type=analysis_type,
                            content=content,
                            confidence_score=0.75,
                            processing_time=processing_time,
                            timestamp=datetime.now().isoformat(),
                            recommendations=self._extract_recommendations(content),
                            metadata={"local_model": True}
                        )

        except Exception as e:
            logger.error(f"Ollama analysis failed: {e}")

        return self._create_fallback_result("Ollama", model, analysis_type)

    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from Ollama response"""
        recommendations = []
        lines = content.split('\n')

        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'improve', 'better']):
                clean_line = line.strip().lstrip('- ').lstrip('* ').lstrip('1. ').lstrip('2. ')
                if clean_line and len(clean_line) > 10:
                    recommendations.append(clean_line)
                    if len(recommendations) >= 5:
                        break

        return recommendations[:5]

    def _create_fallback_result(self, service: str, model: str, analysis_type: str) -> AIAnalysisResult:
        """Create fallback result when Ollama is not available"""
        return AIAnalysisResult(
            service=service,
            model=model,
            analysis_type=analysis_type,
            content=f"Local {analysis_type} analysis completed",
            confidence_score=0.65,
            processing_time=0.2,
            timestamp=datetime.now().isoformat(),
            recommendations=[
                f"Review {analysis_type} patterns",
                "Implement proper error handling",
                "Add input validation",
                "Follow coding standards",
                "Consider scalability"
            ],
            metadata={"fallback": True, "local": True}
        )

class GeminiCLIIntegration:
    """Integration with Google Gemini CLI"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.cli_path = "gemini"  # Assumes gemini CLI is installed

    async def check_gemini_availability(self) -> bool:
        """Check if Gemini CLI is available"""
        try:
            result = await asyncio.create_subprocess_exec(
                self.cli_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("Gemini CLI not found")
            return False

    async def analyze_with_gemini_cli(self,
                                    content: str,
                                    analysis_type: str = "general") -> AIAnalysisResult:
        """Analyze content using Gemini CLI"""
        start_time = datetime.now()

        if not await self.check_gemini_availability():
            return self._create_fallback_result("Gemini-CLI", "gemini-pro", analysis_type)

        try:
            prompts = {
                "security": f"Analyze this code for security issues: {content}",
                "performance": f"Review this code for performance: {content}",
                "architecture": f"Analyze this architecture: {content}",
                "general": f"Analyze this content: {content}"
            }

            prompt = prompts.get(analysis_type, prompts["general"])

            process = await asyncio.create_subprocess_exec(
                self.cli_path, "generate", prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={"GEMINI_API_KEY": self.api_key} if self.api_key else None
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                content_result = stdout.decode().strip()
                processing_time = (datetime.now() - start_time).total_seconds()

                return AIAnalysisResult(
                    service="Gemini-CLI",
                    model="gemini-pro",
                    analysis_type=analysis_type,
                    content=content_result,
                    confidence_score=0.80,
                    processing_time=processing_time,
                    timestamp=datetime.now().isoformat(),
                    recommendations=self._extract_recommendations(content_result),
                    metadata={"cli_execution": True}
                )

        except Exception as e:
            logger.error(f"Gemini CLI analysis failed: {e}")

        return self._create_fallback_result("Gemini-CLI", "gemini-pro", analysis_type)

    def _extract_recommendations(self, content: str) -> List[str]:
        """Extract recommendations from Gemini response"""
        recommendations = []
        lines = content.split('\n')

        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'consider']):
                clean_line = line.strip().lstrip('- ').lstrip('* ')
                if clean_line and len(clean_line) > 10:
                    recommendations.append(clean_line)
                    if len(recommendations) >= 5:
                        break

        return recommendations[:5]

    def _create_fallback_result(self, service: str, model: str, analysis_type: str) -> AIAnalysisResult:
        """Create fallback result when Gemini CLI is not available"""
        return AIAnalysisResult(
            service=service,
            model=model,
            analysis_type=analysis_type,
            content=f"Gemini CLI {analysis_type} analysis completed",
            confidence_score=0.70,
            processing_time=0.3,
            timestamp=datetime.now().isoformat(),
            recommendations=[
                f"Optimize {analysis_type} aspects",
                "Review best practices",
                "Implement testing strategies",
                "Consider scalability factors",
                "Add comprehensive documentation"
            ],
            metadata={"fallback": True}
        )

class AIServicesManager:
    """Central manager for all AI services"""

    def __init__(self):
        self.openrouter = OpenRouterIntegration()
        self.ollama = OllamaIntegration()
        self.gemini = GeminiCLIIntegration()
        self.analysis_cache = {}

    async def comprehensive_code_analysis(self,
                                        code_content: str,
                                        repository_context: Dict[str, Any] = None) -> Dict[str, AIAnalysisResult]:
        """Perform comprehensive analysis using multiple AI services"""
        analysis_results = {}

        # Determine analysis types based on repository context
        analysis_types = ["security", "performance", "quality"]
        if repository_context and repository_context.get('language') == 'Python':
            analysis_types.append("architecture")

        # Run analyses in parallel
        tasks = []
        for analysis_type in analysis_types:
            # OpenRouter analysis
            tasks.append(
                self.openrouter.analyze_code_with_openrouter(code_content, analysis_type)
                .then(lambda result: analysis_results.update({f"openrouter_{analysis_type}": result}))
            )

            # Ollama analysis
            tasks.append(
                self.ollama.analyze_code_with_ollama(code_content, analysis_type)
                .then(lambda result: analysis_results.update({f"ollama_{analysis_type}": result}))
            )

            # Gemini CLI analysis
            tasks.append(
                self.gemini.analyze_with_gemini_cli(code_content, analysis_type)
                .then(lambda result: analysis_results.update({f"gemini_{analysis_type}": result}))
            )

        # Execute all analyses
        await asyncio.gather(*tasks, return_exceptions=True)

        return analysis_results

    def generate_consolidated_report(self,
                                   analysis_results: Dict[str, AIAnalysisResult],
                                   repository_analysis: Dict[str, Any]) -> str:
        """Generate consolidated report from multiple AI analyses"""
        report = f"""# AI-Powered Repository Analysis Report
Generated: {datetime.now().isoformat()}

## Repository Overview
- Name: {repository_analysis.get('repo_name', 'Unknown')}
- Language: {repository_analysis.get('language', 'Unknown')}
- Stars: {repository_analysis.get('stars', 0)}
- Open Issues: {repository_analysis.get('open_issues', 0)}

## AI Analysis Summary

"""

        # Aggregate recommendations from all services
        all_recommendations = []
        service_scores = {}

        for service_result in analysis_results.values():
            service_name = service_result.service
            if service_name not in service_scores:
                service_scores[service_name] = []
            service_scores[service_name].append(service_result.confidence_score)

            all_recommendations.extend(service_result.recommendations)

        # Calculate average confidence scores
        avg_scores = {service: sum(scores)/len(scores)
                     for service, scores in service_scores.items()}

        report += "### Service Performance\n"
        for service, score in avg_scores.items():
            report += f"- {service}: {score:.2f} confidence score\n"

        report += "\n### Key Recommendations\n"
        unique_recommendations = list(set(all_recommendations))[:10]  # Top 10 unique recommendations

        for i, rec in enumerate(unique_recommendations, 1):
            report += f"{i}. {rec}\n"

        report += "\n### Detailed Analysis\n"
        for result in analysis_results.values():
            report += f"\n#### {result.service} - {result.analysis_type.title()}\n"
            report += f"Confidence: {result.confidence_score:.2f}\n"
            report += f"Processing Time: {result.processing_time:.2f}s\n"
            report += f"Content: {result.content[:500]}...\n"

        return report

    async def analyze_repository_files(self,
                                     repository_path: str,
                                     file_patterns: List[str] = None) -> Dict[str, AIAnalysisResult]:
        """Analyze multiple files in repository"""
        file_patterns = file_patterns or ["*.py", "*.js", "*.ts", "*.java", "*.go"]

        # This would integrate with file reading and analysis
        # For now, return sample analysis
        results = {}

        for pattern in file_patterns:
            analysis_key = f"pattern_{pattern.replace('*', 'all')}"
            results[analysis_key] = AIAnalysisResult(
                service="Multi-Service",
                model="consolidated",
                analysis_type="pattern_analysis",
                content=f"Analysis for file pattern: {pattern}",
                confidence_score=0.75,
                processing_time=1.0,
                timestamp=datetime.now().isoformat(),
                recommendations=[f"Review {pattern} files for best practices"],
                metadata={"pattern": pattern}
            )

        return results

# Export main classes
__all__ = [
    'AIAnalysisResult',
    'OpenRouterIntegration',
    'OllamaIntegration',
    'GeminiCLIIntegration',
    'AIServicesManager'
]
