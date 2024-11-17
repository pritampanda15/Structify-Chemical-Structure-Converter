from flask import Flask, request, render_template, send_file
import os
import subprocess

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # Save uploaded file
            input_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(input_path)
            
            # Extract base name (without extension)
            base_name, _ = os.path.splitext(file.filename)
            
            # Determine output file name
            conversion_type = request.form['conversion_type']
            if conversion_type == 'sdf_to_mol2':
                output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}.mol2")
                cmd = f"obabel {input_path} -O {output_path}"
            elif conversion_type == 'sdf_to_pdbqt':
                output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}.pdbqt")
                cmd = f"obabel {input_path} -O {output_path} --partialcharge --addh"
            elif conversion_type == 'mol2_to_pdbqt':
                output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}.pdbqt")
                cmd = f"obabel {input_path} -O {output_path} --partialcharge --addh"
            elif conversion_type == 'pdb_to_pdbqt':
                output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}.pdbqt")
                cmd = f"obabel {input_path} -O {output_path} --partialcharge --addh"
            else:
                return "Invalid conversion type.", 400
            
            # Execute the command and handle errors
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                return f"Conversion failed: {e}", 500
            
            # Check if output file exists
            if not os.path.exists(output_path):
                return "Error: Output file not found. Conversion may have failed.", 500
            
            # Return the file for download
            return send_file(output_path, as_attachment=True)
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000), debug=True))

