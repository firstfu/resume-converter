import os
import shutil
import tempfile
from pathlib import Path

import pytesseract
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

app = FastAPI(title="Resume Converter API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載靜態文件
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# 創建臨時文件夾
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def process_image_with_tesseract(image_path: str) -> str:
    """
    使用 Tesseract 處理圖像
    """
    try:
        return pytesseract.image_to_string(Image.open(image_path), lang="eng+chi_tra")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tesseract處理失敗: {str(e)}")


@app.post("/api/upload")
async def upload_file(file: UploadFile):
    """
    處理上傳的簡歷圖像文件
    """
    # 檢查文件類型
    allowed_types = {"image/jpeg", "image/png", "application/pdf"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件類型")

    # 保存上傳的文件
    temp_file = Path(tempfile.gettempdir()) / f"upload_{file.filename}"
    try:
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 處理圖像
        text_result = process_image_with_tesseract(str(temp_file))

        return JSONResponse({"status": "success", "text": text_result})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # 清理臨時文件
        if temp_file.exists():
            temp_file.unlink()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
