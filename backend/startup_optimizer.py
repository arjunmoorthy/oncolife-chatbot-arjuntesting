"""
Startup Optimizer for Cloud Deployment

This pre-loads all models and data before the FastAPI server starts.
"""

import os
import time
import threading
from optimized_context import OptimizedContextLoader

def preload_everything():
    """Pre-load all models and data at startup."""
    print("🚀 Pre-loading models and data for cloud deployment...")
    start_time = time.time()
    
    try:
        # Get the model_inputs directory
        model_inputs_path = os.path.join(os.path.dirname(__file__), 'model_inputs')
        
        # Initialize the optimized context loader
        context_loader = OptimizedContextLoader(model_inputs_path)
        
        # Test the context loading
        test_context = context_loader.load_context(symptoms=['fever', 'nausea'])
        
        print(f"✅ Pre-loading completed in {time.time() - start_time:.2f}s")
        print(f"📊 Test context length: {len(test_context)} characters")
        
        return context_loader
        
    except Exception as e:
        print(f"❌ Error during pre-loading: {e}")
        return None

# Global context loader instance
_global_context_loader = None

def get_context_loader():
    """Get the global context loader instance."""
    global _global_context_loader
    if _global_context_loader is None:
        _global_context_loader = preload_everything()
    return _global_context_loader

if __name__ == "__main__":
    # Test the pre-loading
    loader = preload_everything()
    if loader:
        print("🎉 Startup optimization successful!")
    else:
        print("⚠️ Startup optimization failed, will use fallback mode") 