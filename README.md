# chrani-bot-tng
Flexible, modern, and easy to extend bot/webinterface for the game 7dtd

### Current state
* Module based functionality
* Monitor the games telnet-log
* Simple triggers to react to the telnet-log
  * player-join events are monitored to update playerdata during login
* Central Database with access triggers
* Socket/Push based webinterface that is triggered by changes to the database
* Widget system to easily extend the webinterface
  * Telnet-log widget
  * Player-table widget
  * (Timed) Remote shutdown procedure
  * Simple gametime display
  
### Future
Functions will gradually be added. One at a time
