# coding=utf-8
import abc
import logging
import re
import weakref
from typing import Union, List
import packaging.requirements

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class DistributionInfo(object):
    def __init__(self):
        self._name = None
        self.__name_general = None
        self._version = None
        self._lib_path_location = None
        self._available_extras = None
        self._requirements = None

    def __str__(self):
        return (
                "DistributionInfo(name=" + str(self.name) +
                (", version=" + str(self.version) if self.version else "") +
                (", available_extras=" + str(self.available_extras)
                 if self.available_extras else "") +
                (", lib_path_location=" + str(self.lib_path_location)
                 if self.lib_path_location else "") +
                ")")

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_general(self) -> str:
        if not self.__name_general and self.name:
            self.__name_general = get_package_general_name(self.name)
        # print(self.__name_general)
        return self.__name_general

    @property
    def version(self) -> str:
        return self._version

    @property
    def lib_path_location(self) -> str:
        return self._lib_path_location

    @property
    def available_extras(self) -> List[str]:
        return self._available_extras

    @property
    def requirements(self) -> List['RequirementInfo']:
        return self._requirements

    def requirements_filter(self, enabled_extras: List[str] = None) \
            -> List['RequirementInfo']:
        if not self.requirements:
            return self.requirements
        enabled_extras = enabled_extras or list()
        res = list(filter(
            lambda x: not x.condition_extra or x.condition_extra in enabled_extras,
            self._requirements))
        return res

    class Builder:
        def __init__(self):
            self._instance = DistributionInfo()

        def name(self, name: str):
            self._instance._name = name
            return self

        def version(self, version: str):
            self._instance._version = version
            return self

        def lib_path_location(self, lib_path_location: str):
            self._instance._lib_path_location = lib_path_location
            return self

        def available_extras(self, available_extras: List[str]):
            self._instance._available_extras = available_extras
            return self

        def requirements(self, requirements: List['RequirementInfo']):
            self._instance._requirements = requirements
            return self

        def build(self):
            return self._instance


class RequirementInfo(object):
    def __init__(self):
        self._name = None
        self.__name_general = None
        self._enabled_extras = None
        self._condition_extra = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_general(self) -> str:
        if not self.__name_general and self.name:
            self.__name_general = get_package_general_name(self.name)
        return self.__name_general

    @property
    def enabled_extras(self):
        if not self._enabled_extras:
            return None
        return list(self._enabled_extras).copy()

    @property
    def condition_extra(self):
        return self._condition_extra

    def __str__(self):
        return (
                "RequirementInfo(name=" + str(self.name) +
                (", enabled_extras=" + str(self._enabled_extras)
                 if self._enabled_extras else "") +
                (", condition_extra=" + str(self.condition_extra)
                 if self.condition_extra else "") +
                ")"
        )

    def __eq__(self, other):
        if not isinstance(other, RequirementInfo):
            return super(self.__class__, self) == other
        if self.name_general != other.name_general:
            return False
        if self.condition_extra != other.condition_extra:
            return False
        if self.enabled_extras != other.enabled_extras:
            return False
        return True

    @classmethod
    def __parse_str_regex(cls, str_repr: str) -> 'RequirementInfo':
        regex = (
            r"^\s*(?P<requirement_name>[\w\-]+)\s*"
            r"(?:\[(?P<requirement_extras>.*)\])?"
            r"(?:.*extra\s*==\s*"
            r"(?P<_quote>[\"\'])(?P<condition_extra>[\w\-]+)(?P=_quote))?.*$")
        match = re.match(regex, str_repr)
        if not match:
            raise ValueError(
                "Invalid requirement string format: " + str_repr + ". " +
                "Expected format: name[extra1,extra2,...]; extra == \"condition_extra\"")
        name = match.group('requirement_name')
        # res_builder = self.Builder()
        if not name:
            raise ValueError("Requirement name cannot be empty.")

        enabled_extras_str = match.group('requirement_extras')
        enabled_extras = str(enabled_extras_str).strip().split(',') \
            if enabled_extras_str else []
        condition_extra = match.group('condition_extra')
        res = (cls.Builder()
               .name(name)
               .enabled_extras(enabled_extras)
               .condition_extra(condition_extra)
               ).build()
        return res

    @classmethod
    def __parse_str_packaging_satisfy(
            cls, str_repr: str, condition_extra: Union[str, None] = None
    ) -> bool:
        try:
            req = packaging.requirements.Requirement(str_repr)
        except packaging.requirements.InvalidRequirement:
            raise ValueError("Invalid requirement string format: " + str_repr)
        custom_env = dict()
        if condition_extra:
            custom_env['extra'] = condition_extra
        res = True
        if req.marker:
            res = req.marker.evaluate(custom_env)
        return res

    @classmethod
    def parse_str(cls, str_repr: str) -> 'RequirementInfo':
        """
        Parses the string representation of the requirement.
        The format is:
        name[extra1,extra2,...]; extra == "condition_extra"
        """
        res = cls.__parse_str_regex(str_repr)
        if not cls.__parse_str_packaging_satisfy(str_repr, res.condition_extra):
            raise cls.SatisfyException(str_repr, res.condition_extra)
        return res

    class SatisfyException(Exception):
        """
        Exception raised when the requirement string does not satisfy the condition.
        """

        def __init__(self, str_repr: str, condition_extra: Union[str, None] = None):
            self.str_repr = str_repr
            self.condition_extra = condition_extra

        def __str__(self):
            return ("Requirement string \"" + self.str_repr + "\" does not satisfy" +
                    ((" with the condition extra \"" + str(self.condition_extra))
                     if self.condition_extra else "") +
                    "\".")

    class Builder(object):
        def __init__(self):
            self._instance = RequirementInfo()
            self._instance._enabled_extras = list()

        def name(self, name: str):
            self._instance._name = name
            return self

        def enabled_extras(self, enabled_extras: List[str]):
            self._instance._enabled_extras = enabled_extras
            return self

        def condition_extra(self, condition_extra: Union[str, None]):
            self._instance._condition_extra = condition_extra
            return self

        def build(self):
            if not self._instance.name:
                raise ValueError("RequirementInfo must have a name.")
            res = self._instance
            self._instance = None
            return res  # do not use builder after build


