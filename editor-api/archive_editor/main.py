from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
from pydantic import BaseModel, Field
import os
from tempfile import NamedTemporaryFile
import json  # Import json for parsing JSON strings
from archive_editor.editor import ArchiveEditorApi  # Ensure your API module is importable

app = FastAPI()

# CORS setup for a wide range of origins.
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationEditRequest(BaseModel):
    # kisao_id: Optional[str] = Field(None, description="KiSAO id of the algorithm for simulating the model.")
    changes_to_apply: dict = Field(..., description="Changes to apply, referenced by the name of the value you want to change.")


'''@app.post("/edit_simulation/")
async def edit_simulation(
        archive: UploadFile = File(...),
        edit_request_str: str = Form(...)  # Receive JSON data as a string
    ):
    try:
        # Parse the JSON string into a Python dictionary
        edit_request = json.loads(edit_request_str)

        # Validate the edit_request with Pydantic model (optional, for validation)
        edit_request_model = SimulationEditRequest(**edit_request)

        temp_dir = NamedTemporaryFile(delete=False).name
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, archive.filename)
        with open(file_path, 'wb') as file_object:
            file_object.write(archive.file.read())
        # Assuming ArchiveEditorApi is adapted to handle file paths and changes directly.
        # Use edit_request_model.dict() if you want to pass the validated data
        ArchiveEditorApi.run(omex_fp=file_path, **edit_request_model.dict(), kisao_id=edit_request_model.kisao_id)
        return {"message": "Simulation edited successfully.", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''

from tempfile import TemporaryDirectory

@app.post("/edit_simulation/")
async def edit_simulation(
        archive: UploadFile = File(...),
        edit_request_str: str = Form(...)  # Receive JSON data as a string
    ):
    try:
        # Parse the JSON string into a Python dictionary
        edit_request = json.loads(edit_request_str)

        # Validate the edit_request with Pydantic model (optional, for validation)
        edit_request_model = SimulationEditRequest(**edit_request)

        # Use a temporary directory
        with TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, archive.filename)
            with open(file_path, 'wb') as file_object:
                file_object.write(archive.file.read())

            # Assuming ArchiveEditorApi is adapted to handle file paths and changes directly.
            # Use edit_request_model.dict() if you want to pass the validated data
            ArchiveEditorApi.run(omex_fp=file_path, **edit_request_model.dict())

        # Note: The temp directory and files within are automatically deleted here

        return {"message": "Simulation edited successfully.", "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
