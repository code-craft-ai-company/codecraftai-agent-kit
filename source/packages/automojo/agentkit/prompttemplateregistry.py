"""
    Defines the PromptTemplateRegistry class for tracking available
    PromptTemplate instances in the automojo-agent-kit framework.

    PromptTemplateRegistry provides registration, lookup by name and
    optional version, enumeration, count, and loading from JSON and
    YAML files. Templates are keyed by a composite key of (name, version).
    When looking up by name without a version, the registry returns the
    latest version based on lexicographic sort of version strings.
"""

import json

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.prompttemplate import PromptTemplate


class PromptTemplateRegistry:
    """
        Registry for PromptTemplate instances, keyed by name and version.

        Provides registration with duplicate detection, lookup by name
        and optional version, enumeration of all templates, a count
        property, and loading from JSON and YAML file paths.
    """

    def __init__(self) -> None:
        self._templates: dict = {}
        return

    def register(self, template: PromptTemplate) -> None:
        """
            Registers a PromptTemplate using name + version as a composite key.

            :param template: The PromptTemplate instance to register.

            :raises: SemanticError if a template with the same name and version
                     is already registered.
        """
        template_name = template.name
        template_version = template.version
        key = (template_name, template_version)

        is_duplicate = key in self._templates

        if is_duplicate is True:
            errmsg = "PromptTemplate {!r} version {!r} is already registered.".format(
                template_name, template_version
            )
            raise SemanticError(errmsg)

        self._templates[key] = template

        return

    def lookup(self, name: str, version: str = None) -> PromptTemplate:
        """
            Looks up a PromptTemplate by name and optional version.

            When version is provided, returns the exact match or None.
            When version is not provided, returns the latest version
            for the given name based on lexicographic sort of version
            strings, or None if no templates match the name.

            :param name: The template name.
            :param version: Optional version string.

            :returns: The PromptTemplate instance, or None if not found.
        """
        if version is not None:
            key = (name, version)
            rtnval = self._templates.get(key, None)
            return rtnval

        matching = [(k, t) for k, t in self._templates.items() if k[0] == name]

        if len(matching) == 0:
            return None

        matching.sort(key=lambda item: item[0][1])
        rtnval = matching[-1][1]
        return rtnval

    def list_all(self) -> list:
        """
            Returns all registered PromptTemplate instances.

            :returns: A list of PromptTemplate objects.
        """
        rtnval = list(self._templates.values())
        return rtnval

    @property
    def count(self) -> int:
        """
            The number of currently registered templates.

            :returns: The count of registered templates.
        """
        rtnval = len(self._templates)
        return rtnval

    def load_from_json_file(self, file_path: str) -> None:
        """
            Loads PromptTemplate definitions from a JSON file.

            The JSON file is expected to contain a top-level object with
            a "templates" key whose value is a list of template definition
            dictionaries, each compatible with PromptTemplate.from_dict.

            :param file_path: Path to the JSON file.
        """
        with open(file_path, "r") as fhandle:
            data = json.load(fhandle)

        templates = data.get("templates", [])

        for tdata in templates:
            template = PromptTemplate.from_dict(tdata)
            self.register(template)

        return

    def load_from_yaml_file(self, file_path: str) -> None:
        """
            Loads PromptTemplate definitions from a YAML file.

            The YAML file is expected to contain a top-level mapping with
            a "templates" key whose value is a list of template definition
            mappings, each compatible with PromptTemplate.from_dict.

            :param file_path: Path to the YAML file.
        """
        import yaml

        with open(file_path, "r") as fhandle:
            data = yaml.safe_load(fhandle)

        templates = data.get("templates", [])

        for tdata in templates:
            template = PromptTemplate.from_dict(tdata)
            self.register(template)

        return
