#!/usr/bin/env python3
"""
ChatMind Tag Effectiveness Tester

This script tests the quality and effectiveness of tags in the ChatMind knowledge graph.
"""

import json
import logging
from typing import List, Dict, Tuple
from collections import Counter, defaultdict

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


class TagEffectivenessTester:
    """Test tag effectiveness in ChatMind."""
    
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
    
    def test_tag_coverage(self) -> Dict:
        """Test tag coverage across chunks."""
        logger.info("🔍 Testing tag coverage...")
        
        with self.driver.session() as session:
            # Count total chunks
            total_chunks_query = "MATCH (c:Chunk) RETURN count(c) as count"
            total_chunks = session.run(total_chunks_query).single()['count']
            
            # Count tagged chunks
            tagged_chunks_query = """
            MATCH (c:Chunk)-[:TAGGED_WITH]->(t:Tag)
            RETURN count(DISTINCT c) as count
            """
            tagged_chunks = session.run(tagged_chunks_query).single()['count']
            
            # Count total tags
            total_tags_query = "MATCH (t:Tag) RETURN count(t) as count"
            total_tags = session.run(total_tags_query).single()['count']
            
            # Count total tag relationships
            total_relationships_query = """
            MATCH ()-[r:TAGGED_WITH]->()
            RETURN count(r) as count
            """
            total_relationships = session.run(total_relationships_query).single()['count']
            
            coverage = {
                'total_chunks': total_chunks,
                'tagged_chunks': tagged_chunks,
                'total_tags': total_tags,
                'total_relationships': total_relationships,
                'coverage_percentage': (tagged_chunks / total_chunks * 100) if total_chunks > 0 else 0,
                'avg_tags_per_chunk': (total_relationships / tagged_chunks) if tagged_chunks > 0 else 0,
                'avg_chunks_per_tag': (total_relationships / total_tags) if total_tags > 0 else 0
            }
            
            logger.info(f"  Total chunks: {total_chunks:,}")
            logger.info(f"  Tagged chunks: {tagged_chunks:,}")
            logger.info(f"  Total tags: {total_tags:,}")
            logger.info(f"  Coverage: {coverage['coverage_percentage']:.1f}%")
            logger.info(f"  Avg tags per chunk: {coverage['avg_tags_per_chunk']:.1f}")
            logger.info(f"  Avg chunks per tag: {coverage['avg_chunks_per_tag']:.1f}")
            
            return coverage
    
    def test_tag_usage_distribution(self) -> Dict:
        """Test tag usage distribution."""
        logger.info("🔍 Testing tag usage distribution...")
        
        with self.driver.session() as session:
            # Get tag usage statistics
            usage_query = """
            MATCH (t:Tag)<-[:TAGGED_WITH]-(c:Chunk)
            RETURN t.name as tag_name, count(c) as usage_count
            ORDER BY usage_count DESC
            """
            
            tag_usage = []
            for record in session.run(usage_query):
                tag_usage.append({
                    'tag': record['tag_name'],
                    'usage_count': record['usage_count']
                })
            
            if not tag_usage:
                logger.warning("No tag usage data found")
                return {}
            
            # Calculate distribution statistics
            usage_counts = [t['usage_count'] for t in tag_usage]
            import numpy as np
            
            distribution = {
                'total_tags': len(tag_usage),
                'total_usage': sum(usage_counts),
                'mean_usage': np.mean(usage_counts),
                'median_usage': np.median(usage_counts),
                'max_usage': np.max(usage_counts),
                'min_usage': np.min(usage_counts),
                'high_usage_tags': len([u for u in usage_counts if u > 10]),
                'medium_usage_tags': len([u for u in usage_counts if 5 <= u <= 10]),
                'low_usage_tags': len([u for u in usage_counts if u < 5]),
                'top_tags': tag_usage[:20]
            }
            
            logger.info(f"  Total tags: {distribution['total_tags']:,}")
            logger.info(f"  High usage (>10): {distribution['high_usage_tags']:,}")
            logger.info(f"  Medium usage (5-10): {distribution['medium_usage_tags']:,}")
            logger.info(f"  Low usage (<5): {distribution['low_usage_tags']:,}")
            logger.info(f"  Mean usage: {distribution['mean_usage']:.1f}")
            
            # Show top tags
            logger.info("  Top 10 tags:")
            for i, tag in enumerate(distribution['top_tags'][:10]):
                logger.info(f"    {i+1}. {tag['tag']}: {tag['usage_count']:,}")
            
            return distribution
    
    def test_tag_diversity(self) -> Dict:
        """Test tag diversity and uniqueness."""
        logger.info("🔍 Testing tag diversity...")
        
        with self.driver.session() as session:
            # Get all tags with their usage
            diversity_query = """
            MATCH (t:Tag)<-[:TAGGED_WITH]-(c:Chunk)
            RETURN t.name as tag_name, count(c) as usage_count
            ORDER BY usage_count DESC
            """
            
            tags = []
            for record in session.run(diversity_query):
                tags.append({
                    'tag': record['tag_name'],
                    'usage_count': record['usage_count']
                })
            
            if not tags:
                return {}
            
            # Analyze tag diversity
            total_usage = sum(t['usage_count'] for t in tags)
            unique_tags = len(tags)
            
            # Calculate diversity metrics
            usage_counts = [t['usage_count'] for t in tags]
            import numpy as np
            
            # Gini coefficient for tag usage inequality
            sorted_counts = sorted(usage_counts)
            n = len(sorted_counts)
            if n > 0:
                cumsum = np.cumsum(sorted_counts)
                gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0
            else:
                gini = 0
            
            diversity = {
                'total_tags': unique_tags,
                'total_usage': total_usage,
                'avg_usage_per_tag': total_usage / unique_tags if unique_tags > 0 else 0,
                'gini_coefficient': gini,
                'usage_inequality': 'High' if gini > 0.6 else 'Medium' if gini > 0.3 else 'Low',
                'most_used_tags': tags[:10],
                'least_used_tags': tags[-10:] if len(tags) >= 10 else tags
            }
            
            logger.info(f"  Total unique tags: {unique_tags:,}")
            logger.info(f"  Total usage: {total_usage:,}")
            logger.info(f"  Avg usage per tag: {diversity['avg_usage_per_tag']:.1f}")
            logger.info(f"  Gini coefficient: {gini:.3f} ({diversity['usage_inequality']} inequality)")
            
            return diversity
    
    def test_tag_search_effectiveness(self) -> Dict:
        """Test how effective tags are for search."""
        logger.info("🔍 Testing tag search effectiveness...")
        
        with self.driver.session() as session:
            # Get popular tags to test
            popular_tags_query = """
            MATCH (t:Tag)<-[:TAGGED_WITH]-(c:Chunk)
            WITH t, count(c) as usage_count
            WHERE usage_count >= 5 AND usage_count <= 50
            RETURN t.name as tag_name, usage_count
            ORDER BY usage_count DESC
            LIMIT 10
            """
            
            test_tags = []
            for record in session.run(popular_tags_query):
                test_tags.append({
                    'tag': record['tag_name'],
                    'usage_count': record['usage_count']
                })
            
            search_results = []
            for tag_info in test_tags[:5]:  # Test first 5
                tag_name = tag_info['tag']
                
                # Find chunks with this tag
                search_query = """
                MATCH (c:Chunk)-[:TAGGED_WITH]->(t:Tag {name: $tag_name})
                RETURN c.content as content, c.chat_title as chat_title
                LIMIT 10
                """
                
                chunks = []
                for record in session.run(search_query, tag_name=tag_name):
                    chunks.append({
                        'content': record['content'][:100] + "...",
                        'chat_title': record['chat_title']
                    })
                
                search_results.append({
                    'tag': tag_name,
                    'expected_count': tag_info['usage_count'],
                    'found_chunks': len(chunks),
                    'sample_chunks': chunks[:3]
                })
            
            # Calculate effectiveness metrics
            total_searches = len(search_results)
            successful_searches = len([r for r in search_results if r['found_chunks'] > 0])
            high_quality_searches = len([r for r in search_results if r['found_chunks'] >= 3])
            
            effectiveness = {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'high_quality_searches': high_quality_searches,
                'success_rate': successful_searches / total_searches if total_searches > 0 else 0,
                'high_quality_rate': high_quality_searches / total_searches if total_searches > 0 else 0,
                'search_results': search_results
            }
            
            logger.info(f"  Total searches: {total_searches}")
            logger.info(f"  Successful searches: {successful_searches}")
            logger.info(f"  High quality searches: {high_quality_searches}")
            logger.info(f"  Success rate: {effectiveness['success_rate']:.1%}")
            
            return effectiveness
    
    def test_tag_relationships(self) -> Dict:
        """Test tag co-occurrence and relationships."""
        logger.info("🔍 Testing tag relationships...")
        
        with self.driver.session() as session:
            # Find tags that co-occur frequently
            cooccurrence_query = """
            MATCH (c:Chunk)-[:TAGGED_WITH]->(t1:Tag)
            MATCH (c)-[:TAGGED_WITH]->(t2:Tag)
            WHERE t1 <> t2
            WITH t1, t2, count(c) as cooccurrence_count
            WHERE cooccurrence_count >= 2
            RETURN t1.name as tag1, t2.name as tag2, cooccurrence_count
            ORDER BY cooccurrence_count DESC
            LIMIT 20
            """
            
            cooccurrences = []
            for record in session.run(cooccurrence_query):
                cooccurrences.append({
                    'tag1': record['tag1'],
                    'tag2': record['tag2'],
                    'count': record['cooccurrence_count']
                })
            
            # Find tags that are most commonly used together
            tag_pairs = defaultdict(int)
            for cooc in cooccurrences:
                pair = tuple(sorted([cooc['tag1'], cooc['tag2']]))
                tag_pairs[pair] += cooc['count']
            
            # Get top tag pairs
            top_pairs = sorted(tag_pairs.items(), key=lambda x: x[1], reverse=True)[:10]
            
            relationships = {
                'total_cooccurrences': len(cooccurrences),
                'unique_tag_pairs': len(tag_pairs),
                'top_tag_pairs': [{'tags': list(pair), 'count': count} for pair, count in top_pairs],
                'high_cooccurrence_pairs': [c for c in cooccurrences if c['count'] >= 5]
            }
            
            logger.info(f"  Total co-occurrences: {relationships['total_cooccurrences']:,}")
            logger.info(f"  Unique tag pairs: {relationships['unique_tag_pairs']:,}")
            logger.info(f"  High co-occurrence pairs: {len(relationships['high_cooccurrence_pairs']):,}")
            
            # Show top tag pairs
            logger.info("  Top tag pairs:")
            for i, pair_info in enumerate(relationships['top_tag_pairs'][:5]):
                tags = pair_info['tags']
                count = pair_info['count']
                logger.info(f"    {i+1}. {tags[0]} + {tags[1]}: {count} co-occurrences")
            
            return relationships
    
    def test_domain_tag_effectiveness(self) -> Dict:
        """Test effectiveness of domain tags specifically."""
        logger.info("🔍 Testing domain tag effectiveness...")
        
        with self.driver.session() as session:
            # Find domain tags
            domain_query = """
            MATCH (t:Tag)
            WHERE t.name CONTAINS 'domain:'
            RETURN t.name as domain_tag
            """
            
            domain_tags = []
            for record in session.run(domain_query):
                domain_tags.append(record['domain_tag'])
            
            if not domain_tags:
                logger.warning("No domain tags found")
                return {}
            
            # Analyze domain tag usage
            domain_usage = {}
            for domain_tag in domain_tags:
                usage_query = """
                MATCH (c:Chunk)-[:TAGGED_WITH]->(t:Tag {name: $domain_tag})
                RETURN count(c) as usage_count
                """
                result = session.run(usage_query, domain_tag=domain_tag).single()
                domain_usage[domain_tag] = result['usage_count']
            
            # Calculate domain distribution
            total_domain_usage = sum(domain_usage.values())
            domain_distribution = {
                domain: (count / total_domain_usage * 100) if total_domain_usage > 0 else 0
                for domain, count in domain_usage.items()
            }
            
            domain_analysis = {
                'total_domain_tags': len(domain_tags),
                'total_domain_usage': total_domain_usage,
                'domain_distribution': domain_distribution,
                'most_common_domain': max(domain_usage.items(), key=lambda x: x[1]) if domain_usage else None,
                'domain_tags': domain_tags
            }
            
            logger.info(f"  Total domain tags: {len(domain_tags)}")
            logger.info(f"  Total domain usage: {total_domain_usage:,}")
            
            # Show domain distribution
            logger.info("  Domain distribution:")
            sorted_domains = sorted(domain_distribution.items(), key=lambda x: x[1], reverse=True)
            for domain, percentage in sorted_domains[:5]:
                logger.info(f"    {domain}: {percentage:.1f}%")
            
            return domain_analysis
    
    def run_all_tests(self):
        """Run all tag effectiveness tests."""
        logger.info("🚀 Starting ChatMind Tag Effectiveness Tests")
        
        if not self.connect():
            return None
        
        results = {}
        
        # Run all tests
        tests = [
            ('Coverage', self.test_tag_coverage),
            ('Usage Distribution', self.test_tag_usage_distribution),
            ('Diversity', self.test_tag_diversity),
            ('Search Effectiveness', self.test_tag_search_effectiveness),
            ('Tag Relationships', self.test_tag_relationships),
            ('Domain Tags', self.test_domain_tag_effectiveness)
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
        logger.info("📊 TAG EFFECTIVENESS SUMMARY")
        logger.info(f"{'='*50}")
        
        if 'coverage' in results:
            cov = results['coverage']
            logger.info(f"📈 Tag Coverage:")
            logger.info(f"  • Coverage: {cov.get('coverage_percentage', 0):.1f}%")
            logger.info(f"  • Avg tags per chunk: {cov.get('avg_tags_per_chunk', 0):.1f}")
            logger.info(f"  • Avg chunks per tag: {cov.get('avg_chunks_per_tag', 0):.1f}")
        
        if 'usage_distribution' in results:
            dist = results['usage_distribution']
            logger.info(f"📊 Usage Distribution:")
            logger.info(f"  • High usage tags: {dist.get('high_usage_tags', 0):,}")
            logger.info(f"  • Medium usage tags: {dist.get('medium_usage_tags', 0):,}")
            logger.info(f"  • Low usage tags: {dist.get('low_usage_tags', 0):,}")
        
        if 'diversity' in results:
            div = results['diversity']
            logger.info(f"🎯 Tag Diversity:")
            logger.info(f"  • Gini coefficient: {div.get('gini_coefficient', 0):.3f}")
            logger.info(f"  • Usage inequality: {div.get('usage_inequality', 'Unknown')}")
        
        if 'search_effectiveness' in results:
            search = results['search_effectiveness']
            logger.info(f"🔍 Search Effectiveness:")
            logger.info(f"  • Success rate: {search.get('success_rate', 0):.1%}")
            logger.info(f"  • High quality rate: {search.get('high_quality_rate', 0):.1%}")
        
        logger.info(f"\n{'='*50}")
        logger.info("🎉 Tag effectiveness testing completed!")
        logger.info(f"{'='*50}")


@click.command()
@click.option('--uri', default="bolt://localhost:7687", help='Neo4j URI')
@click.option('--user', default="neo4j", help='Neo4j username')
@click.option('--password', default="password", help='Neo4j password')
@click.option('--output', type=click.Path(), help='Save results to JSON file')
def main(uri: str, user: str, password: str, output: str):
    """Run ChatMind tag effectiveness tests."""
    
    tester = TagEffectivenessTester(uri, user, password)
    results = tester.run_all_tests()
    
    if output and results:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"📄 Results saved to: {output}")


if __name__ == "__main__":
    main() 