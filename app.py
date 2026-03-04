from pathlib import Path
from flask import Flask, request, redirect, url_for, send_from_directory, abort, flash, render_template_string
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = Path("uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB max upload
app.secret_key = "change-this-secret-key"

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>File Manager</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; max-width: 900px; }
    h1 { margin-bottom: 1rem; }
    .flash { padding: .6rem; margin: .5rem 0; border-radius: 8px; background: #f1f5f9; }
    table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
    th, td { border-bottom: 1px solid #ddd; padding: .6rem; text-align: left; }
    form.inline { display: inline; }
    code.preview { display: block; white-space: pre-wrap; background: #f8fafc; border: 1px solid #ddd; padding: 1rem; border-radius: 8px; }
    .actions a, .actions button { margin-right: .4rem; }
  </style>
</head>
<body>
  <h1>Python File Upload + Manager</h1>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for m in messages %}
        <div class="flash">{{ m }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <form action="{{ url_for('upload_file') }}" method="post" enctype="multipart/form-data">
    <input type="file" name="file" required>
    <button type="submit">Upload</button>
  </form>

  <table>
    <thead>
      <tr><th>Filename</th><th>Size (bytes)</th><th>Actions</th></tr>
    </thead>
    <tbody>
      {% for file in files %}
      <tr>
        <td>{{ file.name }}</td>
        <td>{{ file.stat().st_size }}</td>
        <td class="actions">
          <a href="{{ url_for('download_file', filename=file.name) }}">Download</a>
          <a href="{{ url_for('read_file', filename=file.name) }}">Read</a>
          <form class="inline" action="{{ url_for('delete_file', filename=file.name) }}" method="post">
            <button type="submit">Delete</button>
          </form>
        </td>
      </tr>
      {% else %}
      <tr><td colspan="3">No files yet.</td></tr>
      {% endfor %}
    </tbody>
  </table>

  {% if selected %}
    <h2>Reading: {{ selected }}</h2>
    {% if content is not none %}
      <code class="preview">{{ content }}</code>
    {% else %}
      <p>This file is not a readable UTF-8 text file.</p>
    {% endif %}
  {% endif %}
</body>
</html>
"""


def safe_file_path(filename: str) -> Path:
    cleaned = secure_filename(filename)
    if not cleaned:
        abort(400, "Invalid filename")
    path = UPLOAD_FOLDER / cleaned
    if not path.exists():
        abort(404, "File not found")
    return path


@app.get("/")
def index():
    files = sorted(UPLOAD_FOLDER.iterdir(), key=lambda p: p.name.lower())
    return render_template_string(HTML, files=files, selected=None, content=None)


@app.post("/upload")
def upload_file():
    uploaded = request.files.get("file")
    if not uploaded or uploaded.filename == "":
        flash("Please choose a file first.")
        return redirect(url_for("index"))

    filename = secure_filename(uploaded.filename)
    if not filename:
        flash("Invalid filename.")
        return redirect(url_for("index"))

    destination = UPLOAD_FOLDER / filename
    uploaded.save(destination)
    flash(f"Uploaded: {filename}")
    return redirect(url_for("index"))


@app.get("/download/<path:filename>")
def download_file(filename: str):
    safe_file_path(filename)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@app.get("/read/<path:filename>")
def read_file(filename: str):
    path = safe_file_path(filename)
    files = sorted(UPLOAD_FOLDER.iterdir(), key=lambda p: p.name.lower())

    content = None
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pass

    return render_template_string(HTML, files=files, selected=path.name, content=content)


@app.post("/delete/<path:filename>")
def delete_file(filename: str):
    path = safe_file_path(filename)
    path.unlink(missing_ok=True)
    flash(f"Deleted: {path.name}")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
