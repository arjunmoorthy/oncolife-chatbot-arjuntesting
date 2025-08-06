import modal

app = modal.App("test-app")

image = modal.Image.debian_slim().pip_install(["fastapi", "uvicorn"])

@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def test_imports():
    """Test what modules are available."""
    import os
    import sys
    
    # List current directory contents
    current_dir = os.listdir(".")
    print(f"Current directory contents: {current_dir}")
    
    # List Python path
    print(f"Python path: {sys.path}")
    
    # Try to import routers
    try:
        import routers
        print("✅ routers imported successfully")
        print(f"routers contents: {dir(routers)}")
    except ImportError as e:
        print(f"❌ routers import failed: {e}")
    
    return {
        "current_dir": current_dir,
        "python_path": sys.path,
        "routers_available": "routers" in current_dir
    } 