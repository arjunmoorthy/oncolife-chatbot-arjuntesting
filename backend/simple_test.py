import modal

app = modal.App("simple-test")

image = modal.Image.debian_slim().pip_install(["fastapi"])

@app.function(image=image)
@modal.fastapi_endpoint(method="GET")
def hello():
    return {"message": "Hello from Modal!"} 