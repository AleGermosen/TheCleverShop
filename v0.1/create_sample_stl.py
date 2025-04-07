import numpy as np
from stl import mesh
import os
import traceback

def create_cube_stl(output_path, size=1.0):
    """Create a sample cube STL file."""
    try:
        print(f"Creating cube STL at {output_path}...")
        # Define the 8 vertices of the cube
        vertices = np.array([
            [-size/2, -size/2, -size/2],
            [+size/2, -size/2, -size/2],
            [+size/2, +size/2, -size/2],
            [-size/2, +size/2, -size/2],
            [-size/2, -size/2, +size/2],
            [+size/2, -size/2, +size/2],
            [+size/2, +size/2, +size/2],
            [-size/2, +size/2, +size/2]
        ])

        # Define the 12 triangles composing the cube
        faces = np.array([
            [0, 3, 1],
            [1, 3, 2],
            [0, 4, 7],
            [0, 7, 3],
            [4, 5, 6],
            [4, 6, 7],
            [5, 1, 2],
            [5, 2, 6],
            [2, 3, 6],
            [3, 7, 6],
            [0, 1, 5],
            [0, 5, 4]
        ])

        # Create the mesh
        cube = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                cube.vectors[i][j] = vertices[f[j]]

        # Save the mesh to file
        cube.save(output_path)
        print(f"Cube STL created at {output_path} ({os.path.getsize(output_path)} bytes)")
        return True
    except Exception as e:
        print(f"Error creating cube STL: {e}")
        traceback.print_exc()
        return False

def create_pyramid_stl(output_path, size=1.0, height=1.5):
    """Create a sample pyramid STL file."""
    try:
        print(f"Creating pyramid STL at {output_path}...")
        # Define the 5 vertices of the pyramid
        vertices = np.array([
            [-size/2, -size/2, 0],      # Base - bottom left
            [+size/2, -size/2, 0],      # Base - bottom right
            [+size/2, +size/2, 0],      # Base - top right
            [-size/2, +size/2, 0],      # Base - top left
            [0, 0, height]              # Apex
        ])

        # Define the 4 triangles of the sides + 2 triangles for the base
        faces = np.array([
            [0, 1, 4],  # Side 1
            [1, 2, 4],  # Side 2
            [2, 3, 4],  # Side 3
            [3, 0, 4],  # Side 4
            [0, 2, 1],  # Base 1
            [0, 3, 2]   # Base 2
        ])

        # Create the mesh
        pyramid = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                pyramid.vectors[i][j] = vertices[f[j]]

        # Save the mesh to file
        pyramid.save(output_path)
        print(f"Pyramid STL created at {output_path} ({os.path.getsize(output_path)} bytes)")
        return True
    except Exception as e:
        print(f"Error creating pyramid STL: {e}")
        traceback.print_exc()
        return False

def create_3d_print_model(output_path):
    """Create a more complex 3D print model."""
    try:
        print(f"Creating sample 3D print model at {output_path}...")
        # Base platform vertices
        base_vertices = np.array([
            [-2, -2, 0],  # 0
            [+2, -2, 0],  # 1
            [+2, +2, 0],  # 2
            [-2, +2, 0],  # 3
            [-1.8, -1.8, 0.2],  # 4
            [+1.8, -1.8, 0.2],  # 5
            [+1.8, +1.8, 0.2],  # 6
            [-1.8, +1.8, 0.2]   # 7
        ])
        
        # Base faces
        base_faces = np.array([
            [0, 1, 5], [0, 5, 4],  # Front
            [1, 2, 6], [1, 6, 5],  # Right
            [2, 3, 7], [2, 7, 6],  # Back
            [3, 0, 4], [3, 4, 7],  # Left
            [4, 5, 6], [4, 6, 7],  # Top
            [3, 2, 1], [3, 1, 0]   # Bottom
        ])
        
        # Add a simple cylinder on top
        cylinder_vertices = []
        cylinder_faces = []
        
        # Top and bottom centers of cylinder
        center_bottom = np.array([0, 0, 0.2])  # 8
        center_top = np.array([0, 0, 1.2])     # 9
        
        cylinder_vertices.append(center_bottom)
        cylinder_vertices.append(center_top)
        
        # Create circle points for top and bottom
        segments = 12
        radius = 0.7
        
        for i in range(segments):
            angle = 2 * np.pi * i / segments
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            
            # Bottom circle point
            cylinder_vertices.append(np.array([x, y, 0.2]))  # 10 + i
            # Top circle point
            cylinder_vertices.append(np.array([x, y, 1.2]))  # 10 + segments + i
        
        # Create cylinder faces
        for i in range(segments):
            # Current and next point indices
            current_bottom = 10 + i
            next_bottom = 10 + ((i + 1) % segments)
            current_top = 10 + segments + i
            next_top = 10 + segments + ((i + 1) % segments)
            
            # Bottom face triangle
            cylinder_faces.append([8, current_bottom, next_bottom])
            
            # Top face triangle
            cylinder_faces.append([9, next_top, current_top])
            
            # Side quad as two triangles
            cylinder_faces.append([current_bottom, current_top, next_bottom])
            cylinder_faces.append([next_bottom, current_top, next_top])
        
        # Combine all vertices and faces
        all_vertices = np.vstack([base_vertices, np.array(cylinder_vertices)])
        
        # Adjust cylinder face indices to account for base vertices
        all_faces = np.vstack([base_faces, np.array(cylinder_faces)])
        
        # Create the mesh
        model = mesh.Mesh(np.zeros(all_faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(all_faces):
            for j in range(3):
                model.vectors[i][j] = all_vertices[f[j]]
        
        # Save the mesh to file
        model.save(output_path)
        print(f"Sample 3D print model created at {output_path} ({os.path.getsize(output_path)} bytes)")
        return True
    except Exception as e:
        print(f"Error creating sample 3D print model: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Get absolute path for the static/models directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(script_dir, "static", "models")
    
    # Ensure directory exists
    print(f"Creating directory: {static_dir}")
    os.makedirs(static_dir, exist_ok=True)
    
    # Check if the directory was created
    if os.path.exists(static_dir):
        print(f"Directory exists at {static_dir}")
    else:
        print(f"ERROR: Failed to create directory at {static_dir}")
        exit(1)
    
    # Create the STL files
    cube_path = os.path.join(static_dir, "cube.stl")
    pyramid_path = os.path.join(static_dir, "pyramid.stl")
    sample_print_path = os.path.join(static_dir, "sample_print.stl")
    
    create_cube_stl(cube_path)
    create_pyramid_stl(pyramid_path)
    create_3d_print_model(sample_print_path)
    
    # Verify the files exist
    files_created = 0
    for path in [cube_path, pyramid_path, sample_print_path]:
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"✓ File exists: {path} ({size_kb:.2f} KB)")
            files_created += 1
        else:
            print(f"✗ File missing: {path}")
    
    if files_created == 3:
        print("\nSUCCESS: All sample STL files created successfully!")
    else:
        print(f"\nWARNING: Only {files_created}/3 files were created successfully.") 