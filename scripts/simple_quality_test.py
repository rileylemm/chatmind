#!/usr/bin/env python3
"""
Simple ChatMind Quality Test

A straightforward test to evaluate the quality of your ChatMind knowledge graph.
"""

import json
import logging
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


def test_knowledge_graph_quality():
    """Test the quality of the ChatMind knowledge graph."""
    
    if not NEO4J_AVAILABLE:
        logger.error("Neo4j driver not available")
        return None
    
    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "chatmind123"))
        
        with driver.session() as session:
            logger.info("🚀 Starting ChatMind Quality Test")
            logger.info(f"📅 Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            results = {}
            
            # Test 1: Data Completeness
            logger.info("\n" + "="*50)
            logger.info("📊 TEST 1: DATA COMPLETENESS")
            logger.info("="*50)
            
            # Count all node types
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
                logger.info(f"  {node_type}: {count:,}")
            
            # Count relationships
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
                logger.info(f"  {rel_type}: {count:,}")
            
            results['data_completeness'] = {
                'node_counts': node_counts,
                'relationship_counts': rel_counts,
                'total_nodes': sum(node_counts.values()),
                'total_relationships': sum(rel_counts.values())
            }
            
            # Test 2: Similarity Quality
            logger.info("\n" + "="*50)
            logger.info("🔗 TEST 2: SIMILARITY QUALITY")
            logger.info("="*50)
            
            # Get similarity distribution
            sim_query = """
            MATCH (c1:Chat)-[r:SIMILAR_TO]->(c2:Chat)
            RETURN r.similarity as similarity
            ORDER BY r.similarity DESC
            """
            
            similarities = []
            for record in session.run(sim_query):
                similarities.append(record['similarity'])
            
            if similarities:
                import numpy as np
                sim_stats = {
                    'count': len(similarities),
                    'mean': np.mean(similarities),
                    'median': np.median(similarities),
                    'std': np.std(similarities),
                    'high_similarities': len([s for s in similarities if s > 0.7]),
                    'medium_similarities': len([s for s in similarities if 0.3 <= s <= 0.7]),
                    'low_similarities': len([s for s in similarities if s < 0.3])
                }
                
                logger.info(f"  Total similarities: {sim_stats['count']:,}")
                logger.info(f"  Mean similarity: {sim_stats['mean']:.3f}")
                logger.info(f"  High similarities (>0.7): {sim_stats['high_similarities']:,}")
                logger.info(f"  Medium similarities (0.3-0.7): {sim_stats['medium_similarities']:,}")
                logger.info(f"  Low similarities (<0.3): {sim_stats['low_similarities']:,}")
                
                results['similarity_quality'] = sim_stats
            else:
                logger.warning("  No similarity relationships found")
                results['similarity_quality'] = {}
            
            # Test 3: Tag Effectiveness
            logger.info("\n" + "="*50)
            logger.info("🏷️ TEST 3: TAG EFFECTIVENESS")
            logger.info("="*50)
            
            # Tag coverage
            total_chunks = node_counts.get('Chunk', 0)
            tagged_chunks_query = """
            MATCH (c:Chunk)-[:TAGGED_WITH]->(t:Tag)
            RETURN count(DISTINCT c) as count
            """
            tagged_chunks = session.run(tagged_chunks_query).single()['count']
            
            # Tag usage distribution
            tag_usage_query = """
            MATCH (t:Tag)<-[:TAGGED_WITH]-(c:Chunk)
            RETURN t.name as tag_name, count(c) as usage_count
            ORDER BY usage_count DESC
            LIMIT 20
            """
            
            tag_usage = []
            for record in session.run(tag_usage_query):
                tag_usage.append({
                    'tag': record['tag_name'],
                    'usage_count': record['usage_count']
                })
            
            tag_stats = {
                'total_chunks': total_chunks,
                'tagged_chunks': tagged_chunks,
                'coverage_percentage': (tagged_chunks / total_chunks * 100) if total_chunks > 0 else 0,
                'top_tags': tag_usage[:10]
            }
            
            logger.info(f"  Total chunks: {total_chunks:,}")
            logger.info(f"  Tagged chunks: {tagged_chunks:,}")
            logger.info(f"  Coverage: {tag_stats['coverage_percentage']:.1f}%")
            logger.info("  Top 10 tags:")
            for i, tag in enumerate(tag_stats['top_tags']):
                logger.info(f"    {i+1}. {tag['tag']}: {tag['usage_count']:,}")
            
            results['tag_effectiveness'] = tag_stats
            
            # Test 4: Search Effectiveness
            logger.info("\n" + "="*50)
            logger.info("🔍 TEST 4: SEARCH EFFECTIVENESS")
            logger.info("="*50)
            
            # Test tag search
            if tag_stats['top_tags']:
                test_tag = tag_stats['top_tags'][0]['tag']
                tag_search_query = """
                MATCH (c:Chunk)-[:TAGGED_WITH]->(t:Tag {name: $tag_name})
                RETURN count(c) as result_count
                """
                tag_search_result = session.run(tag_search_query, tag_name=test_tag).single()['result_count']
                logger.info(f"  Tag search for '{test_tag}': {tag_search_result} results")
            
            # Test similarity search
            sample_chat_query = """
            MATCH (c:Chat)
            WHERE c.title IS NOT NULL
            RETURN c.title as title
            LIMIT 1
            """
            sample_result = session.run(sample_chat_query).single()
            if sample_result:
                chat_title = sample_result['title']
                similar_query = """
                MATCH (c1:Chat {title: $title})-[:SIMILAR_TO]->(c2:Chat)
                RETURN count(c2) as similar_count
                """
                similar_count = session.run(similar_query, title=chat_title).single()['similar_count']
                logger.info(f"  Similarity search for '{chat_title[:50]}...': {similar_count} similar chats")
            
            # Test topic search
            topic_query = """
            MATCH (t:Topic)<-[:SUMMARIZES]-(c:Chunk)
            WITH t, count(c) as chunk_count
            WHERE chunk_count >= 5
            RETURN count(t) as topic_count
            """
            topic_count = session.run(topic_query).single()['topic_count']
            logger.info(f"  Well-sized topics (5+ chunks): {topic_count}")
            
            search_effectiveness = {
                'tag_search_working': tag_stats['top_tags'] and tag_stats['top_tags'][0]['usage_count'] > 0,
                'similarity_search_working': similarities and len(similarities) > 0,
                'topic_search_working': topic_count > 0
            }
            
            results['search_effectiveness'] = search_effectiveness
            
            # Generate Quality Score
            logger.info("\n" + "="*50)
            logger.info("🎯 QUALITY SCORE CALCULATION")
            logger.info("="*50)
            
            quality_scores = {}
            
            # Similarity quality score
            if 'similarity_quality' in results and results['similarity_quality']:
                sim_dist = results['similarity_quality']
                high_quality_sim = sim_dist.get('high_similarities', 0)
                total_sim = sim_dist.get('count', 0)
                quality_scores['similarity'] = high_quality_sim / total_sim if total_sim > 0 else 0
                logger.info(f"  Similarity quality: {quality_scores['similarity']:.1%}")
            
            # Tag coverage score
            tag_cov = results.get('tag_effectiveness', {}).get('coverage_percentage', 0)
            quality_scores['tag_coverage'] = tag_cov / 100
            logger.info(f"  Tag coverage: {quality_scores['tag_coverage']:.1%}")
            
            # Search effectiveness score
            search_working = sum(1 for v in results.get('search_effectiveness', {}).values() if v)
            total_searches = len(results.get('search_effectiveness', {}))
            quality_scores['search_effectiveness'] = search_working / total_searches if total_searches > 0 else 0
            logger.info(f"  Search effectiveness: {quality_scores['search_effectiveness']:.1%}")
            
            # Overall quality score
            if quality_scores:
                overall_score = sum(quality_scores.values()) / len(quality_scores)
                quality_scores['overall'] = overall_score
                logger.info(f"  Overall quality score: {overall_score:.1%}")
            
            results['quality_scores'] = quality_scores
            
            # Generate recommendations
            logger.info("\n" + "="*50)
            logger.info("💡 RECOMMENDATIONS")
            logger.info("="*50)
            
            if 'similarity' in quality_scores:
                sim_score = quality_scores['similarity']
                if sim_score < 0.2:
                    logger.info("  ⚠️ Low similarity quality - consider improving similarity algorithm")
                elif sim_score > 0.5:
                    logger.info("  ✅ Excellent similarity quality")
                else:
                    logger.info("  ⚠️ Moderate similarity quality - room for improvement")
            
            if 'tag_coverage' in quality_scores:
                tag_score = quality_scores['tag_coverage']
                if tag_score < 0.8:
                    logger.info("  ⚠️ Low tag coverage - consider improving tagging")
                elif tag_score > 0.95:
                    logger.info("  ✅ Excellent tag coverage")
                else:
                    logger.info("  ⚠️ Good tag coverage - minor improvements possible")
            
            if 'search_effectiveness' in quality_scores:
                search_score = quality_scores['search_effectiveness']
                if search_score < 0.7:
                    logger.info("  ⚠️ Low search effectiveness - consider improving search algorithms")
                elif search_score > 0.9:
                    logger.info("  ✅ Excellent search effectiveness")
                else:
                    logger.info("  ⚠️ Good search effectiveness - minor improvements possible")
            
            logger.info("\n" + "="*50)
            logger.info("🎉 Quality testing completed!")
            logger.info(f"📅 Test run completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*50)
            
            return results
            
    except Exception as e:
        logger.error(f"❌ Quality test failed: {e}")
        return None


if __name__ == "__main__":
    results = test_knowledge_graph_quality()
    
    if results:
        # Save results to file
        with open('quality_test_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info("📄 Results saved to: quality_test_results.json")
    else:
        logger.error("❌ No results to save") 