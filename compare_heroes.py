import requests
import pandas as pd
import streamlit as st
import altair as alt
import datetime
import random

TIMEFRAMES = ("Current Patch", "Last 7 days", "Last 3 days")
TIMEFRAME_URL_PARAMETERS = {"Last 7 days": "past-seven",
                            "Last 3 days": "past-three",
                            "Current Patch": "last-patch"}

SUBMIT_ISSUE_URL = "https://github.com/TranRed/compare_heroes/issues/new?"
BUG_REPORT_PARAMETERS = "assignees=&labels=&template=bug_report.md&title=%5BBUG%5D+your+title"
FEATURE_SUGGESTION_PARAMETER = "assignees=&labels=&template=feature_request.md&title=%5BFEATURE%5D+your+title"

ICON_LIST = ["🔎", "🔬", "⚗️", "🧪", "🧫", "🧬", "🧮", "📊", "👩‍🔬", "👩🏾‍🔬", "👨🏼‍🔬", "👨🏿‍🔬", "💡", "🧠"]

def call_api(url):
    api_response = requests.get(url)
    update_time = datetime.datetime.now(datetime.timezone.utc)
    return api_response.json(), update_time


@st.cache_data(show_spinner=False, ttl="21600s")
def load_firestone(timeframe):
    # get firestone averages - bypass buffer with v=1 ;)
    api_url = f'https://static.zerotoheroes.com/api/bgs/stats-v2/light/mmr-10/bgs-{timeframe}.gz.json?v=1'
    return call_api(api_url)


#@st.cache_data(show_spinner=False, ttl="21600s")
def load_bgknowhow():
    # get hero names and armor tiers
    api_url = 'https://bgknowhow.com/bgjson/output/bg_heroes_all.json'
    return call_api(api_url)


def read_google_sheets(sheet_id, tab_name):
    google_sheets = 'https://docs.google.com/spreadsheets/d/'
    gviz_prefix = '/gviz/tq?tqx=out:csv&sheet='

    return pd.read_csv(f"{google_sheets}{sheet_id}{gviz_prefix}{tab_name}")


@st.cache_data(show_spinner=False, ttl=21600)
def load_curvesheet():
    curvesheet_raw = read_google_sheets(sheet_id='1J_NuzXHEsppgrAWJzLEZwESfiiNyURo3pCBAO1ga2mE',
                                        tab_name='{Hero}')

    curves = curvesheet_raw[['Managed by Minder Heroes Hero', 'Twitter Ranking Players',
                            ' Support the Curvesheet: Patreon Curves Suggestions Main Curve',
                             'Alternative Curve', 'Questions?: Discord    Jkirek Quick Guide']].copy()
    curves.rename(columns={'Managed by Minder Heroes Hero': "name", 'Twitter Ranking Players': "Player Ranking",
                           ' Support the Curvesheet: Patreon Curves Suggestions Main Curve': "Main Curve",
                           'Questions?: Discord    Jkirek Quick Guide': 'Quick Guide'},
                  inplace=True)

    # no curve suggestions
    curves['Main Curve'].replace('X', '', inplace=True)
    curves['Alternative Curve'].replace('X', '', inplace=True)

    # fit hero names
    hero_names = read_google_sheets(sheet_id='18o-dPKSzGNZyUjP43dBuYD5heFYpKEP_Z680f8c3s8g', tab_name='{Heros}')
    hero_names.drop(columns=['HeroKey', 'French', 'Japanese'], inplace=True)

    name_replacements = hero_names.set_index('HeroName').to_dict()['Official Name']

    curves.replace({'name': name_replacements}, inplace=True)
    return curves


@st.cache_data(show_spinner=False, ttl=1800)
def load_data(timeframe):
    firestone_json, firestone_update_time = load_firestone(timeframe)
    heroes_json, bgknowhow_update_time = load_bgknowhow()
    df_curves = load_curvesheet()

    hero_data = pd.DataFrame(heroes_json['data'])
    hero_data['armorHighMMR'].fillna(hero_data['armor'], inplace=True)
    hero_data['hp'] = hero_data['health'] + hero_data['armorHighMMR']
    hero_data.drop(columns=['nameShort', 'armor', 'pool', 'picture', 'pictureSmall', 'picturePortrait',
                            'pictureWhole', 'heroPowerCost', 'heroPowerText', 'heroPowerId', 'heroPowerPicture',
                            'heroPowerPictureSmall',
                            'websites', 'isActive'], inplace=True)

    firestone_data = pd.DataFrame(firestone_json['heroStats'])
    firestone_data.rename(columns={'heroCardId': "id", 'dataPoints': "total_matches", 'averagePosition': "avg"},
                          inplace=True)

    # drop weird bob hero
    firestone_data.drop(firestone_data.loc[firestone_data['id'] == 'TB_BaconShop_HERO_PH'].index,
                        inplace=True)

    averages = pd.merge(firestone_data, hero_data, how='left', on='id')
    averages = pd.merge(averages, df_curves, how='left', on='name')

    averages.drop(averages.loc[averages['name'].isna()].index, inplace=True)

    return averages, firestone_update_time, bgknowhow_update_time


