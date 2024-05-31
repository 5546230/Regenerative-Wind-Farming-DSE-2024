from Structure_Defs import verif_geom_3 as geometry
from Honeycomb_Truss import Hexagonal_Truss
from Truss_Analysis import Mesh, FEM_Solve, Material, Section
import numpy as np

def run_analysis(section_lib: list, material_lib: list, geometry: callable, verbose: bool = True):
    '''
    :param section_lib: indexed section property library
    :param material_lib: indexed material property library
    :param geometry: geometry function
    :return: [-]
    '''

    XYZ_coords, member_indices, section_indices, material_indices, bc_indices, bc_constraints, load_indices, applied_loads = geometry()

    'initialise mesh'
    MESH = Mesh(XYZ_coords=XYZ_coords, member_indices=member_indices, section_ids=section_indices, material_ids=material_indices, materials=material_lib, sections=section_lib)
    MESH.plot_structure()
    sigys = np.array([MESH.materials[i].E for i in MESH.material_indices])

    'initialise solver'
    SOLVER = FEM_Solve(mesh=MESH, bc_indices=bc_indices, bc_constraints=bc_constraints, load_indices=load_indices, applied_loads=applied_loads)

    'solve'
    d, Q, sigma = SOLVER.solve_system(plot=True, factor=1)

    if verbose:
        print(f'        omega_f [rad/s] = {SOLVER.get_natural_frequencies()}')
        print(f'           omega_f [Hz] = {SOLVER.get_natural_frequencies()*.1592}')
        print(f'      displacement [mm] = {d * 1000}')
        print(f'   Internal forces [kN] = {Q / 1000}')
        print(f'internal stresses [MPa] = {sigma / 1e6}')
    print(np.any(sigma>=sigys))
    return


def run_optimization(section_lib: list, material_lib: list, geometry: callable, verbose: bool = True):
    XYZ_coords, member_indices, section_indices, material_indices, bc_indices, bc_constraints, load_indices, applied_loads = geometry()

    'initialise mesh'
    MESH = Mesh(XYZ_coords=XYZ_coords, member_indices=member_indices, section_ids=section_indices, material_ids=material_indices, materials=material_lib, sections=section_lib)
    MESH.plot_structure()

    'collect element properties'
    Es = MESH.element_Es
    sigys = np.array([MESH.materials[i].E for i in MESH.material_indices])
    As = MESH.element_As

    'initialise solver'
    SOLVER = FEM_Solve(mesh=MESH, bc_indices=bc_indices, bc_constraints=bc_constraints, load_indices=load_indices, applied_loads=applied_loads)

    'solve'
    d, Q, sigma = SOLVER.solve_system(plot=True, factor=1)

    if np.any(sigma>=sigys):
        pass

    return


if __name__ == '__main__':
    'material and section definitions'
    steel = Material()
    standard_section = Section(radius=0.1, thickness=0.0025)

    'create libraries'
    material_library = [steel, steel, steel, steel]
    section_library = [standard_section, standard_section, standard_section, standard_section]

    geom = Hexagonal_Truss(n_rotors = 3, r_per_rotor = 12.5, spacing_factor=1, verbose=False)
    run_analysis(section_lib=section_library, material_lib=material_library, geometry=geom.function)