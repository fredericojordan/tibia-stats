__all__ = ("app",)

import dash
import dash_mantine_components as dmc
import pandas as pd
import plotly.express as px
from dash_iconify import DashIconify
from rich import print


def vocation_badge(vocation):
    vocation_mapping = {
        tibia_stats.Vocation.EK: (
            "mdi:sword",
            {"variant": "gradient", "gradient": {"from": "grey", "to": "black"}},
        ),
        tibia_stats.Vocation.K: ("mdi:sword", {"color": "grey"}),
        tibia_stats.Vocation.MS: (
            "mdi:wand",
            {"variant": "gradient", "gradient": {"from": "purple", "to": "darkblue"}},
        ),
        tibia_stats.Vocation.S: ("mdi:wand", {"color": "purple"}),
        tibia_stats.Vocation.ED: (
            "mdi:leaf",
            {
                "variant": "gradient",
                "gradient": {"from": "darkgreen", "to": "darkslategrey"},
            },
        ),
        tibia_stats.Vocation.D: ("mdi:leaf", {"color": "darkgreen"}),
        tibia_stats.Vocation.RP: (
            "mdi:bow-arrow",
            {"variant": "gradient", "gradient": {"from": "tan", "to": "darkorange"}},
        ),
        tibia_stats.Vocation.P: ("mdi:bow-arrow", {"color": "tan"}),
        tibia_stats.Vocation.NONE: ("mdi:island", {"color": "lightgrey"}),
    }
    icon, kwargs = vocation_mapping.get(vocation)
    return dmc.Badge(
        vocation,
        leftSection=DashIconify(icon=icon),
        **kwargs,
    )


def character_details(character):
    return dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Title(character.name, order=1),
                    dmc.Badge(
                        character.level, color="black", variant="light", size="xl"
                    ),
                ],
                align="center",
            ),
            vocation_badge(character.vocation),
            dmc.Group(
                [
                    dmc.Badge(
                        character.max_life,
                        color="red",
                        leftSection=DashIconify(icon="mdi:drop"),
                    ),
                    dmc.Badge(
                        character.max_mana,
                        color="blue",
                        leftSection=DashIconify(icon="mdi:flask"),
                    ),
                ]
            ),
        ],
    )


def level_graph(char, show_vocation: bool):
    online = tibia_stats.get_online_characters(char.world.name)
    chars = pd.DataFrame.from_records([c.model_dump() for c in online])
    pct = tibia_stats.top_percentage(online, char.level)
    title = f"Top {100*pct:.2f}% of {len(online)} Online Chars in {char.world.name}"
    hist_kw = {"color": "vocation"} if show_vocation else {}
    fig = px.histogram(
        chars,
        marginal="rug",
        x="level",
        nbins=28,
        range_x=[0, 2800],
        # color_discrete_sequence=[char.world.color],
        title=title,
        hover_name="name",
        **hist_kw,
    )
    fig.add_vline(x=char.level)
    fig.add_vrect(
        x0=tibia_stats.utils.min_sharer(char.level),
        x1=tibia_stats.utils.max_sharer(char.level),
        line_width=0,
        fillcolor="blue",
        opacity=0.1,
    )
    return dash.dcc.Graph(figure=fig)


def full_details(character_name: str, show_vocation: bool):
    char = tibia_stats.get_character(character_name)
    return [
        dmc.Center(character_details(char)),
        level_graph(char, show_vocation),
    ]


dash._dash_renderer._set_react_version("18.2.0")

app = dash.Dash()
app.layout = dmc.MantineProvider(
    dmc.Stack(
        [
            dmc.LoadingOverlay(id="loading-overlay"),
            dmc.Stack(
                [
                    dmc.TextInput(id="char-name"),
                    dmc.Checkbox(label="Show vocation", id="show-vocation"),
                    dmc.Group(dmc.Button("Submit", id="char-submit")),
                ]
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
    prevent_initial_call=True,
)
def populate_details(_n, char_name, show_vocation):
    if not char_name:
        return dash.no_update, False

    return full_details(char_name, show_vocation), False


if __name__ == "__main__":
    app.run(debug=True)