def get_package_general_name(name: str) -> str:
    """
    Returns the general name of the package, which is the name in lowercase
    with underscores replaced by hyphens.
    """
    return name.lower().replace('_', '-')


class ImportUtils(abc.ABC):
    def __init__(self):
        self._known_dists = dict()
        # if root class is ImportUtils then exception
        if type(self) is not ImportUtils:
            return
        raise self.ImportUtilsInitializationError(
            "ImportUtils is an abstract class and cannot be instantiated directly.")

    def get_distribution(self, name: str) -> DistributionInfo:
        """
        Returns the distribution information for the given package name.
        """
        requirement = self.get_requirement(name)
        name_general = requirement.name_general
        res = self._known_dists[name_general]
        return res

    def get_requirement(self, str_repr: str) -> RequirementInfo:
        if type(str_repr) is not str:
            raise TypeError("\"str_repr\" must be a str but got " +
                            str(type(str_repr)) + ".")
        if not self._known_dists:
            self.get_installed_distributions()
        requirement = RequirementInfo().parse_str(str_repr)
        name_general = requirement.name_general
        if name_general not in self._known_dists:
            raise self.InstalledDependencyNotFound(requirement.name)
        return requirement

    # @final
    # def fetch_requirements(
    #         self, req: RequirementInfo) -> List[RequirementInfo]:
    #     if not dist.requirements:
    #         dist._requirements = dist.requirements_filter(
    #             enabled_extras=dist.available_extras)

    @abc.abstractmethod
    def get_installed_distributions(self) -> List[DistributionInfo]:
        """
        Returns a list of installed distributions.
        This method is optional and may not be implemented by all subclasses.
        """
        raise NotImplementedError()

    def clear_known_distributions(self):
        """
        Clears the cache of known distributions.
        This is useful to ensure that the next call to get_distribution
        or get_installed_distributions will fetch the latest data.
        """
        self._known_dists.clear()

    # @abc.abstractmethod
    # def get_requirement_dependencies(
    #         self, name: str, enabled_extras: list = None) -> list[RequirementInfo]:
    #     """
    #     Returns a list of requirements for the given package name.
    #     It skips packages that are not installed.
    #     """
    #     raise NotImplementedError()

    class InstalledDependencyNotFound(Exception):
        """
        Exception raised when searched dependency is not found.
        """

        def __init__(self, name: str):
            self.name = name

        def __str__(self):
            return "Installed dependency \"" + self.name + "\" not found."

    class ImportUtilsInitializationError(Exception):
        """
        Exception raised when ImportUtils implementation was wrongly initialized
        """
        pass


