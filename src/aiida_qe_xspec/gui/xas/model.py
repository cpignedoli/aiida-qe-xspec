from importlib import resources
from pathlib import Path

import traitlets as tl
import yaml

from aiidalab_qe.common.mixins import HasInputStructure
from aiidalab_qe.common.panel import PanelModel
from aiida_qe_xspec.gui import xas as xas_folder


class XasConfigurationSettingsModel(PanelModel, HasInputStructure):
    title = 'XAS'
    identifier = 'xas'

    dependencies = [
        'structure_uuid',
        'advanced.pseudos.functional',
    ]

    # structure_type_options = tl.List(
    #     trait=tl.List(tl.Unicode(), tl.Unicode()),
    #     default_value=[
    #         ["Molecule", "molecule"],
    #         ["Crystal", "crystal"],
    #     ],
    # )
    # structure_type = tl.Unicode("crystal")

    supercell_min_parameter = tl.Float(8.0)

    functional = tl.Unicode(allow_none=True)
    pseudo_group = tl.Unicode('xas_pbe')

    kind_names = tl.Dict(
        key_trait=tl.Unicode(),  # kind name
        value_trait=tl.Bool(),  # whether the element is included
    )
    core_hole_treatments_options = tl.List(
        trait=tl.List(tl.Unicode()),
        default_value=[
            ['Full', 'full'],
            ['Excited', 'excited'],
        ],
    )
    core_hole_treatments = tl.Dict(
        key_trait=tl.Unicode(),  # kind name
        value_trait=tl.Unicode(),  # core hole treatment type
        default_value={},
    )
    pseudo_group_options = tl.List(
        trait=tl.Unicode(),
        default_value=[
            'xas_pbe',
        ],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _update(self, specific=''):
        with self.hold_trait_notifications():
            self._update_pseudo_data_dict()
            self._update_core_hole_treatment_recommendations()

    def get_model_state(self):
        pseudo_labels = {}
        core_wfc_data_labels = {}
        for element, is_selected in self.kind_names.items():
            if is_selected:
                pseudo_labels[element] = {
                    'gipaw': self.gipaw_pseudos[element],
                    'core_hole': self.core_hole_pseudos[element],
                }
                core_wfc_data_labels[element] = self.core_wfc_data_dict[element]
            else:
                self.core_hole_treatments.pop(element)

        elements_list = [key for key in self.kind_names if self.kind_names[key]]

        return {
            # "structure_type": self.structure_type,
            'elements_list': elements_list,
            'core_hole_treatments': self.core_hole_treatments,
            'pseudo_labels': pseudo_labels,
            'core_wfc_data_labels': core_wfc_data_labels,
            'supercell_min_parameter': self.supercell_min_parameter,
        }

    def set_model_state(self, parameters: dict):
        self.kind_names = {
            kind_name: kind_name in parameters['elements_list']
            for kind_name in self.kind_names
        }

        self.core_hole_treatments = {
            kind_name: parameters['core_hole_treatments'].get(kind_name, 'full')
            for kind_name in self.kind_names
        }

        self.supercell_min_parameter = parameters.get('supercell_min_parameter', 8.0)
        # self.structure_type = parameters.get("structure_type", "crystal")

    def get_kind_names(self):
        return list(self.kind_names)

    def get_recommendation(self, element):
        return 'excited' if element in self.xch_elements else 'full'

    def reset(self):
        with self.hold_trait_notifications():
            self.supercell_min_parameter = self.traits()[
                'supercell_min_parameter'
            ].default_value
            # self.structure_type = self.traits()["structure_type"].default_value

    def _update_pseudo_data_dict(self):
        base_data_folder = Path.home().joinpath('.aiidalab', 'aiida-qe-xspec', 'data', 'xas')
        with open(base_data_folder.joinpath('data.yaml'), 'r') as f:
            data = yaml.safe_load(f)
            self.pseudo_data_dict = data['pseudos']
            self.xch_elements = data['xas_xch_elements']
            self.gipaw_pseudos = self.pseudo_data_dict['pbe']['gipaw_pseudos']
            self.core_hole_pseudos = self.pseudo_data_dict['pbe']['core_hole_pseudos']['1s']
            self.core_wfc_data_dict = self.pseudo_data_dict['pbe']['core_wavefunction_data']

    def _update_core_hole_treatment_recommendations(self):
        if not self.has_structure:
            self.kind_names = {}
            self.core_hole_treatments = {}
        else:
            self.kind_names = {
                kind_name: self.kind_names.get(kind_name, False)
                for kind_name in self.input_structure.get_kind_names()
                if kind_name in self.core_hole_pseudos
            }
            self.core_hole_treatments = {
                kind_name: self.get_recommendation(kind_name)
                for kind_name in self.kind_names
            }

    def _check_blockers(self):
        functional = str(self.functional).lower()
        pseudo_group = str(self.pseudo_group).split('_')[1]
        if functional != pseudo_group:
            yield (
                f'The selected functional "{functional}" is not compatible with '
                f'the functional "{pseudo_group}" required for XAS.'
            )
