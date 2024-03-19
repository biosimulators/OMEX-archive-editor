from dataclasses import dataclass, asdict
from typing import Union, Dict, List
from biosimulators_utils.sedml.data_model import SedDocument, Model, Simulation


@dataclass
class ParameterValue:
    default: Union[int, float]
    new_value: Union[int, float] = None


@dataclass
class EditableSimulationParameter:
    target: str
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
