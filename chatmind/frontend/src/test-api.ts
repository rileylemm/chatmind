// Simple API test to verify our backend connection
import { getHealthStatus, simpleSearch, semanticSearch, getSearchStats } from './services/api';

async function testAPI() {
  console.log('🧪 Testing API connection...');
  
  try {
    // Test health endpoint
    console.log('Testing health endpoint...');
    const health = await getHealthStatus();
    console.log('✅ Health:', health);
    
    // Test search stats
    console.log('Testing search stats...');
    const stats = await getSearchStats();
    console.log('✅ Stats:', stats);
    
    // Test simple search
    console.log('Testing simple search...');
    const simpleResults = await simpleSearch({ query: 'test', limit: 3 });
    console.log('✅ Simple search results:', simpleResults.length);
    
    // Test semantic search
    console.log('Testing semantic search...');
    const semanticResults = await semanticSearch({ query: 'health', limit: 3 });
    console.log('✅ Semantic search results:', semanticResults.length);
    
    console.log('🎉 All API tests passed!');
    
  } catch (error) {
    console.error('❌ API test failed:', error);
  }
}

// Run test if this file is executed directly
if (typeof window !== 'undefined') {
  // Browser environment
  testAPI();
} else {
  // Node environment
  testAPI();
}

export { testAPI }; 