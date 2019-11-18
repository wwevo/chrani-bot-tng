# chrani-bot-tng
Flexible, modern, and easy to extend bot/webinterface for the game 7dtd

### *Important!*
`Do use the development branch for updates, testing for bleeding edge - master is rarely updated and only meant for stable (not necessarily usable ^^)`

### Vision
After running a gameserver for several years, and using several managers and bots, I have realized one thing: They
heavily modify the game-experience. In both ways, good or bad

While many of their features add elements and experiences to the game, they also take away from the core game itself.
Having teleports to move around, having protected stuff and areas, item shops...

The aim of this bot is to not alter the games experience by much, but only to add to it.
Specially for Admins/Moderators, and Builders. The casual player may not even notice that a bot is at work, apart
from the authentication process of course ^^

### Current state

* Module based functionality
* Monitor the games telnet-log
* Simple triggers to react to the telnet-log
  * player-join events are monitored to update playerdata during login/logout
  * commands can be entered into the games chat-widow and then parsed by tge bot
* Central Database with access triggers
* Socket/Push based webinterface that is triggered by changes to the database
* Widget system to easily extend the webinterface
* Multiple Servers can be managed with one bot (simplified for now)
* Epic **LCARS**-Style Interface :)

* The following widgets are (partly) implemented
  * Telnet-log widget
  * Player-table widget (delete, login-status, info, kick)
  * Location widget (create, edit, delete, records time and place of death)
  * (Timed) Remote shutdown procedure
  * Simple gametime display
  * permissions widget to gate commands
    * a location can be designated as a Lobby to keep people in
    * a password can be used to authenticate a player, for example, to give them the ability to leave the Lobby 

  
### Future
Functions will gradually be added. One at a time

Next up is the batch-processing of selected elements. So kicking, banning and other stuff can be done swiftly
This of course requires the implementation of kicking and banning ^^

The ability to execute telnet commands from within the webinterface is also on the list of things to do this week :)

With those in place we can start on the authentication again and get the place safe(r) 