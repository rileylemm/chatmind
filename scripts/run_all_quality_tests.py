#!/usr/bin/env python3
"""
ChatMind Comprehensive Quality Test Runner

This script runs all quality tests for the ChatMind knowledge graph:
1. Similarity quality tests
2. Tag effectiveness tests
3. Data completeness tests
4. Search effectiveness tests
"""

import json
import logging
import click
from pathlib import Path
from datetime import datetime

# Import our test modules
try:
    from test_similarity_quality import SimilarityTester
    from test_tag_effectiveness import TagEffectivenessTester
    SIMILARITY_AVAILABLE = True
    TAG_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some test modules not available: {e}")
    SIMILARITY_AVAILABLE = False
    TAG_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComprehensiveQualityTester:
    """Run all quality tests for ChatMind."""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.all_results = {}
    
    def run_similarity_tests(self):
        """Run similarity quality tests."""
        if not SIMILARITY_AVAILABLE:
            logger.warning("Similarity tests not available")
            return None
        
        logger.info("🚀 Running Similarity Quality Tests...")
        tester = SimilarityTester(self.uri, self.user, self.password)
        results = tester.run_all_tests()
        self.all_results['similarity'] = results
        return results
    
    def run_tag_tests(self):
        """Run tag effectiveness tests."""
        if not TAG_AVAILABLE:
            logger.warning("Tag tests not available")
            return None
        
        logger.info("🚀 Running Tag Effectiveness Tests...")
        tester = TagEffectivenessTester(self.uri, self.user, self.password)
        results = tester.run_all_tests()
        self.all_results['tags'] = results
        return results
    
    def run_data_completeness_tests(self):
        """Run basic data completeness tests."""
        logger.info("🚀 Running Data Completeness Tests...")
        
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            
            with driver.session() as session:
                # Basic node counts
                node_counts = {}
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
                    node_counts[node_type] = count
                
                # Relationship counts
                rel_counts = {}
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
                    rel_counts[rel_type] = count
                
                # Coverage metrics
                coverage = {}
                coverage_queries = {
                    'chunks_with_tags': "MATCH (c:Chunk)-[:TAGGED_WITH]->(t:Tag) RETURN count(DISTINCT c) as count",
                    'messages_with_chunks': "MATCH (m:Message)-[:HAS_CHUNK]->(c:Chunk) RETURN count(DISTINCT m) as count",
                    'topics_with_coordinates': "MATCH (t:Topic) WHERE t.x IS NOT NULL AND t.y IS NOT NULL RETURN count(t) as count"
                }
                
                for metric, query in coverage_queries.items():
                    result = session.run(query)
                    count = result.single()['count']
                    coverage[metric] = count
                
                completeness = {
                    'node_counts': node_counts,
                    'relationship_counts': rel_counts,
                    'coverage_metrics': coverage,
                    'total_nodes': sum(node_counts.values()),
                    'total_relationships': sum(rel_counts.values())
                }
                
                logger.info("📊 Data Completeness Results:")
                logger.info(f"  • Total nodes: {completeness['total_nodes']:,}")
                logger.info(f"  • Total relationships: {completeness['total_relationships']:,}")
                logger.info(f"  • Chunks with tags: {coverage.get('chunks_with_tags', 0):,}")
                logger.info(f"  • Messages with chunks: {coverage.get('messages_with_chunks', 0):,}")
                logger.info(f"  • Topics with coordinates: {coverage.get('topics_with_coordinates', 0):,}")
                
                self.all_results['completeness'] = completeness
                return completeness
                
        except Exception as e:
            logger.error(f"❌ Data completeness tests failed: {e}")
            return None
    
    def run_search_effectiveness_tests(self):
        """Run search effectiveness tests."""
        logger.info("🚀 Running Search Effectiveness Tests...")
        
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            
            with driver.session() as session:
                # Test 1: Tag-based search
                tag_search_results = []
                popular_tags_query = """
                MATCH (t:Tag)<-[:TAGGED_WITH]-(c:Chunk)
                WITH t, count(c) as usage_count
                WHERE usage_count >= 5
                RETURN t.name as tag_name, usage_count
                ORDER BY usage_count DESC
                LIMIT 5
                """
                
                test_tags = []
                for record in session.run(popular_tags_query):
                    test_tags.append(record['tag_name'])
                
                for tag in test_tags:
                    search_query = """
                    MATCH (c:Chunk)-[:TAGGED_WITH]->(t:Tag {name: $tag_name})
                    RETURN count(c) as result_count
                    """
                    result = session.run(search_query, tag_name=tag).single()
                    tag_search_results.append({
                        'tag': tag,
                        'result_count': result['result_count']
                    })
                
                # Test 2: Similarity-based search
                similarity_search_results = []
                sample_chats_query = """
                MATCH (c:Chat)
                WHERE c.title IS NOT NULL
                RETURN c.title as title
                LIMIT 3
                """
                
                test_chats = []
                for record in session.run(sample_chats_query):
                    test_chats.append(record['title'])
                
                for chat_title in test_chats:
                    similar_query = """
                    MATCH (c1:Chat {title: $title})-[:SIMILAR_TO]->(c2:Chat)
                    RETURN count(c2) as similar_count
                    """
                    result = session.run(similar_query, title=chat_title).single()
                    similarity_search_results.append({
                        'chat': chat_title,
                        'similar_count': result['similar_count']
                    })
                
                # Test 3: Topic-based search
                topic_search_results = []
                topics_query = """
                MATCH (t:Topic)<-[:SUMMARIZES]-(c:Chunk)
                WITH t, count(c) as chunk_count
                WHERE chunk_count >= 5
                RETURN t.name as topic_name, chunk_count
                ORDER BY chunk_count DESC
                LIMIT 5
                """
                
                for record in session.run(topics_query):
                    topic_search_results.append({
                        'topic': record['topic_name'],
                        'chunk_count': record['chunk_count']
                    })
                
                search_effectiveness = {
                    'tag_search': {
                        'total_searches': len(tag_search_results),
                        'successful_searches': len([r for r in tag_search_results if r['result_count'] > 0]),
                        'results': tag_search_results
                    },
                    'similarity_search': {
                        'total_searches': len(similarity_search_results),
                        'successful_searches': len([r for r in similarity_search_results if r['similar_count'] > 0]),
                        'results': similarity_search_results
                    },
                    'topic_search': {
                        'total_topics': len(topic_search_results),
                        'well_sized_topics': len([r for r in topic_search_results if 5 <= r['chunk_count'] <= 50]),
                        'results': topic_search_results
                    }
                }
                
                # Calculate overall effectiveness
                tag_success_rate = search_effectiveness['tag_search']['successful_searches'] / search_effectiveness['tag_search']['total_searches'] if search_effectiveness['tag_search']['total_searches'] > 0 else 0
                sim_success_rate = search_effectiveness['similarity_search']['successful_searches'] / search_effectiveness['similarity_search']['total_searches'] if search_effectiveness['similarity_search']['total_searches'] > 0 else 0
                
                search_effectiveness['overall'] = {
                    'tag_search_success_rate': tag_success_rate,
                    'similarity_search_success_rate': sim_success_rate,
                    'average_success_rate': (tag_success_rate + sim_success_rate) / 2
                }
                
                logger.info("🔍 Search Effectiveness Results:")
                logger.info(f"  • Tag search success rate: {tag_success_rate:.1%}")
                logger.info(f"  • Similarity search success rate: {sim_success_rate:.1%}")
                logger.info(f"  • Average success rate: {search_effectiveness['overall']['average_success_rate']:.1%}")
                
                self.all_results['search_effectiveness'] = search_effectiveness
                return search_effectiveness
                
        except Exception as e:
            logger.error(f"❌ Search effectiveness tests failed: {e}")
            return None
    
    def run_all_tests(self):
        """Run all quality tests."""
        logger.info("🚀 Starting ChatMind Comprehensive Quality Testing")
        logger.info(f"📅 Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test suites
        test_suites = [
            ('Data Completeness', self.run_data_completeness_tests),
            ('Similarity Quality', self.run_similarity_tests),
            ('Tag Effectiveness', self.run_tag_tests),
            ('Search Effectiveness', self.run_search_effectiveness_tests)
        ]
        
        for suite_name, suite_func in test_suites:
            try:
                logger.info(f"\n{'='*60}")
                logger.info(f"Running: {suite_name}")
                logger.info(f"{'='*60}")
                result = suite_func()
                if result:
                    logger.info(f"✅ {suite_name} completed successfully")
                else:
                    logger.warning(f"⚠️ {suite_name} completed with issues")
            except Exception as e:
                logger.error(f"❌ {suite_name} failed: {e}")
        
        # Generate comprehensive summary
        self.generate_comprehensive_summary()
        
        return self.all_results
    
    def generate_comprehensive_summary(self):
        """Generate a comprehensive summary of all test results."""
        logger.info(f"\n{'='*70}")
        logger.info("📊 CHATMIND COMPREHENSIVE QUALITY REPORT")
        logger.info(f"{'='*70}")
        
        # Overall statistics
        total_nodes = 0
        total_relationships = 0
        
        if 'completeness' in self.all_results:
            comp = self.all_results['completeness']
            total_nodes = comp.get('total_nodes', 0)
            total_relationships = comp.get('total_relationships', 0)
            
            logger.info(f"📈 OVERALL GRAPH STATISTICS:")
            logger.info(f"  • Total nodes: {total_nodes:,}")
            logger.info(f"  • Total relationships: {total_relationships:,}")
            logger.info(f"  • Graph density: {total_relationships / total_nodes:.1f} relationships per node" if total_nodes > 0 else "  • Graph density: N/A")
        
        # Quality scores
        quality_scores = {}
        
        # Similarity quality
        if 'similarity' in self.all_results and 'distribution' in self.all_results['similarity']:
            sim_dist = self.all_results['similarity']['distribution']
            high_quality_sim = sim_dist.get('high_similarities', 0)
            total_sim = sim_dist.get('count', 0)
            quality_scores['similarity'] = high_quality_sim / total_sim if total_sim > 0 else 0
        
        # Tag effectiveness
        if 'tags' in self.all_results and 'coverage' in self.all_results['tags']:
            tag_cov = self.all_results['tags']['coverage']
            quality_scores['tag_coverage'] = tag_cov.get('coverage_percentage', 0) / 100
        
        # Search effectiveness
        if 'search_effectiveness' in self.all_results and 'overall' in self.all_results['search_effectiveness']:
            search_overall = self.all_results['search_effectiveness']['overall']
            quality_scores['search_effectiveness'] = search_overall.get('average_success_rate', 0)
        
        # Calculate overall quality score
        if quality_scores:
            overall_score = sum(quality_scores.values()) / len(quality_scores)
            quality_scores['overall'] = overall_score
            
            logger.info(f"\n🎯 QUALITY SCORES:")
            for metric, score in quality_scores.items():
                if metric != 'overall':
                    logger.info(f"  • {metric.replace('_', ' ').title()}: {score:.1%}")
            logger.info(f"  • Overall Quality Score: {overall_score:.1%}")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        
        if 'similarity' in self.all_results:
            sim_dist = self.all_results['similarity'].get('distribution', {})
            high_sim_pct = (sim_dist.get('high_similarities', 0) / sim_dist.get('count', 1) * 100) if sim_dist.get('count', 0) > 0 else 0
            if high_sim_pct < 20:
                logger.info("  • ⚠️ Low high-quality similarity rate - consider improving similarity algorithm")
            elif high_sim_pct > 50:
                logger.info("  • ✅ Excellent similarity quality")
            else:
                logger.info("  • ⚠️ Moderate similarity quality - room for improvement")
        
        if 'tags' in self.all_results:
            tag_cov = self.all_results['tags'].get('coverage', {})
            coverage_pct = tag_cov.get('coverage_percentage', 0)
            if coverage_pct < 80:
                logger.info("  • ⚠️ Low tag coverage - consider improving tagging")
            elif coverage_pct > 95:
                logger.info("  • ✅ Excellent tag coverage")
            else:
                logger.info("  • ⚠️ Good tag coverage - minor improvements possible")
        
        if 'search_effectiveness' in self.all_results:
            search_overall = self.all_results['search_effectiveness'].get('overall', {})
            search_rate = search_overall.get('average_success_rate', 0)
            if search_rate < 0.7:
                logger.info("  • ⚠️ Low search effectiveness - consider improving search algorithms")
            elif search_rate > 0.9:
                logger.info("  • ✅ Excellent search effectiveness")
            else:
                logger.info("  • ⚠️ Good search effectiveness - minor improvements possible")
        
        logger.info(f"\n{'='*70}")
        logger.info("🎉 Comprehensive quality testing completed!")
        logger.info(f"📅 Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'='*70}")


@click.command()
@click.option('--uri', default="bolt://localhost:7687", help='Neo4j URI')
@click.option('--user', default="neo4j", help='Neo4j username')
@click.option('--password', default="password", help='Neo4j password')
@click.option('--output', type=click.Path(), help='Save comprehensive results to JSON file')
@click.option('--skip-similarity', is_flag=True, help='Skip similarity tests')
@click.option('--skip-tags', is_flag=True, help='Skip tag tests')
def main(uri: str, user: str, password: str, output: str, skip_similarity: bool, skip_tags: bool):
    """Run comprehensive ChatMind quality tests."""
    
    tester = ComprehensiveQualityTester(uri, user, password)
    
    # Modify test suites based on skip flags
    if skip_similarity:
        tester.run_similarity_tests = lambda: None
    if skip_tags:
        tester.run_tag_tests = lambda: None
    
    results = tester.run_all_tests()
    
    if output and results:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"📄 Comprehensive results saved to: {output}")


if __name__ == "__main__":
    main() 