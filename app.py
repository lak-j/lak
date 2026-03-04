from pathlib import Path
import secrets
from flask import (
    Flask,
    abort,
    jsonify,
    render_template_string,
    request,
    send_from_directory,
)
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB max upload

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>React File Manager</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }
    .container { max-width: 1000px; margin: 2rem auto; padding: 0 1rem; }
    .card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(2, 8, 20, 0.08); padding: 1rem; }
    h1 { margin-top: 0; }
    .toolbar { display: flex; gap: .6rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem; }
    button { border: 0; background: #2563eb; color: white; padding: .55rem .8rem; border-radius: 8px; cursor: pointer; }
    button.secondary { background: #475569; }
    button.danger { background: #dc2626; }
    button:disabled { opacity: .6; cursor: not-allowed; }
    input[type='file'] { padding: .4rem; background: #f1f5f9; border-radius: 8px; }
    table { width: 100%; border-collapse: collapse; }
    th, td { text-align: left; border-bottom: 1px solid #e2e8f0; padding: .65rem .4rem; }
    code { white-space: pre-wrap; display: block; background: #0f172a; color: #e2e8f0; padding: 1rem; border-radius: 10px; max-height: 340px; overflow: auto; }
    .alert { padding: .6rem .8rem; border-radius: 8px; margin-bottom: .8rem; }
    .alert.ok { background: #dcfce7; color: #166534; }
    .alert.err { background: #fee2e2; color: #991b1b; }
    .actions { display: flex; gap: .4rem; flex-wrap: wrap; }
  </style>
</head>
<body>
  <div id="root"></div>

  <script type="text/babel">
    const { useEffect, useState } = React;

    function App() {
      const [files, setFiles] = useState([]);
      const [pickedFile, setPickedFile] = useState(null);
      const [selectedFile, setSelectedFile] = useState(null);
      const [fileContent, setFileContent] = useState('');
      const [message, setMessage] = useState(null);
      const [error, setError] = useState(null);
      const [loading, setLoading] = useState(false);

      const showMessage = (text) => {
        setMessage(text);
        setError(null);
      };

      const showError = (text) => {
        setError(text);
        setMessage(null);
      };

      const loadFiles = async () => {
        try {
          const res = await fetch('/api/files');
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Failed to load files');
          setFiles(data.files);
        } catch (err) {
          showError(err.message);
        }
      };

      useEffect(() => {
        loadFiles();
      }, []);

      const handleUpload = async () => {
        if (!pickedFile) {
          showError('Please choose a file first.');
          return;
        }

        const formData = new FormData();
        formData.append('file', pickedFile);

        setLoading(true);
        try {
          const res = await fetch('/api/upload', { method: 'POST', body: formData });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Upload failed');

          setPickedFile(null);
          document.getElementById('uploader').value = '';
          showMessage(`Uploaded: ${data.filename}`);
          await loadFiles();
        } catch (err) {
          showError(err.message);
        } finally {
          setLoading(false);
        }
      };

      const handleRead = async (filename) => {
        setLoading(true);
        try {
          const res = await fetch(`/api/read/${encodeURIComponent(filename)}`);
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Read failed');

          setSelectedFile(filename);
          setFileContent(data.content);
          showMessage(`Showing content for ${filename}`);
        } catch (err) {
          showError(err.message);
        } finally {
          setLoading(false);
        }
      };

      const handleDelete = async (filename) => {
        if (!confirm(`Delete ${filename}?`)) return;

        setLoading(true);
        try {
          const res = await fetch(`/api/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
          const data = await res.json();
          if (!res.ok) throw new Error(data.error || 'Delete failed');

          if (selectedFile === filename) {
            setSelectedFile(null);
            setFileContent('');
          }

          showMessage(`Deleted: ${filename}`);
          await loadFiles();
        } catch (err) {
          showError(err.message);
        } finally {
          setLoading(false);
        }
      };

      return (
        <div className="container">
          <div className="card">
            <h1>React File Manager</h1>
            <p>Upload, browse, read text files, download, and delete files.</p>

            {message && <div className="alert ok">{message}</div>}
            {error && <div className="alert err">{error}</div>}

            <div className="toolbar">
              <input
                id="uploader"
                type="file"
                onChange={(e) => setPickedFile(e.target.files?.[0] || null)}
              />
              <button onClick={handleUpload} disabled={loading}>Upload</button>
              <button className="secondary" onClick={loadFiles} disabled={loading}>Refresh</button>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Filename</th>
                  <th>Size (bytes)</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {files.length === 0 ? (
                  <tr><td colSpan="3">No files yet.</td></tr>
                ) : files.map((file) => (
                  <tr key={file.name}>
                    <td>{file.name}</td>
                    <td>{file.size}</td>
                    <td className="actions">
                      <button className="secondary" onClick={() => handleRead(file.name)} disabled={loading}>Read</button>
                      <a href={`/download/${encodeURIComponent(file.name)}`}><button className="secondary" disabled={loading}>Download</button></a>
                      <button className="danger" onClick={() => handleDelete(file.name)} disabled={loading}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {selectedFile && (
              <>
                <h2>Reading: {selectedFile}</h2>
                <code>{fileContent}</code>
              </>
            )}
          </div>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""


def safe_file_path(filename: str) -> Path:
    cleaned = secure_filename(filename)
    if not cleaned:
        abort(400, "Invalid filename")

    path = UPLOAD_FOLDER / cleaned
    if not path.exists() or not path.is_file():
        abort(404, "File not found")

    return path


def unique_filename(filename: str) -> str:
    candidate = secure_filename(filename)
    if not candidate:
        candidate = f"upload-{secrets.token_hex(4)}"

    path = UPLOAD_FOLDER / candidate
    if not path.exists():
        return candidate

    stem = Path(candidate).stem
    suffix = Path(candidate).suffix
    return f"{stem}-{secrets.token_hex(4)}{suffix}"


def list_files() -> list[dict]:
    items = []
    for file_path in sorted(UPLOAD_FOLDER.iterdir(), key=lambda p: p.name.lower()):
        if file_path.is_file():
            items.append({"name": file_path.name, "size": file_path.stat().st_size})
    return items


@app.get("/")
def index():
    return render_template_string(HTML)


@app.get("/api/files")
def api_files():
    return jsonify({"files": list_files()})


@app.post("/api/upload")
def api_upload():
    uploaded = request.files.get("file")
    if not uploaded or uploaded.filename == "":
        return jsonify({"error": "Please choose a file first."}), 400

    filename = unique_filename(uploaded.filename)
    destination = UPLOAD_FOLDER / filename

    try:
        uploaded.save(destination)
    except OSError:
        return jsonify({"error": "Upload failed: unable to write file to the server."}), 500

    return jsonify({"filename": filename}), 201


@app.get("/api/read/<path:filename>")
def api_read(filename: str):
    path = safe_file_path(filename)
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return jsonify({"error": "This file is not a readable UTF-8 text file."}), 400

    return jsonify({"filename": path.name, "content": content})


@app.delete("/api/files/<path:filename>")
def api_delete(filename: str):
    path = safe_file_path(filename)
    path.unlink(missing_ok=True)
    return jsonify({"deleted": path.name})


@app.get("/download/<path:filename>")
def download_file(filename: str):
    safe_file_path(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
