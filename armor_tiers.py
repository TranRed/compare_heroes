import requests
import pandas as pd
import streamlit as st
import altair as alt
import datetime

ARMOR_TIERS = (1, 2, 3, 4, 5, 6, 7)
TIMEFRAMES = ("Current Patch", "Last 7 days", "Last 3 days")
TIMEFRAME_URL_PARAMETERS = {"Last 7 days": "past-seven",
                            "Last 3 days": "past-three",
                            "Current Patch": "last-patch"}

SUBMIT_ISSUE_URL = "https://github.com/TranRed/armor_tiers/issues/new?"
BUG_REPORT_PARAMETERS = "assignees=&labels=&template=bug_report.md&title=%5BBUG%5D+your+title"
FEATURE_SUGGESTION_PARAMETER = "assignees=&labels=&template=feature_request.md&title=%5BFEATURE%5D+your+title"

def call_api(url):
    api_response = requests.get(url)
    update_time = datetime.datetime.now(datetime.timezone.utc)
    return api_response.json(), update_time

@st.cache_data(show_spinner=False, ttl=1800)
def load_firestone(timeframe):
    # get firestone averages
    api_url = 'https://static.zerotoheroes.com/api/bgs/heroes/bgs-global-stats-all-tribes-' + timeframe + '.gz.json'
    return call_api(api_url)

@st.cache_data(show_spinner=False, ttl=7200)
def load_bgknowhow():
    # get hero names and armor tiers
    api_url = 'https://bgknowhow.com/bgjson/output/bg_heroes_all.json'
    return call_api(api_url)


@st.cache_data(show_spinner=False, ttl=1800)
def load_data(timeframe):
    firestone_json, firestone_update_time = load_firestone(timeframe)
    heroes_json, bgknowhow_update_time = load_bgknowhow()

    hero_data = pd.DataFrame(heroes_json['data'])
    hero_data.drop(columns=['nameShort', 'pool', 'health', 'armor', 'picture', 'pictureSmall', 'picturePortrait',
                            'heroPowerCost', 'heroPowerText', 'heroPowerId', 'heroPowerPicture',
                            'heroPowerPictureSmall',
                            'websites', 'isActive'], inplace=True)

    hero_data.rename(columns={'armorTier': 'armor_tier'}, inplace=True)

    hero_list = []
    for item in firestone_json['heroStats']:
        if item['mmrPercentile'] == 10:
            hero_series = pd.Series({'id': item['cardId'],
                                     'total_matches': item['totalMatches'],
                                     '1': 0,
                                     '2': 0,
                                     '3': 0,
                                     '4': 0,
                                     '5': 0,
                                     '6': 0,
                                     '7': 0,
                                     '8': 0})

            for placement in item['placementDistribution']:
                hero_series[str(placement['rank'])] = placement['totalMatches']

            hero_list.append(hero_series)

    firestone_data = pd.DataFrame(hero_list)
    firestone_data['avg'] = (firestone_data['1'] * 1 +
                             firestone_data['2'] * 2 +
                             firestone_data['3'] * 3 +
                             firestone_data['4'] * 4 +
                             firestone_data['5'] * 5 +
                             firestone_data['6'] * 6 +
                             firestone_data['7'] * 7 +
                             firestone_data['8'] * 8) / firestone_data['total_matches']

    averages = pd.merge(firestone_data, hero_data, how='left', on='id')

    armor_tier_totals = averages[['armor_tier', 'total_matches']].groupby(['armor_tier'], as_index=False).sum()
    armor_tier_totals.rename(columns={'total_matches': 'armor_tier_total_matches'}, inplace=True)
    averages = pd.merge(averages, armor_tier_totals, how='left', on='armor_tier')
    averages['weighted_avg_armor'] = averages['avg'] * averages['total_matches'] / averages['armor_tier_total_matches']

    armor_averages = averages[['armor_tier', 'weighted_avg_armor', 'total_matches']].groupby(['armor_tier'],
                                                                                             as_index=False).sum()
    armor_averages['min'] = 0
    armor_averages['min_name'] = ''
    armor_averages['min_games'] = 0
    armor_averages['max'] = 0
    armor_averages['max_name'] = ''
    armor_averages['max_games'] = 0

    for index, row in armor_averages.iterrows():
        armor_averages.at[index, 'min'] = averages.loc[averages.armor_tier == int(row.armor_tier)]['avg'].min()

        armor_averages.at[index, 'min_name'] = \
            averages.loc[averages.loc[averages.armor_tier == int(row.armor_tier)].avg.idxmin()]['name']

        armor_averages.at[index, 'min_games'] = \
            averages.loc[averages.loc[averages.armor_tier == int(row.armor_tier)].avg.idxmin()]['total_matches']

        armor_averages.at[index, 'max'] = averages.loc[averages.armor_tier == int(row.armor_tier)]['avg'].max()

        armor_averages.at[index, 'max_name'] = \
            averages.loc[averages.loc[averages.armor_tier == int(row.armor_tier)].avg.idxmax()]['name']

        armor_averages.at[index, 'max_games'] = \
            averages.loc[averages.loc[averages.armor_tier == int(row.armor_tier)].avg.idxmax()]['total_matches']

    return averages, armor_averages, firestone_update_time, bgknowhow_update_time


title = st.title('Armor Tier Averages')

selected_timeframe = st.sidebar.selectbox('Time Frame', TIMEFRAMES)

