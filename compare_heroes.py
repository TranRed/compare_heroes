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

@st.cache_data(show_spinner=False, ttl=21600)
def load_firestone(timeframe):
    # get firestone averages
    api_url = 'https://static.zerotoheroes.com/api/bgs/heroes/bgs-global-stats-all-tribes-' + timeframe + '.gz.json'
    return call_api(api_url)

@st.cache_data(show_spinner=False, ttl=21600)
def load_bgknowhow():
    # get hero names and armor tiers
    api_url = 'https://bgknowhow.com/bgjson/output/bg_heroes_all.json'
    return call_api(api_url)

@st.cache_data(show_spinner=False, ttl=21600)
def load_curvesheet():
    google_sheets = 'https://docs.google.com/spreadsheets/d/'
    # noinspection SpellCheckingInspection
    sheet_id = '1J_NuzXHEsppgrAWJzLEZwESfiiNyURo3pCBAO1ga2mE'
    gviz_prefix = '/gviz/tq?tqx=out:csv&sheet='
    tab_name = '{Hero}'

    curvesheet_raw = pd.read_csv(f"{google_sheets}{sheet_id}{gviz_prefix}{tab_name}")

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
    # noinspection SpellCheckingInspection
    name_replacements = {'Al Akir': 'Al\'Akir',
                         'Aranna': 'Aranna Starseeker',
                         'Rafaam': 'Arch-Villain Rafaam',
                         'Brukan': 'Bru\'kan',
                         'Cthun': 'C\'Thun',
                         'Eudora': 'Captain Eudora',
                         'Hooktusk': 'Captain Hooktusk',
                         'Cariel': 'Cariel Roame',
                         'Cookie': 'Cookie the Cook',
                         'Deryl': 'Dancin\' Deryl',
                         'Blackthorn': 'Death Speaker Blackthorn',
                         'Brann': 'Dinotamer Brann',
                         'ETC': 'E.T.C., Band Manager',
                         'Edwin': 'Edwin VanCleef',
                         'Elise': 'Elise Starseeker',
                         'Omu': 'Forest Warden Omu',
                         'Flurgl': 'Fungalmancer Flurgl',
                         'George': 'George the Fallen',
                         'Guff': 'Guff Runetotem',
                         'Illidan': 'Illidan Stormrage',
                         'Toki': 'Infinite Toki',
                         'Jandice': 'Jandice Barov',
                         'Kaelthas': 'Kael\'thas Sunstrider',
                         'Mukla': 'King Mukla',
                         'Kurtrus': 'Kurtrus Ashfallen',
                         'Lich Bazhial': 'Lich Baz\'hial',
                         'Barov': 'Lord Barov',
                         'Jaraxxus': 'Lord Jaraxxus',
                         'Maiev': 'Maiev Shadowsong',
                         'Nguyen': 'Master Nguyen',
                         'Millhouse': 'Millhouse Manastorm',
                         'Millificent': 'Millificent Manastorm',
                         'Bigglesworth': 'Mr. Bigglesworth',
                         'Mutanus': 'Mutanus the Devourer',
                         'Nzoth': 'N\'Zoth',
                         'Saurfang': 'Overlord Saurfang',
                         'Patches': 'Patches the Pirate',
                         'Wagtoggle': 'Queen Wagtoggle',
                         'Ragnaros': 'Ragnaros the Firelord',
                         'Scabbs': 'Scabbs Cutterbutter',
                         'Silas': 'Silas Darkmoon',
                         'Finley': 'Sir Finley Mrrgglton',
                         'Kragg': 'Skycap\'n Kragg',
                         'Tamsin': 'Tamsin Roame',
                         'Tess': 'Tess Greymane',
                         'Curator': 'The Curator',
                         'Akazamzarak': 'The Great Akazamzarak',
                         'Jailer': 'The Jailer',
                         'Lich King': 'The Lich King',
                         'Rat King': 'The Rat King',
                         'Gallywix': 'Trade Prince Gallywix',
                         'Vanndar': 'Vanndar Stormpike',
                         'Varden': 'Varden Dawngrasp',
                         'Voljin': 'Vol\'jin',
                         'Yshaarj': 'Y\'Shaarj',
                         'Yogg': 'Yogg-Saron, Hope\'s End',
                         'Zephrys': 'Zephrys, the Great'}

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
    hero_data.drop(columns=['nameShort', 'armorTier', 'armor', 'pool', 'picture', 'pictureSmall', 'picturePortrait',
                            'heroPowerCost', 'heroPowerText', 'heroPowerId', 'heroPowerPicture',
                            'heroPowerPictureSmall',
                            'websites', 'isActive'], inplace=True)

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
    averages = pd.merge(averages, df_curves, how='left', on='name')

    return averages, firestone_update_time, bgknowhow_update_time


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

st.sidebar.markdown(f"**GitHub**"
                    f"  \n[README](https://github.com/TranRed/armor_tiers#readme)"
                    f"  \n[report a bug]({SUBMIT_ISSUE_URL}{BUG_REPORT_PARAMETERS})"
                    f"  \n[suggest a feature]({SUBMIT_ISSUE_URL}{FEATURE_SUGGESTION_PARAMETER})")

st.sidebar.markdown(f"**Links**"
                    f"  \n[BG Curve Sheet](https://www.bgcurvesheet.com/)"
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

# rename:
# ['name', 'hp', 'health', 'armorHighMMR', 'avg', 'total_matches',
#           'Player Ranking', 'Main Curve', 'Alternative Curve']].

# format:
# 'HP total', 'Health', 'Armor',
st.dataframe(selected_data[['name', 'Player Ranking', 'avg', 'total_matches', 'Main Curve', 'Alternative Curve']]
             .rename(columns={"name": "Hero", "avg": "Avg.", "total_matches": "Games", "Player Ranking": "Ranking"})
             .set_index('Hero').sort_values(by="Avg.")
             .style.format(subset=['Games'], formatter="{:,.0f}")
             .format(subset=['Avg.'], formatter="{:,.2f}"), use_container_width=True)
