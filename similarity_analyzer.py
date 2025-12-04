#!/usr/bin/env python3
"""
OpenDiscourse Similarity Analyzer

This script calculates and stores similarity scores between bill embeddings.
"""

import os
import sys
import logging
import argparse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import numpy as np

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import execute_values, DictCursor
from dotenv import load_dotenv

# Try to import sklearn
try:
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: sklearn not available. Install with: pip install scikit-learn")

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SimilarityConfig:
    """Configuration for similarity analysis"""

    model_name: str = "all-minilm:l6-v2"
    similarity_threshold: float = 0.7
    batch_size: int = 100
    max_comparisons: int = 10000  # Limit to avoid explosion


class SimilarityAnalyzer:
    """Calculate and store similarity between bill embeddings"""

    def __init__(self, config: SimilarityConfig):
        self.config = config
        self.setup_database_connection()

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
            self.cursor = self.conn.cursor(cursor_factory=DictCursor)
            logger.info("Database connection established")

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_all_embeddings(self) -> tuple:
        """Get all embeddings for similarity calculation"""
        query = """
        SELECT bill_id, embedding_vector 
        FROM analysis.bill_embeddings 
        WHERE processing_status = 'completed' AND model_name = %s
        ORDER BY bill_id
        """

        self.cursor.execute(query, (self.config.model_name,))

        bill_ids = []
        embeddings = []

        for row in self.cursor.fetchall():
            bill_ids.append(row["bill_id"])
            embeddings.append(np.array(row["embedding_vector"]))

        return bill_ids, np.array(embeddings)

    def calculate_similarity_matrix(self, embeddings: np.ndarray) -> np.ndarray:
        """Calculate similarity matrix using cosine similarity"""
        if not SKLEARN_AVAILABLE:
            # Fallback: manual cosine similarity
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized_embeddings = embeddings / norms
            similarity_matrix = np.dot(normalized_embeddings, normalized_embeddings.T)
            return similarity_matrix

        # Use sklearn for efficiency
        similarity_matrix = cosine_similarity(embeddings)
        return similarity_matrix

    def find_high_similarity_pairs(
        self, similarity_matrix: np.ndarray, bill_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Find pairs with similarity above threshold"""
        high_similarity_pairs = []
        n = len(bill_ids)

        for i in range(n):
            for j in range(i + 1, n):  # Only upper triangle, avoid self-comparison
                similarity_score = similarity_matrix[i, j]

                if similarity_score >= self.config.similarity_threshold:
                    high_similarity_pairs.append(
                        {
                            "bill_id_1": bill_ids[i],
                            "bill_id_2": bill_ids[j],
                            "similarity_score": float(similarity_score),
                        }
                    )

        # Sort by similarity score (highest first)
        high_similarity_pairs.sort(key=lambda x: x["similarity_score"], reverse=True)

        # Limit to max_comparisons
        if len(high_similarity_pairs) > self.config.max_comparisons:
            high_similarity_pairs = high_similarity_pairs[: self.config.max_comparisons]

        return high_similarity_pairs

    def store_similarities(self, similarities: List[Dict[str, Any]]):
        """Store similarity results in database"""
        if not similarities:
            logger.info("No similarities to store")
            return

        values = []
        for sim in similarities:
            values.append(
                (
                    sim["bill_id_1"],
                    sim["bill_id_2"],
                    sim["similarity_score"],
                    self.config.model_name,
                )
            )

        query = """
        INSERT INTO analysis.bill_similarity 
        (bill_id_1, bill_id_2, similarity_score, model_name)
        VALUES %s
        ON CONFLICT (bill_id_1, bill_id_2, model_name) 
        DO UPDATE SET 
            similarity_score = EXCLUDED.similarity_score,
            analysis_date = NOW()
        """

        try:
            execute_values(self.cursor, query, values)
            self.conn.commit()
            logger.info(f"Stored {len(similarities)} similarity pairs")

        except Exception as e:
            logger.error(f"Failed to store similarities: {e}")
            self.conn.rollback()
            raise

    def calculate_similarities_for_bill(
        self, target_bill_id: str
    ) -> List[Dict[str, Any]]:
        """Calculate similarities for a specific bill"""
        # Get target embedding
        self.cursor.execute(
            """
            SELECT embedding_vector 
            FROM analysis.bill_embeddings 
            WHERE bill_id = %s AND processing_status = 'completed' AND model_name = %s
        """,
            (target_bill_id, self.config.model_name),
        )

        target_result = self.cursor.fetchone()
        if not target_result:
            logger.warning(f"No embedding found for bill {target_bill_id}")
            return []

        target_embedding = np.array(target_result["embedding_vector"])

        # Get all other embeddings
        self.cursor.execute(
            """
            SELECT bill_id, embedding_vector 
            FROM analysis.bill_embeddings 
            WHERE bill_id != %s AND processing_status = 'completed' AND model_name = %s
        """,
            (target_bill_id, self.config.model_name),
        )

        similarities = []
        for row in self.cursor.fetchall():
            other_id = row["bill_id"]
            other_embedding = np.array(row["embedding_vector"])

            # Calculate cosine similarity
            if SKLEARN_AVAILABLE:
                similarity = cosine_similarity(
                    target_embedding.reshape(1, -1), other_embedding.reshape(1, -1)
                )[0][0]
            else:
                # Manual calculation
                dot_product = np.dot(target_embedding, other_embedding)
                norm_a = np.linalg.norm(target_embedding)
                norm_b = np.linalg.norm(other_embedding)
                similarity = dot_product / (norm_a * norm_b)

            if similarity >= self.config.similarity_threshold:
                similarities.append(
                    {
                        "bill_id_1": target_bill_id,
                        "bill_id_2": other_id,
                        "similarity_score": float(similarity),
                    }
                )

        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similarities

    def run_full_similarity_analysis(self) -> Dict[str, Any]:
        """Run similarity analysis for all bills"""
        logger.info("Starting full similarity analysis")

        # Get all embeddings
        bill_ids, embeddings = self.get_all_embeddings()

        if len(bill_ids) == 0:
            logger.warning("No embeddings found for analysis")
            return {"success": False, "message": "No embeddings found"}

        logger.info(f"Calculating similarities for {len(bill_ids)} bills")

        # Calculate similarity matrix
        similarity_matrix = self.calculate_similarity_matrix(embeddings)

        # Find high similarity pairs
        high_similarity_pairs = self.find_high_similarity_pairs(
            similarity_matrix, bill_ids
        )

        # Store results
        self.store_similarities(high_similarity_pairs)

        result = {
            "success": True,
            "total_bills": len(bill_ids),
            "total_comparisons": len(high_similarity_pairs),
            "threshold": self.config.similarity_threshold,
            "model_name": self.config.model_name,
        }

        logger.info(f"Similarity analysis completed: {result}")
        return result

    def get_similarity_stats(self) -> Dict[str, Any]:
        """Get statistics about stored similarities"""
        query = """
        SELECT 
            COUNT(*) as total_pairs,
            AVG(similarity_score) as avg_similarity,
            MAX(similarity_score) as max_similarity,
            MIN(similarity_score) as min_similarity,
            COUNT(CASE WHEN similarity_score >= 0.9 THEN 1 END) as very_high_pairs,
            COUNT(CASE WHEN similarity_score >= 0.8 AND similarity_score < 0.9 THEN 1 END) as high_pairs,
            COUNT(CASE WHEN similarity_score >= 0.7 AND similarity_score < 0.8 THEN 1 END) as medium_pairs
        FROM analysis.bill_similarity 
        WHERE model_name = %s
        """

        self.cursor.execute(query, (self.config.model_name,))
        result = dict(self.cursor.fetchone())

        return result

    def cleanup_existing_similarities(self):
        """Remove existing similarities for this model"""
        query = "DELETE FROM analysis.bill_similarity WHERE model_name = %s"
        self.cursor.execute(query, (self.config.model_name,))
        self.conn.commit()
        logger.info(
            f"Cleaned up existing similarities for model {self.config.model_name}"
        )


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Analyze bill similarities")
    parser.add_argument(
        "--model", type=str, default="all-minilm:l6-v2", help="Model name for analysis"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.7, help="Similarity threshold"
    )
    parser.add_argument(
        "--max-comparisons",
        type=int,
        default=10000,
        help="Maximum number of similarity pairs to store",
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up existing similarities first"
    )
    parser.add_argument(
        "--stats", action="store_true", help="Show similarity statistics"
    )
    parser.add_argument(
        "--bill-id", type=str, help="Calculate similarities for specific bill"
    )

    args = parser.parse_args()

    # Create configuration
    config = SimilarityConfig(
        model_name=args.model,
        similarity_threshold=args.threshold,
        max_comparisons=args.max_comparisons,
    )

    # Create analyzer
    try:
        analyzer = SimilarityAnalyzer(config)

        # Show stats if requested
        if args.stats:
            stats = analyzer.get_similarity_stats()
            print("\n" + "=" * 50)
            print("SIMILARITY STATISTICS")
            print("=" * 50)
            print(f"Model: {config.model_name}")
            print(f"Total pairs: {stats['total_pairs']}")
            print(f"Average similarity: {stats['avg_similarity']:.3f}")
            print(f"Max similarity: {stats['max_similarity']:.3f}")
            print(f"Min similarity: {stats['min_similarity']:.3f}")
            print(f"Very high pairs (>=0.9): {stats['very_high_pairs']}")
            print(f"High pairs (0.8-0.9): {stats['high_pairs']}")
            print(f"Medium pairs (0.7-0.8): {stats['medium_pairs']}")
            print("=" * 50)
            return

        # Calculate for specific bill if requested
        if args.bill_id:
            similarities = analyzer.calculate_similarities_for_bill(args.bill_id)
            print(f"\nFound {len(similarities)} similar bills for {args.bill_id}")
            for sim in similarities[:10]:  # Show top 10
                print(f"  {sim['bill_id_2']}: {sim['similarity_score']:.3f}")
            return

        # Cleanup if requested
        if args.cleanup:
            analyzer.cleanup_existing_similarities()

        # Run full analysis
        result = analyzer.run_full_similarity_analysis()

        if result["success"]:
            print("\n" + "=" * 50)
            print("SIMILARITY ANALYSIS COMPLETE")
            print("=" * 50)
            print(f"Total bills: {result['total_bills']}")
            print(f"Similarity pairs found: {result['total_comparisons']}")
            print(f"Threshold: {result['threshold']}")
            print(f"Model: {result['model_name']}")
            print("=" * 50)
        else:
            print(f"Analysis failed: {result['message']}")

    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
