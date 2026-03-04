# React + Flask File Manager Web App

This project now includes a **React user interface** backed by a Flask API.

## Features
- Upload files
- List/manage uploaded files
- Read UTF-8 text file contents
- Download files
- Delete files

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: `http://localhost:5000`

## API Endpoints
- `GET /api/files` - list uploaded files
- `POST /api/upload` - upload file (`multipart/form-data` with `file`)
- `GET /api/read/<filename>` - read UTF-8 text content
- `DELETE /api/files/<filename>` - delete file
- `GET /download/<filename>` - download file

Uploaded files are stored in the `uploads/` folder.
