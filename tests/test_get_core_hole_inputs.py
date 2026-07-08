from aiida import load_profile, orm

from aiida_qe_xspec.workflows.functions.get_core_hole_inputs import get_core_hole_inputs
from aiida_qe_xspec.workflows.functions.get_xspectra_structures import process_molecule_input
from aiida_qe_xspec.gui.xps.workchain import _core_levels_for_atom_indices
from aiida_qe_xspec.workflows.functions.get_marked_structures import get_marked_structures


load_profile()


def generate_core_hole_structure():
    structure = orm.StructureData(cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]])
    structure.append_atom(position=(0, 0, 0), symbols='C')
    structure.append_atom(position=(1, 0, 0), symbols='Co', name='X')
    return structure


def test_full_core_hole_with_total_magnetization_is_charged():
    parameters = {
        'SYSTEM': {
            'nspin': 2,
            'tot_charge': 0,
            'tot_magnetization': 3,
        },
    }

    updated = get_core_hole_inputs(
        structure=generate_core_hole_structure(),
        treatment='full',
        parameters=parameters,
        abs_site_data={'site_index': 1, 'symbol': 'Co'},
    )

    assert updated['SYSTEM']['tot_charge'] == 1
    assert updated['SYSTEM']['tot_magnetization'] == 3
    assert 'starting_magnetization' not in updated['SYSTEM']


def test_full_core_hole_with_starting_magnetization_is_charged():
    parameters = {
        'SYSTEM': {
            'nspin': 2,
            'tot_charge': 0,
            'starting_magnetization': {
                'C': 0.1,
                'Co': 0.3,
            },
        },
    }

    updated = get_core_hole_inputs(
        structure=generate_core_hole_structure(),
        treatment='full',
        parameters=parameters,
        abs_site_data={'site_index': 1, 'symbol': 'Co'},
    )

    assert updated['SYSTEM']['tot_charge'] == 1
    assert updated['SYSTEM']['starting_magnetization'] == {
        'C': 0.1,
        'X': 0.3,
    }
    assert 'tot_magnetization' not in updated['SYSTEM']
    assert parameters['SYSTEM']['starting_magnetization'] == {
        'C': 0.1,
        'Co': 0.3,
    }


def test_excited_core_hole_with_total_magnetization_is_neutral():
    parameters = {
        'SYSTEM': {
            'nspin': 2,
            'tot_charge': 0,
            'tot_magnetization': 3,
        },
    }

    updated = get_core_hole_inputs(
        structure=generate_core_hole_structure(),
        treatment='excited',
        parameters=parameters,
        abs_site_data={'site_index': 1, 'symbol': 'Co'},
    )

    assert updated['SYSTEM']['tot_charge'] == 0
    assert updated['SYSTEM']['tot_magnetization'] == 4
    assert 'starting_magnetization' not in updated['SYSTEM']


def test_excited_core_hole_with_starting_magnetization_is_neutral():
    parameters = {
        'SYSTEM': {
            'nspin': 2,
            'tot_charge': 0,
            'starting_magnetization': {
                'C': 0.1,
                'Co': 0.3,
            },
        },
    }

    updated = get_core_hole_inputs(
        structure=generate_core_hole_structure(),
        treatment='excited',
        parameters=parameters,
        abs_site_data={'site_index': 1, 'symbol': 'Co'},
    )

    assert updated['SYSTEM']['tot_charge'] == 0
    assert updated['SYSTEM']['starting_magnetization'] == {
        'C': 0.1,
        'X': 1,
    }
    assert 'tot_magnetization' not in updated['SYSTEM']


def test_molecule_symmetry_data_preserves_kind_name_for_tagged_atoms():
    structure = orm.StructureData(cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]])
    structure.append_atom(position=(6.1509291, 5, 5), symbols='O', name='O1')
    structure.append_atom(position=(5, 5, 5), symbols='O', name='O1')

    result = process_molecule_input(structure, absorbing_elements_list=['O'])
    equivalent_sites_data = result['output_params']['equivalent_sites_data']

    assert equivalent_sites_data['site_1']['symbol'] == 'O'
    assert equivalent_sites_data['site_1']['kind_name'] == 'O1'


def test_starting_magnetization_uses_tagged_absorber_kind_name():
    structure = orm.StructureData(cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]])
    structure.append_atom(position=(0, 0, 0), symbols='O', name='O1')
    structure.append_atom(position=(1, 0, 0), symbols='O', name='X')
    parameters = {
        'SYSTEM': {
            'nspin': 2,
            'tot_charge': 0,
            'starting_magnetization': {
                'O1': 0.1,
            },
        },
    }

    updated = get_core_hole_inputs(
        structure=structure,
        treatment='full',
        parameters=parameters,
        abs_site_data={'site_index': 1, 'symbol': 'O', 'kind_name': 'O1'},
    )

    assert updated['SYSTEM']['starting_magnetization'] == {
        'O1': 0.1,
        'X': 0.1,
    }


def test_atom_indices_are_one_based_in_gui_builder():
    structure = orm.StructureData(cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]])
    structure.append_atom(position=(0, 0, 0), symbols='C')
    structure.append_atom(position=(1, 0, 0), symbols='O', name='O1')
    pseudo_group = orm.Group(label='test_xps_pseudos')
    pseudo_group.base.extras.set('correction', {
        'C_1s': {'core': 0.0, 'exp': 0.0},
        'O_1s': {'core': 0.0, 'exp': 0.0},
    })

    atom_indices, core_levels = _core_levels_for_atom_indices(structure, [1, 2], pseudo_group)

    assert atom_indices == [0, 1]
    assert core_levels == {'C': ['1s'], 'O': ['1s']}


def test_marked_structures_use_symbol_for_tagged_absorber_kind():
    structure = orm.StructureData(cell=[[10, 0, 0], [0, 10, 0], [0, 0, 10]])
    structure.append_atom(position=(0, 0, 0), symbols='O', name='O1')
    structure.append_atom(position=(1, 0, 0), symbols='C')

    result = get_marked_structures(
        structure,
        atom_indices=orm.List([0]),
        marker=orm.Str('X'),
    )

    marked = result['site_0']
    output_parameters = result['output_parameters'].get_dict()['equivalent_sites_data']

    assert [(kind.name, kind.symbol) for kind in marked.kinds] == [('X', 'O'), ('C', 'C')]
    assert [site.kind_name for site in marked.sites] == ['X', 'C']
    assert output_parameters['site_0']['kind_name'] == 'O1'
    assert output_parameters['site_0']['symbol'] == 'O'
