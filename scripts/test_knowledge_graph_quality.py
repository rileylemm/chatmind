#!/usr/bin/env python3
"""
ChatMind Knowledge Graph Quality Testing Suite

This script tests the effectiveness and quality of the final knowledge graph:
1. Data completeness and integrity
2. Similarity relationship quality
3. Tag effectiveness and coverage
4. Topic clustering quality
5. Search and retrieval effectiveness
6. Graph connectivity and navigation
"""

import json
import jsonlines
import logging
import click
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter, defaultdict
import numpy as np
from datetime import datetime

# Neo4j imports
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not available")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeGraphTester:
    """Comprehensive testing suite for ChatMind knowledge graph quality."""
    
    def __init__(self, neo4j_uri="bolt://localhost:7687", neo4j_user="neo4j", neo4j_password="password"):
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.driver = None
        self.test_results = {}
        
    def connect_neo4j(self):
        """Connect to Neo4j database."""
        if not NEO4J_AVAILABLE:
            logger.error("Neo4j driver not available")
            return False
            
        try:
            self.driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                logger.info("✅ Successfully connected to Neo4j")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Neo4j: {e}")
            return False
    
    def test_data_completeness(self) -> Dict:
        """Test 1: Data completeness and integrity."""
        logger.info("🔍 Test 1: Data Completeness and Integrity")
        
        results = {
            'node_counts': {},
            'relationship_counts': {},
            'data_quality': {},
            'coverage_metrics': {}
        }
        
        try:
            with self.driver.session() as session:
                # Count all node types
                node_queries = {
                    'Chat': "MATCH (c:Chat) RETURN count(c) as count",
                    'Message': "MATCH (m:Message) RETURN count(m) as count", 
                    'Chunk': "MATCH (c:Chunk) RETURN count(c) as count",
                    'Tag': "MATCH (t:Tag) RETURN count(t) as count",
                    'Topic': "MATCH (t:Topic) RETURN count(t) as count"
                }
                
                for node_type, query in node_queries.items():
                    result = session.run(query)
                    count = result.single()['count']
                    results['node_counts'][node_type] = count
                    logger.info(f"  {node_type}: {count:,}")
                
                # Count relationships
                rel_queries = {
                    'CONTAINS': "MATCH ()-[r:CONTAINS]->() RETURN count(r) as count",
                    'HAS_CHUNK': "MATCH ()-[r:HAS_CHUNK]->() RETURN count(r) as count",
                    'TAGGED_WITH': "MATCH ()-[r:TAGGED_WITH]->() RETURN count(r) as count",
                    'SUMMARIZES': "MATCH ()-[r:SUMMARIZES]->() RETURN count(r) as count",
                    'SIMILAR_TO': "MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) as count"
                }
                
                for rel_type, query in rel_queries.items():
                    result = session.run(query)
                    count = result.single()['count']
                    results['relationship_counts'][rel_type] = count
                    logger.info(f"  {rel_type}: {count:,}")
                
                # Data quality checks
                quality_checks = {
                    'chats_with_messages': "MATCH (c:Chat)-[:CONTAINS]->(m:Message) RETURN count(DISTINCT c) as count",
                    'chunks_with_tags': "MATCH (c:Chunk)-[:TAGGED_WITH]->(t:Tag) RETURN count(DISTINCT c) as count",
                    'topics_with_coordinates': "MATCH (t:Topic) WHERE t.x IS NOT NULL AND t.y IS NOT NULL RETURN count(t) as count",
                    'messages_with_chunks': "MATCH (m:Message)-[:HAS_CHUNK]->(c:Chunk) RETURN count(DISTINCT m) as count"
                }
                
                for check_name, query in quality_checks.items():
                    result = session.run(query)
                    count = result.single()['count']
                    results['data_quality'][check_name] = count
                    logger.info(f"  {check_name}: {count:,}")
                
                # Coverage metrics
                total_chats = results['node_counts']['Chat']
                total_messages = results['node_counts']['Message']
                total_chunks = results['node_counts']['Chunk']
                
                coverage = {
                    'chat_to_message_ratio': total_messages / total_chats if total_chats > 0 else 0,
                    'message_to_chunk_ratio': total_chunks / total_messages if total_messages > 0 else 0,
                    'chunks_with_tags_pct': (results['data_quality']['chunks_with_tags'] / total_chunks * 100) if total_chunks > 0 else 0,
                    'messages_with_chunks_pct': (results['data_quality']['messages_with_chunks'] / total_messages * 100) if total_messages > 0 else 0
                }
                
                results['coverage_metrics'] = coverage
                
                for metric, value in coverage.items():
                    logger.info(f"  {metric}: {value:.2f}")
                
        except Exception as e:
            logger.error(f"❌ Data completeness test failed: {e}")
            return None
            
        self.test_results['data_completeness'] = results
        return results
    
    def test_similarity_quality(self) -> Dict:
        """Test 2: Similarity relationship quality and effectiveness."""
        logger.info("🔍 Test 2: Similarity Relationship Quality")
        
        results = {
            'similarity_distribution': {},
            'similarity_examples': [],
            'connectivity_analysis': {},
            'quality_metrics': {}
        }
        
        try:
            with self.driver.session() as session:
                # Analyze similarity score distribution
                similarity_query = """
                MATCH (c1:Chat)-[r:SIMILAR_TO]->(c2:Chat)
                RETURN r.similarity as similarity
                ORDER BY r.similarity DESC
                LIMIT 1000
                """
                
                similarities = []
                for record in session.run(similarity_query):
                    similarities.append(record['similarity'])
                
                if similarities:
                    results['similarity_distribution'] = {
                        'mean': np.mean(similarities),
                        'median': np.median(similarities),
                        'std': np.std(similarities),
                        'min': np.min(similarities),
                        'max': np.max(similarities),
                        'count': len(similarities)
                    }
                    
                    logger.info(f"  Similarity stats: mean={results['similarity_distribution']['mean']:.3f}, "
                              f"std={results['similarity_distribution']['std']:.3f}")
                
                # Get high-quality similarity examples
                high_sim_query = """
                MATCH (c1:Chat)-[r:SIMILAR_TO]->(c2:Chat)
                WHERE r.similarity > 0.7
                RETURN c1.title as chat1_title, c2.title as chat2_title, r.similarity as similarity
                ORDER BY r.similarity DESC
                LIMIT 10
                """
                
                for record in session.run(high_sim_query):
                    results['similarity_examples'].append({
                        'chat1': record['chat1_title'],
                        'chat2': record['chat2_title'],
                        'similarity': record['similarity']
                    })
                
                # Connectivity analysis
                connectivity_query = """
                MATCH (c:Chat)
                OPTIONAL MATCH (c)-[r:SIMILAR_TO]->()
                RETURN c.title as title, count(r) as similarity_count
                ORDER BY similarity_count DESC
                LIMIT 20
                """
                
                connectivity = []
                for record in session.run(connectivity_query):
                    connectivity.append({
                        'title': record['title'],
                        'similarity_count': record['similarity_count']
                    })
                
                results['connectivity_analysis'] = connectivity
                
                # Quality metrics
                total_similarities = results['similarity_distribution'].get('count', 0)
                high_similarities = len([s for s in similarities if s > 0.5])
                
                results['quality_metrics'] = {
                    'total_similarities': total_similarities,
                    'high_similarities': high_similarities,
                    'high_similarity_ratio': high_similarities / total_similarities if total_similarities > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Similarity quality test failed: {e}")
            return None
            
        self.test_results['similarity_quality'] = results
        return results
    
    def test_tag_effectiveness(self) -> Dict:
        """Test 3: Tag effectiveness and coverage."""
        logger.info("🔍 Test 3: Tag Effectiveness and Coverage")
        
        results = {
            'tag_statistics': {},
            'tag_coverage': {},
            'tag_examples': [],
            'tag_quality': {}
        }
        
        try:
            with self.driver.session() as session:
                # Tag usage statistics
                tag_stats_query = """
                MATCH (t:Tag)
                OPTIONAL MATCH (t)<-[:TAGGED_WITH]-(c:Chunk)
                RETURN t.name as tag_name, count(c) as usage_count
                ORDER BY usage_count DESC
                """
                
                tag_stats = []
                for record in session.run(tag_stats_query):
                    tag_stats.append({
                        'tag': record['tag_name'],
                        'usage_count': record['usage_count']
                    })
                
                results['tag_statistics'] = tag_stats
                
                # Tag coverage analysis
                coverage_query = """
                MATCH (c:Chunk)
                OPTIONAL MATCH (c)-[:TAGGED_WITH]->(t:Tag)
                RETURN count(DISTINCT c) as total_chunks, 
                       count(DISTINCT CASE WHEN t IS NOT NULL THEN c END) as tagged_chunks
                """
                
                coverage_result = session.run(coverage_query).single()
                results['tag_coverage'] = {
                    'total_chunks': coverage_result['total_chunks'],
                    'tagged_chunks': coverage_result['tagged_chunks'],
                    'coverage_percentage': (coverage_result['tagged_chunks'] / coverage_result['total_chunks'] * 100) if coverage_result['total_chunks'] > 0 else 0
                }
                
                # Most useful tags (high usage, good distribution)
                useful_tags_query = """
                MATCH (t:Tag)<-[:TAGGED_WITH]-(c:Chunk)
                WITH t, count(c) as usage_count
                WHERE usage_count > 5 AND usage_count < 100  // Good balance
                RETURN t.name as tag_name, usage_count
                ORDER BY usage_count DESC
                LIMIT 20
                """
                
                useful_tags = []
                for record in session.run(useful_tags_query):
                    useful_tags.append({
                        'tag': record['tag_name'],
                        'usage_count': record['usage_count']
                    })
                
                results['tag_examples'] = useful_tags
                
                # Tag quality metrics
                total_tags = len(tag_stats)
                high_usage_tags = len([t for t in tag_stats if t['usage_count'] > 10])
                low_usage_tags = len([t for t in tag_stats if t['usage_count'] <= 2])
                
                results['tag_quality'] = {
                    'total_tags': total_tags,
                    'high_usage_tags': high_usage_tags,
                    'low_usage_tags': low_usage_tags,
                    'tag_diversity_score': high_usage_tags / total_tags if total_tags > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Tag effectiveness test failed: {e}")
            return None
            
        self.test_results['tag_effectiveness'] = results
        return results
    
    def test_topic_clustering_quality(self) -> Dict:
        """Test 4: Topic clustering quality and effectiveness."""
        logger.info("🔍 Test 4: Topic Clustering Quality")
        
        results = {
            'topic_statistics': {},
            'topic_coverage': {},
            'topic_examples': [],
            'clustering_quality': {}
        }
        
        try:
            with self.driver.session() as session:
                # Topic statistics
                topic_stats_query = """
                MATCH (t:Topic)
                OPTIONAL MATCH (t)<-[:SUMMARIZES]-(c:Chunk)
                RETURN t.name as topic_name, count(c) as chunk_count, t.domain as domain, t.complexity as complexity
                ORDER BY chunk_count DESC
                """
                
                topic_stats = []
                for record in session.run(topic_stats_query):
                    topic_stats.append({
                        'topic': record['topic_name'],
                        'chunk_count': record['chunk_count'],
                        'domain': record['domain'],
                        'complexity': record['complexity']
                    })
                
                results['topic_statistics'] = topic_stats
                
                # Topic coverage
                coverage_query = """
                MATCH (c:Chunk)
                OPTIONAL MATCH (c)-[:SUMMARIZES]->(t:Topic)
                RETURN count(DISTINCT c) as total_chunks, 
                       count(DISTINCT CASE WHEN t IS NOT NULL THEN c END) as summarized_chunks
                """
                
                coverage_result = session.run(coverage_query).single()
                results['topic_coverage'] = {
                    'total_chunks': coverage_result['total_chunks'],
                    'summarized_chunks': coverage_result['summarized_chunks'],
                    'coverage_percentage': (coverage_result['summarized_chunks'] / coverage_result['total_chunks'] * 100) if coverage_result['total_chunks'] > 0 else 0
                }
                
                # Best topic examples (good size, meaningful)
                good_topics_query = """
                MATCH (t:Topic)<-[:SUMMARIZES]-(c:Chunk)
                WITH t, count(c) as chunk_count
                WHERE chunk_count >= 5 AND chunk_count <= 50
                RETURN t.name as topic_name, chunk_count, t.domain as domain
                ORDER BY chunk_count DESC
                LIMIT 15
                """
                
                good_topics = []
                for record in session.run(good_topics_query):
                    good_topics.append({
                        'topic': record['topic_name'],
                        'chunk_count': record['chunk_count'],
                        'domain': record['domain']
                    })
                
                results['topic_examples'] = good_topics
                
                # Clustering quality metrics
                total_topics = len(topic_stats)
                well_sized_topics = len([t for t in topic_stats if 5 <= t['chunk_count'] <= 50])
                oversized_topics = len([t for t in topic_stats if t['chunk_count'] > 50])
                undersized_topics = len([t for t in topic_stats if t['chunk_count'] < 5])
                
                results['clustering_quality'] = {
                    'total_topics': total_topics,
                    'well_sized_topics': well_sized_topics,
                    'oversized_topics': oversized_topics,
                    'undersized_topics': undersized_topics,
                    'quality_score': well_sized_topics / total_topics if total_topics > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Topic clustering test failed: {e}")
            return None
            
        self.test_results['topic_clustering'] = results
        return results
    
    def test_search_effectiveness(self) -> Dict:
        """Test 5: Search and retrieval effectiveness."""
        logger.info("🔍 Test 5: Search and Retrieval Effectiveness")
        
        results = {
            'search_tests': [],
            'retrieval_quality': {},
            'navigation_tests': []
        }
        
        try:
            with self.driver.session() as session:
                # Test 1: Tag-based search
                tag_search_query = """
                MATCH (t:Tag {name: $tag_name})<-[:TAGGED_WITH]-(c:Chunk)
                RETURN c.content as content, c.chat_title as chat_title
                LIMIT 5
                """
                
                # Test with a common tag
                common_tags = ["#technical", "#python", "#help", "#question"]
                for tag in common_tags:
                    try:
                        search_results = []
                        for record in session.run(tag_search_query, tag_name=tag):
                            search_results.append({
                                'content': record['content'][:100] + "...",
                                'chat_title': record['chat_title']
                            })
                        
                        results['search_tests'].append({
                            'search_type': 'tag_search',
                            'query': tag,
                            'results_count': len(search_results),
                            'sample_results': search_results[:3]
                        })
                    except Exception as e:
                        logger.warning(f"Tag search failed for {tag}: {e}")
                
                # Test 2: Similarity-based recommendations
                similarity_search_query = """
                MATCH (c1:Chat {title: $chat_title})-[:SIMILAR_TO]->(c2:Chat)
                RETURN c2.title as similar_chat, c2.similarity as similarity
                ORDER BY similarity DESC
                LIMIT 5
                """
                
                # Get a sample chat to test similarity
                sample_chat_query = "MATCH (c:Chat) RETURN c.title as title LIMIT 1"
                sample_result = session.run(sample_chat_query).single()
                
                if sample_result:
                    chat_title = sample_result['title']
                    similar_results = []
                    for record in session.run(similarity_search_query, chat_title=chat_title):
                        similar_results.append({
                            'similar_chat': record['similar_chat'],
                            'similarity': record['similarity']
                        })
                    
                    results['search_tests'].append({
                        'search_type': 'similarity_search',
                        'query': chat_title,
                        'results_count': len(similar_results),
                        'sample_results': similar_results[:3]
                    })
                
                # Test 3: Topic-based navigation
                topic_nav_query = """
                MATCH (t:Topic)<-[:SUMMARIZES]-(c:Chunk)
                WITH t, count(c) as chunk_count
                WHERE chunk_count >= 5
                RETURN t.name as topic_name, chunk_count, t.domain as domain
                ORDER BY chunk_count DESC
                LIMIT 10
                """
                
                topic_results = []
                for record in session.run(topic_nav_query):
                    topic_results.append({
                        'topic': record['topic_name'],
                        'chunk_count': record['chunk_count'],
                        'domain': record['domain']
                    })
                
                results['navigation_tests'] = topic_results
                
                # Retrieval quality metrics
                total_search_tests = len(results['search_tests'])
                successful_searches = len([t for t in results['search_tests'] if t['results_count'] > 0])
                
                results['retrieval_quality'] = {
                    'total_search_tests': total_search_tests,
                    'successful_searches': successful_searches,
                    'success_rate': successful_searches / total_search_tests if total_search_tests > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Search effectiveness test failed: {e}")
            return None
            
        self.test_results['search_effectiveness'] = results
        return results
    
    def run_all_tests(self) -> Dict:
        """Run all quality tests and generate comprehensive report."""
        logger.info("🚀 Starting ChatMind Knowledge Graph Quality Testing Suite")
        
        if not self.connect_neo4j():
            logger.error("❌ Cannot run tests without Neo4j connection")
            return None
        
        # Run all tests
        tests = [
            ('Data Completeness', self.test_data_completeness),
            ('Similarity Quality', self.test_similarity_quality),
            ('Tag Effectiveness', self.test_tag_effectiveness),
            ('Topic Clustering', self.test_topic_clustering_quality),
            ('Search Effectiveness', self.test_search_effectiveness)
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Running: {test_name}")
                logger.info(f"{'='*50}")
                result = test_func()
                if result:
                    logger.info(f"✅ {test_name} completed successfully")
                else:
                    logger.error(f"❌ {test_name} failed")
            except Exception as e:
                logger.error(f"❌ {test_name} failed with exception: {e}")
        
        # Generate summary report
        self.generate_summary_report()
        
        return self.test_results
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report."""
        logger.info(f"\n{'='*60}")
        logger.info("📊 CHATMIND KNOWLEDGE GRAPH QUALITY REPORT")
        logger.info(f"{'='*60}")
        
        if 'data_completeness' in self.test_results:
            dc = self.test_results['data_completeness']
            logger.info(f"\n📈 DATA COMPLETENESS:")
            logger.info(f"  • Total Chats: {dc['node_counts'].get('Chat', 0):,}")
            logger.info(f"  • Total Messages: {dc['node_counts'].get('Message', 0):,}")
            logger.info(f"  • Total Chunks: {dc['node_counts'].get('Chunk', 0):,}")
            logger.info(f"  • Total Tags: {dc['node_counts'].get('Tag', 0):,}")
            logger.info(f"  • Total Topics: {dc['node_counts'].get('Topic', 0):,}")
            
            coverage = dc.get('coverage_metrics', {})
            logger.info(f"  • Chunks with Tags: {coverage.get('chunks_with_tags_pct', 0):.1f}%")
            logger.info(f"  • Messages with Chunks: {coverage.get('messages_with_chunks_pct', 0):.1f}%")
        
        if 'similarity_quality' in self.test_results:
            sq = self.test_results['similarity_quality']
            dist = sq.get('similarity_distribution', {})
            logger.info(f"\n🔗 SIMILARITY QUALITY:")
            logger.info(f"  • Total Similarities: {sq.get('quality_metrics', {}).get('total_similarities', 0):,}")
            logger.info(f"  • High Quality Similarities (>0.5): {sq.get('quality_metrics', {}).get('high_similarities', 0):,}")
            logger.info(f"  • Mean Similarity Score: {dist.get('mean', 0):.3f}")
            logger.info(f"  • Similarity Score Std Dev: {dist.get('std', 0):.3f}")
        
        if 'tag_effectiveness' in self.test_results:
            te = self.test_results['tag_effectiveness']
            coverage = te.get('tag_coverage', {})
            quality = te.get('tag_quality', {})
            logger.info(f"\n🏷️ TAG EFFECTIVENESS:")
            logger.info(f"  • Total Tags: {quality.get('total_tags', 0):,}")
            logger.info(f"  • High Usage Tags (>10): {quality.get('high_usage_tags', 0):,}")
            logger.info(f"  • Tag Coverage: {coverage.get('coverage_percentage', 0):.1f}%")
            logger.info(f"  • Tag Diversity Score: {quality.get('tag_diversity_score', 0):.2f}")
        
        if 'topic_clustering' in self.test_results:
            tc = self.test_results['topic_clustering']
            coverage = tc.get('topic_coverage', {})
            quality = tc.get('clustering_quality', {})
            logger.info(f"\n📊 TOPIC CLUSTERING:")
            logger.info(f"  • Total Topics: {quality.get('total_topics', 0):,}")
            logger.info(f"  • Well-Sized Topics (5-50 chunks): {quality.get('well_sized_topics', 0):,}")
            logger.info(f"  • Topic Coverage: {coverage.get('coverage_percentage', 0):.1f}%")
            logger.info(f"  • Clustering Quality Score: {quality.get('quality_score', 0):.2f}")
        
        if 'search_effectiveness' in self.test_results:
            se = self.test_results['search_effectiveness']
            quality = se.get('retrieval_quality', {})
            logger.info(f"\n🔍 SEARCH EFFECTIVENESS:")
            logger.info(f"  • Search Tests Run: {quality.get('total_search_tests', 0)}")
            logger.info(f"  • Successful Searches: {quality.get('successful_searches', 0)}")
            logger.info(f"  • Search Success Rate: {quality.get('success_rate', 0):.1%}")
        
        logger.info(f"\n{'='*60}")
        logger.info("🎉 Quality testing completed!")
        logger.info(f"{'='*60}")


@click.command()
@click.option('--neo4j-uri', default="bolt://localhost:7687", help='Neo4j connection URI')
@click.option('--neo4j-user', default="neo4j", help='Neo4j username')
@click.option('--neo4j-password', default="password", help='Neo4j password')
@click.option('--output-file', type=click.Path(), help='Save detailed results to JSON file')
def main(neo4j_uri: str, neo4j_user: str, neo4j_password: str, output_file: str):
    """Run comprehensive ChatMind knowledge graph quality tests."""
    
    tester = KnowledgeGraphTester(neo4j_uri, neo4j_user, neo4j_password)
    results = tester.run_all_tests()
    
    if output_file and results:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"📄 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    main() 