st.set_page_config(layout="wide",
                   page_icon=random.choice(ICON_LIST),
                   page_title="Compare BG Heroes",
                   )

title = st.title('Compare Heroes:')

selected_timeframe = st.sidebar.selectbox('Time Frame', TIMEFRAMES)

heroes, last_firestone_update, last_bgknowhow_update = \
    load_data(TIMEFRAME_URL_PARAMETERS[selected_timeframe])

all_heroes = heroes['name'].unique()
all_heroes.sort()

last_firestone_update = last_firestone_update.strftime("%Y-%m-%d %H:%M:%S %Z+0")
last_bgknowhow_update = last_bgknowhow_update.strftime("%Y-%m-%d %H:%M:%S %Z+0")

st.sidebar.markdown(f"Top 10%  averages updated at:"
                    f"  \n{last_firestone_update}"
                    f"  \nprovided by [Firestone](https://www.firestoneapp.com/)")

st.sidebar.markdown(f"Hero Data updated at:"
                    f"  \n{last_bgknowhow_update}"
                    f"  \nprovided by [BG Know-How](https://bgknowhow.com)")

st.sidebar.markdown(f"Rankings, curves and Quick Guides:"
                    f"  \nprovided by [BG Curve Sheet](https://www.bgcurvesheet.com/)")

st.sidebar.markdown(f"**GitHub**"
                    f"  \n[README](https://github.com/TranRed/armor_tiers#readme)"
                    f"  \n[report a bug]({SUBMIT_ISSUE_URL}{BUG_REPORT_PARAMETERS})"
                    f"  \n[suggest a feature]({SUBMIT_ISSUE_URL}{FEATURE_SUGGESTION_PARAMETER})")

st.sidebar.markdown(f"**Links**"
                    f"  \n[Competitive BG Discord](https://discord.gg/DrmA2xWX45)"
                    f"  \n[additional resources and guides](https://www.reddit.com/r/BobsTavern/wiki/index/)")

selected_heroes = st.multiselect('Pick the heroes you want to compare', all_heroes)

if selected_heroes:
    hero_filter = selected_heroes
else:
    hero_filter = all_heroes

rounded_min = round(heroes['avg'].min(), 1) - 0.1
rounded_max = round(heroes['avg'].max(), 1) + 0.1

selected_data = heroes.loc[heroes.name.isin(hero_filter)]

scatter_plot = alt.Chart(selected_data).mark_circle(size=60).encode(
                    alt.Y('hp', title='HP Total', scale=alt.Scale(domain=[30, 65])),
                    alt.X('avg', title='Average Placement', scale=alt.Scale(domain=[rounded_min, rounded_max])),
                    alt.Color('total_matches', title='Games Played',
                              scale=alt.Scale(scheme="redblue",
                                              domain=[heroes.total_matches.min(), heroes.total_matches.max()],
                                              reverse=True)),
                    tooltip=[alt.Tooltip('name', title='Hero'),
                             alt.Tooltip('Quick Guide'),
                             alt.Tooltip('avg', title="Average Placement", format=",.2f"),
                             alt.Tooltip('total_matches', title="Games Played", format=",.0f"),
                             alt.Tooltip('hp', title='HP total'),
                             alt.Tooltip('health', title='Health'),
                             alt.Tooltip('armorHighMMR', title='Armor (High MMR)')]
                ).interactive()
st.caption("Hover for Jkirek Quick Guide")

st.altair_chart(scatter_plot, use_container_width=True)

st.dataframe(selected_data[['name', 'armorHighMMR', 'Player Ranking', 'avg',  'total_matches',
                            'Main Curve', 'Alternative Curve']]
             .rename(columns={"name": "Hero", "armorHighMMR": "Armor", "avg": "Avg.",
                              "total_matches": "Games", "Player Ranking": "Ranking"})
             .set_index('Hero').sort_values(by="Avg.")
             .style.format(subset=['Games', "Armor"], formatter="{:,.0f}")
             .format(subset=['Avg.'], formatter="{:,.2f}"), use_container_width=True)
