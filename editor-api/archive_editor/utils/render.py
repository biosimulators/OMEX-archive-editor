from flask import Flask, request, render_template_string, redirect, url_for
from archive_editor.editor import ArchiveEditorApi


app = Flask(__name__)

HTML_FORM = """
<html>
<body>
   <form enctype="multipart/form-data" action="/upload" method="post">
   <p>File: <input type="file" name="filename" /></p>
   <p><input type="submit" value="Upload" /></p>
   </form>
</body>
</html>
"""


@app.route('/')
def form():
    return render_template_string(HTML_FORM)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'filename' not in request.files:
        return redirect(request.url)
    file = request.files['filename']
    if file.filename == '':
        return 'No selected file'
    if file:
        filename = secure_filename(file.filename)
        fp = os.path.join('/tmp', filename)
        file.save(fp)
        try:
            result = ArchiveEditorApi.run(omex_fp=fp, colab=False, kisao_id=None)
            return f'The file "{result}" was processed successfully.'
        except Exception as e:
            return f'An error occurred while processing the file: {e}'
    else:
        return 'An error occurred.'


if __name__ == '__main__':
    from werkzeug.utils import secure_filename
    import os
    app.run(debug=True)
