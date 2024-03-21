import os 
from fastapi.responses import FileResponse
from archive_editor.data_model import ArchiveDownloadResponse


async def get_archive_file_response(file_identifier: str, file_storage_root: str) -> FileResponse: # ArchiveDownloadResponse:
    file_path = os.path.join(file_storage_root, f"{file_identifier}.omex")
    if os.path.exists(file_path):
        response = FileResponse(
            path=file_path, 
            filename=f"{file_identifier}.omex", 
            media_type='application/octet-stream')
        
        '''response_config = response.__dict__
        for key in response_config.keys():
            if key not in ['path', 'filename', 'media_type']:
                response_config.pop(key)
                
        return ArchiveDownloadResponse(**response_config)'''
        return response 
