# chrani-bot-tng
Flexible, modern, and easy to extend bot/webinterface for the game 7dtd

### Current state

* Epic **LCARS**-Style Interface :)
* Module based functionality
* Monitor the games telnet-log
* Simple triggers to react to the telnet-log
  * player-join events are monitored to update playerdata during login
* Central Database with access triggers
* Socket/Push based webinterface that is triggered by changes to the database
* Widget system to easily extend the webinterface


* The following widgets are (partly) implemented
  * Telnet-log widget
  * Player-table widget (login-status, info, kick)
  * (Timed) Remote shutdown procedure
  * Simple gametime display
  * Whitelist widget (enable/disable, add/remove user)
  
### Future
Functions will gradually be added. One at a time

I am currently working on a locations-widget for players to create snd manage in-game locations 