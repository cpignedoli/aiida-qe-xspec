from aiida.common import ValidationError
from aiida.orm import Bool, Dict, Float, Group
from aiida.plugins import WorkflowFactory
from aiida_quantumespresso.common.types import ElectronicType, SpinType
from aiida_qe_xspec.workflows.xps import XpsWorkChain
from aiida_qe_xspec.utils import load_core_hole_pseudos
from aiidalab_qe.utils import (
    enable_pencil_decomposition,
    set_component_resources,
)

# supercell min parameter for different protocols
supercell_min_parameter_map = {
    'fast': 4.0,
    'balanced': 8.0,
    'stringent': 12.0,
}


def _core_levels_for_atom_indices(structure, atom_indices, pseudo_group):
    """Return zero-based atom indices and supported core levels for selected one-based UI indices."""
    if not atom_indices:
        return atom_indices, {}

    correction_energies = pseudo_group.base.extras.get('correction', {})
    supported_core_levels = {}
    for key in correction_energies:
        element, orbital = key.split('_', maxsplit=1)
        supported_core_levels.setdefault(element, []).append(orbital)

    zero_based_indices = []
    core_levels = {}
    num_sites = len(structure.sites)
    for index in atom_indices:
        if index < 1 or index > num_sites:
            raise ValidationError(
                f'Atom index {index} is out of range. Use one-based indices between 1 and {num_sites}.'
            )
        zero_based_index = index - 1
        zero_based_indices.append(zero_based_index)
        kind = structure.get_kind(structure.sites[zero_based_index].kind_name)
        element = kind.symbol
        if element not in supported_core_levels:
            raise ValidationError(
                f'Element {element} for atom index {index} is not supported by pseudo group {pseudo_group.label}.'
            )
        core_levels.setdefault(element, supported_core_levels[element])

    return zero_based_indices, core_levels

def update_resources(builder, codes):
    """Update the resources for the builder."""
    set_component_resources(builder.ch_scf.pw, codes.get('pw'))
    enable_pencil_decomposition(builder.ch_scf.pw)


def get_builder(codes, structure, parameters, **kwargs):
    from copy import deepcopy

    protocol = parameters['workchain']['protocol']
    xps_parameters = parameters.get('xps', {})
    core_levels = xps_parameters.pop('core_levels')
    atom_indices = xps_parameters.pop('atom_indices', None)
    # load pseudo for excited-state and group-state.
    pseudo_group_label = xps_parameters.pop('pseudo_group')
    pseudo_group = Group.collection.get(label=pseudo_group_label)
    if atom_indices:
        atom_indices, inferred_core_levels = _core_levels_for_atom_indices(structure, atom_indices, pseudo_group)
        if not core_levels:
            core_levels = inferred_core_levels
    core_hole_pseudos, correction_energies = load_core_hole_pseudos(core_levels, pseudo_group_label)
    # update the correction energies by the band gap correction
    band_gap_correction = xps_parameters.pop('band_gap_correction', 0.0)
    for element, levels in correction_energies.items():
        for level, energy in levels.items():
            correction_energies[element][level] = energy - band_gap_correction

    is_molecule_input = True if xps_parameters.get('structure_type') == 'molecule' else False
    if is_molecule_input:
        core_hole_treatment = 'full'
    else:
        core_hole_treatment = 'excited'
    core_hole_treatments = {element: core_hole_treatment for element in core_levels}
    structure_preparation_settings = {
        'supercell_min_parameter': Float(supercell_min_parameter_map[protocol]),
        'is_molecule_input': Bool(is_molecule_input),
    }
    pw_code = codes['pw']['code']
    overrides_ch_scf = deepcopy(parameters['advanced'])
    if is_molecule_input:
        overrides_ch_scf['pw']['parameters']['SYSTEM']['assume_isolated'] = 'mt'
    overrides = {
        'ch_scf': overrides_ch_scf,
    }
    # Ensure that VdW corrections are not applied for the core-hole SCF calculation
    # Required to resolve issue #765 (https://github.com/aiidalab/aiidalab-qe/issues/765)
    overrides['ch_scf']['pw']['parameters']['SYSTEM']['vdw_corr'] = 'none'

    builder = XpsWorkChain.get_builder_from_protocol(
        code=pw_code,
        structure=structure,
        protocol=protocol,
        core_hole_pseudos=core_hole_pseudos,
        core_levels=core_levels,
        atom_indices=atom_indices,
        calc_binding_energy=Bool(True),
        correction_energies=Dict(correction_energies),
        core_hole_treatments=core_hole_treatments,
        structure_preparation_settings=structure_preparation_settings,
        electronic_type=ElectronicType(parameters['workchain']['electronic_type']),
        spin_type=SpinType(parameters['workchain']['spin_type']),
        initial_magnetic_moments=parameters['advanced']['initial_magnetic_moments'],
        overrides=overrides,
        **kwargs,
    )
    builder.pop('relax', None)
    builder.pop('clean_workdir', None)
    # update resources
    update_resources(builder, codes)
    if is_molecule_input:
        # set a large kpoints_distance value to set the kpoints to 1x1x1
        builder.ch_scf.kpoints_distance = Float(5)
        builder.ch_scf.pw.settings = Dict(dict={'gamma_only': True})
    return builder


def update_inputs(inputs, ctx):
    """Update the inputs using context."""
    inputs.structure = ctx.current_structure


workchain_and_builder = {
    'workchain': XpsWorkChain,
    'exclude': ('structure', 'relax'),
    'get_builder': get_builder,
    'update_inputs': update_inputs,
}
