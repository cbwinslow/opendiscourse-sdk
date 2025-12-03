#!/usr/bin/env python3
"""
OpenDiscourse Bills Analysis Script

This script analyzes congress bills data using NLP techniques, embeddings,
and multi-dimensional binning to extract insights about legislation and
voting patterns.
"""

import os
import sys
import logging
import json
import argparse
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
import re

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import DictCursor, RealDictCursor
from dotenv import load_dotenv

# NLP and ML imports
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.feature_extraction.text import TfidfVectorizer
    import spacy

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print(
        "Warning: Transformer libraries not available. Using basic text analysis only."
    )

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for bills analysis"""

    congress_numbers: List[int] = None
    sample_size: int = 1000
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    n_clusters: int = 20
    use_gpu: bool = True
    output_dir: str = "./analysis_results"


class BillsAnalyzer:
    """Comprehensive bills analysis engine"""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.setup_database_connection()
        self.setup_nlp_tools()
        self.results = {}

    def setup_database_connection(self):
        """Setup database connection"""
        try:
            db_host = os.getenv("DB_HOST", "/var/run/postgresql")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "opendiscourse")
            db_user = os.getenv("DB_USER", "cbwinslow")

            self.conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                host=db_host,
                port=db_port,
            )
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Database connection established")

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def setup_nlp_tools(self):
        """Setup NLP and ML tools"""
        self.nlp_tools = {}

        # Basic text processing
        try:
            self.nlp_tools["spacy"] = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded")
        except OSError:
            logger.warning(
                "SpaCy model not found. Install with: python -m spacy download en_core_web_sm"
            )
            self.nlp_tools["spacy"] = None

        # Transformers for embeddings
        if TRANSFORMERS_AVAILABLE:
            try:
                self.nlp_tools["tokenizer"] = AutoTokenizer.from_pretrained(
                    self.config.embedding_model
                )
                self.nlp_tools["model"] = AutoModel.from_pretrained(
                    self.config.embedding_model
                )

                if self.config.use_gpu and torch.cuda.is_available():
                    self.nlp_tools["model"] = self.nlp_tools["model"].to("cuda")
                    logger.info("Using GPU for embeddings")
                else:
                    logger.info("Using CPU for embeddings")

            except Exception as e:
                logger.warning(f"Could not load transformer model: {e}")
                self.nlp_tools["tokenizer"] = None
                self.nlp_tools["model"] = None

    def extract_bills_data(self) -> List[Dict[str, Any]]:
        """Extract bills data from database"""
        logger.info("Extracting bills data...")

        query = """
        SELECT 
            b.bill_id,
            b.congress_number,
            b.bill_type,
            b.bill_number,
            b.official_title,
            b.summary_text,
            b.policy_area,
            b.sponsor_bioguide_id,
            b.introduced_date,
            b.latest_action_date,
            b.latest_action_text,
            m.first_name || ' ' || m.last_name as sponsor_name,
            m.party as sponsor_party,
            m.state as sponsor_state,
            array_agg(DISTINCT s.subject_name) as subjects
        FROM congress.bills b
        LEFT JOIN congress.members m ON b.sponsor_bioguide_id = m.bioguide_id
        LEFT JOIN congress.bill_subjects bs ON b.bill_id = bs.bill_id
        LEFT JOIN congress.subjects s ON bs.subject_id = s.subject_id
        WHERE b.official_title IS NOT NULL
        """

        if self.config.congress_numbers:
            query += f" AND b.congress_number IN ({','.join(map(str, self.config.congress_numbers))})"

        query += " GROUP BY b.bill_id, m.bioguide_id"

        if self.config.sample_size:
            query += f" LIMIT {self.config.sample_size}"

        self.cursor.execute(query)
        bills = [dict(row) for row in self.cursor.fetchall()]

        logger.info(f"Extracted {len(bills)} bills")
        return bills

    def extract_bill_actions(
        self, bill_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract bill actions for analysis"""
        logger.info("Extracting bill actions...")

        query = """
        SELECT bill_id, action_date, action_text, action_code
        FROM congress.bill_actions
        WHERE bill_id = ANY(%s)
        ORDER BY action_date
        """

        self.cursor.execute(query, (bill_ids,))
        actions = [dict(row) for row in self.cursor.fetchall()]

        # Group by bill_id
        actions_by_bill = defaultdict(list)
        for action in actions:
            actions_by_bill[action["bill_id"]].append(action)

        logger.info(f"Extracted {len(actions)} bill actions")
        return dict(actions_by_bill)

    def create_text_bins(self, bills: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Create multi-dimensional text bins"""
        logger.info("Creating text bins...")

        bins = {
            "policy_areas": defaultdict(list),
            "action_types": defaultdict(list),
            "sponsor_parties": defaultdict(list),
            "sponsor_states": defaultdict(list),
            "time_periods": defaultdict(list),
            "bill_types": defaultdict(list),
            "subject_clusters": defaultdict(list),
            "semantic_clusters": defaultdict(list),
            "complexity_levels": {
                "simple": [],  # < 50 words
                "moderate": [],  # 50-200 words
                "complex": [],  # > 200 words
            },
        }

        for bill in bills:
            bill_id = bill["bill_id"]
            title = bill["official_title"] or ""
            summary = bill["summary_text"] or ""
            full_text = f"{title} {summary}"

            # Policy area binning
            policy_area = bill["policy_area"] or "Unknown"
            bins["policy_areas"][policy_area].append(bill_id)

            # Bill type binning
            bill_type = bill["bill_type"]
            bins["bill_types"][bill_type].append(bill_id)

            # Sponsor party binning
            party = bill.get("sponsor_party") or "Unknown"
            bins["sponsor_parties"][party].append(bill_id)

            # Sponsor state binning
            state = bill.get("sponsor_state") or "Unknown"
            bins["sponsor_states"][state].append(bill_id)

            # Time period binning
            year = bill.get("introduced_date")
            if year:
                year = year.year if hasattr(year, "year") else int(str(year)[:4])
                decade = (year // 10) * 10
                bins["time_periods"][f"{decade}s"].append(bill_id)

            # Complexity binning
            word_count = len(full_text.split())
            if word_count < 50:
                bins["complexity_levels"]["simple"].append(bill_id)
            elif word_count <= 200:
                bins["complexity_levels"]["moderate"].append(bill_id)
            else:
                bins["complexity_levels"]["complex"].append(bill_id)

        # Log bin statistics
        for bin_name, bin_data in bins.items():
            if isinstance(bin_data, dict):
                logger.info(f"{bin_name}: {len(bin_data)} categories")
                for category, items in list(bin_data.items())[:5]:  # Show top 5
                    logger.info(f"  {category}: {len(items)} items")

        return bins

    def extract_statements_and_actions(
        self,
        bills: List[Dict[str, Any]],
        actions_by_bill: Dict[str, List[Dict[str, Any]]],
    ) -> Dict[str, List[str]]:
        """Extract actionable statements and commitments from bills"""
        logger.info("Extracting statements and actions...")

        statements = {
            "commitments": [],
            "prohibitions": [],
            "requirements": [],
            "authorizations": [],
            "establishments": [],
            "amendments": [],
            "directives": [],
            "findings": [],
            "purposes": [],
            "definitions": [],
        }

        # Action-oriented patterns
        patterns = {
            "commitments": [
                r"shall\s+(?:provide|ensure|maintain|establish|create|fund)",
                r"must\s+(?:provide|ensure|maintain|establish)",
                r"is\s+(?:required|obligated|mandated)\s+to",
                r"commits\s+to",
                r"will\s+(?:provide|ensure|establish)",
            ],
            "prohibitions": [
                r"shall\s+not",
                r"must\s+not",
                r"is\s+(?:prohibited|forbidden|banned)",
                r"no\s+(?:person|entity|agency)\s+shall",
                r"prohibits",
            ],
            "requirements": [
                r"requires?\s+that",
                r"shall\s+(?:require|mandate)",
                r"must\s+(?:comply|adhere)",
                r"is\s+(?:required|mandatory)",
            ],
            "authorizations": [
                r"authorizes?\s+",
                r"may\s+(?:provide|establish|create)",
                r"is\s+(?:authorized|permitted)",
                r"has\s+(?:authority|power)\s+to",
            ],
            "establishments": [
                r"establishes?\s+",
                r"creates?\s+",
                r"shall\s+(?:establish|create|form)",
                r"forms?\s+a",
            ],
            "amendments": [
                r"amends?\s+",
                r"modifies?\s+",
                r"revises?\s+",
                r"changes?\s+",
                r"alters?\s+",
            ],
            "directives": [
                r"directs?\s+that",
                r"shall\s+(?:direct|order)",
                r"instructs?\s+",
                r"orders?\s+that",
            ],
            "findings": [
                r"finds?\s+that",
                r"determines?\s+that",
                r"concludes?\s+that",
                r"recognizes?\s+that",
            ],
            "purposes": [
                r"purpose\s+(?:of|is)",
                r"aims?\s+to",
                r"intends?\s+to",
                r"objectives?\s+(?:include|are)",
            ],
            "definitions": [
                r"defines?\s+",
                r"means?\s+",
                r"refers?\s+to",
                r"shall\s+(?:mean|be\s+defined)",
            ],
        }

        for bill in bills:
            bill_id = bill["bill_id"]
            title = bill["official_title"] or ""
            summary = bill["summary_text"] or ""
            full_text = f"{title} {summary}"

            # Extract statements using patterns
            for statement_type, pattern_list in patterns.items():
                for pattern in pattern_list:
                    matches = re.finditer(pattern, full_text, re.IGNORECASE)
                    for match in matches:
                        # Extract context around the match
                        start = max(0, match.start() - 50)
                        end = min(len(full_text), match.end() + 100)
                        context = full_text[start:end].strip()

                        statement = {
                            "bill_id": bill_id,
                            "type": statement_type,
                            "text": context,
                            "pattern": pattern,
                            "confidence": self.calculate_statement_confidence(
                                match, full_text
                            ),
                        }

                        statements[statement_type].append(statement)

        # Log extraction results
        for stmt_type, stmt_list in statements.items():
            logger.info(f"Extracted {len(stmt_list)} {stmt_type} statements")

        return statements

    def calculate_statement_confidence(self, match, text: str) -> float:
        """Calculate confidence score for extracted statement"""
        # Simple confidence calculation based on context
        confidence = 0.5  # Base confidence

        # Boost for complete sentences
        matched_text = match.group()
        if matched_text.endswith((".", "!", "?")):
            confidence += 0.2

        # Boost for formal language indicators
        formal_words = ["shall", "must", "hereby", "pursuant", "in accordance with"]
        if any(word in matched_text.lower() for word in formal_words):
            confidence += 0.2

        # Boost for specific legislative language
        legislative_words = ["act", "law", "statute", "regulation", "section"]
        if any(word in matched_text.lower() for word in legislative_words):
            confidence += 0.1

        return min(confidence, 1.0)

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text analysis"""
        if not TRANSFORMERS_AVAILABLE or not self.nlp_tools["tokenizer"]:
            logger.warning("Using TF-IDF fallback for embeddings")
            vectorizer = TfidfVectorizer(max_features=384, stop_words="english")
            return vectorizer.fit_transform(texts).toarray()

        logger.info(f"Generating embeddings for {len(texts)} texts...")

        embeddings = []
        batch_size = 32

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            # Tokenize
            inputs = self.nlp_tools["tokenizer"](
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )

            if self.config.use_gpu and torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}

            # Generate embeddings
            with torch.no_grad():
                outputs = self.nlp_tools["model"](**inputs)
                batch_embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
                embeddings.extend(batch_embeddings)

        return np.array(embeddings)

    def perform_semantic_clustering(
        self, bills: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform semantic clustering of bills"""
        logger.info("Performing semantic clustering...")

        # Prepare texts for clustering
        texts = []
        bill_ids = []

        for bill in bills:
            title = bill["official_title"] or ""
            summary = bill["summary_text"] or ""
            combined_text = f"{title} {summary}".strip()

            if combined_text:
                texts.append(combined_text)
                bill_ids.append(bill["bill_id"])

        if not texts:
            logger.warning("No texts available for clustering")
            return {}

        # Generate embeddings
        embeddings = self.generate_embeddings(texts)

        # Perform clustering
        kmeans = KMeans(n_clusters=self.config.n_clusters, random_state=42)
        cluster_labels = kmeans.fit_predict(embeddings)

        # Organize results
        clusters = defaultdict(list)
        for bill_id, cluster_id in zip(bill_ids, cluster_labels):
            clusters[f"cluster_{cluster_id}"].append(bill_id)

        # Generate cluster descriptions using key terms
        cluster_descriptions = {}
        vectorizer = TfidfVectorizer(max_features=10, stop_words="english")

        for cluster_id, cluster_bills in clusters.items():
            # Get texts for this cluster
            cluster_texts = []
            for bill in bills:
                if bill["bill_id"] in cluster_bills:
                    title = bill["official_title"] or ""
                    summary = bill["summary_text"] or ""
                    cluster_texts.append(f"{title} {summary}")

            if cluster_texts:
                # Get key terms
                tfidf_matrix = vectorizer.fit_transform(cluster_texts)
                feature_names = vectorizer.get_feature_names_out()
                scores = tfidf_matrix.sum(axis=0).A1

                # Get top terms
                top_indices = scores.argsort()[-5:][::-1]
                top_terms = [feature_names[i] for i in top_indices]

                cluster_descriptions[cluster_id] = {
                    "size": len(cluster_bills),
                    "key_terms": top_terms,
                    "sample_bills": cluster_bills[:3],  # Show first 3 as examples
                }

        logger.info(f"Created {len(clusters)} semantic clusters")

        return {
            "clusters": dict(clusters),
            "descriptions": cluster_descriptions,
            "model_info": {
                "embedding_model": self.config.embedding_model,
                "n_clusters": self.config.n_clusters,
                "total_texts": len(texts),
            },
        }

    def analyze_sponsor_patterns(self, bills: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sponsor patterns and behaviors"""
        logger.info("Analyzing sponsor patterns...")

        sponsor_stats = defaultdict(
            lambda: {
                "bill_count": 0,
                "policy_areas": Counter(),
                "bill_types": Counter(),
                "subjects": Counter(),
                "success_rate": 0,
                "bipartisan_score": 0,
            }
        )

        total_bills = len(bills)
        passed_bills = 0

        for bill in bills:
            sponsor_id = bill.get("sponsor_bioguide_id")
            if not sponsor_id:
                continue

            stats = sponsor_stats[sponsor_id]
            stats["bill_count"] += 1

            # Track policy areas
            policy_area = bill.get("policy_area") or "Unknown"
            stats["policy_areas"][policy_area] += 1

            # Track bill types
            bill_type = bill.get("bill_type", "Unknown")
            stats["bill_types"][bill_type] += 1

            # Track subjects
            subjects = bill.get("subjects", [])
            if subjects:
                for subject in subjects:
                    if subject:
                        stats["subjects"][subject] += 1

            # Track success (simplified - based on latest action)
            latest_action = bill.get("latest_action_text", "").lower()
            if any(
                word in latest_action for word in ["passed", "enacted", "became law"]
            ):
                passed_bills += 1
                stats["success_rate"] += 1

        # Calculate rates and scores
        for sponsor_id, stats in sponsor_stats.items():
            if stats["bill_count"] > 0:
                stats["success_rate"] = stats["success_rate"] / stats["bill_count"]

        # Get top sponsors
        top_sponsors = sorted(
            sponsor_stats.items(), key=lambda x: x[1]["bill_count"], reverse=True
        )[:10]

        return {
            "total_sponsors": len(sponsor_stats),
            "top_sponsors": dict(top_sponsors),
            "overall_pass_rate": passed_bills / total_bills if total_bills > 0 else 0,
        }

    def create_analysis_report(
        self,
        bills: List[Dict[str, Any]],
        bins: Dict[str, List[str]],
        statements: Dict[str, List[str]],
        clusters: Dict[str, Any],
        sponsor_patterns: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create comprehensive analysis report"""
        logger.info("Creating analysis report...")

        report = {
            "metadata": {
                "analysis_date": datetime.now().isoformat(),
                "total_bills": len(bills),
                "congress_numbers": self.config.congress_numbers,
                "sample_size": self.config.sample_size,
                "analysis_methods": [
                    "text_binning",
                    "pattern_extraction",
                    "semantic_clustering",
                    "sponsor_analysis",
                ],
            },
            "summary": {
                "total_bills_analyzed": len(bills),
                "policy_areas_found": len(bins.get("policy_areas", {})),
                "statement_types_extracted": len([s for s in statements.values() if s]),
                "semantic_clusters_created": len(clusters.get("clusters", {})),
                "unique_sponsors": sponsor_patterns.get("total_sponsors", 0),
            },
            "bins": bins,
            "statements": statements,
            "semantic_clusters": clusters,
            "sponsor_patterns": sponsor_patterns,
            "insights": self.generate_insights(
                bills, bins, statements, clusters, sponsor_patterns
            ),
        }

        return report

    def generate_insights(
        self,
        bills: List[Dict[str, Any]],
        bins: Dict[str, List[str]],
        statements: Dict[str, List[str]],
        clusters: Dict[str, Any],
        sponsor_patterns: Dict[str, Any],
    ) -> List[str]:
        """Generate key insights from the analysis"""
        insights = []

        # Policy area insights
        policy_areas = bins.get("policy_areas", {})
        if policy_areas:
            top_policy = max(policy_areas.items(), key=lambda x: len(x[1]))
            insights.append(
                f"Most common policy area: {top_policy[0]} ({len(top_policy[1])} bills)"
            )

        # Statement insights
        total_statements = sum(len(stmts) for stmts in statements.values())
        if total_statements > 0:
            top_statement_type = max(statements.items(), key=lambda x: len(x[1]))
            insights.append(
                f"Most common statement type: {top_statement_type[0]} ({len(top_statement_type[1])} instances)"
            )

        # Sponsor insights
        if sponsor_patterns.get("top_sponsors"):
            top_sponsor = list(sponsor_patterns["top_sponsors"].items())[0]
            insights.append(
                f"Most active sponsor: {top_sponsor[0]} ({top_sponsor[1]['bill_count']} bills)"
            )

        # Cluster insights
        cluster_descriptions = clusters.get("descriptions", {})
        if cluster_descriptions:
            largest_cluster = max(
                cluster_descriptions.items(), key=lambda x: x[1]["size"]
            )
            insights.append(
                f"Largest semantic cluster: {largest_cluster[0]} ({largest_cluster[1]['size']} bills)"
            )
            insights.append(
                f"Key terms in largest cluster: {', '.join(largest_cluster[1]['key_terms'])}"
            )

        # Complexity insights
        complexity_levels = bins.get("complexity_levels", {})
        if complexity_levels:
            most_complex = max(complexity_levels.items(), key=lambda x: len(x[1]))
            insights.append(
                f"Most common complexity level: {most_complex[0]} ({len(most_complex[1])} bills)"
            )

        return insights

    def save_results(self, report: Dict[str, Any]):
        """Save analysis results to files"""
        os.makedirs(self.config.output_dir, exist_ok=True)

        # Save full report
        report_file = os.path.join(self.config.output_dir, "bills_analysis_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # Save insights separately
        insights_file = os.path.join(self.config.output_dir, "key_insights.txt")
        with open(insights_file, "w") as f:
            f.write("OpenDiscourse Bills Analysis - Key Insights\n")
            f.write("=" * 50 + "\n\n")
            for insight in report["insights"]:
                f.write(f"• {insight}\n")

        # Save bins summary
        bins_file = os.path.join(self.config.output_dir, "bins_summary.csv")
        bins_data = []
        for bin_type, bin_categories in report["bins"].items():
            if isinstance(bin_categories, dict):
                for category, items in bin_categories.items():
                    bins_data.append(
                        {
                            "bin_type": bin_type,
                            "category": category,
                            "count": len(items),
                        }
                    )

        if bins_data:
            pd.DataFrame(bins_data).to_csv(bins_file, index=False)

        logger.info(f"Results saved to {self.config.output_dir}")
        logger.info(f"Main report: {report_file}")
        logger.info(f"Key insights: {insights_file}")
        logger.info(f"Bins summary: {bins_file}")

    def run_analysis(self) -> Dict[str, Any]:
        """Run complete analysis pipeline"""
        logger.info("Starting bills analysis...")

        # Extract data
        bills = self.extract_bills_data()
        if not bills:
            logger.error("No bills data found")
            return {}

        bill_ids = [bill["bill_id"] for bill in bills]
        actions_by_bill = self.extract_bill_actions(bill_ids)

        # Perform analysis
        bins = self.create_text_bins(bills)
        statements = self.extract_statements_and_actions(bills, actions_by_bill)
        clusters = self.perform_semantic_clustering(bills)
        sponsor_patterns = self.analyze_sponsor_patterns(bills)

        # Create report
        report = self.create_analysis_report(
            bills, bins, statements, clusters, sponsor_patterns
        )

        # Save results
        self.save_results(report)

        logger.info("Analysis completed successfully!")
        return report


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze OpenDiscourse bills data")
    parser.add_argument(
        "--congress", type=int, nargs="+", help="Congress numbers to analyze"
    )
    parser.add_argument(
        "--sample-size", type=int, default=1000, help="Sample size for analysis"
    )
    parser.add_argument(
        "--clusters", type=int, default=20, help="Number of semantic clusters"
    )
    parser.add_argument(
        "--output-dir", type=str, default="./analysis_results", help="Output directory"
    )
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU usage")

    args = parser.parse_args()

    # Create configuration
    config = AnalysisConfig(
        congress_numbers=args.congress,
        sample_size=args.sample_size,
        n_clusters=args.clusters,
        output_dir=args.output_dir,
        use_gpu=not args.no_gpu,
    )

    # Run analysis
    try:
        analyzer = BillsAnalyzer(config)
        report = analyzer.run_analysis()

        # Print summary
        print("\n" + "=" * 50)
        print("ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"Total bills analyzed: {report['summary']['total_bills_analyzed']}")
        print(f"Policy areas found: {report['summary']['policy_areas_found']}")
        print(
            f"Statement types extracted: {report['summary']['statement_types_extracted']}"
        )
        print(
            f"Semantic clusters created: {report['summary']['semantic_clusters_created']}"
        )
        print(f"Unique sponsors: {report['summary']['unique_sponsors']}")
        print("\nKey Insights:")
        for insight in report["insights"]:
            print(f"  • {insight}")
        print(f"\nFull report saved to: {config.output_dir}/bills_analysis_report.json")

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
