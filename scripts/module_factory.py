class ClsModuleFactory:
    @staticmethod
    def get_module(config, connection_handler):
        module = {
            "http": ClsModuleFactory.http_module
        }.get(
            config.getValue("default", "module"),
            ClsModuleFactory.http_module
        )

        return module(config, connection_handler)

    @staticmethod
    def http_module(config, connection_handler):
        from scripts.http_module_util import HTTPmodule
        return HTTPmodule(config, connection_handler)
