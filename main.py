from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os
from PIL import Image
import zipfile
 
app = FastAPI()
 
# Create necessary folders
IMAGE_UPLOAD_FOLDER = "uploads/images"
PDF_UPLOAD_FOLDER = "uploads/pdfs"
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_UPLOAD_FOLDER, exist_ok=True)
 
# Serve Static Files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
 
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif"}
ALLOWED_PDF_EXTENSION = "pdf"
 
 
def is_valid_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
 
 
def resize_image(file_path: str):
    with Image.open(file_path) as img:
        original_size = img.size
        img = img.resize((800, 800))  
        img.save(file_path, quality=85)  
        return original_size, img.size  
 
 
@app.get("/")
async def home():
    return FileResponse("static/index.html")
 
 
@app.post("/uploadfiles/")
async def upload_files(files: list[UploadFile] = File(...)):
    uploaded_files_info = []
 
    for file in files:
        if not is_valid_file(file.filename):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Only images are allowed.")
 
        file_path = os.path.join(IMAGE_UPLOAD_FOLDER, file.filename)
 
        try:
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
 
            original_size, new_size = resize_image(file_path)  
 
            uploaded_files_info.append({
                "filename": file.filename,
                "original_size": original_size,
                "new_size": new_size,
                "path": f"/uploads/images/{file.filename}",  
                "message": "File uploaded successfully"
            })
 
        except Exception as e:
            return {"error": f"Failed to upload {file.filename}: {str(e)}"}
 
    return {"uploaded_files": uploaded_files_info}
 
 
@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join(IMAGE_UPLOAD_FOLDER, filename)
 
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
 
    return FileResponse(file_path)
 
 
@app.get("/download_images_zip/")
async def download_images_zip():
    zip_filename = "images.zip"
    zip_filepath = os.path.join("uploads", zip_filename)
 
    with zipfile.ZipFile(zip_filepath, "w") as zipf:
        for root, _, files in os.walk(IMAGE_UPLOAD_FOLDER):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, arcname=file)
 
    return FileResponse(zip_filepath, filename=zip_filename, media_type="application/zip")
 
 
@app.post("/uploadpdf/")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(f".{ALLOWED_PDF_EXTENSION}"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")
 
    file_path = os.path.join(PDF_UPLOAD_FOLDER, file.filename)
 
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
 
        return {
            "filename": file.filename,
            "path": file_path,
            "message": "PDF uploaded successfully"
        }
 
    except Exception as e:
        return {"error": str(e)}
 