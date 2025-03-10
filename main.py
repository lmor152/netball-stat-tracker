from dataclasses import dataclass
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide")

# Initialize session state
if "game" not in st.session_state:
    st.session_state.game = None
if "quarter" not in st.session_state:
    st.session_state.quarter = 1
if "plays" not in st.session_state:
    st.session_state.plays = []
if "game_finished" not in st.session_state:
    st.session_state.game_finished = False
if "shooting" not in st.session_state:
    st.session_state.shooting = {}


@dataclass
class Game:
    date: date
    opposition: str
    team: list[str]
    venue: str


# use the sidebar to display stats in progress for the quarter
with st.sidebar:
    st.header("Quarter Stats")

    if st.session_state.plays:
        df = pd.DataFrame(st.session_state.plays)

        summary = df.groupby(["quarter", "play_start"]).agg(
            {"shot_made": lambda x: "{:.0%}".format(x.sum() / x.count())}
        )

        for q, qdf in summary.groupby("quarter"):
            formatted = (
                qdf.reset_index()
                .rename(columns={"shot_made": "Shot %", "play_start": "Play Start"})[
                    ["Play Start", "Shot %"]
                ]
                .set_index("Play Start")
                .sort_index()
            )
            st.divider()
            st.subheader(f"Quarter {q}")
            st.table(formatted)


# Game setup
def setup_game() -> None:
    st.header("Game Setup")

    game_date = st.date_input("Game Date")
    opposition = st.text_input("Opposition")
    venue = st.text_input("Venue")
    players = st.text_area("Enter player names (comma separated)").split(",")
    if st.button("Start Game"):
        st.session_state.game = True
        st.session_state.game = Game(
            date=game_date,
            opposition=opposition,
            team=players,
            venue=venue,
        )
        st.toast("Game setup complete!")
        st.rerun()


def enter_play() -> None:
    col1, col2 = st.columns(2, gap="large")
    with col1:
        play_form()

    with col2:
        shooting_form()

    st.divider()

    if st.session_state.quarter == 4:
        if st.button("Finish Match"):
            st.session_state.game_finished = True
            st.rerun()
    else:
        if st.button("Next Quarter", type="primary"):
            st.session_state.quarter += 1
            st.rerun()


def shooting_form() -> None:
    quarter_number = st.session_state.quarter
    st.title(f"Shot Tracker for Q{quarter_number}")

    c1, c2 = st.columns(2)

    def add_shots(player: str, made: bool) -> None:
        if quarter_number not in st.session_state.shooting:
            st.session_state.shooting[quarter_number] = {}

        if player not in st.session_state.shooting[quarter_number]:
            st.session_state.shooting[quarter_number][player] = {
                "Scored": 0,
                "Missed": 0,
            }

        if made:
            st.session_state.shooting[quarter_number][player]["Scored"] += 1
        else:
            st.session_state.shooting[quarter_number][player]["Missed"] += 1

    for player in st.session_state.game.team:
        with c1:
            try:
                shots_so_far = st.session_state.shooting[quarter_number][player][
                    "Missed"
                ]
            except KeyError:
                shots_so_far = 0

            st.button(
                f"🗑️😢 {player} Missed ({shots_so_far})",
                on_click=lambda player=player: add_shots(player, False),
                use_container_width=True,
                type="secondary",
            )
        with c2:
            try:
                shots_so_far = st.session_state.shooting[quarter_number][player][
                    "Scored"
                ]
            except KeyError:
                shots_so_far = 0

            st.button(
                f"🏀🎉 {player} Scored ({shots_so_far})",
                on_click=lambda player=player: add_shots(player, True),
                use_container_width=True,
                type="secondary",
            )


def play_form() -> None:
    dropdown_options = [""] + st.session_state.game.team
    play_dict = {"quarter": st.session_state.quarter}

    st.title(f"Enter Play for Q{st.session_state.quarter}")

    play_start = st.pills("Play Start", ["Centre Pass", "Turnover"], key="play_start")

    play_dict["play_start"] = play_start

    if play_start == "Turnover":
        turnover_type = st.selectbox(
            "Turnover Type",
            [
                "Pick up",
                "Intercept",
                "Rebound",
                "Opposition error",
                "Out of Court",
                "Other",
            ],
        )

        who_turnover = st.selectbox("Who got the turnover", dropdown_options)

        play_dict["turnover_type"] = turnover_type
        play_dict["who_turnover"] = who_turnover

    if play_start != "Turnover":
        receiver = st.selectbox("Receiver", dropdown_options)
        play_dict["receiver"] = receiver

    play = st.pills("Play", ["Circle Edge Feed", "Long Feed", "Lost"])
    play_dict["play"] = play

    if play == "Lost":
        loss_type = st.selectbox(
            "How was it lost?",
            [
                "Bad Pass",
                "Bad Hands",
                "Missed Shot",
                "Out of Court",
                "Step",
                "Held",
                "Short Pass",
                "Other",
            ],
        )
        play_dict["loss_type"] = loss_type

        who_lost = st.selectbox("Who lost", dropdown_options)
        play_dict["who_lost"] = who_lost

    if play != "Lost":
        who_played = st.selectbox("Who made the play", dropdown_options)
        play_dict["who_played"] = who_played

        shot_made = st.checkbox("Scored?")
        play_dict["shot_made"] = shot_made

    if st.button("Submit Play"):
        st.session_state.plays.append(play_dict.copy())
        st.toast("Play recorded!")
        st.rerun()