heroes, armor_tiers, last_firestone_update, last_bgknowhow_update = \
    load_data(TIMEFRAME_URL_PARAMETERS[selected_timeframe])

last_firestone_update = last_firestone_update.strftime("%Y-%m-%d %H:%M:%S %Z+0")
last_bgknowhow_update = last_bgknowhow_update.strftime("%Y-%m-%d %H:%M:%S %Z+0")

st.sidebar.markdown(f"Top 10%  averages updated at:"
                    f"  \n{last_firestone_update}"
                    f"  \nprovided by [Firestone](https://www.firestoneapp.com/)")
st.sidebar.markdown(f"Armor Tiers updated at:"
                    f"  \n{last_bgknowhow_update}"
                    f"  \nprovided by [BG Know-How](https://bgknowhow.com)")

st.sidebar.markdown(f"**GitHub**"
                    f"  \n[README](https://github.com/TranRed/armor_tiers#readme)"
                    f"  \n[report a bug]({SUBMIT_ISSUE_URL}{BUG_REPORT_PARAMETERS})"
                    f"  \n[suggest a feature]({SUBMIT_ISSUE_URL}{FEATURE_SUGGESTION_PARAMETER})")

st.sidebar.markdown(f"**Links**"
                    f"  \n[BG Curve Sheet](https://www.bgcurvesheet.com/)"
                    f"  \n[Competitive BG Discord](https://discord.gg/DrmA2xWX45)"
                    f"  \n[additional resources and guides](https://www.reddit.com/r/BobsTavern/wiki/index/)")


show_min_max = st.checkbox("Show best and worse Heroes per Tier")

max_column = "weighted_avg_armor"
rounded_min = 3.8

if show_min_max:
    min_column = "min"
    max_column = "max"

    rounded_min = round(armor_tiers[min_column].min(), 1) - 0.2

rounded_max = round(armor_tiers[max_column].max(), 1)
if rounded_max <= armor_tiers[max_column].max():
    rounded_max += 0.1

bar_chart = alt.Chart(armor_tiers).mark_bar(size=75).encode(
    alt.X('armor_tier', title='Armor Tier'),
    alt.Y('weighted_avg_armor', title='Average Placement', scale=alt.Scale(domain=[rounded_min, rounded_max])),
    tooltip=[alt.Tooltip('armor_tier', title="Armor Tier"),
             alt.Tooltip('weighted_avg_armor', title="Average Placement", format=",.2f"),
             alt.Tooltip('total_matches', title="Games Played", format=",.0f")],
    color=alt.condition(alt.datum.weighted_avg_armor < armor_tiers["weighted_avg_armor"].mean(),
                        alt.value('orange'), alt.value('steelblue')))
if show_min_max:

    tick_min = alt.Chart(armor_tiers).mark_tick(
        color='red',
        thickness=50,
        size=3,
    ).encode(x='armor_tier',
             y='min',
             tooltip=[alt.Tooltip('min_name', title='Hero'),
                      alt.Tooltip('min', title="Average Placement", format=",.2f"),
                      alt.Tooltip('min_games', title="Games Played", format=",.0f")])

    tick_max = alt.Chart(armor_tiers).mark_tick(
        color='red',
        thickness=50,
        size=3
    ).encode(x='armor_tier',
             y='max',
             tooltip=[alt.Tooltip('max_name', title='Hero'),
                      alt.Tooltip('max', title="Average Placement", format=",.2f"),
                      alt.Tooltip('max_games', title="Games Played", format=",.0f")])

    error_bars = alt.Chart(armor_tiers).mark_errorbar(color='red', opacity=0.4, thickness=3).encode(
        x='armor_tier',
        y=alt.Y('min', title='Average Placement'),
        y2='max',
        tooltip=[alt.Tooltip('max', title="Worst Average", format=",.2f"),
                 alt.Tooltip('weighted_avg_armor', title="Weighted Average", format=",.2f"),
                 alt.Tooltip('min', title="Best Average", format=",.2f")])

    bar_chart = bar_chart + error_bars + tick_min + tick_max

bar_chart = bar_chart.configure_axisX(tickMinStep=1)
bar_chart = bar_chart.configure_axisY(title="Average Placement")

st.altair_chart(bar_chart, use_container_width=True)

with st.expander("Heroes per Tier"):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader("Heroes per tier")
    with col2:
        selected_tier = st.selectbox(label='Armor Tier', options=ARMOR_TIERS)

    st.table(heroes.loc[heroes.armor_tier == selected_tier, ['name', 'avg', 'total_matches']].
             set_index('name').sort_values(by='avg').
             rename(columns={"avg": "Average Placement", "total_matches": "Games played"})
             .style.format(subset=['Games played'], formatter="{:,.0f}")
             .format(subset=['Average Placement'], formatter="{:,.2f}"))

with st.expander("Compare Heroes"):
    all_heroes = heroes['name'].unique()
    all_heroes.sort()
    selected_heroes = st.multiselect('Pick the heroes you want to compare', all_heroes)

    if selected_heroes:
        hero_filter = selected_heroes
    else:
        hero_filter = all_heroes

    st.table(heroes.loc[heroes.name.isin(hero_filter), ['name', 'armor_tier', 'avg', 'total_matches']].
             set_index('name').sort_values(by='avg').
             rename(columns={"armor_tier": "Armor Tier", "avg": "Average Placement", "total_matches": "Games played"})
             .style.format(subset=['Games played'], formatter="{:,.0f}").
             format(subset=['Average Placement'], formatter="{:,.2f}"))
