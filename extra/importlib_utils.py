import abc
import re
from typing import final, Union

from extra.profiling_test import make_all_profiling_in_module


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
            self.__name_general = self.name.lower().replace('_', '-')
        # print(self.__name_general)
        return self.__name_general

    @property
    def version(self) -> str:
        return self._version

    @property
    def lib_path_location(self) -> str:
        return self._lib_path_location

    @property
    def available_extras(self) -> list[str]:
        return self._available_extras

    @property
    def requirements(self) -> list['RequirementInfo']:
        return self._requirements

    def requirements_filter(self, enabled_extras: list[str] = None) \
            -> list['RequirementInfo']:
        if not self.requirements:
            return self.requirements
        enabled_extras = enabled_extras or list()
        return list(filter(
            lambda x: not x.condition_extra or x.condition_extra in enabled_extras,
            self._requirements))

    class Builder:
        def __init__(self):
            self._instance = DistributionInfo()

        def name(self, name: str):
            self._instance._name = name
            self._instance.__name_general = name.lower().replace('_', '-')
            return self

        def version(self, version: str):
            self._instance._version = version
            return self

        def lib_path_location(self, lib_path_location: str):
            self._instance._lib_path_location = lib_path_location
            return self

        def available_extras(self, available_extras: list[str]):
            self._instance._available_extras = available_extras
            return self

        def requirements(self, requirements: list['RequirementInfo']):
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
            self.__name_general = self.name.lower().replace('_', '-')
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

    class Builder(object):
        def __init__(self):
            self._instance = RequirementInfo()

        def name(self, name: str):
            self._instance._name = name
            return self

        def enabled_extras(self, enabled_extras: list[str]):
            self._instance._enabled_extras = enabled_extras
            return self

        def condition_extra(self, condition_extra: Union[str, None]):
            self._instance._condition_extra = condition_extra
            return self

        def build(self):
            return self._instance  # do not use builder after build


