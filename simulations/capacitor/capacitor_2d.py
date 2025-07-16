import devsim

device="2d capacitor"
region="silicon"

xmin=-25
x1  =-24.975
x2  =-2
x3  =2
x4  =24.975
xmax=25.0

ymin=0.0
y1  =0.1
y2  =0.2
y3  =0.8
y4  =0.9
ymax=50.0

devsim.create_2d_mesh(mesh=device)
devsim.add_2d_mesh_line(mesh=device, dir="y", pos=ymin, ps=0.1)
devsim.add_2d_mesh_line(mesh=device, dir="y", pos=y1  , ps=0.1)
devsim.add_2d_mesh_line(mesh=device, dir="y", pos=y2  , ps=0.1)
devsim.add_2d_mesh_line(mesh=device, dir="y", pos=y3  , ps=0.1)
devsim.add_2d_mesh_line(mesh=device, dir="y", pos=y4  , ps=0.1)
devsim.add_2d_mesh_line(mesh=device, dir="y", pos=ymax, ps=5.0)

device=device
region="air"

devsim.add_2d_mesh_line(mesh=device, dir="x", pos=xmin, ps=5)
devsim.add_2d_mesh_line(mesh=device, dir="x", pos=x1  , ps=2)
devsim.add_2d_mesh_line(mesh=device, dir="x", pos=x2  , ps=0.05)
devsim.add_2d_mesh_line(mesh=device, dir="x", pos=x3  , ps=0.05)
devsim.add_2d_mesh_line(mesh=device, dir="x", pos=x4  , ps=2)
devsim.add_2d_mesh_line(mesh=device, dir="x", pos=xmax, ps=5)

devsim.add_2d_region(mesh=device, material="gas"  , region="air", yl=ymin, yh=ymax, xl=xmin, xh=xmax)
devsim.add_2d_region(mesh=device, material="metal", region="m1" , yl=y1  , yh=y2  , xl=x1  , xh=x4)
devsim.add_2d_region(mesh=device, material="metal", region="m2" , yl=y3  , yh=y4  , xl=x2  , xh=x3)

# must be air since contacts don't have any equations
devsim.add_2d_contact(mesh=device, name="bot", region="air", material="metal", yl=y1, yh=y2, xl=x1, xh=x4)
devsim.add_2d_contact(mesh=device, name="top", region="air", material="metal", yl=y3, yh=y4, xl=x2, xh=x3)
devsim.finalize_mesh(mesh=device)
devsim.create_device(mesh=device, device=device)

### Set parameters on the region
devsim.set_parameter(device=device, region=region, name="Permittivity", value=3.9*8.85e-14)

### Create the Potential solution variable
devsim.node_solution(device=device, region=region, name="Potential")

### Creates the Potential@n0 and Potential@n1 edge model
devsim.edge_from_node_model(device=device, region=region, node_model="Potential")

### Electric field on each edge, as well as its derivatives with respect to
### the potential at each node
devsim.edge_model(device=device, region=region, name="ElectricField",
                 equation="(Potential@n0 - Potential@n1)*EdgeInverseLength")

devsim.edge_model(device=device, region=region, name="ElectricField:Potential@n0",
                 equation="EdgeInverseLength")

devsim.edge_model(device=device, region=region, name="ElectricField:Potential@n1",
                 equation="-EdgeInverseLength")

### Model the D Field
devsim.edge_model(device=device, region=region, name="DField",
           equation="Permittivity*ElectricField")

devsim.edge_model(device=device, region=region, name="DField:Potential@n0",
           equation="diff(Permittivity*ElectricField, Potential@n0)")

devsim.edge_model(device=device, region=region, name="DField:Potential@n1",
           equation="-DField:Potential@n0")

### Create the bulk equation
devsim.equation(device=device, region=region, name="PotentialEquation",
  variable_name="Potential", edge_model="DField",
  variable_update="default")

### Contact models and equations
for c in ("top", "bot"):
  devsim.contact_node_model(device=device, contact=c, name="%s_bc" % c,
           equation="Potential - %s_bias" % c)

  devsim.contact_node_model(device=device, contact=c, name="%s_bc:Potential" % c,
             equation="1")

  devsim.contact_equation(device=device, contact=c, name="PotentialEquation",
             node_model="%s_bc" % c, edge_charge_model="DField")

### Set the contact
devsim.set_parameter(device=device, name="top_bias", value=1.0e-0)
devsim.set_parameter(device=device, name="bot_bias", value=0.0)

devsim.edge_model(device=device, region="m1", name="ElectricField", equation="0")
devsim.edge_model(device=device, region="m2", name="ElectricField", equation="0")
devsim.node_model(device=device, region="m1", name="Potential", equation="bot_bias;")
devsim.node_model(device=device, region="m2", name="Potential", equation="top_bias;")

devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=30,
  solver_type="direct")

devsim.element_from_edge_model(edge_model="ElectricField", device=device, region=region)
print(devsim.get_contact_charge(device=device, contact="top", equation="PotentialEquation"))
print(devsim.get_contact_charge(device=device, contact="bot", equation="PotentialEquation"))

devsim.write_devices(file="../../capacitor/cap2d.msh", type="devsim")
devsim.write_devices(file="../../capacitor/cap2d.dat", type="tecplot")


### Plot using matplotlib
import matplotlib.pyplot as plt
import numpy as np
import sys
sys.path.append('../../')
import utilities.gmesh_parser as parse

x = np.array(devsim.get_node_model_values(device=device, region=region, name="x"))
y = np.array(devsim.get_node_model_values(device=device, region=region, name="y"))
potential = np.array(devsim.get_node_model_values(device=device, region=region, name="Potential"))


lines = parse.parse_msh_file("../../capacitor/cap2d.msh")
# Get mesh
nodes_air, triangles_air = parse.get_mesh_per_region(lines, 0)
nodes_m1, triangles_m1 = parse.get_mesh_per_region(lines, 1)
nodes_m2, triangles_m2 = parse.get_mesh_per_region(lines, 2)
triangles_air_global = parse.get_global_triangles(nodes_air, triangles_air)
triangles_m1_global  = parse.get_global_triangles(nodes_m1,  triangles_m1)
triangles_m2_global  = parse.get_global_triangles(nodes_m2,  triangles_m2)

plt.figure()

# Show potential
contour = plt.tricontourf(x, y, triangles_air_global, potential, levels=50, cmap='viridis')
plt.colorbar(contour, label="Potential (V)")

# Show grid
plt.triplot(x, y, triangles_air_global, color="white", label="air", linewidth=0.1)
plt.triplot(x, y, triangles_m1_global, color="orange", label="metal m1")
plt.triplot(x, y, triangles_m2_global, color="red", label="metal m2")

plt.xlabel("x (µm)")
plt.ylabel("y (µm)")
plt.legend()
plt.show()