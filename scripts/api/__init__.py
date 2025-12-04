"""API clients package."""

from scripts.api.congress_api import (
    CongressAPIClient,
    BillType,
    Chamber,
    CongressEndpoints,
)

from scripts.api.openstates_api import (
    OpenStatesAPIClient,
    Jurisdiction,
    Classification,
    OpenStatesEndpoints,
)

from scripts.api.govinfo_api import (
    GovInfoAPIClient,
    Collection,
    DocClass,
    GovInfoEndpoints,
)

__all__ = [
    # Congress
    'CongressAPIClient',
    'BillType',
    'Chamber',
    'CongressEndpoints',

    # OpenStates
    'OpenStatesAPIClient',
    'Jurisdiction',
    'Classification',
    'OpenStatesEndpoints',

    # GovInfo
    'GovInfoAPIClient',
    'Collection',
    'DocClass',
    'GovInfoEndpoints',
]
