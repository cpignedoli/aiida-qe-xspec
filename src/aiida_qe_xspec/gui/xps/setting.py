"""Panel for XPS plugin."""

import ipywidgets as ipw
from aiidalab_qe.common.panel import ConfigurationSettingsPanel
from aiidalab_qe.common.infobox import InAppGuide
from .model import BASE_URL, XpsConfigurationSettingsModel


class XpsConfigurationSettingsPanel(
    ConfigurationSettingsPanel[XpsConfigurationSettingsModel],
):
    def __init__(self, model: XpsConfigurationSettingsModel, **kwargs):
        super().__init__(model, **kwargs)

        self._model.observe(
            self._on_input_structure_change,
            'structure_uuid',
        )
        self._model.observe(
            self._on_functional_change,
            'functional',
        )
        self._model.observe(
            self._on_pseudo_group_change,
            'pseudo_group',
        )

    def render(self):
        if self.rendered:
            return

        self.core_hole_treatment = ipw.ToggleButtons()
        ipw.dlink(
            (self._model, 'core_hole_treatment_options'),
            (self.core_hole_treatment, 'options'),
        )
        ipw.link(
            (self._model, 'core_hole_treatment'),
            (self.core_hole_treatment, 'value'),
        )

        self.pseudo_group = ipw.Dropdown(
            description='Group:',
            style={'description_width': 'initial'},
        )
        ipw.dlink(
            (self._model, 'pseudo_group_options'),
            (self.pseudo_group, 'options'),
        )
        ipw.link(
            (self._model, 'pseudo_group'),
            (self.pseudo_group, 'value'),
        )
        # Selection mode toggle: choose between core-level and atom indices
        self.selection_mode = ipw.ToggleButtons(
            options=['Core-level', 'Atom indices'],
            description='Select by:',
            style={'description_width': 'initial'},
        )
        self.selection_mode.observe(self._on_selection_mode_change, names='value')

        self.core_levels_widget = ipw.VBox()
        self.atom_indices_input = ipw.Text(
            description='Indices:',
            placeholder='Enter indices separated by commas',
            style={'description_width': 'initial'},
        )
        ipw.link(
            (self._model, 'atom_indices'),
            (self.atom_indices_input, 'value'),
            [
                lambda value: ', '.join(str(index) for index in value),
                lambda value: [int(i.strip()) for i in value.split(',') if i.strip()],
            ],
        )
        self.core_levels_container = ipw.VBox(
            children=[
                ipw.HTML(
                    """
                <div style="line-height: 140%;">
                    The list of core-levels to be considered for analysis.
                </div>
            """
                ),
                self.core_levels_widget,
            ]
        )
        self.atom_indices_container = ipw.VBox(
            children=[
                ipw.HTML("""
                     <div style="margin-top: 10px;">
                     Input the indices of atoms to be considered for analysis.
                </div>
                """),
                self.atom_indices_input,
            ]
        )

        self.structure_type = ipw.ToggleButtons()
        ipw.dlink(
            (self._model, 'structure_type_options'),
            (self.structure_type, 'options'),
        )
        ipw.link(
            (self._model, 'structure_type'),
            (self.structure_type, 'value'),
        )

        self.supercell_min_parameter = ipw.FloatText(
            description='The minimum cell length (Å):',
            disabled=False,
            style={'description_width': 'initial'},
        )
        ipw.link(
            (self._model, 'supercell_min_parameter'),
            (self.supercell_min_parameter, 'value'),
        )

        self.calc_binding_energy = ipw.Checkbox(
            description='Calculate binding energy: ',
            indent=False,
        )
        ipw.link(
            (self._model, 'calc_binding_energy'),
            (self.calc_binding_energy, 'value'),
        )
        self.band_gap_correction = ipw.FloatText(
            description='The band gap correction for insulator (eV):',
            disabled=False,
            style={'description_width': 'initial'},
        )
        ipw.link(
            (self._model, 'band_gap_correction'),
            (self.band_gap_correction, 'value'),
        )

        self.children = [
            InAppGuide(identifier='xps-settings'),
            ipw.HTML('<h4>Structure</h4>'),
            ipw.HTML(
                """
                <div style="line-height: 140%; margin-bottom: 10px">
                    Below you can indicate if the material should be treated as a
                    molecule or a solid.
                </div>
            """
            ),
            ipw.HBox(
                children=[
                    self.structure_type,
                ]
            ),
            ipw.HTML(
                """
                <div style="margin-top: 15px;">
                    <h4>Core-Hole pseudopotential group</h4>
                </div>
            """
            ),
            ipw.HTML(
                f"""
                <div style="line-height: 140%; margin-bottom: 10px">
                    Please select a pseudopotential group, which provide the
                    ground-state and excited-state pseudopotentials for the element.
                    The pseudopotentials are downloaded from this <a href="{BASE_URL}">
                    repository</a>.
                </div>
            """
            ),
            self.pseudo_group,
            ipw.HTML("""
                <div style='margin-top: 15px;'>
                    <h4>Select mode</h4>
                </div>
            """),
            ipw.HTML("""
                <div style='line-height: 140%; margin-bottom: 10px'>
                    You have two options:
                    <ul style='margin-top: 5px;'>
                        <li><b>Core-level</b>: select by element and orbital (typical for simple, symmetric systems).</li>
                        <li><b>Atom indices</b>: select specific atoms by index (useful for large or low-symmetry systems, e.g., surfaces or supported nanoparticles).</li>
                    </ul>
                </div>
            """),
            self.selection_mode,
            ipw.VBox(
                children=[
                    self.core_levels_container,
                    self.atom_indices_container,
                ]
            ),
            ipw.HTML(
                f"""
                <div style="line-height: 140%; margin-bottom: 10px">
                    <h4>Band gap correction</h4>
                    For insulators, XCH binding energies need to be corrected by subtracting <b>half of the band gap</b>.<br>
                    Please enter the value of the band gap here. It can be:<br>
                    - An <i>experimental</i> band gap (e.g. from literature), or<br>
                    - A <i>theoretical</i> band gap obtained from a separate calculation (e.g. using this app).<br>
                </div>
            """
            ),
            self.band_gap_correction,
        ]

        # Initial build and visibility
        self._on_selection_mode_change({'new': self.selection_mode.value})
        self.rendered = True

        self.refresh(specific='widgets')

    def _on_input_structure_change(self, _):
        self.refresh(specific='structure')

    def _on_functional_change(self, _):
        self.refresh(specific='functional')

    def _on_pseudo_group_change(self, _):
        self.refresh(specific='pseudo_group')

    def _on_selection_mode_change(self, change):
        mode = change.get('new', self.selection_mode.value)
        # Show only the selected widget
        if mode == 'Core-level':
            self.core_levels_container.layout.display = None
            self.atom_indices_container.layout.display = 'none'
        else:
            self.core_levels_container.layout.display = 'none'
            self.atom_indices_container.layout.display = None

    def _update_ui(self):
        self._show_loading()
        self._build_core_levels_widget()

    def _show_loading(self):
        if self.rendered:
            self.core_levels_widget.children = [self.loading_message]

    def _build_core_levels_widget(self):
        if not self.rendered:
            return

        children = []
        elements = self._model.input_structure.get_symbols_set()
        supported_core_levels = self._model.get_supported_core_levels()

        for element in elements:
            if element in supported_core_levels:
                for orbital in supported_core_levels[element]:
                    checkbox = ipw.Checkbox(
                        description=f'{element}_{orbital}',
                        indent=False,
                        layout=ipw.Layout(max_width='100%'),
                    )

                    def get_checked(levels, kind=element, orb=orbital):
                        return orb in levels.get(kind, [])

                    def set_checked(value, kind=element, orb=orbital):
                        updated_levels = self._model.core_levels.copy()
                        if value:
                            updated_levels.setdefault(kind, []).append(orb)
                        else:
                            updated_levels[kind] = [o for o in updated_levels.get(kind, []) if o != orb]
                            if not updated_levels[kind]:
                                del updated_levels[kind]
                        return updated_levels

                    link = ipw.link(
                        (self._model, 'core_levels'),
                        (checkbox, 'value'),
                        [get_checked, set_checked],
                    )
                    self._links.append(link)
                    children.append(checkbox)
            else:
                checkbox = ipw.Checkbox(
                    description=f'{element}, not supported by the selected pseudo group',
                    indent=False,
                    disabled=True,
                    value=False,
                    style={'description_width': 'initial'},
                    layout=ipw.Layout(max_width='100%'),
                )
                children.append(checkbox)

        self.core_levels_widget.children = children
