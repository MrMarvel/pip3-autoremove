import inspect
# noinspection PyCompatibility
import pathlib
import time

from line_profiler import profile


def make_all_profiling_in_module(module_globals: dict = None):
    if module_globals is None:
        module_globals = globals()
    function_type = type(lambda: None)
    callable_globals = {name: obj for name, obj in module_globals.items()
                        if isinstance(obj, function_type) and not name.endswith('__')}
    functions_to_profile = dict()
    script_dir = pathlib.Path(module_globals.get('__file__')).parent.resolve()
    exclude_path_words = ['.venv', 'site-packages']
    for name, obj in callable_globals.items():
        # obj_attrs = {key: getattr(obj, key) for key in dir(obj)}
        obj_code_location = pathlib.Path(inspect.getfile(obj)).resolve()
        if any(x in str(obj_code_location) for x in exclude_path_words):
            continue
        try:
            obj_code_location.relative_to(script_dir)
        except ValueError:
            continue
        functions_to_profile[name] = obj
    for name, obj in functions_to_profile.items():
        module_globals[name] = profile(obj)
    classes_globals = {name: obj for name, obj in module_globals.items()
                       if isinstance(obj, type) and not name.endswith('__')}
    classes_developed = dict()
    for name, obj in classes_globals.items():
        obj_file = pathlib.Path(inspect.getfile(obj)).resolve()
        if any(x in str(obj_file) for x in exclude_path_words):
            continue
        try:
            obj_file.relative_to(script_dir)
        except ValueError:
            continue
        classes_developed[name] = obj
    for name, obj in classes_developed.items():
        obj_methods = {key: getattr(obj, key) for key in dir(obj)}
        developed_methods = dict()
        developed_class_methods = dict()
        # methods_static_info = dict(inspect.getmembers(obj))
        developed_static_methods = dict()
        for method_name, method_obj in obj_methods.items():
            if not isinstance(method_obj, function_type):
                if not inspect.ismethod(method_obj):
                    continue
            method_path = pathlib.Path(inspect.getfile(method_obj)).resolve()
            if any(x in str(method_path) for x in exclude_path_words):
                continue
            try:
                method_path.relative_to(script_dir)
            except ValueError:
                continue
            method_type_static_info = obj.__dict__.get(method_name, None)
            if method_type_static_info is None:
                continue
            if isinstance(method_type_static_info, function_type):
                developed_methods[method_name] = method_obj
                continue
            if isinstance(method_type_static_info, classmethod):
                developed_class_methods[method_name] = method_obj
                continue
            if isinstance(method_type_static_info, staticmethod):
                developed_static_methods[method_name] = method_obj
                continue
        for method_name, method_obj in developed_methods.items():
            method_obj = profile(method_obj)
            setattr(obj, method_name, method_obj)
        for method_name, method_obj in developed_class_methods.items():
            method_obj = profile(method_obj.__func__)
            setattr(obj, method_name, classmethod(method_obj))
        for method_name, method_obj in developed_static_methods.items():
            method_obj = profile(method_obj)
            setattr(obj, method_name, staticmethod(method_obj))

    pass


class ComplexClass(str):
    static_a = 0

    @staticmethod
    def just_my_function():
        time.sleep(0.1)
        time.sleep(1)

    @classmethod
    def just_my_function2(cls):
        cls.just_my_function()

    def just_my_function3(self):
        self.just_my_function()
        time.sleep(0.1)
        time.sleep(1)


def classic_function():
    time.sleep(0.1)
    time.sleep(1)


def main():
    import time
    time.sleep(1)
    classic_function()
    my_class = ComplexClass()
    my_class.static_a = 2
    my_class.just_my_function3()
    my_class.just_my_function2()
    my_class.just_my_function()
    ComplexClass.just_my_function2()
    ComplexClass.just_my_function()
    print("Profiling test completed.")


if __name__ == "__main__":
    make_all_profiling_in_module(globals())
    main()
