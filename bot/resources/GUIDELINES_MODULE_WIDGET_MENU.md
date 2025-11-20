### Add a menu button and view to a module widget (How‑To)

This guide explains how to add a new button to a widget's pull‑out menu and display a corresponding screen ("view"). It follows the menu pattern used in the `locations` module and the example implemented in the `telnet` module.

The pattern consists of four parts:
- A view registry in the widget Python file that defines available views and their labels.
- A shared Jinja2 macro `construct_view_menu` to render the menu.
- A small widget template `control_view_menu.html` that invokes the macro for the module.
- A server action `toggle_<module>_widget_view` that switches the current view.

Below, `<module>` stands for your module name (e.g., `telnet`, `locations`), and `<view_id>` is the identifier of the view you are adding (e.g., `test`).

---

#### 1) Ensure the view menu macro is available for your module

Your module's Jinja2 macros file (e.g., `bot/modules/<module>/templates/jinja2_macros.html`) should contain the macro `construct_view_menu`. If your module doesn't have it yet, mirror the implementation from:
- `bot/modules/locations/templates/jinja2_macros.html`

The macro expects these parameters:
- `views`: dict of view entries (see step 2)
- `current_view`: name of the active view
- `module_name`: the module identifier (e.g., `telnet`)
- `steamid`: the current user's steamid
- `default_view`: the view to return to from an active state (usually `frontend`)

The macro renders toggle links that emit the standard socket event:
```
['widget_event', [module_name, ['toggle_' ~ module_name ~ '_widget_view', {'steamid': steamid, 'action': action}]]]
```

---

#### 2) Define or extend the VIEW_REGISTRY in the widget Python file

In your widget file (e.g., `bot/modules/<module>/widgets/<widget_name>.py`) define a `VIEW_REGISTRY` mapping of view IDs to config objects. Each entry can have:
- `label_active`: label when this view is currently active (typically `back`)
- `label_inactive`: label when the view is not active (e.g., `options`, `test`)
- `action`: the action string to be sent by the menu (e.g., `show_options`, `show_test`)
- `include_in_menu`: whether to show it in the menu (set `False` for base `frontend`)

Example (excerpt with a new `test` view):
```python
VIEW_REGISTRY = {
    'frontend': {
        'label_active': 'back',
        'label_inactive': 'main',
        'action': 'show_frontend',
        'include_in_menu': False
    },
    'options': {
        'label_active': 'back',
        'label_inactive': 'options',
        'action': 'show_options',
        'include_in_menu': True
    },
    'test': {
        'label_active': 'back',
        'label_inactive': 'test',
        'action': 'show_test',
        'include_in_menu': True
    }
}
```

Update `select_view` to route to your new view:
```python
def select_view(*args, **kwargs):
    module = args[0]
    dispatchers_steamid = kwargs.get('dispatchers_steamid', None)
    current_view = module.get_current_view(dispatchers_steamid)
    if current_view == 'options':
        options_view(module, dispatchers_steamid=dispatchers_steamid)
    elif current_view == 'test':
        test_view(module, dispatchers_steamid=dispatchers_steamid)
    else:
        frontend_view(module, dispatchers_steamid=dispatchers_steamid)
```

---

#### 3) Create the control_view_menu.html template for the widget

Create a template next to your widget's templates folder that renders the menu by importing the macro and passing the registry:

`bot/modules/<module>/templates/<widget_name>/control_view_menu.html`
```jinja2
{%- from 'jinja2_macros.html' import construct_view_menu with context -%}
<div id="<widget_dom_id>_options_toggle" class="pull_out right">
    {{ construct_view_menu(
        views=views,
        current_view=current_view,
        module_name='<module>',
        steamid=steamid,
        default_view='frontend'
    )}}
</div>
```

Replace `<widget_dom_id>` with the widget DOM id (e.g., `telnet_table_widget_options_toggle`), and `<module>` with the module name literal (e.g., `telnet`).

