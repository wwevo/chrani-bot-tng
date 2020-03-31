# default options
Store default configurations for your modules

## naming scheme
Name the config file exactly the same as the module_identifier / the directory-name of the module with a prepended
"module_" and an appended ".json".
For example: The default options file for the module "webserver" would become "module_webserver.json"

## priorities
If no config file or database is found, the hardcoded ones from the module will be used
Options-file settings will override hardcoded module settings
Database settings will override the options-file settings

## minimum settings for 7dtd:
### setting up the telnet component
host would be your IP address, or if the bot is on the same machine, localhost  
port + password is what you have set up in your 7dtd serverconfig  

    chrani-bot-tng/bot/options/module_telnet.json
> {  
>     "host": "127.0.0.1",  
>     "port": 26902,  
>     "password": "supersecret"  
> }  

You might want to set the telnet buffer to a higher value if you have a high-pop server or are using mods like
Darkness Falls. the standard 16k is too small for extensive amount of entities
> "max_telnet_buffer": 32768
	
### setting up the webserver component
host would be your servers public IP address
port and secret-key can be whatever you feel is clever

    chrani-bot-tng/bot/options/module_webserver.json
> {  
>     "host": "YOUR PUBLIC SERVER IP",  
>     "port": 26905,  
>     "Flask_secret_key": "whateverisclever"  
> }

With those two files in place and some sensible data to populate them, the bot should start up and provide it's
webinterface and should start listening to the games telnet.
