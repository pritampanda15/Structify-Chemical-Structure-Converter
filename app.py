from flask import Flask, request, render_template, send_file, redirect, url_for, abort
import os
import subprocess

app = Flask(__name__, static_folder='static', template_folder='templates')
UPLOAD_FOLDER = "uploads"
CONVERTED_FOLDER = "converted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

def is_2d_sdf(file_path):
    """
    Check if the SDF file contains Z-coordinates (3D information).
    Returns True if the file is 2D, otherwise False.
    """
    with open(file_path, 'r') as sdf_file:
        for line in sdf_file:
            if "V2000" in line:  # Look for the atom block header
                # Read the next few lines to check for Z-coordinates
                atom_lines = sdf_file.readlines(10)
                for atom_line in atom_lines:
                    try:
                        # Extract X, Y, Z coordinates
                        coords = atom_line.split()[:3]
                        if len(coords) == 3:
                            z_coord = float(coords[2])
                            if z_coord != 0.0:
                                return False  # File is 3D
                    except (ValueError, IndexError):
                        pass
                return True  # File is 2D if no valid Z-coordinates found
    return True  # Assume 2D if unable to determine

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        smiles_input = request.form.get('smiles_input', None)
        conversion_type = request.form['conversion_type']
        apply_minimization = request.form.get('apply_minimization', False)
        add_hydrogens = request.form.get('add_hydrogens', False)
        apply_partial_charges = request.form.get('apply_partial_charges', False)  # New option
        protonation_ph = request.form.get('protonation_ph', None)
        

        # Ensure conversion_type is valid
        valid_conversion_types = [
            'smiles_to_sdf', 'smiles_to_mol2', 'smiles_to_pdbqt',
            'sdf_to_mol2', 'sdf_to_pdbqt', 'mol2_to_pdbqt', 'pdb_to_pdbqt'
        ]
        if conversion_type not in valid_conversion_types:
            return "Invalid conversion type.", 400
        
        if smiles_input:
            # Write SMILES string to a temporary file
            input_path = os.path.join(UPLOAD_FOLDER, "input.smi")
            with open(input_path, 'w') as smi_file:
                smi_file.write(smiles_input)
        else:
            # Handle file upload
            file = request.files['file']
            if file:
                input_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(input_path)
            else:
                return "No file or SMILES input provided.", 400

        # Extract base name (without extension)
        base_name, _ = os.path.splitext(os.path.basename(input_path))
        output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_converted")
        # Conversion paths and commands
        if conversion_type == 'smiles_to_sdf':
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.sdf")
            renamed_output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.sdf")
            cmd = f"obabel {input_path} -O {output_path} --gen3d"

        elif conversion_type == 'smiles_to_mol2':
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.mol2")
            renamed_output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.mol2")
            cmd = f"obabel {input_path} -O {output_path} --gen3d"
            if apply_partial_charges:
                cmd += " --partialcharge gasteiger"  # Add partial charges if selected
            if apply_minimization:
                cmd += " --minimize"

        elif conversion_type == 'smiles_to_pdbqt':
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
            renamed_output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
            cmd = f"obabel {input_path} -O {output_path} --gen3d"
            if add_hydrogens:
                cmd += " --addh"  # Add hydrogens if selected
            if apply_partial_charges:
                cmd += " --partialcharge gasteiger"  # Add partial charges if selected
            if apply_minimization:
                cmd += " --minimize"

        elif conversion_type == 'sdf_to_mol2':
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}.mol2")
            renamed_output_path = output_path  # No "3D" for non-3D conversions
            cmd = f"obabel {input_path} -O {output_path}"
            if apply_partial_charges:
                cmd += " --partialcharge gasteiger"  # Add partial charges if selected
            if is_2d_sdf(input_path):
                cmd += " --gen3d"
            if apply_minimization:
                cmd += " --minimize"

        elif conversion_type == 'sdf_to_pdbqt':
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}.pdbqt")
            renamed_output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
            cmd = f"obabel {input_path} -O {output_path}"
            if add_hydrogens:
                cmd += " --addh"  # Add hydrogens if selected
            if apply_partial_charges:
                cmd += " --partialcharge gasteiger"  # Add partial charges if selected
            if is_2d_sdf(input_path):
                cmd += " --gen3d"
            if apply_minimization:
                cmd += " --minimize"

        elif conversion_type == 'mol2_to_pdbqt':
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
            renamed_output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
            cmd = f"obabel {input_path} -O {output_path}"
            if add_hydrogens:
                cmd += " --addh"  # Add hydrogens if selected
            if apply_partial_charges:
                cmd += " --partialcharge gasteiger"  # Add partial charges if selected
            if apply_minimization:
                cmd += " --minimize"

        elif conversion_type == 'pdb_to_pdbqt':
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
            renamed_output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
            cmd = f"obabel {input_path} -O {output_path}"
            if add_hydrogens:
                cmd += " --addh"  # Add hydrogens if selected
            if apply_partial_charges:
                cmd += " --partialcharge gasteiger"  # Add partial charges if selected
            if apply_minimization:
                cmd += " --minimize"

        else:
            return "Invalid conversion type.", 400

        # Add pH protonation option if specified
        if protonation_ph:
            try:
                protonation_ph = float(protonation_ph)  # Ensure pH is numeric
                if 0 <= protonation_ph <= 12:  # Validate pH range
                    cmd += f" --ph {protonation_ph}"
                else:
                    return "Invalid pH value. Please provide a value between 0 and 12.", 400
            except ValueError:
                return "Invalid pH value. Please enter a numeric value.", 400

        # Execute the conversion
        try:
            subprocess.run(cmd, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            return f"Conversion failed: {e}", 500

        # Check if output file exists
        if not os.path.exists(output_path):
            return "Error: Output file not found. Conversion may have failed.", 500

        # Rename the file if necessary
        if output_path != renamed_output_path:
            os.rename(output_path, renamed_output_path)

        # Return the file for download
        return send_file(renamed_output_path, as_attachment=True)

        # Return the file for download
        try:
            return send_file(
                renamed_output_path,
                as_attachment=True,
                mimetype='application/octet-stream',
                download_name=os.path.basename(renamed_output_path)
            )
        except Exception as e:
            return f"Failed to send the file: {e}", 500
        
        return redirect(url_for('download_file', filename=os.path.basename(renamed_output_path)))
    return render_template('index.html')

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    """
    Additional endpoint to serve files from the CONVERTED_FOLDER.
    """
    file_path = os.path.join(CONVERTED_FOLDER, filename)
    if os.path.exists(file_path):
        try:
            return send_file(
                file_path,
                as_attachment=True,
                mimetype='application/octet-stream',
                download_name=filename
            )
        except Exception as e:
            abort(500, description=f"Failed to download file: {e}")
    else:
        abort(404, description="File not found.")

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
