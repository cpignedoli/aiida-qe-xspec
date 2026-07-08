"""XPS results view widgets"""

import ipywidgets as ipw
import plotly.graph_objects as go
from aiidalab_qe.common.panel import ResultsPanel
from aiidalab_qe.common.infobox import InAppGuide
from .model import XpsResultsModel
from weas_widget import WeasWidget
from table_widget import TableWidget


class XpsResultsPanel(ResultsPanel[XpsResultsModel]):
    experimental_data = None  # Placeholder for experimental data

    def _on_file_upload(self, change):
        self._model.upload_experimental_data(change['new'])

    def _render(self):
        self.result_table = TableWidget()
        self.result_table.observe(self._on_row_index_change, 'selectedRowId')
        self.table_help = ipw.HTML(
            """
            <div style='margin: 10px 0;'>
                <h4 style='margin-bottom: 5px; color: #3178C6;'>Result</h4>
                <p style='margin: 5px 0; font-size: 14px;'>
                    Click on the row to highlight the specific atom for the selected site.
                </p>
            </div>
            """,
            layout=ipw.Layout(margin='0 0 10px 0'),
        )
        spectra_type = ipw.ToggleButtons()
        ipw.dlink(
            (self._model, 'spectra_type_options'),
            (spectra_type, 'options'),
        )
        ipw.link(
            (self._model, 'spectra_type'),
            (spectra_type, 'value'),
        )
        spectra_type.observe(
            self._update_plot,
            'value',
        )

        gamma = ipw.FloatSlider(
            min=0.01,
            max=0.5,
            step=0.01,
            description=r'Lorentzian profile ($\gamma$)',
            style={'description_width': 'initial'},
        )
        ipw.link(
            (self._model, 'gamma'),
            (gamma, 'value'),
        )
        gamma.observe(
            self._update_plot,
            'value',
        )

        sigma = ipw.FloatSlider(
            min=0.01,
            max=0.5,
            step=0.01,
            description=r'Gaussian profile ($\sigma$)',
            style={'description_width': 'initial'},
        )
        ipw.link(
            (self._model, 'sigma'),
            (sigma, 'value'),
        )
        sigma.observe(
            self._update_plot,
            'value',
        )

        self.intensity = ipw.FloatText(
            min=0.001,
            description='Intensity factor',
            style={'description_width': 'initial'},
        )
        ipw.link(
            (self._model, 'intensity'),
            (self.intensity, 'value'),
        )
        self.intensity.observe(
            self._update_plot,
            'value',
        )

        fill = ipw.Checkbox(
            description='Fill',
            style={'description_width': 'initial'},
        )
        ipw.link(
            (self._model, 'fill'),
            (fill, 'value'),
        )
        fill.observe(
            self._update_plot,
            'value',
        )

        # Create a description label
        upload_description = ipw.HTML(
            value='Upload Experimental Data (<b>csv format, without header</b>):',
            placeholder='',
            description='',
        )

        # Create the upload button
        upload_btn = ipw.FileUpload(
            description='Choose File',
            multiple=False,
        )
        upload_btn.observe(
            self._on_file_upload,
            'value',
        )

        upload_container = ipw.VBox(
            children=[
                ipw.HBox([upload_description, upload_btn]),
            ],
        )

        parameters_container = ipw.HBox(
            children=[
                gamma,
                sigma,
                fill,
            ]
        )

        self.spectrum_select = ipw.Dropdown(
            description='',
            disabled=False,
            layout=ipw.Layout(width='20%'),
        )
        ipw.dlink(
            (self._model, 'spectrum_options'),
            (self.spectrum_select, 'options'),
        )
        ipw.link(
            (self._model, 'spectrum'),
            (self.spectrum_select, 'value'),
        )
        self.spectrum_select.observe(
            self._update_plot,
            'value',
        )

        self.plot = go.FigureWidget(
            layout=go.Layout(
                title={'text': 'XPS'},
                barmode='overlay',
            )
        )
        self.plot.layout.xaxis.title = 'Chemical shift (eV)'
        self.plot.layout.xaxis.autorange = 'reversed'

        gui_config = {
            'components': {'enabled': True, 'atomsControl': True, 'buttons': True},
            'buttons': {
                'enabled': True,
                'fullscreen': True,
                'download': True,
                'measurement': True,
            },
        }

        self.structure_view = WeasWidget(
            guiConfig=gui_config, viewerStyle={'width': '100%', 'height': '400px'}
        )

        self.results_container.children = [
            InAppGuide(identifier='xps-container-results'),
            spectra_type,
            ipw.HBox(
                children=[
                    ipw.HTML(
                        """
                        <div style="line-height: 140%; padding-top: 10px; padding-right: 10px; padding-bottom: 0px;">
                            <b>Select spectrum to plot</b>
                        </div>
                    """
                    ),
                    self.spectrum_select,
                ]
            ),
            ipw.HTML(
                """
                <div style="line-height: 140%; padding-top: 10px; padding-bottom: 10px">
                    Set the <a href="https://en.wikipedia.org/wiki/Voigt_profile" target="_blank">Voigt profile</a> to broaden the XPS spectra:
                </div>
            """
            ),
            parameters_container,
            self.intensity,
            upload_container,
            self.plot,
            ipw.HBox(
            children=[
                ipw.VBox(
                    [self.table_help, self.result_table],
                    layout=ipw.Layout(width='50%', margin='0 10px 0 0'),
                ),
                ipw.VBox(
                    [self.structure_view],
                    layout=ipw.Layout(width='50%'),
                ),
            ],
            layout=ipw.Layout(justify_content='space-between', margin='10px'),
        )
        ]
        self.rendered = True
        self._post_render()
        self._update_plot(None)

    def _post_render(self):
        self._model.update_spectrum_options()
        self._populate_table()
        self._setup_structure_view()

    def _on_spectrum_select_change(self, change):
        self._update_plot(change)
        self._populate_table()

    def _update_plot(self, _):
        if not self.rendered:
            return

        data, x_axis_label, fill_type = self._model.get_data()

        with self.plot.batch_update():
            if len(self.plot.data) == len(data):
                for i in range(len(data)):
                    self.plot.data[i].x = data[i]['x']
                    self.plot.data[i].y = data[i]['y']
                    self.plot.data[i].fill = fill_type
                    self.plot.data[i].name = data[i]['site'].replace('_', ' ')

            else:
                self.plot.data = []
                for d in data:
                    self.plot.add_scatter(
                        x=d['x'],
                        y=d['y'],
                        fill=fill_type,
                        name=d['site'],
                    )

            self.plot.layout.barmode = 'overlay'
            self.plot.layout.xaxis.title = x_axis_label

        self._plot_experimental_data()

    def _plot_experimental_data(self):
        """Plot the experimental data alongside the calculated data."""
        if not self.rendered:
            return
        if self._model.experimental_data is not None:
            x = self._model.experimental_data[0]
            y = self._model.experimental_data[1]
            self.plot.add_scatter(x=x, y=y, mode='lines', name='Experimental Data')

    def _populate_table(self):
        columns = [
            {'field': 'site_index', 'headerName': 'Site', 'editable': False},
            {'field': 'element', 'headerName': 'Symbol', 'editable': False},
            {
                'field': 'chemical_shift',
                'headerName': 'Chemical shift (eV)',
                'editable': False,
            },
            {'field': 'binding_energy', 'headerName': 'Binding energy (eV)', 'editable': False},
        ]
        data = []

        element, orbital = self.spectrum_select.value.split('_')

        for key, value in self._model.binding_energies[element][orbital].items():
            atom_index = int(key.split('_')[-1])
            data.append(
                {
                    'site_index': atom_index + 1,
                    'atom_index': atom_index,
                    'element': element,
                    'chemical_shift': round(self._model.chemical_shifts[element][orbital][key]['energy'], 2),
                    'binding_energy': round(value['energy'], 2),
                }
            )

        self.result_table.from_data(
            data,
            columns=columns,
        )

    def _setup_structure_view(self):
        if self._model.structure:
            ase_atoms = self._model.structure.get_ase()
            self.structure_view.from_ase(ase_atoms)

    def _on_row_index_change(self, change):
        if change['new'] is not None:
            row_index = int(change['new'])
            atom_index = self.result_table.data[row_index]['atom_index']
            self.structure_view.avr.selected_atoms_indices = [atom_index]
