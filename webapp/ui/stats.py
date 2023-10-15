import plotly.express as px
import streamlit as st


def filter_stats(df_stats_agg, df_filt, min_w):
    df_stats = df_stats_agg.query(f"wedstrijden >= {min_w}").merge(
        df_filt,
        on=["name", "team"],
        how="inner",
    )[["name", "team", "wedstrijden", "goals", "assists", "(G+A)/W"]]

    return df_stats


def filter_players(df, dict_filters):
    for cname, filter in dict_filters.items():
        if len(filter) > 0:
            df = df[df[cname].isin(filter)]

    return df


def make_page_vanity_stats(df_players, df_stats_agg):
    st.header("Display player-level game statistics")

    st.markdown("#### Filters")
    st.markdown("Leave a filter blank to select all available options.")

    dict_filters = {}

    # iteratively propose and adjust filters
    row1col1, row1col2, row1col3 = st.columns(3)
    row2col1, row2col2 = st.columns(2)

    with row1col1:
        dict_filters.update(
            {"area": st.multiselect("Areas", df_players["area"].unique())}
        )
        df_players = filter_players(df_players, dict_filters)
    with row1col2:
        dict_filters.update(
            {"region": st.multiselect("Regions", df_players["region"].unique())}
        )
        df_players = filter_players(df_players, dict_filters)
    with row1col3:
        dict_filters.update(
            {
                "competition": st.multiselect(
                    "Competitions", df_players["competition"].unique()
                )
            }
        )
        df_players = filter_players(df_players, dict_filters)
    with row2col1:
        dict_filters.update(
            {"team": st.multiselect("Teams", df_players["team"].unique())}
        )
        df_players = filter_players(df_players, dict_filters)
    with row2col2:
        dict_filters.update(
            {"name": st.multiselect("Players", df_players["name"].unique())}
        )
        df_players = filter_players(df_players, dict_filters)

    df_players = df_players.drop(columns=["area", "region", "competition"])

    st.markdown("#### All-time statistics")

    # get desired metric, minimum number of games played and plot type
    col1, col2, col3 = st.columns(3)
    with col1:
        stat_col = st.selectbox(
            "Statistic", ["Wedstrijden", "Goals", "Assists", "(G+A)/W"], index=1
        )
    with col2:
        min_w = st.number_input("Minimum games played", min_value=1, value=5, step=1)
    with col3:
        # define figtype to be "bar" or "scatter"
        fig_type = st.selectbox("Plot type", ["Bar", "Scatter"])

    # filter stats
    df_sel = filter_stats(df_stats_agg, df_players, min_w)
    df_sel.sort_values(stat_col, ascending=False, inplace=True)

    # plot stats if button clicked
    button = st.button("Show")
    if button:
        if fig_type == "Bar":
            fig = px.bar(
                df_sel,
                x="name",
                y=stat_col,
                color="team",
                category_orders={"name": df_sel["name"]},
            )
        elif fig_type == "Scatter":
            fig = px.scatter(
                df_sel, x="wedstrijden", y=stat_col, color="team", hover_data=["name"]
            )
            fig.update_traces(marker_size=10)

        st.plotly_chart(fig, use_container_width=True)
