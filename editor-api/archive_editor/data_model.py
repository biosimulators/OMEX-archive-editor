from dataclasses import dataclass, asdict, field
from pydantic import BaseModel as Base, create_model, ConfigDict, field_validator
from typing import Union, Dict, List, Tuple
from fastapi import HTTPException
from biosimulators_utils.combine.data_model import CombineArchive
from biosimulators_utils.sedml.data_model import SedDocument, Model, Simulation


class BaseModel(Base):
    model_config = ConfigDict(arbitrary_types_allowed=True)


def create_dynamic_class(model_name, model_base, **params) -> BaseModel:
    dynamic_config_types = {}
    for param_name, param_val in params.items():
        dynamic_config_types[param_name] = (type(param_val), ...)

    Dynamic = create_model(
        __model_name=model_name,
        __base__=model_base,
        **dynamic_config_types)

    # return edited_params
    return Dynamic(**params)


class EditedParametersBase(BaseModel):
    pass


class SerializedParametersBase(BaseModel):
    pass


class ResultConfirmation(BaseModel):
    message: str 
    
    
class UnsuccessfulSimulationEditConfirmation(ResultConfirmation):
    message: str = "Could not successfully edit the simulation"
    exception: Exception
    error: HTTPException
    
    @field_validator('error')
    @classmethod
    def raise_error(cls, error: HTTPException):
        return error(status_code=500, detail=str(cls.exception))
    
    
class SuccessfulSimulationEditConfirmation(BaseModel):
    message: str = "Simulation edited successfully."
    download_link: str


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
        prefix = parts[0].replace('[', '')
        param_id = parts[1].replace('id=', '').replace("'", "").replace(']/', '')
        _type = '@' + parts[-1]
        return prefix, param_id, _type

    def _add_marker(self, parts: List[str], marker: str) -> List[str]:
        for i, v in enumerate(parts):
            val = parts.pop()
            val += marker
            parts.insert(i, val)
        return parts


@dataclass
class ParameterValue:
    default: Union[int, float]
    new_value: Union[int, float] = None


@dataclass
class ParameterTag:
    tag_id: str
    tag_type: str


@dataclass
class _EditableSimulationParameter:
    target: Union[str, ParameterTarget]
    value: Union[ParameterValue, Dict[str, Union[float, int]]]
    name: str
    target_namespaces: Dict
    id: str
    tag: ParameterTag = None

    def __init__(self, target, value, name, target_namespaces, id):
        self.target = target
        self.value = value
        self.name = name
        self.target_namespaces = target_namespaces
        self.id = id

        if isinstance(self.target, str):
            self.target = ParameterTarget(value=self.target)

        self.tag = ParameterTag(self.target.id, self.target._type)

    def to_dict(self):
        return asdict(self)


@dataclass
class EditableSimulationParameter:
    target: Union[str, ParameterTarget]
    value: Union[ParameterValue, Dict[str, Union[float, int]]]
    name: str
    target_namespaces: Dict
    id: str

    def to_dict(self):
        return asdict(self)


@dataclass
class SimulationParameters:
    simulation: Simulation
    sim_model: Model
    model_source: str
    editable_parameters: List[EditableSimulationParameter]
    model_lang_urn: str = 'urn:sedml:language:sbml'

    def to_dict(self):
        return asdict(self)


class ChangedSedDocument(SedDocument):
    def __init__(self,
                 models: List[Model],
                 simulations: List[Simulation]):
        super().__init__(models=models, simulations=simulations)

    def serialize(self):
        return self.__dict__


class SimulationEditResult(BaseModel):
    archive: CombineArchive
    edited_sedml: ChangedSedDocument
    original_sedml: SedDocument
