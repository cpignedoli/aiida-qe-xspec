# -*- coding: utf-8 -*-
"""Utility to generate suitable inputs for a PwCalculation based on a given core-hole treatment setting.

Returns a `dict` object with suitable inputs for a subsequent PwCalculation
"""
from aiida.common import ValidationError


# pylint: disable=too-many-statements
def _process_afm_system(**kwargs):
    """Set the magnetic structure correctly for the system with the core-hole present."""
    structure = kwargs.get('structure')
    starting_mag = kwargs.get('starting_mag')
    tot_mag = kwargs.get('tot_mag')
    abs_atom_marker = kwargs.get('abs_atom_marker', 'X')
    abs_atom_kind = kwargs.get('abs_atom_kind')
    site_index = kwargs.get('site_index')
    treatment = kwargs.get('treatment')
    final_starting_mag = starting_mag.copy()

    # first, figure out which site index we need, if not given
    if not site_index:
        for index, site in enumerate(structure.sites):
            if site.kind_name == abs_atom_marker:
                site_index = index
                break
    else:
        site_index = site_index

    target_site_mag = starting_mag[abs_atom_kind]

    final_starting_mag[abs_atom_marker] = target_site_mag
    if treatment not in ['full', 'FCH'] and tot_mag is not None:
        if target_site_mag >= 0:
            tot_mag += 1
        else:
            tot_mag -= 1

    return final_starting_mag, tot_mag

def _check_for_abs_kind(structure, abs_atom_marker):
    """Check the `Site`s in the structure to confirm that the `abs_atom_marker` is present."""
    abs_atom_found = False
    for site in structure.sites:
        if site.kind_name == abs_atom_marker:
            abs_atom_found = True

    return abs_atom_found

def get_core_hole_inputs(structure, treatment, parameters, abs_site_data, **kwargs):
    """Generate PwCalculation input parameters based on a given core-hole treatment type."""

    abs_atom_marker = kwargs.get('abs_atom_marker', 'X')
    site_index = abs_site_data['site_index']
    abs_atom_kind = abs_site_data.get('kind_name', abs_site_data['symbol'])
    updated_parameters = parameters.copy()
    updated_parameters['SYSTEM'] = parameters['SYSTEM'].copy()
    starting_mag = updated_parameters['SYSTEM'].get('starting_magnetization', None)
    if starting_mag is not None:
        starting_mag = starting_mag.copy()
        updated_parameters['SYSTEM']['starting_magnetization'] = starting_mag
    tot_mag = updated_parameters['SYSTEM'].get('tot_magnetization', None)
    if not starting_mag and tot_mag is None and updated_parameters['SYSTEM'].get('nspin', None) == 2:
        raise ValidationError(
            'A spin-polarised calculation was requested, but neither starting nor total magnetization was provided.'
        )
    tot_charge = updated_parameters['SYSTEM'].get('tot_charge', 0)
    afm_inputs = {
        'structure': structure,
        'starting_mag': starting_mag,
        'tot_mag': tot_mag,
        'abs_atom_marker': abs_atom_marker,
        'site_index': site_index,
        'abs_atom_kind' : abs_atom_kind,
        'treatment': treatment
    }

    if not _check_for_abs_kind(structure, abs_atom_marker):
        raise ValidationError(
            f'The Kind for the absorbing atom {abs_atom_marker} was not found in the structure. '
            f'Kinds found: {structure.get_kind_names()}'
        )
    valid_treatments = ['FCH', 'HCH', 'XCH', 'full', 'half', 'excited']
    if treatment not in valid_treatments:
        if treatment == 'none':
            raise NotImplementedError(
                'Treatment option "none" should not be used. If no core-hole treatment is required, '
                'then this function should not be called.'
            )
        else:
            raise ValidationError(
                f'The selected treatment option "{treatment}" is not valid. '
                f'Valid treatment options are:\n{valid_treatments}.'
            )

    if starting_mag:
        # check for both negative and positive numbers (i.e. is the system FM or AFM?)
        positive_mag = False
        negative_mag = False
        for value in starting_mag.values():
            if value > 0:
                positive_mag = True
            elif value < 0:
                negative_mag = True
            if positive_mag and negative_mag:
                break
        system_afm = positive_mag and negative_mag
    else:
        system_afm = False

    if treatment in ['FCH', 'full']:
        tot_charge += 1
        if starting_mag:
            if system_afm:
                starting_mag, tot_mag = _process_afm_system(**afm_inputs)
            else:
                starting_mag[abs_atom_marker] = starting_mag[abs_atom_kind]
    elif treatment in ['HCH', 'half']:
        tot_charge += 0.5
        if starting_mag:
            starting_mag[abs_atom_marker] = starting_mag[abs_atom_kind]
    # elif treatment in ['XCH', 'xch_fixed', 'xch_smear']:
    elif treatment in ['XCH', 'excited']:
        if system_afm:
            starting_mag, tot_mag = _process_afm_system(**afm_inputs)
        elif updated_parameters['SYSTEM'].get('nspin') == 2:
            if starting_mag:
                starting_mag[abs_atom_marker] = 1
            if tot_mag is not None:
                tot_mag += 1
        else:
            starting_mag = {abs_atom_marker: 1}
            updated_parameters['SYSTEM']['nspin'] = 2
            if updated_parameters['SYSTEM'].get('occupations', None) == 'fixed':
                if tot_mag is not None:
                    tot_mag += 1
                else:
                    tot_mag = 1

    updated_parameters['SYSTEM']['tot_charge'] = tot_charge
    if updated_parameters['SYSTEM'].get('nspin') == 2 and starting_mag:
        structure_kind_names = structure.get_kind_names()
        starting_mag = {
            kind: value for kind, value in starting_mag.items()
            if kind in structure_kind_names
        }
        for kind in structure_kind_names:
            if kind not in starting_mag:
                starting_mag[kind] = 0
        updated_parameters['SYSTEM']['starting_magnetization'] = starting_mag
    if tot_mag is not None:
        updated_parameters['SYSTEM']['tot_magnetization'] = tot_mag

    return updated_parameters
