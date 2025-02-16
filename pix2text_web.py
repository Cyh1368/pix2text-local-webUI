import os
from flask import Flask, request, jsonify, render_template_string
from pix2text import Pix2Text
from PIL import Image

app = Flask(__name__)

# Initialize the pix2text model once at startup.
p2t = Pix2Text.from_config()

# HTML interface with improved UI, paste support, and result box.
UPLOAD_FORM = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Image to Markdown/LaTeX</title>
    <style>
      body {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100vh;
        margin: 0;
        background-color: #f3f4f6;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      }
      h1 {
        margin-bottom: 20px;
      }
      form {
        text-align: center;
        margin-bottom: 20px;
      }
      input[type="file"] {
        display: block;
        margin: 10px auto;
      }
      .upload-btn {
        width: 100%;
        padding: 15px;
        border: none;
        border-radius: 12px;
        background-color: #2563eb;
        color: white;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
      }
      .upload-btn:hover {
        background-color: #1d4ed8;
      }
      #result-box {
        width: 80%;
        height: 200px;
        margin-top: 20px;
        padding: 10px;
        border: 1px solid #ccc;
        background-color: #fff;
        overflow-y: auto;
        white-space: pre-wrap;
      }
      .copy-btn {
        margin-top: 10px;
        padding: 10px 20px;
        border: none;
        border-radius: 8px;
        background-color: #10b981;
        color: white;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.3s;
      }
      .copy-btn:hover {
        background-color: #059669;
      }
    </style>
  </head>
  <body>
    <h1>Upload or Paste Image for Text & Formula Recognition</h1>
    <form id="upload-form" method="POST" action="/recognize" enctype="multipart/form-data">
      <input type="file" name="file" accept="image/*" id="file-input" required>
      <button type="submit" class="upload-btn">Upload and Process</button>
    </form>
    <div id="result-box">Results will appear here...</div>
    <button class="copy-btn" onclick="copyToClipboard()">Copy All Text</button>

    <script>
      // Allow pasting images directly
      document.body.addEventListener('paste', async (event) => {
          const items = event.clipboardData.items;
          for (let item of items) {
              if (item.type.startsWith('image/')) {
                  document.getElementById('result-box').innerText = "Generating, please wait...";
                  const file = item.getAsFile();
                  const formData = new FormData();
                  formData.append('file', file);
                  
                  const response = await fetch('/recognize', {
                      method: 'POST',
                      body: formData
                  });
                  const result = await response.json();
                  document.getElementById('result-box').innerText = result.result;
              } else {
                  alert("You did not upload an image.")
              }
          }
      });

      // Handle form submission to display results
      document.getElementById('upload-form').addEventListener('submit', async (e) => {
          e.preventDefault();
          document.getElementById('result-box').innerText = "Generating, please wait...";
          const formData = new FormData(e.target);
          const response = await fetch('/recognize', {
              method: 'POST',
              body: formData
          });
          const result = await response.json();
          document.getElementById('result-box').innerText = result.result;
      });

      // Copy text to clipboard
      function copyToClipboard() {
          const resultBox = document.getElementById('result-box');
          navigator.clipboard.writeText(resultBox.innerText).then(() => {
              alert('Text copied to clipboard!');
          }).catch(err => {
              alert('Failed to copy text: ' + err);
          });
      }
    </script>
  </body>
</html>

"""


@app.route('/', methods=['GET'])
def index():
    return render_template_string(UPLOAD_FORM)


@app.route('/recognize', methods=['POST'])
def recognize():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        image = Image.open(file.stream).convert("RGB")
    except Exception as e:
        return jsonify({"error": "Invalid image file", "details": str(e)}), 400

    try:
        outs = p2t.recognize_text_formula(image, resized_shape=768, return_text=True)
        return jsonify({"result": outs})
    except Exception as e:
        return jsonify({"error": "Error processing image", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
