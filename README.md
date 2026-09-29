# AiiDA QE Xspec

## Overview

AiiDA QE Xspec is an AiiDA plugin designed for core-level spectroscopy calculations using Quantum ESPRESSO. It provides workflows for X-ray Absorption Spectroscopy (XAS) and X-ray Photoelectron Spectroscopy (XPS), enabling automated and reproducible calculations within the AiiDA framework.

## Features

- **X-ray Absorption Spectroscopy (XAS)** using the `XSpectra` module of Quantum ESPRESSO.
- **X-ray Photoelectron Spectroscopy (XPS)** calculations via the `XpsWorkChain`.
- **Integration with AiiDAlab**, providing a user-friendly interface for spectroscopy simulations.
- **FAIR data principles** with provenance tracking via AiiDA.

## Installation

To install AiiDA QE Xspec, ensure you have AiiDA and Quantum ESPRESSO set up, then run:

```bash
pip install aiida-qe-xspec
```

## Compatibility

The `0.3.x` maintenance line supports AiiDA Core `>=2.6,<2.8`, AiiDA Quantum ESPRESSO `4.12.1`, and Python `>=3.9`. Use the `main` branch for AiiDA Core 2.8 and AiiDA Quantum ESPRESSO 5.

## Usage
Please refer to the [documentation](https://aiida-qe-xspec.readthedocs.io) for detailed instructions on how to use AiiDA QE Xspec.

## Citing AiiDA QE Xspec

If you use AiiDA QE Xspec in your research, please cite the following resources:

- [Cite AiiDA](https://aiida.readthedocs.io/projects/aiida-core/en/latest/#how-to-cite)
- [Cite AiiDAlab](https://aiidalab.readthedocs.io/en/latest/index.html#how-to-cite)
- [Cite Quantum ESPRESSO](https://www.quantum-espresso.org/Doc/user_guide/node6.html)

If you use the AiiDAlab QE app in your research, please cite:

<div style="padding: 6px 20px 0;">
  Wang, X., Bainglass, E., Bonacci, M., Ortega-Guerrero, A. et al.<br />
  Making atomistic materials calculations accessible with the AiiDAlab Quantum ESPRESSO app<br />
  <em>npj. Comput. Mater.</em> <b>12</b>, 72 (2026). <a href="https://doi.org/10.1038/s41524-025-01936-4" target="_blank">https://doi.org/10.1038/s41524-025-01936-4</a>
</div>

## Acknowledgements

We acknowledge support from:

- [BIG-MAP project](https://www.big-map.eu) (Horizon 2020 Grant No. 957189)
- [MARVEL National Centre for Competency in Research](http://nccr-marvel.ch) (Swiss National Science Foundation)
- [MARKETPLACE project](https://www.the-marketplace-project.eu/) (Horizon 2020 Grant No. 760173)
- [MaX European Centre of Excellence](http://www.max-centre.eu/) (Horizon 2020 EINFRA-5 Grant No. 676598)
- [DOME 4.0 project](https://dome40.eu/) (Horizon 2020 Grant No. 953163)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
