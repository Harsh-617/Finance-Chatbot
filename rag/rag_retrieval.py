import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RAGRetrieval:
    def __init__(self, rag_folder: str = "rag"):
        self.rag_folder = rag_folder
        self.db_path = os.path.join(rag_folder, "chroma_db")
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        try:
            self.collection = self.client.get_collection(name="financial_knowledge")
        except Exception as e:
            logger.warning(f"Could not load collection: {e}")
            self.collection = None
        
        # Initialize sentence transformer (same model as ingestion)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def is_available(self) -> bool:
        """Check if RAG system is available"""
        return self.collection is not None and self.collection.count() > 0

    def search_knowledge(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant information"""
        if not self.is_available():
            logger.warning("RAG system not available")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query])
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity_score': 1 - distance,  # Convert distance to similarity
                        'distance': distance
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during RAG search: {e}")
            return []

    def search_by_category(self, query: str, category: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search within a specific category"""
        if not self.is_available():
            return []
        
        try:
            query_embedding = self.model.encode([query])
            
            # Search with category filter
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k,
                where={"category": category},
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity_score': 1 - distance,
                        'distance': distance
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error during category search: {e}")
            return []

    def get_related_concepts(self, concept_title: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Get concepts related to a specific concept"""
        if not self.is_available():
            return []
        
        try:
            # Search using the concept title
            query_embedding = self.model.encode([concept_title])
            
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k + 5,  # Get more to filter out the original concept
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    # Skip if it's the same concept
                    if metadata.get('title', '').lower() == concept_title.lower():
                        continue
                        
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity_score': 1 - distance,
                        'distance': distance
                    })
                    
                    if len(formatted_results) >= top_k:
                        break
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting related concepts: {e}")
            return []

    def search_examples(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search specifically for examples"""
        if not self.is_available():
            return []
        
        try:
            query_embedding = self.model.encode([query])
            
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=top_k,
                where={"chunk_type": "example"},
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for doc, metadata, distance in zip(documents, metadatas, distances):
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'similarity_score': 1 - distance,
                        'distance': distance
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching examples: {e}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        if not self.is_available():
            return {"status": "unavailable", "count": 0}
        
        try:
            count = self.collection.count()
            
            # Get all metadatas to analyze
            all_results = self.collection.get(include=['metadatas'])
            
            categories = set()
            chunk_types = set()
            sources = set()
            
            if all_results['metadatas']:
                for metadata in all_results['metadatas']:
                    categories.add(metadata.get('category', 'Unknown'))
                    chunk_types.add(metadata.get('chunk_type', 'Unknown'))
                    sources.add(metadata.get('source', 'Unknown'))
            
            return {
                "status": "available",
                "total_documents": count,
                "categories": list(categories),
                "chunk_types": list(chunk_types),
                "sources": list(sources),
                "db_path": self.db_path
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"status": "error", "error": str(e)}

    def format_search_results_for_llm(self, results: List[Dict[str, Any]], max_results: int = 3) -> str:
        """Format search results for LLM context"""
        if not results:
            return ""
        
        formatted_context = "Relevant Financial Knowledge:\n\n"
        
        for i, result in enumerate(results[:max_results], 1):
            content = result['content']
            metadata = result['metadata']
            similarity = result['similarity_score']
            
            formatted_context += f"[Knowledge {i}] (Relevance: {similarity:.2f})\n"
            formatted_context += f"Title: {metadata.get('title', 'N/A')}\n"
            formatted_context += f"Category: {metadata.get('category', 'N/A')}\n"
            formatted_context += f"Type: {metadata.get('chunk_type', 'N/A')}\n"
            formatted_context += f"Content:\n{content}\n"
            formatted_context += "-" * 50 + "\n\n"
        
        return formatted_context

    def smart_search(self, query: str, similarity_threshold: float = 0.3) -> Dict[str, Any]:
        """Intelligent search that tries different strategies"""
        if not self.is_available():
            return {
                "found_relevant": False,
                "context": "",
                "method": "unavailable",
                "results": []
            }
        
        # First try general search
        general_results = self.search_knowledge(query, top_k=5)
        
        # Filter by similarity threshold
        relevant_results = [r for r in general_results if r['similarity_score'] >= similarity_threshold]
        
        if relevant_results:
            return {
                "found_relevant": True,
                "context": self.format_search_results_for_llm(relevant_results),
                "method": "general_search",
                "results": relevant_results,
                "total_checked": len(general_results)
            }
        
        # If no relevant results, try searching for examples
        example_results = self.search_examples(query, top_k=3)
        example_relevant = [r for r in example_results if r['similarity_score'] >= similarity_threshold]
        
        if example_relevant:
            return {
                "found_relevant": True,
                "context": self.format_search_results_for_llm(example_relevant),
                "method": "example_search",
                "results": example_relevant,
                "total_checked": len(example_results)
            }
        
        # Return best results even if below threshold, but mark as low relevance
        best_results = general_results[:2] if general_results else []
        return {
            "found_relevant": False,
            "context": self.format_search_results_for_llm(best_results) if best_results else "",
            "method": "low_relevance",
            "results": best_results,
            "total_checked": len(general_results),
            "max_similarity": max([r['similarity_score'] for r in general_results]) if general_results else 0
        }


# Global instance for easy access
_rag_retrieval = None

def get_rag_retrieval() -> RAGRetrieval:
    """Get global RAG retrieval instance"""
    global _rag_retrieval
    if _rag_retrieval is None:
        _rag_retrieval = RAGRetrieval()
    return _rag_retrieval

def search_financial_knowledge(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Convenience function for knowledge search"""
    rag = get_rag_retrieval()
    return rag.search_knowledge(query, top_k)

def get_knowledge_context(query: str) -> str:
    """Get formatted knowledge context for LLM"""
    rag = get_rag_retrieval()
    search_result = rag.smart_search(query)
    return search_result.get("context", "")