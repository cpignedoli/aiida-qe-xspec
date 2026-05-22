import traitlets as tl
from aiida.common import NotExistent
from aiida.orm import load_group
from aiidalab_qe.common.mixins import HasInputStructure
from aiidalab_qe.common.panel import PanelModel

BASE_URL = 'https://github.com/superstar54/xps-data/raw/main/pseudo_demo/'


class XpsConfigurationSettingsModel(PanelModel, HasInputStructure):
    title = 'XPS'
    identifier = 'xps'

    dependencies = [
        'structure_uuid',
    ]

    core_hole_treatment_options = tl.List(
        trait=tl.List(tl.Unicode()),
        default_value=[
            ['Excited', 'excited'],
            ['Full', 'full'],
        ],
    )
    core_hole_treatment = tl.Unicode('excited')
    pseudo_group_options = tl.List(
        trait=tl.Unicode(),
        default_value=[
            'xps_pbe',
            'xps_pbesol',
        ],
    )
    pseudo_group = tl.Unicode('xps_pbe')
    structure_type_options = tl.List(
        trait=tl.List(tl.Unicode()),
        default_value=[
            ['Molecule', 'molecule'],
            ['Solid', 'solid'],
        ],
    )
    structure_type = tl.Unicode('solid')
    supercell_min_parameter = tl.Float(8.0)
    calc_binding_energy = tl.Bool(False)
    correction_energies = tl.Dict(
        key_trait=tl.Unicode(),  # <element>_<orbital>
        value_trait=tl.Dict(
            key_trait=tl.Unicode(),
            value_trait=tl.Float(),
        ),
        default_value={},
    )
    core_levels = tl.Dict(
        key_trait=tl.Unicode(),  # core level
        value_trait=tl.List(),
        default_value={},
    )
    atom_indices = tl.List(trait=tl.Int(), default_value=[])
    band_gap_correction = tl.Float(0.0)

    def _update(self, specific=''):
        with self.hold_trait_notifications():
            self._update_correction_energies()

    def get_supported_core_levels(self):
        supported_core_levels = {}
        for key in self.correction_energies:
            element = key.split('_')[0]
            if element not in supported_core_levels:
                supported_core_levels[element] = [key.split('_')[1]]
            else:
                supported_core_levels[element].append(key.split('_')[1])
        return supported_core_levels

    def get_model_state(self):
        return {
            # "core_hole_treatment": self.core_hole_treatment,
            'structure_type': self.structure_type,
            'pseudo_group': self.pseudo_group,
            'correction_energies': self.correction_energies,
            'core_levels': self.core_levels,
            'atom_indices': self.atom_indices,
            'band_gap_correction': self.band_gap_correction,
        }

    def set_model_state(self, parameters: dict):
        self.pseudo_group = parameters.get(
            'pseudo_group',
            self.traits()['pseudo_group'].default_value,
        )
        self.structure_type = parameters.get(
            'structure_type',
            self.traits()['structure_type'].default_value,
        )

        self.core_levels = parameters.get('core_levels', [])
        self.atom_indices = parameters.get('atom_indices', [])

    def reset(self):
        with self.hold_trait_notifications():
            for key in [
                'core_hole_treatment',
                'pseudo_group',
                'structure_type',
                'supercell_min_parameter',
                'calc_binding_energy',
            ]:
                setattr(self, key, self.traits()[key].default_value)

    def _update_correction_energies(self):
        try:
            group = load_group(self.pseudo_group)
            self.correction_energies = group.base.extras.get('correction')
        except NotExistent:
            self.correction_energies = {}
            # TODO What if the group does not exist? Should we proceed? Can this happen?
