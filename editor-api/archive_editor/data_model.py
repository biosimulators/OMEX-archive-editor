from dataclasses import dataclass, asdict
from typing import Union, Dict


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
