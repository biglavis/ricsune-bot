import os
from dotenv import load_dotenv
import difflib

import requests
import urllib.parse

load_dotenv()

API_KEY = os.getenv("RIOT_KEY")

AMERICA_URL = "https://americas.api.riotgames.com"
NA_URL = "https://na1.api.riotgames.com"
DD_URL = "https://ddragon.leagueoflegends.com"

# Riot API
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_account_by_name(gameName: str, tagLine: str) -> dict | None:
    '''
    Get Riot account by Riot ID.\n
    Returns: AccountDto
    '''
    gameName = urllib.parse.quote(gameName)

    url = AMERICA_URL + f"/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()

def get_account_by_puuid(puuid: str) -> dict | None:
    '''
    Get Riot account by puuid.\n
    Returns: AccountDto
    '''
    url = AMERICA_URL + f"/riot/account/v1/accounts/by-puuid/{puuid}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()   

def get_summoner_by_name(gameName: str, tagLine: str) -> dict | None:
    '''
    Get summoner by Riot ID.\n
    Returns: merge(SummonerDTO, AccountDto)
    '''
    if not (account := get_account_by_name(gameName, tagLine)):
        return None
    
    puuid = account['puuid']

    url = NA_URL + f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        summoner = resp.json()
        summoner.update(account)
        return summoner
    
def get_summoner_by_puuid(puuid: str) -> dict | None:
    '''
    Get summoner by puuid.\n
    Returns: merge(SummonerDTO, AccountDto)
    '''
    if not (account := get_account_by_puuid(puuid)):
        return None

    url = NA_URL + f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        summoner = resp.json()
        summoner.update(account)
        return summoner

def get_stats_by_summoner(summonerId: str) -> list[dict] | None:
    '''
    Get summoner stats.\n
    Returns: list[LeagueEntryDTO]
    '''
    url = NA_URL + f"/lol/league/v4/entries/by-summoner/{summonerId}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()
    
def get_matchId_by_puuid(puuid: str, count: int = 20) -> list | None:
    '''
    Get match IDs.\n
    Returns: list[str]
    '''
    url = AMERICA_URL + f"/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    resp = requests.get(url + f"&api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()
    
def get_match_by_id(matchId: str) -> dict | None:
    '''
    Get match info by match ID.\n
    Returns: MatchDto
    '''
    url = AMERICA_URL + f"/lol/match/v5/matches/{matchId}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()
    
def get_champion_masteries_by_puuid(puuid: str, count = 3) -> list[dict] | None:
    '''
    Get top champion masteries for a summoner by puuid.
    '''
    url = NA_URL + f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}/top?count=3"
    resp = requests.get(url + f"&api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()

# Data Dragon
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------#

def get_dd_version() -> str | None:
    '''
    Returns the latest Data Dragon version.
    '''
    resp = requests.get(DD_URL + "/api/versions.json")

    if resp.status_code == 200:
        return resp.json()[0]

def get_summoner_icon(iconId: int | str) -> str | None:
    '''
    Returns summoner icon link.
    '''
    if not (version := get_dd_version()):
        return
    
    return DD_URL + f"/cdn/{version}/img/profileicon/{iconId}.png"

def get_champions() -> dict | None:
    '''
    Get champions.
    '''
    if not (version := get_dd_version()):
        return
    
    url = DD_URL + f"/cdn/{version}/data/en_US/champion.json"
    resp = requests.get(url)

    if resp.status_code == 200:
        return resp.json()['data']
    
def get_champion_by_id(championId: int | str) -> dict | None:
    '''
    Get champion by ID.
    '''
    if not (version := get_dd_version()):
        return

    if not (champions := get_champions()):
        return
    
    if not (championName := [champion['id'] for champion in champions.values() if champion['key'] == str(championId)]):
        return
    
    url = DD_URL + f"/cdn/{version}/data/en_US/champion/{championName[0]}.json"
    resp = requests.get(url)

    if resp.status_code == 200:
        return resp.json()['data'][championName[0]]
    
def get_champion_by_name(championName: str) -> dict | None:
    '''
    Get champion by name.
    '''
    if not (version := get_dd_version()):
        return

    if not (champions := get_champions()):
        return
    
    if not (championName := difflib.get_close_matches(championName, champions.keys(), 1)):
        return
    
    url = DD_URL + f"/cdn/{version}/data/en_US/champion/{championName[0]}.json"
    resp = requests.get(url)

    if resp.status_code == 200:
        return resp.json()['data'][championName[0]]
    
def get_champion_skins_by_name(championName: str) -> list[dict]:
    '''
    Get champion skins by name.
    '''
    if champion := get_champion_by_name(championName):
        [skin.update({'url' : DD_URL + f"/cdn/img/champion/splash/{champion['id']}_{skin['num']}.jpg"}) for skin in champion['skins']]
        return champion['skins']
