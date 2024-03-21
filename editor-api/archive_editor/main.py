import os
import json
from tempfile import TemporaryDirectory, mkdtemp
import shutil  # For copying files
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from archive_editor.api import ArchiveEditorApi
from archive_editor.aio import get_archive_file_response
from archive_editor.data_model import (
    SuccessfulSimulationEditConfirmation, 
    UnsuccessfulSimulationEditConfirmation,
    SimulationEditResult,
    SimulationEditRequest,
    ArchiveDownloadRequest,
    ArchiveDownloadResponse
)


app = FastAPI(title="editor-api", version="1.0.0")


# TODO: Change this to Settings/S3
EDITED_FILES_STORAGE_DIR = mkdtemp()


@app.get("/")
async def root():
    return {"message": "Hello world, this is editor-api!"}


@app.post(
    "/edit_simulation/",
    response_model=SuccessfulSimulationEditConfirmation,
    name="Edit Archive Simulation",
    operation_id="edit-simulation")
async def edit_simulation(
        archive: UploadFile = File(...),
        edit_request_str: str = Form(...),
        new_omex_filename: str = Form(...)) -> SuccessfulSimulationEditConfirmation:
    try:
        edit_request = json.loads(edit_request_str)
        edit_request_model = SimulationEditRequest(**edit_request)

        with TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, archive.filename)
            with open(file_path, 'wb') as file_object:
                file_object.write(archive.file.read())

            result: SimulationEditResult = ArchiveEditorApi.run(omex_fp=file_path, **edit_request_model.dict())

            # move the edited dir to the temp "database"
            edited_file_path = os.path.join(EDITED_FILES_STORAGE_DIR, f"{new_omex_filename}.omex")
            shutil.move(file_path, edited_file_path)

        return SuccessfulSimulationEditConfirmation(download_link=f"/download/{edited_file_path}").model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/download/{file_identifier}",
    # response_model=ArchiveDownloadResponse,
    name="Download COMBINE archive",
    operation_id="download-archive")
async def download_edited_file(file_identifier: str) -> FileResponse: # ArchiveDownloadResponse:
    """Serve the edited COMBINE archive for download."""
    try:
        file_id = json.loads(file_identifier)
        download_request = ArchiveDownloadRequest(**file_id)
        response = await get_archive_file_response(file_identifier, EDITED_FILES_STORAGE_DIR)
        return response 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
