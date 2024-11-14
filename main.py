from scripts.UI import run_ui
from scripts.config_handler import ClsConfigParser
from scripts.cli_connector import ClsCliConnector
from scripts.module_factory import ClsModuleFactory


def main():
    with ClsConfigParser() as config:
        with ClsCliConnector(config) as connection_handler:
            playerUtil = ClsModuleFactory.get_module(
                config, connection_handler
            )
            run_ui(config, connection_handler, playerUtil)


if __name__ == '__main__':
    main()