class ImportUtilsFactory:
    """
    Factory class to create an instance of ImportUtils depending on
    which packages are available.
    """

    @staticmethod
    def create() -> ImportUtils:
        try:
            return ImportUtilsImportlib()
        except ImportUtils.ImportUtilsInitializationError:
            pass
        try:
            return ImportUtilsPkgResources()
        except ImportUtils.ImportUtilsInitializationError:
            raise ImportUtils.ImportUtilsInitializationError(
                "No suitable ImportUtils implementation found. "
                "Please install importlib.metadata or pkg_resources.")


class ImportUtilsPkgResources(ImportUtils):
    """
    Implementation of ImportUtils using pkg_resources for old python.
    """

    __pkg_resources = None

    def __import(self):
        if self.__pkg_resources is None:
            try:
                import pkg_resources
                self.__pkg_resources = pkg_resources
            except ImportError:
                raise Exception("pkg_resources module is not available.")

    def __init__(self):
        super(self.__class__, self).__init__()
        self.__import()

    def clear_known_distributions(self):
        self.__pkg_resources = None
        self.__import()
        getattr(self.__pkg_resources, '_initialize_master_working_set', lambda: None)()
        super(self.__class__, self).clear_known_distributions()

    def get_installed_distributions(self) -> List[DistributionInfo]:
        if self._known_dists:
            return list(self._known_dists.values())
        distributions_raw = list(self.__pkg_resources.working_set)
        distributions = list()
        for dist_raw in distributions_raw:
            dist = self.__DistributionInfoProxyPkgResources(dist_raw)
            if dist.name is None:
                continue
            if 'vendor' in dist.lib_path_location:
                continue
            distributions.append(dist)
        distributions = list(sorted(distributions, key=lambda x: x.name_general))
        self._known_dists = {dist.name_general: dist for dist in distributions}
        return self.get_installed_distributions()

    def _get_requirement_dependencies(
            self, name: str, enabled_extras: list = None) -> List[RequirementInfo]:
        try:
            d = self.__pkg_resources.get_distribution(name)
            requirements_raw = d.requires(extras=enabled_extras)
            requirements_raw = requirements_raw if requirements_raw else list()
            requirements = list()
            for req in requirements_raw:
                try:
                    req_fetched_requirement = self.get_requirement(str(req))
                except self.InstalledDependencyNotFound:
                    continue
                # condition_extra = req.ex
                # req_info = (RequirementInfo().Builder()
                #             .name(req_fetched_requirement.name)
                #             .enabled_extras(list(req.extras) if req.extras else list())
                #             ).build()
                requirements.append(req_fetched_requirement)
            requirements = list(sorted(
                requirements, key=lambda x: x.name_general))
            return requirements
        except self.__pkg_resources.DistributionNotFound:
            raise self.InstalledDependencyNotFound(name)

    class __DistributionInfoProxyPkgResources(DistributionInfo):
        def __init__(self, dist_raw):
            super(self.__class__, self).__init__()
            self._name = dist_raw.project_name
            self._version = dist_raw.version
            self._lib_path_location = dist_raw.location
            available_extras = list()
            try:
                available_extras = list(dist_raw.extras)
            except FileNotFoundError as e:
                logger.info(
                    "Failed to get extras for distribution %s: %s",
                    dist_raw.project_name, str(e))
            self._available_extras = available_extras

        @property
        def requirements(self) -> List['RequirementInfo']:
            if not self._requirements:
                requirements = ImportUtilsPkgResources()._get_requirement_dependencies(
                    self.name, self.available_extras)
                self._requirements = requirements
            return super(self.__class__, self).requirements

        # def requirements_filter(self, enabled_extras: List[str] = None) \
        #         -> List[RequirementInfo]:
        #     requirements = ImportUtilsPkgResources()._get_requirement_dependencies(
        #         self.name, enabled_extras)
        #     return requirements

        def __str__(self):
            return super(self.__class__, self).__str__()


