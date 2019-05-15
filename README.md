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
  Widgets can have different "widget-views"
  The following widgets are (partly) implemented
  * Telnet-log widget
  * Player-table widget
  * (Timed) Remote shutdown procedure
  * Simple gametime display
  * Whitelist widget dummy, to be continued once the "widget-views" are done
  
### Future
Functions will gradually be added. One at a time

I am currently working on a view system for the widgets so we can have different pages/views, like player-infos or display options for the widget