import pytest
from aiida import load_profile, orm
from aiida.common import ValidationError
from aiida.engine import run
from aiida_qe_xspec.utils import load_core_hole_pseudos
from aiida_qe_xspec.workflows.xps import XpsWorkChain

load_profile()

def test_validate_get_builder_from_protocol(etfa_molecule):
    code = orm.load_code('qe-7.2-pw@localhost')
    core_levels = {'C': ['1s']}
    core_hole_pseudos, correction_energies = load_core_hole_pseudos(core_levels, 'pseudo_demo_pbe')
    with pytest.raises(ValidationError, match="The following elements: {'Fe'} in `core_levels` are not present in the structure"):
        builder = XpsWorkChain.get_builder_from_protocol(
            structure=etfa_molecule,
            code=code,
            core_hole_pseudos=core_hole_pseudos,
            core_levels={'Fe': ['1s']},
            correction_energies=orm.Dict(correction_energies),
        )
        run(builder)
    with pytest.raises(ValidationError, match="Elements {'O'} are requested in `core_levels` but no corresponding pseudopotentials are found in"):
        builder = XpsWorkChain.get_builder_from_protocol(
            structure=etfa_molecule,
            code=code,
            core_hole_pseudos=core_hole_pseudos,
            core_levels={'C': ['1s'], 'O': ['1s']},
            correction_energies=orm.Dict(correction_energies),
        )
        run(builder)
    with pytest.raises(ValidationError, match='All atom indices in `atom_indices` must be valid indices within the structure.'):
        builder = XpsWorkChain.get_builder_from_protocol(
            structure=etfa_molecule,
            code=code,
            core_hole_pseudos=core_hole_pseudos,
            core_levels={'C': ['1s']},
            atom_indices = [0, 100],
            correction_energies=orm.Dict(correction_energies),
        )
        run(builder)
    with pytest.raises(ValidationError, match="The following elements: {'O'} are required for analysis but no pseudopotentials are provided for them in `core_hole_pseudos`."):
        builder = XpsWorkChain.get_builder_from_protocol(
            structure=etfa_molecule,
            code=code,
            core_hole_pseudos=core_hole_pseudos,
            core_levels={'C': ['1s']},
            atom_indices = [8],
            correction_energies=orm.Dict(correction_energies),
        )
        run(builder)
    with pytest.raises(ValidationError, match="`core_levels` for element \"C\" must be a list of strings,"):
        builder = XpsWorkChain.get_builder_from_protocol(
            structure=etfa_molecule,
            code=code,
            core_hole_pseudos=core_hole_pseudos,
            core_levels={'C': '1s'},
            correction_energies=orm.Dict(correction_energies),
        )
        run(builder)
    with pytest.raises(ValidationError, match="Unrecognized orbital \"1 s\" for element \"C\". Valid orbitals are:"):
        builder = XpsWorkChain.get_builder_from_protocol(
            structure=etfa_molecule,
            code=code,
            core_hole_pseudos=core_hole_pseudos,
            core_levels={'C': ['1 s']},
            correction_energies=orm.Dict(correction_energies),
        )
        run(builder)
    with pytest.raises(ValidationError, match='`calc_binding_energy=True` was requested, but `correction_energies` is not provided.'):
        builder = XpsWorkChain.get_builder_from_protocol(
            structure=etfa_molecule,
            code=code,
            core_hole_pseudos=core_hole_pseudos,
            core_levels={'C': ['1s']},
        )
        builder.calc_binding_energy = orm.Bool(True)
        run(builder)
    with pytest.raises(ValidationError, match="No pseudopotential entry found for orbital \"2s\" under element \"C\" in `core_hole_pseudos`"):
        builder = XpsWorkChain.get_builder_from_protocol(
            structure=etfa_molecule,
            code=code,
            core_hole_pseudos=core_hole_pseudos,
            core_levels={'C': ['1s', '2s']},
            correction_energies=orm.Dict(correction_energies),
        )
        run(builder)


def test_builder_allows_total_magnetization_without_starting_magnetization(etfa_molecule):
    code = orm.load_code('qe-7.2-pw@localhost')
    core_levels = {'C': ['1s']}
    core_hole_pseudos, correction_energies = load_core_hole_pseudos(core_levels, 'pseudo_demo_pbe')

    builder = XpsWorkChain.get_builder_from_protocol(
        structure=etfa_molecule,
        code=code,
        core_hole_pseudos=core_hole_pseudos,
        core_levels=core_levels,
        correction_energies=orm.Dict(correction_energies),
        overrides={
            'ch_scf': {
                'pw': {
                    'parameters': {
                        'SYSTEM': {
                            'nspin': 2,
                            'tot_magnetization': 1,
                        },
                    },
                },
            },
        },
    )

    system = builder.ch_scf.pw.parameters.get_dict()['SYSTEM']

    assert system['nspin'] == 2
    assert system['tot_magnetization'] == 1
    assert 'starting_magnetization' not in system
