# API source
import os
import tempfile
import urllib.request
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Union
from process_bigraph import pp
from biosimulators_utils.combine.data_model import CombineArchive, CombineArchiveContent, CombineArchiveContentFormat
from biosimulators_utils.combine.io import CombineArchiveWriter, CombineArchiveReader
from biosimulators_utils.sedml.io import SedmlSimulationReader, SedmlSimulationWriter
from biosimulators_utils.sedml.utils import get_all_sed_objects  # change this
from biosimulators_utils.sedml.model_utils import get_parameters_variables_outputs_for_simulation
from biosimulators_utils.sedml.data_model import *
from archive_editor.data_model import (
    EditableSimulationParameter,
    ParameterValue,
    ChangedSedDocument,
    ParameterTarget,
    _EditableSimulationParameter
)


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
    def get_sedml_filepath_from_archive(cls, uploaded_archive: CombineArchive, overwrite: True) -> str:
        sed_fp = []
        for content in uploaded_archive.contents:
            if 'sedml' in content.location:
                sed_fp.append(content.location)
                if overwrite:
                    uploaded_archive.contents.remove(content)
        return sed_fp.pop()

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
            attributes: List[ModelAttributeChange]) -> List[EditableSimulationParameter]:
        params = []
        for attribute in attributes:
            # new_value is default and target is target
            param_value = ParameterValue(default=attribute.new_value)
            param_target = ParameterTarget(value=attribute.target)
            pp(_EditableSimulationParameter(
                target=param_target,
                value=param_value,
                target_namespaces=attribute.target_namespaces,
                name=attribute.name,
                id=attribute.name))
            editable_param = EditableSimulationParameter(
                target=attribute.target,
                value=param_value,
                target_namespaces=attribute.target_namespaces,
                name=attribute.name,
                id=attribute.name)
            params.append(editable_param)
        return params

    @classmethod
    def _get_serialized_params(
            cls,
            editable_params: List[EditableSimulationParameter]) -> Dict[str, List[Dict[str, Union[str, Dict[str, Union[int, float]]]]]]:
        serialized = []
        for param in editable_params:
            serialized.append(param.to_dict())
        return {'values': serialized}

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
    def prompt_edit_simulation_parameters(
            cls,
            serialized_parameters: Dict,
            prompt: bool = True,
            **changes) -> Dict:
        """Provide new values to the serialized_parameters dict and return the same
            dict, but edited.

            Args:
                serialized_parameters:`Dict`: params datastructure that will be edited.
                prompt:`bool`: whether to prompt the user through the changes. Defaults to
                    `True`.

            Returns:
                the edited parameters
        """
        for i, param in enumerate(serialized_parameters['values']):
            param_name = param['name']
            if prompt:
                param_val = input(f'Please enter the new value for {param_name}. Enter to skip: ')
            else:
                # if no kwargs passed
                if not changes:
                    param_val = serialized_parameters['values'][i]['value']['default']
                #otherwise use kwargs
                else:
                    param_val = changes[param_name]
            # set value
            serialized_parameters['values'][i]['value']['new_value'] = param_val
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
            **changes
    ) -> ChangedSedDocument:
        """Introspect uploaded COMBINE/OMEX file for possible changes, apply user changes, and
            generate a new sed doc from the changes.

            Args:
                uploaded_archive:`CombineArchive`: archive from which possible changes will be inferred.
                extraction_dir:`str`: dirpath into which the archive contents will be extracted.
                kisao_id:`str`: id of the simulation algorithm. Defaults to `None`.
                **changes:`kwargs`, `Dict[str, str]`: key/value change specifications where param target names are
                    keys and new values are the values in string form.

            Returns:
                `SedDocument` instance configured with user changes.
        """
        # gather introspection
        introspection = cls.introspect_archive(
            uploaded_archive=uploaded_archive,
            extraction_dir=extraction_dir,
            kisao_id=kisao_id)

        # source model params
        sim_model = introspection['sim_model']
        model_lang = introspection['model_lang']
        model_source = introspection['model_source']
        changed_attributes = cls.edit_simulation_parameters(
            serialized_parameters=introspection,
            **changes)
        # changed_attributes = cls.prompt_edit_simulation_parameters(introspection)
        # remove old changes to existing model/introspection
        introspection['sim_model'].changes.clear()

        # add new changes
        for param in introspection['values']:
            param_values = param.pop('value')
            val = param_values['new_value']  # or param_values['default']
            attribute_change = ModelAttributeChange(
                id=param['id'],
                name=param['name'],
                target=param['target'],
                target_namespaces=param['target_namespaces'],
                new_value=str(val))
            introspection['sim_model'].changes.append(attribute_change)

        sed_doc = ChangedSedDocument(
            models=[introspection['sim_model']],
            simulations=introspection['simulation'])
        return sed_doc

    @classmethod
    def write_changed_sed_doc(cls, doc: ChangedSedDocument, fp: str) -> None:
        """Write a changed sed document to a specified filepath."""
        return SedmlSimulationWriter().run(doc=doc, filename=fp)

    @classmethod
    def add_changed_sed_to_uploaded_archive(
            cls,
            uploaded_archive: CombineArchive,
            changed_sed_doc: ChangedSedDocument,
            sed_fp: str
    ) -> CombineArchive:
        # remove previous sedml and get the original filepath name (moved to run)
        # sed_fp = cls.get_sedml_filepath_from_archive(uploaded_archive, overwrite=True)  # .replace('.sedml', '_edited.sedml')

        # make a new content instance for the uploaded archive and apply it
        sed_content = CombineArchiveContent(
            location=sed_fp,
            format=CombineArchiveContentFormat.SED_ML.value,
            master=True)
        uploaded_archive.contents.append(sed_content)
        return uploaded_archive

    @classmethod
    def introspect_archive(
            cls,
            uploaded_archive: CombineArchive,
            extraction_dir: str,
            kisao_id: str = None) -> Dict:
        # TODO: add this to the yaml spec
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

                        # get the objects
                        editable_params = cls.parse_editable_params(attributes)
                        # for param in editable_params:
                        #     pp(param)

                        serialized_editable_params = cls._get_serialized_params(editable_params)
                        serialized_editable_params['simulation'] = sim
                        serialized_editable_params['sim_model'] = sim_model
                        serialized_editable_params['model_lang'] = model_lang
                        serialized_editable_params['model_source'] = model_fp
                        pp(serialized_editable_params)
                        return serialized_editable_params

    @classmethod
    def assert_same_archive(cls, original_archive: CombineArchive, new_archive: CombineArchive):
        if original_archive != new_archive:
            raise OSError('Could not update the uploaded archive contents.')
        else:
            return print('This change is valid')

    @classmethod
    def write_edited_archive(
            cls,
            edited_archive: CombineArchive,
            archive_working_dir: str,
            save_fp: str
    ) -> None:
        return CombineArchiveWriter().run(archive=edited_archive, in_dir=archive_working_dir, out_file=save_fp)

    @classmethod
    def download_archive_clientside(cls, url: str, destination: str) -> Tuple:
        """Use this to download the uploaded archive in memory to a client destination.

            Args:
                url:`str`: non-local location of the uploaded archive.
                destination:`str`: save destination on local/client for omex.

            Returns:
                `Tuple[str, HTTPMessage]` see `urllib`
            TODO: employ S3 here?
        """
        return urllib.request.urlretrieve(url, destination)

    @classmethod
    def run(
        cls,
        omex_fp: str = None,
        working_dir: str = None,
        save_fp: str = None,
        colab: bool = False,
        kisao_id: str = None,
        download_result: bool = True,
        **changes_to_apply
    ):
        """Introspect an archive for all editable changes to the simulation and
            return a JSON representation of the editable parameters.

            Args:
                omex_fp:`str`: direct path of the archive to upload.
                working_dir:`str`: path of location in which the COMBINE archive
                    is stored.
                save_fp:`str`: save filepath for the edited archive. If no value is passed,
                    use temp dir. Defaults to `None`.
                colab:`bool`: If using colab, prompts user for archive input. Defaults
                    to `False`.
                kisao_id:`str`: KiSAO id of the algorithm for simulating the model.
                    Defaults to `None`.
                download_result:`bool`: whether to download the edited archive after
                    changing it. Defaults to `True`.
                **changes_to_apply:`kwargs`: changes to apply that are referenced in key
                    by the name to of that val you want to change. # TODO: more robust
        """
        # handle upload TODO: expand this for entrypoints
        if working_dir and omex_fp is None:
            if colab:
                from google.colab import files
                cls.upload_archive()
            omex_fp: str = cls.get_uploaded_omex_fp(working_dir)

        # extract uploaded file and derive CombineArchive object
        temp_extraction_dir = tempfile.mkdtemp()
        uploaded_archive: CombineArchive = cls.read_omex(omex_fp, temp_extraction_dir)

        # get editable params as dict
        serialized_editable_params = cls.introspect_archive(uploaded_archive, temp_extraction_dir, kisao_id)

        pp(serialized_editable_params['values'][0])

        # generate new sed doc and write it to temp dir
        adjusted_sed_doc: ChangedSedDocument = cls.generate_sed_doc_from_changed_model(
            uploaded_archive=uploaded_archive,
            extraction_dir=temp_extraction_dir,
            kisao_id=kisao_id,
            **changes_to_apply)
        adjusted_sed_fp = os.path.join(temp_extraction_dir, 'adjusted_simulation.sedml')
        cls.write_changed_sed_doc(
            doc=adjusted_sed_doc,
            fp=adjusted_sed_fp)

        # rename adjusted sed doc to original name
        sed_fp = cls.get_sedml_filepath_from_archive(uploaded_archive, overwrite=True)
        os.rename(src=adjusted_sed_fp, dst=sed_fp)

        # add the changed sed to the archive contents
        edited_archive: CombineArchive = cls.add_changed_sed_to_uploaded_archive(
            uploaded_archive=uploaded_archive,
            changed_sed_doc=adjusted_sed_doc,
            sed_fp=sed_fp)

        # TODO: change this
        cls.assert_same_archive(uploaded_archive, edited_archive)

        # save to temp file if dest is not specified
        if save_fp is None:
            save_fp = tempfile.mktemp()

        # write the edited archive
        cls.write_edited_archive(
            edited_archive=edited_archive,
            archive_working_dir=temp_extraction_dir,
            save_fp=save_fp)

        # download edited archive
        print(os.path.exists(save_fp))


def test_editor():
    file_src_root = './editor-api/archive_editor/file_assets'
    fp = os.path.join(
        file_src_root,
        'Ciliberto-J-Cell-Biol-2003-morphogenesis-checkpoint-continuous.omex')
    ArchiveEditorApi.run(omex_fp=fp)


test_editor()


