from dataclasses import dataclass, asdict
from typing import Union, Dict, List, Tuple
from biosimulators_utils.sedml.data_model import SedDocument, Model, Simulation


@dataclass
class ParameterTarget:
    prefix: str = None  # ie: "/sbml:sbml/sbml:model/sbml:listOfSpecies/sbml:species
    id: str = None  # found within [@id=''], for example 'Cdh1'
    _type: str = None  # found after id with an @, for example '@initialConcentration'

    def __init__(self, value: str):
        """Datamodel object for SEDML parameter URIs.

            Parameters:
                value:`str`: full URI from SEDML.
        """
        self.prefix, self.id, self._type = self.parse_uri(value)

    def parse_uri(self, val: str) -> Tuple[str, str, str]:
        parts = val.split('@')
        print(parts)
        prefix = parts[0].replace('[', '')
        param_id = parts[1].replace('id=', '').replace("'", "").replace(']/', '')
        _type = parts[-1]
        return prefix, param_id, _type


@dataclass
class ParameterValue:
    default: Union[int, float]
    new_value: Union[int, float] = None


@dataclass
class EditableSimulationParameter:
    target: Union[str, ParameterTarget]
    value: Union[ParameterValue, Dict[str, Union[float, int]]]
    name: str
    target_namespaces: Dict
    id: str

    def to_dict(self):
        return asdict(self)


class ChangedSedDocument(SedDocument):
    def __init__(self,
                 models: List[Model],
                 simulations: List[Simulation]):
        super().__init__(models=models, simulations=simulations)
