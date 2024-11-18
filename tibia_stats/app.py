__all__ = ("app",)

import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash_iconify import DashIconify

from . import api, objects


def vocation_badge(vocation):
    vocation_mapping = {
        objects.Vocation.EK: (
            "mdi:sword",
            {"variant": "gradient", "gradient": {"from": "grey", "to": "black"}},
        ),
        objects.Vocation.K: ("mdi:sword", {"color": "grey"}),
        objects.Vocation.MS: (
            "mdi:wand",
            {"variant": "gradient", "gradient": {"from": "purple", "to": "darkblue"}},
        ),
        objects.Vocation.S: ("mdi:wand", {"color": "purple"}),
        objects.Vocation.ED: (
            "mdi:leaf",
            {
                "variant": "gradient",
                "gradient": {"from": "darkgreen", "to": "darkslategrey"},
            },
        ),
        objects.Vocation.D: ("mdi:leaf", {"color": "darkgreen"}),
        objects.Vocation.RP: (
            "mdi:bow-arrow",
            {"variant": "gradient", "gradient": {"from": "tan", "to": "darkorange"}},
        ),
        objects.Vocation.P: ("mdi:bow-arrow", {"color": "tan"}),
        objects.Vocation.NONE: ("mdi:island", {"color": "lightgrey"}),
    }
    icon, kwargs = vocation_mapping.get(vocation)
    return dmc.Badge(
        vocation,
        leftSection=DashIconify(icon=icon),
        **kwargs,
    )


def character_details(character, online):
    is_online = any(online_char.name == character.name for online_char in online)
    color = "green" if is_online else "gray"
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Tooltip(
                        label=character.last_login_human,
                        withArrow=True,
                        children=[
                            dmc.Badge(
                                character.level,
                                color=color,
                                variant="dot",
                                size="xl",
                            ),
                        ],
                    ),
                    dmc.Title(character.name, order=1),
                ],
                align="center",
            ),
            dmc.Group(
                [
                    vocation_badge(character.vocation),
                    dmc.Badge(
                        character.achievements,
                        color="goldenrod",
                        leftSection=DashIconify(icon="mdi:star"),
                    ),
                ]
            ),
            dmc.Group(
                [
                    dmc.Badge(
                        character.life,
                        color="red",
                        leftSection=DashIconify(icon="mdi:heart"),
                    ),
                    dmc.Badge(
                        character.mana,
                        color="blue",
                        leftSection=DashIconify(icon="mdi:lightning-bolt"),
                    ),
                    dmc.Badge(
                        character.cap,
                        color="tan",
                        leftSection=DashIconify(icon="mdi:weight"),
                    ),
                    dmc.Badge(
                        f"{character.min_sharing_lvl}-{character.max_sharing_lvl}",
                        color="gray",
                        leftSection=DashIconify(icon="mdi:shield"),
                    ),
                ]
            ),
        ],
    )


def level_graph(char, online, show_vocation: bool, lvl_group: int):
    chars = pd.DataFrame.from_records([c.model_dump() for c in online])
    pct = api.top_percentage(online, char.level)
    title = f"Top {100*pct:.2f}% of {len(online)} Online Chars in {char.world.name}"
    hist_kw = {"color": "vocation"} if show_vocation else {}
    try:
        nbins = int(3000 / int(lvl_group))
    except:
        nbins = 60

    fig = px.histogram(
        chars,
        marginal="rug",
        x="level",
        nbins=nbins,
        range_x=[0, 3000],
        # color_discrete_sequence=[char.world.color],
        title=title,
        hover_name="name",
        **hist_kw,
    )
    fig.add_vline(x=char.level)
    fig.add_vrect(
        x0=char.min_sharing_lvl,
        x1=char.max_sharing_lvl,
        line_width=0,
        fillcolor="blue",
        opacity=0.1,
    )
    return dash.dcc.Graph(figure=fig)


def full_details(character_name: str, show_vocation: bool, lvl_group: int):
    try:
        char = api.get_character(character_name)
        online = api.get_online_characters(char.world.name)
        return [
            dmc.Center(
                dmc.Card(
                    character_details(char, online),
                    withBorder=True,
                    shadow="sm",
                    radius="md",
                )
            ),
            level_graph(char, online, show_vocation, lvl_group),
        ]
    except Exception:
        return [
            dmc.Center(
                dmc.Alert(
                    icon=DashIconify(icon="mdi:account-warning"),
                    children=f"Unable to fetch character {character_name!r}",
                    color="red",
                ),
            )
        ]


dash._dash_renderer._set_react_version("18.2.0")

grid_options = dmc.Group(
    [
        dmc.Select(
            label="Level Group",
            id="lvl-group",
            data=[
                {"value": str(x), "label": str(x)}
                for x in [10, 20, 25, 50, 100, 200, 250, 500, 1000]
            ],
            value="50",
            size="m",
        ),
        dmc.Checkbox(label="Show vocations", id="show-vocation", checked=True),
    ],
    align="flex-end",
)

app = dash.Dash()
app.layout = dmc.MantineProvider(
    dmc.Stack(
        [
            dmc.LoadingOverlay(id="loading-overlay"),
            dmc.Center(
                dmc.Card(
                    dmc.Stack(
                        [
                            dmc.Group(
                                [
                                    dmc.TextInput(
                                        id="char-name", placeholder="Character name"
                                    ),
                                    dmc.Button("Submit", id="char-submit"),
                                ]
                            ),
                            grid_options,
                        ]
                    ),
                ),
            ),
            dmc.Stack([], id="char-details"),
        ],
        pos="relative",
    )
)

dash.clientside_callback(
    """function loading(n_clicks) { return true; }""",
    dash.Output("loading-overlay", "visible", allow_duplicate=True),
    dash.Input("char-submit", "n_clicks"),
    prevent_initial_call=True,
)

dash.clientside_callback(
    """function disable(name) { return !name; }""",
    dash.Output("char-submit", "disabled"),
    dash.Input("char-name", "value"),
)


@dash.callback(
    dash.Output("char-details", "children"),
    dash.Output("loading-overlay", "visible"),
    dash.Input("char-submit", "n_clicks"),
    dash.State("char-name", "value"),
    dash.State("show-vocation", "checked"),
    dash.State("lvl-group", "value"),
    prevent_initial_call=True,
)
def populate_details(_n, char_name, show_vocation, lvl_group):
    if not char_name:
        return dash.no_update, False

    return full_details(char_name, show_vocation, lvl_group), False


if __name__ == "__main__":
    app.run(debug=True)
