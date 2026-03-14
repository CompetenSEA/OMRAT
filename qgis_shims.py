"""QGIS / PyQt5 headless shims.

Call ``install()`` before importing any OMRAT module that depends on QGIS or
PyQt5.  Every QGIS symbol becomes a :class:`unittest.mock.MagicMock` so the
compute layer can be imported and executed without a QGIS installation.

Usage::

    import qgis_shims
    qgis_shims.install()

    # Now safe to import OMRAT compute modules
    from compute.run_calculations import Calculation
    from compute.data_preparation import clean_traffic, load_areas
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# All namespaces that OMRAT modules import from.
# The list is complete as of OMRAT v0.4.x; add entries here when new QGIS
# imports appear in the plugin source.
# ---------------------------------------------------------------------------
_QGIS_NAMESPACES: list[str] = [
    # Top-level qgis package
    "qgis",
    # Private C-extension that QgsVectorDataProvider lives in
    "qgis._core",
    # Public API modules
    "qgis.core",
    "qgis.gui",
    # PyQt re-exported through qgis.PyQt
    "qgis.PyQt",
    "qgis.PyQt.QtCore",
    "qgis.PyQt.QtGui",
    "qgis.PyQt.QtWidgets",
    "qgis.PyQt.QtNetwork",
    "qgis.PyQt.QtXml",
    # Stand-alone PyQt5 (some OMRAT helpers import directly)
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "PyQt5.QtNetwork",
    "PyQt5.QtXml",
    # PyQt6 (forward-compat; plugin metadata says Qt6 is supported)
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    # matplotlib Qt backends — imported by geometries/get_drifting_overlap.py
    # and geometries/get_powered_overlap.py for the visualisation widgets.
    # The headless runner does not render, so mock them out entirely.
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.qt_compat",
    # OMRAT UI widgets — depend on Qt and .ui file loading via uic.loadUiType().
    # In headless mode all UI classes are stubs; the compute layer never calls them.
    "ui",
    "ui.show_geom_res",
    "ui.ais_connection_widget",
    "ui.causation_factor_widget",
    "ui.drift_settings_widget",
    "ui.result_widget",
    "ui.ship_categories_widget",
    "ui.traffic_data_widget",
]

_installed: bool = False


def install() -> None:
    """Register MagicMock stubs for every QGIS / PyQt namespace.

    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _installed
    if _installed:
        return

    for mod_name in _QGIS_NAMESPACES:
        if mod_name not in sys.modules:
            mock = MagicMock(name=mod_name)
            # Make child attribute access return a new MagicMock (default
            # behaviour), but also make the mock callable so that
            # ``QgsProject.instance()`` returns a usable object.
            sys.modules[mod_name] = mock

    # Patch QgsProject.instance() to return a MagicMock with a real
    # transformContext() (needed by data_preparation.transform_to_utm before
    # the pyproj patch is applied).
    _qgs_project = sys.modules.get("qgis.core")
    if _qgs_project is not None:
        instance_mock = MagicMock()
        instance_mock.transformContext.return_value = MagicMock()
        _qgs_project.QgsProject.instance.return_value = instance_mock

    _installed = True


def is_installed() -> bool:
    """Return True if the shims have been installed."""
    return _installed
