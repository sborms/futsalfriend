import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Vanity Stats", page_icon="😏", layout="wide")

def filter_stats(df_stats_agg, df_filt, min_w):
    df_stats = df_stats_agg.query(f"Games >= {min_w}").merge(
        df_filt,
        on=["Name", "Team"],
        how="inner",
    )[["Name", "Team", "Games", "Goals", "Assists", "(G+A)/W"]]

    return df_stats


def filter_players(df, dict_filters):
    for cname, filter in dict_filters.items():
        if len(filter) > 0:
            df = df[df[cname].isin(filter)]

    return df


import queries
df_players = queries.query_players()
df_stats_agg = queries.query_stats_agg()

##################
########## UI   ##
##################

st.title("Vanity Stats")
st.markdown("### Analyze player-level game performance")

st.markdown("Leave a filter blank to select all available options.")

# iteratively propose and adjust filters
dict_filters = {}

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    dict_filters.update({"Area": st.multiselect("Areas", df_players["Area"].unique())})
    df_players = filter_players(df_players, dict_filters)
with col2:
    dict_filters.update(
        {"Region": st.multiselect("Regions", df_players["Region"].unique())}
    )
    df_players = filter_players(df_players, dict_filters)
with col3:
    dict_filters.update(
        {
            "Competition": st.multiselect(
                "Competitions", df_players["Competition"].unique()
            )
        }
    )
    df_players = filter_players(df_players, dict_filters)

with col4:
    dict_filters.update({"Team": st.multiselect("Teams", df_players["Team"].unique())})
    df_players = filter_players(df_players, dict_filters)
with col5:
    dict_filters.update(
        {"Name": st.multiselect("Players", df_players["Name"].unique())}
    )
    df_players = filter_players(df_players, dict_filters)

df_players = df_players.drop(
    columns=["Area", "Region", "Competition"]
).drop_duplicates()  # avoid goals to be double-counted due to source data issues

st.markdown("#### All-time statistics")

# get desired metric, minimum number of games played, and plot type
col1, col2, col3, _ = st.columns(4)
stat_col = col1.selectbox(
    "Statistic", ["Games", "Goals", "Assists", "(G+A)/W"], index=1
)
min_w = col2.number_input("Minimum games", min_value=1, value=5, step=1)
fig_type = col3.selectbox("Plot type", ["Bar", "Scatter"])

# filter stats
df_sel = filter_stats(df_stats_agg, df_players, min_w)
df_sel.sort_values(stat_col, ascending=False, inplace=True)

# plot stats if button clicked
button = st.button("Show", on_click=st.cache_data.clear())
if button:
    if fig_type == "Bar":
        fig = px.bar(
            df_sel,
            x="Name",
            y=stat_col,
            color="Team",
            category_orders={"Name": df_sel["Name"]},
        )
    elif fig_type == "Scatter":
        fig = px.scatter(
            df_sel, x="Games", y=stat_col, color="Team", hover_data=["Name"]
        )
        fig.update_traces(marker_size=10)

    st.plotly_chart(fig, use_container_width=True)
