# API source
import os
import tempfile
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Union
from process_bigraph import pp
from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent
from biosimulators_utils.combine.io import CombineArchiveWriter, CombineArchiveReader
from biosimulators_utils.sedml.io import SedmlSimulationReader, SedmlSimulationWriter
from biosimulators_utils.sedml.utils import get_all_sed_objects  # change this
from biosimulators_utils.sedml.model_utils import get_parameters_variables_outputs_for_simulation
from biosimulators_utils.sedml.data_model import *
from archive_editor.data_model import EditableSimulationParameter, ParameterValue


# exec
class ArchiveEditorApi:
    @classmethod
    def upload_archive(cls):
        from google.colab import files
        return files.upload()

    @classmethod
    def get_uploaded_omex_fp(cls, root: str) -> str:
        """Get content from colab env"""
        fpaths = []
        for f in os.listdir(root):
            if '.omex' in f:
                fpaths.append(f)
        # if len(fpaths) > 1:
        #     raise OSError('You can only edit one omex archive at a time.')
        # else:
        return fpaths[0]

    @classmethod
    def read_omex(cls, omex_fp: str, out_dir: str) -> CombineArchive:
        return CombineArchiveReader().run(in_file=omex_fp, out_dir=out_dir)

    @classmethod
    def is_sedml(cls, content: CombineArchiveContent) -> bool:
        return 'simulation' in content.location

    @classmethod
    def get_sedml(cls, fp: str) -> SedDocument:
        return SedmlSimulationReader().run(filename=fp)

    @classmethod
    def get_editable_params(
            cls,
            fp: str,
            model_lang: str,
            sim_type: Simulation,
            kisao_id: str
            ) -> Tuple[List[ModelAttributeChange], List[Simulation], List[Variable], List[Plot]]:
        attrb_changes, sim, variables, plots = get_parameters_variables_outputs_for_simulation(
                           model_filename=fp,
                           model_language=model_lang,
                           simulation_type=sim_type,
                           change_level=SedDocument,
                           algorithm_kisao_id=kisao_id)
        return attrb_changes, sim, variables, plots

    @classmethod
    def parse_editable_params(
            cls,
            attributes: List[ModelAttributeChange]
            ) -> List[EditableSimulationParameter]:
        params = []
        for attribute in attributes:
            # new_value is default and target is target
            param_value = ParameterValue(default=attribute.new_value)
            editable_param = EditableSimulationParameter(
                target=attribute.target,
                value=param_value,
                target_namespaces=attribute.target_namespaces,
                name=attribute.name,
                id=attribute.name)
            params.append(editable_param)
        return params

    @classmethod
    def get_serialized_params(cls, attributes: List[ModelAttributeChange]) -> Dict[str, List[Dict[str, Union[str, Dict[str, Union[int, float]]]]]]:
        editable_params = cls.parse_editable_params(attributes)
        serialized = []
        for param in editable_params:
            serialized.append(param.to_dict())
        return {'values': serialized}

    @classmethod
    def edit_simulation_parameters(cls, serialized_parameters: Dict, **new_values) -> Dict:
        """Provide new values to the serialized_parameters dict and return the same
            dict, but edited.

            Args:
                serialized_parameters:`Dict`: params datastructure that will be edited.
                **new_values:`kwargs`: new key value assignments to the values.

            Returns:
                the edited parameters
        """
        for param_name, param_val in new_values.items():
            serialized_parameters['values'][param_name]['value']['new_value'] = param_val
        return serialized_parameters

    @classmethod
    def generate_model(
            cls,
            model_id: str,
            model_name: str,
            model_source: str,
            model_language: str,
            changes: List[ModelAttributeChange]
            ) -> Model:
        return Model(model_id, model_name, model_source, model_language, changes)

    @classmethod
    def generate_sed_doc_from_changed_model(
            cls,
            uploaded_archive: CombineArchive,
            extraction_dir: str,
            kisao_id: str = None,
            **changes) -> SedDocument:
        introspection = cls.introspect_archive(
            uploaded_archive=uploaded_archive,
            extraction_dir=extraction_dir,
            kisao_id=kisao_id)

        sim_type = introspection['sim_type']
        sim_model = introspection['sim_model']
        model_lang = introspection['model_lang']
        model_source = introspection['model_source']
        changed_attributes = cls.edit_simulation_parameters(serialized_parameters=introspection, **changes)
        new_model_changes = []
        for param in introspection['values']:
            param_values = param.pop('value')
            val = param_values.get('new_value') or param_values['default']
            attribute_change = ModelAttributeChange(
                id=param['id'],
                name=param['name'],
                target=param['target'],
                target_namespaces=param['target_namespaces'],
                new_value=str(val))
            new_model_changes.append(attribute_change)

        assert sim_model.changes != new_model_changes
        introspection['sim_model'].changes = new_model_changes
        pp(introspection)
        # TODO: Create sed doc

    @classmethod
    def add_changed_sed_to_uploaded_archive(cls, uploaded_archive: CombineArchive) -> None:
        # remove previous sedml
        print(len(uploaded_archive.contents))
        for content in uploaded_archive.contents:
            if 'sedml' in content.location:
                uploaded_archive.contents.remove(content)
        print(len(uploaded_archive.contents))

    # TODO: add this to the yaml spec
    @classmethod
    def introspect_archive(
            cls,
            uploaded_archive: CombineArchive,
            extraction_dir: str,
            kisao_id: str = None) -> Dict:
        for content in uploaded_archive.contents:
            if 'sedml' in content.location:
                sed_fp = content.location.replace('./', '')
                sed_doc: SedDocument = cls.get_sedml(
                    os.path.join(extraction_dir, sed_fp))
                sed_doc_objects = get_all_sed_objects(sed_doc)
                for obj in sed_doc_objects:
                    if isinstance(obj, Task):
                        sim_type = type(obj.simulation)
                        sim_model = obj.model
                        model_lang = sim_model.language
                        model_fp = os.path.join(extraction_dir, sim_model.source)

                        attributes, sim, variables, plots = cls.get_editable_params(
                            fp=model_fp,
                            model_lang=model_lang,
                            sim_type=sim_type,
                            kisao_id=kisao_id)

                        serialized_editable_params = cls.get_serialized_params(attributes)
                        serialized_editable_params['sim_type'] = sim_type
                        serialized_editable_params['sim_model'] = sim_model
                        serialized_editable_params['model_lang'] = model_lang
                        serialized_editable_params['model_source'] = model_fp
                        return serialized_editable_params

    @classmethod
    def run(
            cls,
            omex_fp: str = None,
            working_dir: str = None,
            colab: bool = False,
            kisao_id: str = None
    ):
        """Introspect an archive for all editable changes to the simulation and
            return a JSON representation of the editable parameters.

            Args:
                omex_fp:`str`: direct path of the archive to upload.
                working_dir:`str`: path of location in which the COMBINE archive
                    is stored.
                colab:`bool`: If using colab, prompts user for archive input. Defaults
                    to `False`.
                kisao_id:`str`: KiSAO id of the algorithm for simulating the model.
                    Defaults to `None`.

            Returns:
                Dict: JSON representation of all editable parameters.
        """
        if working_dir and not omex_fp:
            if colab:
                from google.colab import files
                cls.upload_archive()
            omex_fp: str = cls.get_uploaded_omex_fp(working_dir)

        temp_extraction_dir = tempfile.mkdtemp()
        uploaded_archive: CombineArchive = cls.read_omex(omex_fp, temp_extraction_dir)
        serialized_editable_params = cls.introspect_archive(uploaded_archive, temp_extraction_dir, kisao_id)

        adjusted_sed: SedDocument = cls.generate_sed_doc_from_changed_model(uploaded_archive, temp_extraction_dir, kisao_id)
        return adjusted_sed


def test_editor():
    ArchiveEditorApi.run()