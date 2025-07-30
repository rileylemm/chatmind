#!/usr/bin/env python3
"""
ChatMind Similarity Quality Tester

This script specifically tests the quality and effectiveness of similarity relationships
in the ChatMind knowledge graph.
"""

import json
import logging
from typing import List, Dict, Tuple
from collections import Counter

# Click import
try:
    import click
    CLICK_AVAILABLE = True
except ImportError:
    CLICK_AVAILABLE = False
    logging.warning("Click not available")

# Neo4j imports
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimilarityTester:
    """Test similarity relationship quality in ChatMind."""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
    
    def connect(self):
        """Connect to Neo4j."""
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j driver not available")
            return False
            
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                logger.info("✅ Connected to Neo4j")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def test_similarity_distribution(self) -> Dict:
        """Test similarity score distribution."""
        logger.info("🔍 Testing similarity distribution...")
        
        with self.driver.session() as session:
            # Get all similarity scores
            query = """
            MATCH (c1:Chat)-[r:SIMILAR_TO]->(c2:Chat)
            RETURN r.similarity as similarity
            ORDER BY r.similarity DESC
            """
            
            similarities = []
            for record in session.run(query):
                similarities.append(record['similarity'])
            
            if not similarities:
                logger.warning("No similarity relationships found")
                return {}
            
            # Calculate statistics
            import numpy as np
            stats = {
                'count': len(similarities),
                'mean': np.mean(similarities),
                'median': np.median(similarities),
                'std': np.std(similarities),
                'min': np.min(similarities),
                'max': np.max(similarities),
                'high_similarities': len([s for s in similarities if s > 0.7]),
                'medium_similarities': len([s for s in similarities if 0.3 <= s <= 0.7]),
                'low_similarities': len([s for s in similarities if s < 0.3])
            }
            
            logger.info(f"  Total similarities: {stats['count']:,}")
            logger.info(f"  Mean similarity: {stats['mean']:.3f}")
            logger.info(f"  High similarities (>0.7): {stats['high_similarities']:,}")
            logger.info(f"  Medium similarities (0.3-0.7): {stats['medium_similarities']:,}")
            logger.info(f"  Low similarities (<0.3): {stats['low_similarities']:,}")
            
            return stats
    
    def test_high_quality_similarities(self) -> List[Dict]:
        """Test high-quality similarity examples."""
        logger.info("🔍 Testing high-quality similarities...")
        
        with self.driver.session() as session:
            query = """
            MATCH (c1:Chat)-[r:SIMILAR_TO]->(c2:Chat)
            WHERE r.similarity > 0.7
            RETURN c1.title as chat1, c2.title as chat2, r.similarity as similarity
            ORDER BY r.similarity DESC
            LIMIT 20
            """
            
            examples = []
            for record in session.run(query):
                examples.append({
                    'chat1': record['chat1'],
                    'chat2': record['chat2'],
                    'similarity': record['similarity']
                })
            
            logger.info(f"  Found {len(examples)} high-quality similarities")
            
            # Show top examples
            for i, example in enumerate(examples[:5]):
                logger.info(f"  {i+1}. {example['chat1'][:50]}... ↔ {example['chat2'][:50]}... ({example['similarity']:.3f})")
            
            return examples
    
    def test_similarity_connectivity(self) -> Dict:
        """Test how well connected the graph is through similarities."""
        logger.info("🔍 Testing similarity connectivity...")
        
        with self.driver.session() as session:
            # Count total chats
            total_chats_query = "MATCH (c:Chat) RETURN count(c) as count"
            total_chats = session.run(total_chats_query).single()['count']
            
            # Count chats with similarities
            connected_chats_query = """
            MATCH (c:Chat)-[:SIMILAR_TO]->()
            RETURN count(DISTINCT c) as count
            """
            connected_chats = session.run(connected_chats_query).single()['count']
            
            # Get connectivity distribution
            connectivity_query = """
            MATCH (c:Chat)
            OPTIONAL MATCH (c)-[r:SIMILAR_TO]->()
            RETURN c.title as title, count(r) as similarity_count
            ORDER BY similarity_count DESC
            LIMIT 10
            """
            
            connectivity = []
            for record in session.run(connectivity_query):
                connectivity.append({
                    'title': record['title'],
                    'similarity_count': record['similarity_count']
                })
            
            stats = {
                'total_chats': total_chats,
                'connected_chats': connected_chats,
                'connectivity_percentage': (connected_chats / total_chats * 100) if total_chats > 0 else 0,
                'top_connected_chats': connectivity
            }
            
            logger.info(f"  Total chats: {total_chats:,}")
            logger.info(f"  Connected chats: {connected_chats:,}")
            logger.info(f"  Connectivity: {stats['connectivity_percentage']:.1f}%")
            
            return stats
    
    def test_similarity_quality_by_domain(self) -> Dict:
        """Test similarity quality across different domains."""
        logger.info("🔍 Testing similarity quality by domain...")
        
        with self.driver.session() as session:
            # Get similarities with domain information
            query = """
            MATCH (c1:Chat)-[r:SIMILAR_TO]->(c2:Chat)
            MATCH (c1)-[:CONTAINS]->(m1:Message)-[:HAS_CHUNK]->(ch1:Chunk)-[:TAGGED_WITH]->(t1:Tag)
            MATCH (c2)-[:CONTAINS]->(m2:Message)-[:HAS_CHUNK]->(ch2:Chunk)-[:TAGGED_WITH]->(t2:Tag)
            WHERE t1.name CONTAINS 'domain:' AND t2.name CONTAINS 'domain:'
            RETURN r.similarity as similarity, 
                   t1.name as domain1, t2.name as domain2,
                   c1.title as chat1, c2.title as chat2
            ORDER BY r.similarity DESC
            LIMIT 50
            """
            
            domain_similarities = []
            for record in session.run(query):
                domain_similarities.append({
                    'similarity': record['similarity'],
                    'domain1': record['domain1'],
                    'domain2': record['domain2'],
                    'chat1': record['chat1'],
                    'chat2': record['chat2']
                })
            
            # Analyze by domain
            domain_stats = {}
            for sim in domain_similarities:
                domain_pair = f"{sim['domain1']} ↔ {sim['domain2']}"
                if domain_pair not in domain_stats:
                    domain_stats[domain_pair] = []
                domain_stats[domain_pair].append(sim['similarity'])
            
            # Calculate domain-specific stats
            import numpy as np
            domain_analysis = {}
            for domain_pair, similarities in domain_stats.items():
                domain_analysis[domain_pair] = {
                    'count': len(similarities),
                    'mean': np.mean(similarities),
                    'high_quality': len([s for s in similarities if s > 0.7])
                }
            
            logger.info(f"  Found similarities across {len(domain_analysis)} domain pairs")
            
            # Show best domain pairs
            sorted_domains = sorted(domain_analysis.items(), key=lambda x: x[1]['mean'], reverse=True)
            for domain_pair, stats in sorted_domains[:5]:
                logger.info(f"  {domain_pair}: mean={stats['mean']:.3f}, count={stats['count']}")
            
            return domain_analysis
    
    def test_similarity_search_effectiveness(self) -> Dict:
        """Test how effective similarity-based search is."""
        logger.info("🔍 Testing similarity search effectiveness...")
        
        with self.driver.session() as session:
            # Get a sample of chats to test
            sample_query = """
            MATCH (c:Chat)
            WHERE c.title IS NOT NULL
            RETURN c.title as title
            LIMIT 10
            """
            
            test_chats = []
            for record in session.run(sample_query):
                test_chats.append(record['title'])
            
            search_results = []
            for chat_title in test_chats[:3]:  # Test first 3
                # Find similar chats
                similar_query = """
                MATCH (c1:Chat {title: $title})-[:SIMILAR_TO]->(c2:Chat)
                RETURN c2.title as similar_title, c2.similarity as similarity
                ORDER BY similarity DESC
                LIMIT 5
                """
                
                similarities = []
                for record in session.run(similar_query, title=chat_title):
                    similarities.append({
                        'similar_title': record['similar_title'],
                        'similarity': record['similarity']
                    })
                
                search_results.append({
                    'query_chat': chat_title,
                    'similar_chats': similarities,
                    'result_count': len(similarities)
                })
            
            # Calculate effectiveness metrics
            total_searches = len(search_results)
            successful_searches = len([r for r in search_results if r['result_count'] > 0])
            high_quality_results = len([r for r in search_results if any(s['similarity'] > 0.7 for s in r['similar_chats'])])
            
            effectiveness = {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'high_quality_results': high_quality_results,
                'success_rate': successful_searches / total_searches if total_searches > 0 else 0,
                'high_quality_rate': high_quality_results / total_searches if total_searches > 0 else 0,
                'search_results': search_results
            }
            
            logger.info(f"  Total searches: {total_searches}")
            logger.info(f"  Successful searches: {successful_searches}")
            logger.info(f"  High quality results: {high_quality_results}")
            logger.info(f"  Success rate: {effectiveness['success_rate']:.1%}")
            
            return effectiveness
    
    def run_all_tests(self):
        """Run all similarity quality tests."""
        logger.info("🚀 Starting ChatMind Similarity Quality Tests")
        
        if not self.connect():
            return None
        
        results = {}
        
        # Run all tests
        tests = [
            ('Distribution', self.test_similarity_distribution),
            ('High Quality Examples', self.test_high_quality_similarities),
            ('Connectivity', self.test_similarity_connectivity),
            ('Domain Quality', self.test_similarity_quality_by_domain),
            ('Search Effectiveness', self.test_similarity_search_effectiveness)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n{'='*40}")
                logger.info(f"Running: {test_name}")
                logger.info(f"{'='*40}")
                result = test_func()
                results[test_name.lower().replace(' ', '_')] = result
                logger.info(f"✅ {test_name} completed")
            except Exception as e:
                logger.error(f"❌ {test_name} failed: {e}")
        
        # Generate summary
        self.generate_summary(results)
        
        return results
    
    def generate_summary(self, results):
        """Generate a summary of all test results."""
        logger.info(f"\n{'='*50}")
        logger.info("📊 SIMILARITY QUALITY SUMMARY")
        logger.info(f"{'='*50}")
        
        if 'distribution' in results:
            dist = results['distribution']
            logger.info(f"📈 Similarity Distribution:")
            logger.info(f"  • Total: {dist.get('count', 0):,}")
            logger.info(f"  • Mean: {dist.get('mean', 0):.3f}")
            logger.info(f"  • High quality (>0.7): {dist.get('high_similarities', 0):,}")
            logger.info(f"  • Medium quality (0.3-0.7): {dist.get('medium_similarities', 0):,}")
        
        if 'connectivity' in results:
            conn = results['connectivity']
            logger.info(f"🔗 Graph Connectivity:")
            logger.info(f"  • Connected chats: {conn.get('connected_chats', 0):,}/{conn.get('total_chats', 0):,}")
            logger.info(f"  • Connectivity: {conn.get('connectivity_percentage', 0):.1f}%")
        
        if 'search_effectiveness' in results:
            search = results['search_effectiveness']
            logger.info(f"🔍 Search Effectiveness:")
            logger.info(f"  • Success rate: {search.get('success_rate', 0):.1%}")
            logger.info(f"  • High quality rate: {search.get('high_quality_rate', 0):.1%}")
        
        logger.info(f"\n{'='*50}")
        logger.info("🎉 Similarity quality testing completed!")
        logger.info(f"{'='*50}")


@click.command()
@click.option('--uri', default="bolt://localhost:7687", help='Neo4j URI')
@click.option('--user', default="neo4j", help='Neo4j username')
@click.option('--password', default="password", help='Neo4j password')
@click.option('--output', type=click.Path(), help='Save results to JSON file')
def main(uri: str, user: str, password: str, output: str):
    """Run ChatMind similarity quality tests."""
    
    tester = SimilarityTester(uri, user, password)
    results = tester.run_all_tests()
    
    if output and results:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"📄 Results saved to: {output}")


if __name__ == "__main__":
    main() 