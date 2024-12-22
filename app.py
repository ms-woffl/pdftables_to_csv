from flask import Flask, request, send_file, render_template
import os
import pandas as pd
# import tabula
from tabula.io import read_pdf
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configurations
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    """Check if the uploaded file is a PDF."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def flatten_multiline_cells(df):
    """Flatten multiline text in cells."""
    return df.applymap(lambda x: ' '.join(str(x).splitlines()) if isinstance(x, str) else x)


@app.route('/')
def upload_form():
    """Render the file upload form."""
    return render_template('upload.html')  # Ensure you have an `upload.html` file for the form


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle the file upload and process the PDF."""
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Read all tables from the PDF
            tables = read_pdf(file_path, pages='all', multiple_tables=True, stream=True)
            if not tables:
                return "No tables found in the PDF.", 400

            # Flatten multiline cells and combine all tables into a single DataFrame
            flattened_tables = [flatten_multiline_cells(df) for df in tables]
            combined_df = pd.concat(flattened_tables, ignore_index=True)

            # Save the combined table to a CSV file
            csv_filename = f"{filename.rsplit('.', 1)[0]}.csv"
            csv_path = os.path.join(app.config['DOWNLOAD_FOLDER'], csv_filename)
            combined_df.to_csv(csv_path, index=False)

            return send_file(csv_path, as_attachment=True)

        except Exception as e:
            return f"Error processing file: {e}", 500

    return "Invalid file type. Only PDFs are allowed.", 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))







