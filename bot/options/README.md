###### `Do use the development branch for updates, testing for bleeding edge - master is rarely updated and only meant for stable (not necessarily usable ^^)`

# default options
Store default configurations for your modules

### naming scheme
Name the config file exactly the same as the module_identifier / the directory-name of the module with a prepended "module_" and an appended ".json".
For example: The default options file for the module "webserver" would become "module_webserver.json"

### priorities
If no config file or database is found, the hardcoded ones from the module will be used
Options-file settings will override hardcoded module settings
Database settings will override the options-file settings