class ImportUtils(abc.ABC):
    def __init__(self):
        self._known_dists = dict()
        # if root class is ImportUtils then exception
        if type(self) is not ImportUtils:
            return
        raise self.ImportUtilsInitializationError(
            "ImportUtils is an abstract class and cannot be instantiated directly.")

    @abc.abstractmethod
    def get_distribution(self, name: str) -> DistributionInfo:
        """
        Returns the distribution information for the given package name.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def get_installed_distributions(self) -> list[DistributionInfo]:
        """
        Returns a list of installed distributions.
        This method is optional and may not be implemented by all subclasses.
        """
        raise NotImplementedError()

    @final
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
        except ImportError:
            return ImportUtilsPkgResources()


class ImportUtilsPkgResources(ImportUtils):
    """
    Implementation of ImportUtils using pkg_resources for old python.
    """

    __pkg_resources = None

    def __init__(self):
        super(self.__class__, self).__init__()
        if self.__pkg_resources is None:
            try:
                import pkg_resources
                self.__pkg_resources = pkg_resources
            except ImportError:
                raise Exception("pkg_resources module is not available.")

    def get_distribution(self, name: str) -> DistributionInfo:
        if not self._known_dists:
            self.get_installed_distributions()
        if name not in self._known_dists:
            raise self.InstalledDependencyNotFound(name)
        res = self._known_dists[name]
        return res

    def get_installed_distributions(self) -> list[DistributionInfo]:
        if self._known_dists:
            return list(self._known_dists.values())
        distributions_raw = list(self.__pkg_resources.working_set)
        distributions = list()
        for dist_raw in distributions_raw:
            dist = self.__DistributionInfoProxyPkgResources(dist_raw)
            if 'vendor' in dist.lib_path_location:
                continue
            distributions.append(dist)
        distributions = list(sorted(distributions, key=lambda x: x.name_general))
        self._known_dists = {dist.name_general: dist for dist in distributions}
        return self.get_installed_distributions()

    def _get_requirement_dependencies(
            self, name: str, enabled_extras: list = None) -> list[RequirementInfo]:
        try:
            d = self.__pkg_resources.get_distribution(name)
            requirements_raw = d.requires(extras=enabled_extras)
            requirements_raw = requirements_raw if requirements_raw else list()
            requirements = list()
            for req in requirements_raw:
                try:
                    req_fetched_dependency = self.get_distribution(req.project_name)
                except self.InstalledDependencyNotFound:
                    continue
                req_info = (RequirementInfo().Builder()
                            .name(req_fetched_dependency.name)
                            .enabled_extras(list(req.extras) if req.extras else list())
                            ).build()
                requirements.append(req_info)
            return requirements
        except self.__pkg_resources.DistributionNotFound:
            raise self.InstalledDependencyNotFound(name)

    class __DistributionInfoProxyPkgResources(DistributionInfo):
        def __init__(self, dist_raw):
            super(self.__class__, self).__init__()
            self._name = dist_raw.project_name
            self._version = dist_raw.version
            self._lib_path_location = dist_raw.location
            self._available_extras = list(dist_raw.extras)

        @property
        def requirements(self) -> list['RequirementInfo']:
            if not self._requirements:
                self._requirements = self.requirements_filter(
                    enabled_extras=self.available_extras)
            return super(self.__class__, self).requirements

        def requirements_filter(self, enabled_extras: list[str] = None) \
                -> list[RequirementInfo]:
            requirements = ImportUtilsPkgResources()._get_requirement_dependencies(
                self.name, enabled_extras)
            return requirements

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

    def get_distribution(self, name: str) -> DistributionInfo:
        if type(name) is not str:
            raise TypeError("\"name\" must be a str but got " + str(type(name)) + ".")
        if not self._known_dists:
            self.get_installed_distributions()
        if name not in self._known_dists:
            raise self.InstalledDependencyNotFound(name)
        res = self._known_dists[name]
        # try:
        #     d = self._importlib_metadata.distribution(name)
        # except self._importlib_metadata.PackageNotFoundError:
        #     raise self.InstalledDependencyNotFound(name)
        # res = self.__DistributionInfoProxy(d.metadata)
        # res_builder = DistributionInfo.Builder()
        # res_builder.name = str(d.name)
        # res_builder.version = str(d.version)
        # res_builder.available_extras = list(d.metadata.json.get(
        # 'provides_extra', list()))
        # res_builder.lib_path_location = str(d.locate_file('.'))
        return res

    def get_installed_distributions(self) -> list[DistributionInfo]:
        if self._known_dists:
            return list(self._known_dists.values())
        distributions_raw = list(self._importlib_metadata.distributions())
        distributions = list()
        for dist_raw in distributions_raw:
            # dist_metadata = dist_raw.metadata

            dist = self.__DistributionInfoProxyImportLib(dist_raw)
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

    @staticmethod
    def _get_requirement_dependencies(metadata) -> list[RequirementInfo]:
        regex_get_name_extras_condition_extra = (
            r"^\s*(?P<requirement_name>[\w\-]+)\s*"
            r"(?:\[(?P<requirement_extras>.*)\])?"
            r"(?:.*extra\s*==\s*\"(?P<condition_extra>[\w\-]+)\")?.*$")
        requirements_raw = metadata.get_all('requires-dist', list())
        requirements = list()
        for req_raw in requirements_raw:
            req_raw = str(req_raw)
            match = dict(re.match(
                regex_get_name_extras_condition_extra, req_raw).groupdict())
            req_name = str(match['requirement_name'])
            req_extras = list()
            if match['requirement_extras'] is not None:
                req_extras = str(match['requirement_extras']).split(',')
            req_condition_extra = match['condition_extra']
            requirement = (RequirementInfo().Builder()
                           .name(req_name)
                           .enabled_extras(req_extras)
                           .condition_extra(req_condition_extra)
                           ).build()
            requirements.append(requirement)
        return requirements

    class __DistributionInfoProxyImportLib(DistributionInfo):
        """
        Proxy class for DistributionInfo to allow lazy loading of metadata.
        """

        def __init__(self, dist_raw):
            super(self.__class__, self).__init__()
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
        def available_extras(self) -> list[str]:
            if not self._available_extras:
                self._available_extras = self.__metadata.get_all('provides-extra', list())
            return super(self.__class__, self).available_extras

        @property
        def requirements(
                self, enabled_extras: list[str] = None) -> list['RequirementInfo']:
            if not self._requirements:
                self._requirements = ImportUtilsImportlib._get_requirement_dependencies(
                    self.__metadata)
            return super(self.__class__, self).requirements

        def __str__(self):
            return super(self.__class__, self).__str__()


def main():
    util1, util2 = ImportUtilsPkgResources(), ImportUtilsImportlib()
    for _ in range(10):
        utils = [util1, util2]
        a, b = list(util.get_distribution('fastapi') for util in utils)[:2]
        print(a, b)
        # a2, b2 = list(util.get_requirement_dependencies('fastapi')
        # for util in utils)[:2]
        c1, c2 = list(util.get_installed_distributions() for util in utils)[:2]
        for c in [c1, c2]:
            for d in c:
                _ = (d.name, d.version, d.lib_path_location, d.available_extras,
                     d.requirements)
        pass
    pass


if __name__ == '__main__':
    # make_all_profiling_in_module(globals())
    main()
