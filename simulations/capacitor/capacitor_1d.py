'''
    Simple 1D capacitor example
    Solve the Poisson equation:
        ε∇2ψ = 0
    With contact boundary conditions:
        ψi - Vc = 0
    where ψi is the potential at the contact node and Vc is the applied voltage
'''

import devsim

device = "capacitor_1D"
region = "silicon"

ε0 = 8.85e-14
εr_SiO2 = 3.9

# Create a 1D mesh
devsim.create_1d_mesh(mesh="capacitor")
devsim.add_1d_mesh_line(mesh="capacitor", pos=0.0, ps=0.1, tag="contact1")
devsim.add_1d_mesh_line(mesh="capacitor", pos=1.0, ps=0.1, tag="contact2")
devsim.add_1d_contact(mesh="capacitor", material="metal", name="contact1", tag="contact1")
devsim.add_1d_contact(mesh="capacitor", material="metal", name="contact2", tag="contact2")
devsim.add_1d_region(mesh="capacitor", material="Si", region=region, tag1="contact1", tag2="contact2")
devsim.finalize_mesh(mesh="capacitor")
devsim.create_device(mesh="capacitor", device=device)

# Set parameters of the region
devsim.set_parameter(device=device, region=region, name="Permittivity", value=εr_SiO2*ε0)

# Create the Potential solution variable
devsim.node_solution(device=device, region=region, name="Potential")
# Create Potential@n0 and Potential@n1 edge model
devsim.edge_from_node_model(device=device, region=region, node_model="Potential")

# Electric field on each edge, and its derivatives with respect to the potential at each node
devsim.edge_model(device=device, region=region, name="ElectricField", equation="(Potential@n0 - Potential@n1) * EdgeInverseLength")
devsim.edge_model(device=device, region=region, name="ElectricField:Potential@n0", equation="EdgeInverseLength") # The name <ModelName>:<SolutionVariable> means registers the analytical partial derivative of <ModelName> with respect to <SolutionVariable>
devsim.edge_model(device=device, region=region, name="ElectricField:Potential@n1", equation="-EdgeInverseLength")

# Model D-field
devsim.edge_model(device=device, region=region, name="DField", equation="Permittivity * ElectricField")
devsim.edge_model(device=device, region=region, name="DField:Potential@n0", equation="diff(Permittivity * ElectricField, Potential@n0)")
devsim.edge_model(device=device, region=region, name="DField:Potential@n1",equation="-DField:Potential@n0")

# Create bulk equation
devsim.equation(device=device, region=region, name="PotentialEquation", variable_name="Potential", edge_model="DField", variable_update="default")

# Contact models and equations
for c in ("contact1", "contact2"):
    devsim.contact_node_model(device=device, contact=c, name="%s_bc" % c, equation="Potential - %s_bias" % c)
    devsim.contact_node_model(device=device, contact=c, name="%s_bc:Potential" % c, equation="1")
    devsim.contact_equation(device=device, contact=c, name="PotentialEquation", node_model="%s_bc" % c, edge_charge_model="DField")

# Set the contact
devsim.set_parameter(device=device, region=region, name="contact1_bias", value=1.0e-0)
devsim.set_parameter(device=device, region=region, name="contact2_bias", value=0.0)

# Solve
devsim.solve(type="dc", absolute_error=1.0, relative_error=1e-10, maximum_iterations=30)

# Print charge on contacts
for c in ("contact1", "contact2"):
  print("contact: %s charge: %1.5e"
    % (c, devsim.get_contact_charge(device=device, contact=c, equation="PotentialEquation")))