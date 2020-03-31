# chrani-bot-tng
Flexible, modern, and easy to extend bot/webinterface for the game 7dtd

### *Important!*
`Do use the development branch for updates - master is rarely updated and only meant for
stable (not necessarily usable ^^), and testing is the bleeding edge branch that might be broken or full of bugs.
It's usually not though :)`

### Vision
After running a gameserver for several years, and using several managers and bots, I have realized one thing: They
heavily modify the game-experience. In both ways, good or bad

While many of their features add elements and experiences to the game, they also take away from the core game itself.
Having teleports to move around, having protected stuff and areas, item shops...

The aim of this bot is to not alter the games experience by much, but only to add to it.
Specially for Admins/Moderators, and Builders. The casual player may not even notice that a bot is at work, apart
from the authentication process of course ^^

### Current state
The bot works on any Vanilla install, and basic functions will work right out of the box.
For more advanced stuff like hiding chat-commands or exporting prefabs, you will need add a few server-side mods.

There's a fairly [comprehensive installation guide on the projects-wiki](https://github.com/wwevo/chrani-bot-tng/wiki/Installation) 

I've been testing the bot with Vanilla, Alloc's + BCM server-mods and the latest Darkness Falls Stable.

#### Core Functions
* Module based functionality
  * new modules can be added easily and without altering any of the bots files, just drop it in and start using them

* Trigger-based actions and reactions  
  * any telnet log output can be parsed for triggers, using regular expressions
  * any database access can be monitored for triggers, using set paths
  * any user-input from the webinterface... well... yeah of course that is monitored :)

* Socket/Push based, **LCARS**-Style Interface :)
  * Steam-login for authentication
  * Widget system to easily extend the webinterface

#### Modules:
* Telnet-log widget

* Player-table widget (delete, login-status, info, kick)
  * kick players with a custom message
  * view basic info like kills, deaths, last time online etc.

* Location widget (create, edit, delete, records time and place of death)
  * a location can be designated as a Lobby to keep people in
  * locations can be made screamer-proof, all screamers will be killed on spawn
  * locations can be set up as a home, with a dedicated teleport entry
  * locations can be set up as a village, there's no attached functionality as of yet
  * a place of death location will be updated on every player-death
  * locations can be exported and restored if they are of the 'box' type and BCM is installed

* (Timed) Remote shutdown procedure
  * timer is fixed to 30 seconds currently

* Simple gametime display
  * Will show the next Bloodmoon

* Entity widget
  * simply shows all active entities

* Permissions widget to gate commands
  * a password can be used to authenticate a player, for example, to give them the ability to leave the Lobby 
  