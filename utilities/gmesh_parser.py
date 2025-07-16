import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as colors

filepath = "capacitor/cap2d.msh"

def parse_msh_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return lines

def get_coords(lines):
    coords = []
    in_coords = False

    for line in lines:
        line = line.strip()
        if line == "begin_coordinates":
            in_coords = True
            continue
        elif line == "end_coordinates":
            in_coords = False
            continue
    
        if in_coords:
            x, y, _ = map(float, line.split())  # Discard z (2d)
            coords.append((x, y))

    coords = np.array(coords)
    return coords

def get_mesh_per_region(lines, region_id=0):
    i = region_id
    nodes, triangles = [], []
    in_region, in_nodes, in_tris = False, False, False

    for line in lines:
        line = line.strip()
        if line.startswith("begin_region") and not in_region:
            if i == 0:
                in_region = True
            else:
                i -= 1
        if in_region and line.startswith("end_region"):
            break

        elif in_region and line == "begin_nodes":
            in_nodes = True
            continue
        elif in_region and line == "end_nodes":
            in_nodes = False
        elif in_region and line == "begin_triangles":
            in_tris = True
            continue
        elif in_region and line == "end_triangles":
            in_tris = False
       
        if in_tris:
            i1, i2, i3 = map(int, line.split())
            triangles.append((i1, i2, i3))
        elif in_nodes:
            nodes.append(int(line))

    return np.array(nodes), np.array(triangles)

def get_global_triangles(nodes, triangles):
    # Remap local triangle indices to global coordinate indices
    # Trig indices map to nodes, but want this to map to the global xy coordinates
    return np.array([[nodes[i1], nodes[i2], nodes[i3]] for i1, i2, i3 in triangles])

def get_solution_variable(lines, variable_name, region_id=0):
    i = region_id
    in_region, in_solution = False, False
    values = []

    for line in lines:
        line = line.strip()
        if line.startswith("begin_region") and not in_region:
            if i == 0:
                in_region = True
            else:
                i -= 1
        if in_region and line.startswith("end_region"):
            break

        if in_region:
            if line.startswith(f'begin_node_model "{variable_name}"'):
                in_solution = True
                continue
            elif line.startswith("end_node_model"):
                in_solution = False
            elif in_solution:
                if line == "DATA":
                    continue
                values.append(float(line))

    return np.array(values)


# lines = parse_msh_file(filepath)
# coords = get_coords(lines)
# x, y = coords[:, 0], coords[:, 1]

# # Get mesh
# nodes_air, triangles_air = get_mesh_per_region(lines, 0)
# nodes_m1, triangles_m1 = get_mesh_per_region(lines, 1)
# nodes_m2, triangles_m2 = get_mesh_per_region(lines, 2)
# triangles_air_global = get_global_triangles(nodes_air, triangles_air)
# triangles_m1_global  = get_global_triangles(nodes_m1,  triangles_m1)
# triangles_m2_global  = get_global_triangles(nodes_m2,  triangles_m2)

# # Get potential values
# potential_air = get_solution_variable(lines, "Potential", 0)

# full_potential = np.full_like(x, 0)
# full_potential[nodes_air] = potential_air

# plt.figure()
# # Show potential
# contour = plt.tricontourf(x, y, triangles_air_global, full_potential, levels=50, cmap='viridis')
# plt.colorbar(contour, label="Potential (V)")

# # Show grid
# plt.triplot(x, y, triangles_air_global, color="white", label="air", linewidth=0.1)
# plt.triplot(x, y, triangles_m1_global, color="orange", label="metal m1")
# plt.triplot(x, y, triangles_m2_global, color="red", label="metal m2")

# plt.xlabel("x (µm)")
# plt.ylabel("y (µm)")
# plt.legend()
# plt.show()