---

#### 4) Render the menu in each view and add your new view function

In every view function (`frontend_view`, `options_view`, and your new `test_view`) render the menu and include it into the page as `options_toggle`:

```python
template_view_menu = module.templates.get_template('<widget_name>/control_view_menu.html')
current_view = module.get_current_view(dispatchers_steamid)
options_toggle = module.template_render_hook(
    module,
    template=template_view_menu,
    views=VIEW_REGISTRY,
    current_view=current_view,
    steamid=dispatchers_steamid
)

data_to_emit = module.template_render_hook(
    module,
    template=template_for_this_view,
    options_toggle=options_toggle,
    # ... other template params ...
)
```

Create the new view template (e.g., `view_test.html`) that uses the aside area to render the menu:
```jinja2
<header>
    <div>
        <span>Some Title</span>
    </div>
</header>
<aside>
{{ options_toggle }}
</aside>
<main>
    <table>
        <thead>
            <tr>
                <th>Test View</th>
            </tr>
        </thead>
        <tbody>
            <tr><td><span>Test</span></td></tr>
        </tbody>
    </table>
</main>
```

---

#### 5) Wire the server action to toggle views

Each module has an action named `toggle_<module>_widget_view` that updates the current view for a dispatcher. Extend it to support your new action string (`show_<view_id>`):

`bot/modules/<module>/actions/toggle_<module>_widget_view.py`
```python
def main_function(module, event_data, dispatchers_steamid):
    action = event_data[1].get('action', None)
    event_data[1]['action_identifier'] = action_name

    if action == 'show_options':
        current_view = 'options'
    elif action == 'show_frontend':
        current_view = 'frontend'
    elif action == 'show_test':
        current_view = 'test'
    else:
        module.callback_fail(callback_fail, module, event_data, dispatchers_steamid)
        return

    module.set_current_view(dispatchers_steamid, {
        'current_view': current_view
    })
    module.callback_success(callback_success, module, event_data, dispatchers_steamid)
```

Make sure the view ID you set here matches the view IDs used in `VIEW_REGISTRY` and `select_view`.

---

#### 6) Reference implementation to compare

Use these files as working examples:
- Locations menu macro: `bot/modules/locations/templates/jinja2_macros.html`
- Locations widget menu template: `bot/modules/locations/templates/manage_locations_widget/control_view_menu.html`
- Telnet macros with menu: `bot/modules/telnet/templates/jinja2_macros.html`
- Telnet menu template: `bot/modules/telnet/templates/telnet_log_widget/control_view_menu.html`
- Telnet widget with added view: `bot/modules/telnet/widgets/telnet_log_widget.py`
- Telnet action wiring: `bot/modules/telnet/actions/toggle_telnet_widget_view.py`
- Telnet new view template: `bot/modules/telnet/templates/telnet_log_widget/view_test.html`

---

#### 7) Quick checklist

- [ ] `VIEW_REGISTRY` contains your `<view_id>` with a correct `action` (`show_<view_id>`) and `include_in_menu = True`.
- [ ] `select_view` routes to `<view_id>` by calling `<view_id>_view`.
- [ ] The new `<view_id>_view` renders `options_toggle` using `control_view_menu.html`.
- [ ] The new view has a template and includes `{{ options_toggle }}` in the aside.
- [ ] The module's `toggle_<module>_widget_view` action handles `show_<view_id>` and sets `current_view` accordingly.
- [ ] Menu renders without errors and buttons switch between views (`back` returns to `frontend`).

---

#### Notes

- Keep naming consistent: action strings are `show_<view_id>`, event name is `toggle_<module>_widget_view`.
- The base view `frontend` is usually not included in the menu (`include_in_menu: False`), but is the `default_view` used for the "back" behavior.
- Follow the module's existing code style and avoid unrelated refactors when introducing new views/buttons.
