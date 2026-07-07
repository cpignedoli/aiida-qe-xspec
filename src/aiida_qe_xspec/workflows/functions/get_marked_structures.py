"""CalcFunction to create structures with a marked atom for each site in a list."""
from aiida import orm
from aiida.common import ValidationError
from aiida.engine import calcfunction
from aiida.orm.nodes.data.structure import Kind, Site, StructureData


@calcfunction
def get_marked_structures(structure, atom_indices, marker='X'):
    """Read a StructureData object and return structures for XPS calculations.

    :param atom_indices:  the indices of atoms to be marked.
    :param marker: a Str node defining the name of the marked atom Kind. Default is 'X'.
    :returns: StructureData objects for the generated structure.
    """
    marker = marker.value
    elements_present = [kind.symbol for kind in structure.kinds]
    if marker in elements_present:
        raise ValidationError(
            f'The marker ("{marker}") should not match an existing Kind in ' f'the input structure ({elements_present}.'
        )

    output_params = {}
    result = {}

    for index in atom_indices.get_list():
        marked_structure = StructureData()
        kinds = {kind.name: kind for kind in structure.kinds}
        marked_structure.set_cell(structure.cell)

        for i, site in enumerate(structure.sites):
            if i == index:
                site_kind = kinds[site.kind_name]
                marked_kind = Kind(name=marker, symbols=site_kind.symbol)
                marked_site = Site(kind_name=marked_kind.name, position=site.position)
                marked_structure.append_kind(marked_kind)
                marked_structure.append_site(marked_site)
                output_params[f'site_{index}'] = {
                    'kind_name': site.kind_name,
                    'symbol': site_kind.symbol,
                    'site_index': index,
                    'multiplicity': 1,
                    'equivalent_sites_list': [index],
                }
            else:
                if site.kind_name not in [kind.name for kind in marked_structure.kinds]:
                    marked_structure.append_kind(kinds[site.kind_name])
                new_site = Site(kind_name=site.kind_name, position=site.position)
                marked_structure.append_site(new_site)
        result[f'site_{index}'] = marked_structure

    result['output_parameters'] = orm.Dict(dict=output_params)

    return result
