from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
from pydantic import BaseModel, Field
import json
from tempfile import TemporaryDirectory
import shutil  # For copying files

app = FastAPI()

# Example global storage for demonstration; consider a more secure approach for production
edited_files_storage = "/path/to/edited/files/storage"

class SimulationEditRequest(BaseModel):
    changes_to_apply: dict = Field(..., description="Changes to apply, referenced by the name of the value you want to change.")

@app.post("/edit_simulation/")
async def edit_simulation(
        archive: UploadFile = File(...),
        edit_request_str: str = Form(...)
    ):
    file_identifier = "unique_file_identifier"  # Generate or determine a unique identifier for each file
    try:
        edit_request = json.loads(edit_request_str)
        edit_request_model = SimulationEditRequest(**edit_request)

        with TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, archive.filename)
            with open(file_path, 'wb') as file_object:
                file_object.write(archive.file.read())

            ArchiveEditorApi.run(omex_fp=file_path, **edit_request_model.dict())

            # Instead of deleting, move the edited file to the edited_files_storage
            edited_file_path = os.path.join(edited_files_storage, f"{file_identifier}.omex")
            shutil.move(file_path, edited_file_path)

        return {"message": "Simulation edited successfully.", "download_link": f"/download/{file_identifier}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{file_identifier}")
async def download_edited_file(file_identifier: str):
    """Serve the edited COMBINE archive for download."""
    file_path = os.path.join(edited_files_storage, f"{file_identifier}.omex")
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=f"{file_identifier}.omex", media_type='application/octet-stream')
    else:
        raise HTTPException(status_code=404, detail="File not found.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
