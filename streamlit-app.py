import streamlit as st
import os
import subprocess
import tempfile
import base64

# Set page config
st.set_page_config(
    page_title="Structify - Chemical Structure Converter",
    page_icon="🧪",
    layout="wide"
)

# Create folders for uploads and conversions
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

def process_conversion(input_path, conversion_type, apply_minimization, add_hydrogens, apply_partial_charges, protonation_ph):
    # Extract base name (without extension)
    base_name, _ = os.path.splitext(os.path.basename(input_path))
    
    # Set up conversion paths and commands
    if conversion_type == 'smiles_to_sdf':
        output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.sdf")
        cmd = f"obabel {input_path} -O {output_path} --gen3d"

    elif conversion_type == 'smiles_to_mol2':
        output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.mol2")
        cmd = f"obabel {input_path} -O {output_path} --gen3d"
        if apply_partial_charges:
            cmd += " --partialcharge gasteiger"
        if apply_minimization:
            cmd += " --minimize"

    elif conversion_type == 'smiles_to_pdbqt':
        output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
        cmd = f"obabel {input_path} -O {output_path} --gen3d"
        if add_hydrogens:
            cmd += " --addh"
        if apply_partial_charges:
            cmd += " --partialcharge gasteiger"
        if apply_minimization:
            cmd += " --minimize"

    elif conversion_type == 'sdf_to_mol2':
        output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}.mol2")
        cmd = f"obabel {input_path} -O {output_path}"
        if apply_partial_charges:
            cmd += " --partialcharge gasteiger"
        if is_2d_sdf(input_path):
            cmd += " --gen3d"
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.mol2")
        if apply_minimization:
            cmd += " --minimize"

    elif conversion_type == 'sdf_to_pdbqt':
        output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}.pdbqt")
        cmd = f"obabel {input_path} -O {output_path}"
        if add_hydrogens:
            cmd += " --addh"
        if apply_partial_charges:
            cmd += " --partialcharge gasteiger"
        if is_2d_sdf(input_path):
            cmd += " --gen3d"
            output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
        if apply_minimization:
            cmd += " --minimize"

    elif conversion_type == 'mol2_to_pdbqt':
        output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
        cmd = f"obabel {input_path} -O {output_path}"
        if add_hydrogens:
            cmd += " --addh"
        if apply_partial_charges:
            cmd += " --partialcharge gasteiger"
        if apply_minimization:
            cmd += " --minimize"

    elif conversion_type == 'pdb_to_pdbqt':
        output_path = os.path.join(CONVERTED_FOLDER, f"{base_name}_3D.pdbqt")
        cmd = f"obabel {input_path} -O {output_path}"
        if add_hydrogens:
            cmd += " --addh"
        if apply_partial_charges:
            cmd += " --partialcharge gasteiger"
        if apply_minimization:
            cmd += " --minimize"

    # Add pH protonation option if specified
    if protonation_ph:
        cmd += f" --ph {protonation_ph}"

    # Execute the conversion
    try:
        subprocess.run(cmd, shell=True, check=True)
        return output_path
    except subprocess.CalledProcessError as e:
        st.error(f"Conversion failed: {e}")
        return None

def get_binary_file_downloader_html(bin_file, file_label='File'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}">{file_label}</a>'

# Main Streamlit UI
st.title("Structify - Chemical Structure Converter")
st.markdown("Convert between various chemical structure formats using OpenBabel")

# Input section
st.header("Input")
input_tabs = st.tabs(["SMILES Input", "File Upload"])

with input_tabs[0]:
    smiles_input = st.text_area("Enter SMILES string:", height=100, placeholder="E.g., CC(=O)OC1=CC=CC=C1C(=O)O")
    
with input_tabs[1]:
    uploaded_file = st.file_uploader("Upload a file:", type=['smi', 'sdf', 'mol2', 'pdb', 'pdbqt'])

# Conversion options
st.header("Conversion Options")

conversion_types = [
    'smiles_to_sdf', 'smiles_to_mol2', 'smiles_to_pdbqt',
    'sdf_to_mol2', 'sdf_to_pdbqt', 'mol2_to_pdbqt', 'pdb_to_pdbqt'
]

conversion_type = st.selectbox("Select conversion type:", conversion_types)

col1, col2 = st.columns(2)

with col1:
    apply_minimization = st.checkbox("Apply energy minimization")
    add_hydrogens = st.checkbox("Add hydrogens")

with col2:
    apply_partial_charges = st.checkbox("Apply partial charges (Gasteiger)")
    protonation_ph = st.number_input("Protonation pH (optional):", min_value=0.0, max_value=14.0, step=0.1, value=None)

# Process conversion
if st.button("Convert"):
    with st.spinner("Converting..."):
        if smiles_input:
            # Write SMILES string to a temporary file
            input_path = os.path.join(UPLOAD_FOLDER, "input.smi")
            with open(input_path, 'w') as smi_file:
                smi_file.write(smiles_input)
        elif uploaded_file:
            # Save uploaded file
            input_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(input_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
        else:
            st.warning("Please provide either a SMILES string or upload a file.")
            st.stop()
        
        # Validate pH if provided
        if protonation_ph is not None and (protonation_ph < 0 or protonation_ph > 14):
            st.error("Invalid pH value. Please provide a value between 0 and 14.")
            st.stop()
            
        # Run conversion
        output_path = process_conversion(
            input_path, 
            conversion_type,
            apply_minimization,
            add_hydrogens,
            apply_partial_charges,
            protonation_ph
        )
        
        if output_path and os.path.exists(output_path):
            st.success("Conversion completed successfully!")
            
            # Provide download link
            with open(output_path, "rb") as file:
                st.download_button(
                    label="Download Converted File",
                    data=file,
                    file_name=os.path.basename(output_path),
                    mime="application/octet-stream"
                )
        else:
            st.error("Conversion failed or output file not found.")

# Information section
st.sidebar.header("About Structify")
st.sidebar.markdown("""
This app converts between various chemical structure formats using OpenBabel.

**Supported conversions:**
- SMILES → SDF (3D)
- SMILES → MOL2 (3D)
- SMILES → PDBQT (3D)
- SDF → MOL2
- SDF → PDBQT
- MOL2 → PDBQT
- PDB → PDBQT

**Options:**
- Energy minimization
- Hydrogen addition
- Partial charge calculation
- pH-based protonation
""")

st.sidebar.markdown("---")
st.sidebar.markdown("Created by Pritam Kumar Panda @Stanford University")
st.sidebar.markdown("[GitHub Repository](https://github.com/pritampanda15/Structify-Chemical-Structure-Converter)")