class ImportUtilsImportlib(ImportUtils):
    """
    Implementation of ImportUtils using importlib.metadata for python 3.8+.
    """

    _importlib_resources = None
    _importlib_metadata = None
    _importlib = None

    def __init__(self):
        super(self.__class__, self).__init__()
        try:
            import importlib.resources
            import importlib.metadata
            import importlib
            self._importlib_resources = importlib.resources
            self._importlib_metadata = importlib.metadata
            self._importlib = importlib
        except ImportError:
            raise self.ImportUtilsInitializationError(
                "Module \"importlib\" is not available.")

    def get_installed_distributions(self) -> List[DistributionInfo]:
        if self._known_dists:
            return list(self._known_dists.values())
        distributions_raw = list(self._importlib_metadata.distributions())
        distributions = list()
        for dist_raw in distributions_raw:
            # dist_metadata = dist_raw.metadata

            dist = self.__DistributionInfoProxyImportLib(self, dist_raw)
            if dist.name is None:
                continue
            # dist.name = str(dist_metadata['name'])
            # dist.version = str(dist_metadata['version'])
            # dist.available_extras = list(dist_metadata.get('provides_extra', list()))
            # dist.lib_path_location = str(dist_raw.locate_file('.'))
            if 'vendor' in dist.lib_path_location:
                continue
            distributions.append(dist)
        distributions = list(sorted(distributions, key=lambda x: x.name_general))
        self._known_dists = {d.name_general: d for d in distributions}
        return self.get_installed_distributions()

    def _get_requirement_dependencies(self, metadata) -> List[RequirementInfo]:
        requirements_raw = metadata.get_all('requires-dist', list()) or [""][:-1]
        requirements = list()
        for req_raw in requirements_raw:
            try:
                requirement_parsed = self.get_requirement(req_raw)
            except (RequirementInfo.SatisfyException,
                    self.InstalledDependencyNotFound):
                continue
            requirements.append(requirement_parsed)
        requirements = list(sorted(
            requirements, key=lambda x: x.name_general))
        return requirements

    class __DistributionInfoProxyImportLib(DistributionInfo):
        """
        Proxy class for DistributionInfo to allow lazy loading of metadata.
        """

        def __init__(self, import_utils_lib: 'ImportUtilsImportlib', dist_raw):
            super(self.__class__, self).__init__()
            self.__import_utils_lib = weakref.ref(import_utils_lib)
            self.__dist_raw = dist_raw
            self.__metadata = self.__dist_raw.metadata

        @property
        def name(self) -> str:
            if not self._name:
                self._name = self.__metadata['name']
            return super(self.__class__, self).name

        @property
        def version(self) -> str:
            if not self._version:
                self._version = self.__metadata['version']
            return super(self.__class__, self).version

        @property
        def lib_path_location(self):
            if not self._lib_path_location:
                self._lib_path_location = str(self.__dist_raw.locate_file('.'))
            return super(self.__class__, self).lib_path_location

        @property
        def available_extras(self) -> List[str]:
            if not self._available_extras:
                self._available_extras = self.__metadata.get_all('provides-extra', list())
            return super(self.__class__, self).available_extras

        def get_import_utils_lib(self) -> 'ImportUtilsImportlib':
            lib = self.__import_utils_lib()
            if not lib:
                raise Exception("ImportUtils was nulled (weak reference).")
            return lib

        @property
        def requirements(
                self, enabled_extras: List[str] = None) -> List['RequirementInfo']:
            if not self._requirements:
                import_utils_lib = self.get_import_utils_lib()
                requirements = import_utils_lib._get_requirement_dependencies(
                    self.__metadata)
                self._requirements = requirements
            return super(self.__class__, self).requirements

        def __str__(self):
            return super(self.__class__, self).__str__()


def main():
    util1, util2 = ImportUtilsPkgResources(), ImportUtilsImportlib()
    for i in range(10):
        utils = [util1, util2]
        a, b = list(util.get_distribution('fastapi') for util in utils)[:2]
        if i == 0:
            print(a)
            print(b)
        # a2, b2 = list(util.get_requirement_dependencies('fastapi')
        # for util in utils)[:2]
        c1, c2 = list(util.get_installed_distributions() for util in utils)[:2]
        for c in [c1, c2]:
            for d in c:
                _ = (d.name, d.version, d.lib_path_location, d.available_extras,
                     d.requirements)
        pass
        d1, d2 = list(util.get_requirement('fastapi[standard]') for util in utils)[:2]
        if d1 == d2:
            pass
        e1, e2 = list(util.get_distribution('setuptools') for util in utils)[:2]
        if e1 == e2:
            pass
    pass


if __name__ == '__main__':
    # make_all_profiling_in_module(globals())
    main()
