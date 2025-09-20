import json
import os
import hashlib
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGIngestion:
    def __init__(self, rag_folder: str = "rag"):
        self.rag_folder = rag_folder
        self.db_path = os.path.join(rag_folder, "chroma_db")
        self.metadata_path = os.path.join(rag_folder, "ingestion_metadata.json")
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="financial_knowledge",
            metadata={"description": "Financial concepts, strategies, and risk management"}
        )
        
        # Initialize sentence transformer
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # JSON files to process
        self.json_files = [
            "technical_strategies.json",
            "investment_styles.json", 
            "risk_management.json"
        ]

    def get_file_hash(self, filepath: str) -> str:
        """Calculate MD5 hash of a file"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except FileNotFoundError:
            return ""

    def load_metadata(self) -> Dict[str, str]:
        """Load ingestion metadata (file hashes)"""
        try:
            with open(self.metadata_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_metadata(self, metadata: Dict[str, str]):
        """Save ingestion metadata"""
        os.makedirs(self.rag_folder, exist_ok=True)
        with open(self.metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

    def check_if_ingestion_needed(self) -> bool:
        """Check if any files have changed since last ingestion"""
        current_metadata = self.load_metadata()
        
        for json_file in self.json_files:
            filepath = os.path.join(self.rag_folder, json_file)
            if not os.path.exists(filepath):
                continue
                
            current_hash = self.get_file_hash(filepath)
            stored_hash = current_metadata.get(json_file, "")
            
            if current_hash != stored_hash:
                logger.info(f"File {json_file} has changed or is new. Ingestion needed.")
                return True
        
        # Check if collection is empty
        try:
            count = self.collection.count()
            if count == 0:
                logger.info("Collection is empty. Ingestion needed.")
                return True
        except Exception as e:
            logger.info(f"Error checking collection count: {e}. Performing ingestion.")
            return True
            
        logger.info("No changes detected. Skipping ingestion.")
        return False

    def create_document_chunks(self, concept: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create multiple document chunks from a single concept"""
        chunks = []
        
        # Main concept chunk
        main_content = f"""
        Title: {concept['title']}
        Category: {concept['category']}
        
        Concept: {concept['concept']}
        
        Calculation: {concept.get('calculation', 'N/A')}
        
        Parameters: {concept.get('parameters', 'N/A')}
        """
        
        chunks.append({
            'content': main_content.strip(),
            'metadata': {
                'title': concept['title'],
                'category': concept['category'],
                'chunk_type': 'main_concept',
                'source': concept.get('source_file', 'unknown')
            }
        })
        
        # Use cases chunk
        if concept.get('use_cases'):
            use_cases_content = f"""
            {concept['title']} - Use Cases:
            
            {chr(10).join([f"• {use_case}" for use_case in concept['use_cases']])}
            """
            
            chunks.append({
                'content': use_cases_content.strip(),
                'metadata': {
                    'title': concept['title'],
                    'category': concept['category'],
                    'chunk_type': 'use_cases',
                    'source': concept.get('source_file', 'unknown')
                }
            })
        
        # Advantages and disadvantages chunk
        advantages = concept.get('advantages', [])
        disadvantages = concept.get('disadvantages', [])
        
        if advantages or disadvantages:
            pros_cons_content = f"{concept['title']} - Pros and Cons:\n\n"
            
            if advantages:
                pros_cons_content += f"Advantages:\n{chr(10).join([f'• {adv}' for adv in advantages])}\n\n"
            
            if disadvantages:
                pros_cons_content += f"Disadvantages:\n{chr(10).join([f'• {dis}' for dis in disadvantages])}"
            
            chunks.append({
                'content': pros_cons_content.strip(),
                'metadata': {
                    'title': concept['title'],
                    'category': concept['category'],
                    'chunk_type': 'pros_cons',
                    'source': concept.get('source_file', 'unknown')
                }
            })
        
        # Example chunk
        if concept.get('example'):
            example_content = f"""
            {concept['title']} - Example:
            
            {concept['example']}
            """
            
            chunks.append({
                'content': example_content.strip(),
                'metadata': {
                    'title': concept['title'],
                    'category': concept['category'],
                    'chunk_type': 'example',
                    'source': concept.get('source_file', 'unknown')
                }
            })
        
        # Variations chunk
        if concept.get('variations'):
            variations_content = f"""
            {concept['title']} - Variations:
            
            {chr(10).join([f"• {var}" for var in concept['variations']])}
            """
            
            chunks.append({
                'content': variations_content.strip(),
                'metadata': {
                    'title': concept['title'],
                    'category': concept['category'],
                    'chunk_type': 'variations',
                    'source': concept.get('source_file', 'unknown')
                }
            })
        
        return chunks

    def ingest_json_file(self, json_file: str) -> List[Dict[str, Any]]:
        """Load and process a JSON file"""
        filepath = os.path.join(self.rag_folder, json_file)
        
        if not os.path.exists(filepath):
            logger.warning(f"File {filepath} not found. Skipping.")
            return []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_chunks = []
            for concept in data:
                concept['source_file'] = json_file
                chunks = self.create_document_chunks(concept)
                all_chunks.extend(chunks)
            
            logger.info(f"Processed {len(data)} concepts from {json_file} into {len(all_chunks)} chunks")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Error processing {json_file}: {e}")
            return []

    def clear_collection(self):
        """Clear existing collection"""
        try:
            self.client.delete_collection(name="financial_knowledge")
            self.collection = self.client.create_collection(
                name="financial_knowledge",
                metadata={"description": "Financial concepts, strategies, and risk management"}
            )
            logger.info("Cleared existing collection")
        except Exception as e:
            logger.info(f"Collection didn't exist or couldn't be cleared: {e}")

    def perform_ingestion(self):
        """Perform the complete ingestion process"""
        logger.info("Starting RAG ingestion process...")
        
        # Clear existing data
        self.clear_collection()
        
        # Process all files
        all_documents = []
        for json_file in self.json_files:
            chunks = self.ingest_json_file(json_file)
            all_documents.extend(chunks)
        
        if not all_documents:
            logger.warning("No documents to ingest!")
            return
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(all_documents)} document chunks...")
        contents = [doc['content'] for doc in all_documents]
        embeddings = self.model.encode(contents, show_progress_bar=True)
        
        # Prepare data for ChromaDB
        ids = [f"doc_{i}" for i in range(len(all_documents))]
        metadatas = [doc['metadata'] for doc in all_documents]
        documents = contents
        
        # Add to ChromaDB
        logger.info("Adding documents to ChromaDB...")
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Update metadata
        current_metadata = {}
        for json_file in self.json_files:
            filepath = os.path.join(self.rag_folder, json_file)
            if os.path.exists(filepath):
                current_metadata[json_file] = self.get_file_hash(filepath)
        
        self.save_metadata(current_metadata)
        
        logger.info(f"Successfully ingested {len(all_documents)} documents!")
        logger.info(f"Collection now contains {self.collection.count()} documents")

    def run_ingestion_if_needed(self):
        """Main entry point - only run ingestion if needed"""
        if self.check_if_ingestion_needed():
            self.perform_ingestion()
        else:
            logger.info("Ingestion not needed - all files are up to date")


def main():
    """Main function to run ingestion"""
    ingestion = RAGIngestion()
    ingestion.run_ingestion_if_needed()


if __name__ == "__main__":
    main()