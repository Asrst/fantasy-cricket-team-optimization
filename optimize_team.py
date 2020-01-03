# import/install neccessay packages
import subprocess
import sys
import os    
import argparse
import pandas as pd

try:
    from pulp import *
except ImportError:
    print("PuLP module not found, installing...") 
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pulp", "--user"])

    
# functions required to optimize & transform the data
def optimize_team(player_names, features):
    """
    Function to call model the Linear Programming
    
    # min_per_team = 4
    # max_per_team = 7
    # bat_range = range(3, 5+1)
    # ar_range = range(1, 3+1)
    # bowl_range = range(3, 5+1)
    # max_credits = 100
    
    Args:
    ------
    player_names: list->list of all unique player names
    features: dict->dict with following features (as keys)
    ('credits', 'player_roi', 'quantity', 'teamName_1', 'teamName_2', 
               'player_role_ar', 'player_role_bat', 'player_role_bowl', 'player_role_wk')
               
    returns:
    ------
    optimized LP problem (prob)
    sloved variables & values can be accessed as
    for v in prob.variables():
        print(v.varValue)    
    """
    
    # Players chosen 
    player_chosen = LpVariable.dicts("playerChosen", player_names, 0, 1, cat='Integer')
    
    # define np problem
    prob = LpProblem("Fantasy_Cricket", LpMaximize)

    # The objective function is added to 'prob' first
    prob += lpSum([feat['player_roi'][i]*player_chosen[i] for i in player_names]), "MaximizeROI"
    
    # max credits: credits are multiplied by 2 to convert them into integers
    prob += lpSum([feat['credits'][i]*player_chosen[i] for i in player_names]) <= 100, "MaxCredits"
    
    # Total
    prob += lpSum([feat['quantity'][f] * player_chosen[f] for f in player_names]) == 11, "Totalselection"

    # Wk
    prob += lpSum([feat['player_role_wk'][f] * player_chosen[f] for f in player_names]) == 1, "Wkequal"

    # Batsmen
    prob += lpSum([feat['player_role_bat'][f] * player_chosen[f] for f in player_names]) >= 3, "BatsmenMinimum"
    prob += lpSum([feat['player_role_bat'][f] * player_chosen[f] for f in player_names]) <= 5, "BatsmenMaximum"

    # Bowler
    prob += lpSum([feat['player_role_bowl'][f] * player_chosen[f] for f in player_names]) >= 3, "BowlerMinimum"
    prob += lpSum([feat['player_role_bowl'][f] * player_chosen[f] for f in player_names]) <= 5, "BowlerMaximum"

    # All rounder
    prob += lpSum([feat['player_role_ar'][f] * player_chosen[f] for f in player_names]) >= 1, "ArMinimum"
    prob += lpSum([feat['player_role_ar'][f] * player_chosen[f] for f in player_names]) <= 3, "ArMaximum"

    # India
    prob += lpSum([feat['teamName_1'][f] * player_chosen[f] for f in player_names]) >= 4, "Team1Minimum"
    prob += lpSum([feat['teamName_1'][f] * player_chosen[f] for f in player_names]) <= 7, "Team1Maximum"

    # Wi
    prob += lpSum([feat['teamName_2'][f] * player_chosen[f] for f in player_names]) >= 4, "Team2Minimum"
    prob += lpSum([feat['teamName_2'][f] * player_chosen[f] for f in player_names]) <= 7, "Team2Maximum"

    # The problem data is written to an .lp file
    r = prob.writeLP("files/FantasyCricket.lp")
    
    prob.solve()
    print("Status:", LpStatus[prob.status])
    # prob.solver
    
    print("ROI maximized = {}".format(round(value(prob.objective),2)))
    
    return prob
    
    
def transform_data(players_df):
    """
    function to transform the dataframe into features for LP
    
    Args:
    ------
    players_df: DataFrame will all players to choose from & thier attributes
    
    returns:
    -------
    (player_names, features)
    players_names: list--> with all uniquw players names
    features:dict--> contains corresponding features for the players
    """
    
    # copy
    df = players_df.copy()
    
    # replace original team abbv with 1 & 2
    teamNameMap = {i:j+1 for j, i in enumerate(df['teamName'].unique())}
    df['teamName'] = df['teamName'].replace(teamNameMap)
    
    # think it as availability, if player is injured/not available, set it to zero
    df['quantity'] = 1
    
    # dummy ROI values based on the selection popularity
    df['player_roi'] = df['selectionPercent'].apply(lambda x: int(x[:-1]))
    df['player_roi'] = df['player_roi']/df['credits']
    
    # player_roi (maximize), credits (<=100), quantity (Total = 11)
    # onehot encode => player_role, teamName
    df = pd.get_dummies(df, columns=['teamName', 'player_role'])
    
    # defined feature columns
    feature_cols = ['credits', 'player_roi', 'quantity', 'teamName_1', 'teamName_2', 
               'player_role_ar', 'player_role_bat', 'player_role_bowl', 'player_role_wk']
    
    # check if all features are present
    for col in feature_cols:
        if col not in df.columns:
            raise("Required columns missing to form features:", col)
            
    # Creates a list of the Players
    player_names = list(df['playerName'])
    feat_dict = {}
    for col in feature_cols:
        feat_dict[col] = dict(zip(player_names, df[col].values))
        
    return player_names, feat_dict


if __name__ == "__main__":
      
    # arguments parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--csv_path", type = str, 
                        help="path to csv containing all players & features")
    args = parser.parse_args()

    if args.csv_path:
        csv_path = args.csv_path
    else:
        print("\nINFO: csv path argument (-p) not given; using default path:'usecase_players.csv'")
        csv_path = "files/usecase_players.csv"
        
    # read the csv using pandas & transform data
    pdf = pd.read_csv(csv_path)
    player_names, feat = transform_data(pdf)
    
    # optimization call
    print('\nOptimizing...')
    prob = optimize_team(player_names, feat)
    
    
    player_roles = dict(zip(pdf['playerName'], pdf['player_role']))
    
    players_choosen = []
    players_credits = []
    print('\nTeam Choosen: ')
    for v in prob.variables():
        if v.varValue>0:
            act_name = " ".join(v.name.split('_')[-2:])
            credit = feat['credits'][act_name]
            players_choosen.append(act_name)
            players_credits.append(credit)
            print(act_name, ' = ', credit, " Role:", player_roles[act_name])

    print('\nTotal Credits Used:', sum(players_credits))
    
    res_df = pdf[pdf['playerName'].isin(players_choosen)].reset_index(drop = 1)
    res_df.to_csv('files/solution.csv', index = None)