# Main app logic
if not st.session_state.game:
    setup_game()
elif not st.session_state.game_finished:
    enter_play()
else:
    st.title("Game Summary")
    df = pd.DataFrame(st.session_state.plays)

    data = [
        {
            "Player": player,
            "Quarter": quarter,
            "Scored": stats["Scored"],
            "Missed": stats["Missed"],
        }
        for quarter, players in st.session_state.shooting.items()
        for player, stats in players.items()
    ]

    # Construct the DataFrame
    shooting = pd.DataFrame(data)

    st.subheader("Quarters Shooting Summary")
    st.dataframe(shooting)

    st.subheader("Game Shooting Summary")
    st.dataframe(shooting.groupby("Player").agg({"Scored": "sum", "Missed": "sum"}))

    # Shooting Percentages by Player
    st.header("Shooting Percentages by Player")
    shooting["Total"] = shooting["Scored"] + shooting["Missed"]
    shooting["Percentage"] = (
        shooting["Scored"] / shooting["Total"].replace(0, 1)
    ) * 100  # Replace 0 with 1 to avoid division by 0
    shooting_summary = (
        shooting.groupby("Player")
        .agg({"Scored": "sum", "Missed": "sum", "Total": "sum", "Percentage": "mean"})
        .reset_index()
    )
    fig1 = px.bar(
        shooting_summary,
        x="Player",
        y="Percentage",
        title="Shooting Percentage by Player",
        labels={"Player": "Player", "Percentage": "Shooting Percentage (%)"},
    )
    st.plotly_chart(fig1)

    # Shooting Percentages by Quarter
    st.header("Shooting Percentages by Quarter")
    shooting_quarter_summary = (
        shooting.groupby(["Player", "Quarter"])
        .agg({"Scored": "sum", "Missed": "sum", "Total": "sum", "Percentage": "mean"})
        .reset_index()
    )
    fig2 = px.line(
        shooting_quarter_summary,
        x="Quarter",
        y="Percentage",
        color="Player",
        title="Shooting Percentage by Quarter",
        labels={"Quarter": "Quarter", "Percentage": "Shooting Percentage (%)"},
    )
    st.plotly_chart(fig2)

    # Turnovers by Player
    st.header("Turnovers")
    turnovers = df[df["who_turnover"].notna()]["who_turnover"].value_counts()
    fig2 = px.bar(
        turnovers, x=turnovers.index, y=turnovers.values, title="Turnovers by Player"
    )
    fig2.update_layout(xaxis_title="Player", yaxis_title="Number of Turnovers")
    st.plotly_chart(fig2)

    # Lost Plays by Player
    st.header("Lost Plays")
    lost_plays = df[df["who_lost"].notna()]["who_lost"].value_counts()
    fig3 = px.bar(
        lost_plays,
        x=lost_plays.index,
        y=lost_plays.values,
        title="Lost Plays by Player",
    )
    fig3.update_layout(xaxis_title="Player", yaxis_title="Number of Lost Plays")
    st.plotly_chart(fig3)

    # Play Conversion Rates
    st.header("Play Conversion Rates")
    conversion_stats = df.groupby("play")["shot_made"].agg(["count", "sum"])
    conversion_stats["conversion_rate"] = (
        conversion_stats["sum"] / conversion_stats["count"].replace(0, 1)
    ) * 100  # Replace 0 with 1 to avoid division by 0
    fig4 = px.bar(
        conversion_stats,
        x=conversion_stats.index,
        y="conversion_rate",
        title="Play Conversion Rate by Play Type",
    )
    fig4.update_layout(xaxis_title="Play Type", yaxis_title="Conversion Rate (%)")
    st.plotly_chart(fig4)

    # Play Type Distribution
    st.header("Play Type Distribution")
    play_counts = df["play"].value_counts()
    fig5 = px.pie(
        play_counts,
        names=play_counts.index,
        values=play_counts.values,
        title="Play Type Distribution",
    )
    fig5.update_layout(xaxis_title="Play Type", yaxis_title="Count")
    st.plotly_chart(fig5)

    # Turnover Causes
    st.header("Turnover Causes")
    turnover_causes = df[df["loss_type"].notna()]["loss_type"].value_counts()
    fig6 = px.bar(
        turnover_causes,
        x=turnover_causes.index,
        y=turnover_causes.values,
        title="Causes of Turnovers",
    )
    fig6.update_layout(xaxis_title="Turnover Cause", yaxis_title="Count")
    st.plotly_chart(fig6)

    # Game Flow (Quarter-wise plays)
    st.header("Game Flow")
    quarter_counts = df.groupby(["quarter", "play"]).size().reset_index(name="count")
    quarter_counts["count"] = quarter_counts["count"].replace(
        0, 1
    )  # Replace 0 with 1 to avoid division by 0
    fig7 = px.line(
        quarter_counts,
        x="quarter",
        y="count",
        color="play",
        title="Game Flow by Quarter",
    )
    fig7.update_layout(xaxis_title="Quarter", yaxis_title="Number of Plays")
    st.plotly_chart(fig7)
