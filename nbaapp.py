import streamlit as st
import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats
import plotly.graph_objects as go



def get_all_players():
    player_dicts = players.get_players()
    player_names = [player['full_name'] for player in player_dicts]
    return player_names

# Function to get player ID
def get_player_id(player_name):
    player_dict = players.find_players_by_full_name(player_name)
    if player_dict:
        return player_dict[0]['id']
    else:
        raise ValueError(f"No player found with the name {player_name}")

# Function to get career stats and clean the data
def get_clean_career_stats(player_id):
    career = playercareerstats.PlayerCareerStats(player_id=player_id)
    career_df = career.get_data_frames()[0]
    # Filter out any rows with future seasons or incorrect data
    career_df = career_df[career_df['SEASON_ID'].str[:4].astype(int) <= pd.Timestamp.now().year]
    return career_df

# Function to calculate average stats
def calculate_avg_stats(career_df):
    career_df['REB/G'] = career_df['REB'] / career_df['GP']
    career_df['AST/G'] = career_df['AST'] / career_df['GP']
    career_df['STL/G'] = career_df['STL'] / career_df['GP']
    career_df['BLK/G'] = career_df['BLK'] / career_df['GP']
    
    avg_stats = {
        'REB/G': career_df['REB/G'].mean(),
        'AST/G': career_df['AST/G'].mean(),
        'FT_PCT': career_df['FT_PCT'].mean(),
        'FG3_PCT': career_df['FG3_PCT'].mean(),
        'STL/G': career_df['STL/G'].mean(),
        'BLK/G': career_df['BLK/G'].mean()
    }
    return avg_stats

# Known highest season averages (update with real historical data)
max_reb_per_game = 15.0  # Example value for highest rebounds per game in a season
max_ast_per_game = 12.0  # Example value for highest assists per game in a season
max_blk_per_game = 4.0   # Example value for highest blocks per game in a season
max_stl_per_game = 3.0   # Example value for highest steals per game in a season
max_fg3_pct = 0.53       # Example value for highest 3-point field goal percentage in a season

# Function to normalize stats using specific criteria
def normalize_stats(stats):
    normalized_stats = {
        'REB/G': stats['REB/G'] / max_reb_per_game,
        'AST/G': stats['AST/G'] / max_ast_per_game,
        'FT_PCT': stats['FT_PCT'],  # Use the percentage as it is
        'FG3_PCT': stats['FG3_PCT'] / max_fg3_pct,  # Normalize using the highest 3-point percentage
        'STL/G': stats['STL/G'] / max_stl_per_game,
        'BLK/G': stats['BLK/G'] / max_blk_per_game
    }
    return normalized_stats

# Function to create an interactive radar chart with Plotly
def create_interactive_radar_chart(player1_stats, player2_stats, player1_name, player2_name):
    labels = list(player1_stats.keys())
    player1_values = list(player1_stats.values())
    player2_values = list(player2_stats.values())

    # Create radar chart
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=player1_values + [player1_values[0]],
        theta=labels + [labels[0]],
        fill='toself',
        name=player1_name,
        hoverinfo='r+theta'
    ))

    fig.add_trace(go.Scatterpolar(
        r=player2_values + [player2_values[0]],
        theta=labels + [labels[0]],
        fill='toself',
        name=player2_name,
        hoverinfo='r+theta'
    ))

    # Customize the layout to show actual values
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=False,
            )
        ),
        showlegend=True
    )

    return fig

# Function to calculate PER for a single row (season)
def calculate_per(row):
    pts = row['PTS']
    reb = row['OREB'] + row['DREB']
    ast = row['AST']
    stl = row['STL']
    blk = row['BLK']
    fga = row['FGA']
    fgm = row['FGM']
    fta = row['FTA']
    ftm = row['FTM']
    tov = row['TOV']
    min_played = row['MIN']
    
    # Calculate PER using the simplified formula
    per = (pts + reb + ast + stl + blk - (fga - fgm) - (fta - ftm) - tov) / min_played
    return per

# Function to calculate career PER
def calculate_career_per(career_df):
    career_df['PER'] = career_df.apply(calculate_per, axis=1)
    total_per = career_df['PER'].mean()  # Averaging the PER across all seasons
    return total_per

# Function to create a line chart for total points scored each season using Plotly
def create_total_points_chart(player1_career_stats, player2_career_stats, player1_name, player2_name):
    # Ensure 'SEASON_ID' is converted to numerical values for sorting
    player1_career_stats['SEASON_ID_NUM'] = player1_career_stats['SEASON_ID'].str[:4].astype(int)
    player2_career_stats['SEASON_ID_NUM'] = player2_career_stats['SEASON_ID'].str[:4].astype(int)

    # Sort the data by the numerical 'SEASON_ID'
    player1_career_stats = player1_career_stats.sort_values(by='SEASON_ID_NUM')
    player2_career_stats = player2_career_stats.sort_values(by='SEASON_ID_NUM')

    # Combine and sort the seasons to ensure proper ordering
    combined_seasons = sorted(set(player1_career_stats['SEASON_ID'].tolist() + player2_career_stats['SEASON_ID'].tolist()))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=player1_career_stats['SEASON_ID'],
        y=player1_career_stats['PTS'],
        mode='lines+markers',
        name=player1_name
    ))

    fig.add_trace(go.Scatter(
        x=player2_career_stats['SEASON_ID'],
        y=player2_career_stats['PTS'],
        mode='lines+markers',
        name=player2_name
    ))

    fig.update_layout(
        title='Total Points Scored Each Season',
        xaxis_title='Season',
        yaxis_title='Total Points',
        xaxis=dict(type='category', categoryorder='array', categoryarray=combined_seasons, tickangle=-45),  # Ensure x-axis is categorical and labels are rotated
        legend_title='Players',
        template='plotly_dark'
    )

    return fig

# Function to create a line chart for total rebounds scored each season using Plotly
def create_total_rebounds_chart(player1_career_stats, player2_career_stats, player1_name, player2_name):
    # Ensure 'SEASON_ID' is converted to numerical values for sorting
    player1_career_stats['SEASON_ID_NUM'] = player1_career_stats['SEASON_ID'].str[:4].astype(int)
    player2_career_stats['SEASON_ID_NUM'] = player2_career_stats['SEASON_ID'].str[:4].astype(int)

    # Sort the data by the numerical 'SEASON_ID'
    player1_career_stats = player1_career_stats.sort_values(by='SEASON_ID_NUM')
    player2_career_stats = player2_career_stats.sort_values(by='SEASON_ID_NUM')

    # Combine and sort the seasons to ensure proper ordering
    combined_seasons = sorted(set(player1_career_stats['SEASON_ID'].tolist() + player2_career_stats['SEASON_ID'].tolist()))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=player1_career_stats['SEASON_ID'],
        y=player1_career_stats['REB'],
        mode='lines+markers',
        name=player1_name
    ))

    fig.add_trace(go.Scatter(
        x=player2_career_stats['SEASON_ID'],
        y=player2_career_stats['REB'],
        mode='lines+markers',
        name=player2_name
    ))

    fig.update_layout(
        title='Total Rebounds Each Season',
        xaxis_title='Season',
        yaxis_title='Total Rebounds',
        xaxis=dict(type='category', categoryorder='array', categoryarray=combined_seasons, tickangle=-45),  # Ensure x-axis is categorical and labels are rotated
        legend_title='Players',
        template='plotly_dark'
    )

    return fig

# Function to create a line chart for total stocks (steals + blocks) each season using Plotly
def create_total_stocks_chart(player1_career_stats, player2_career_stats, player1_name, player2_name):
    # Ensure 'SEASON_ID' is converted to numerical values for sorting
    player1_career_stats['SEASON_ID_NUM'] = player1_career_stats['SEASON_ID'].str[:4].astype(int)
    player2_career_stats['SEASON_ID_NUM'] = player2_career_stats['SEASON_ID'].str[:4].astype(int)

    # Sort the data by the numerical 'SEASON_ID'
    player1_career_stats = player1_career_stats.sort_values(by='SEASON_ID_NUM')
    player2_career_stats = player2_career_stats.sort_values(by='SEASON_ID_NUM')

    # Combine and sort the seasons to ensure proper ordering
    combined_seasons = sorted(set(player1_career_stats['SEASON_ID'].tolist() + player2_career_stats['SEASON_ID'].tolist()))

    # Calculate stocks
    player1_career_stats['STOCKS'] = player1_career_stats['STL'] + player1_career_stats['BLK']
    player2_career_stats['STOCKS'] = player2_career_stats['STL'] + player2_career_stats['BLK']

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=player1_career_stats['SEASON_ID'],
        y=player1_career_stats['STOCKS'],
        mode='lines+markers',
        name=player1_name
    ))

    fig.add_trace(go.Scatter(
        x=player2_career_stats['SEASON_ID'],
        y=player2_career_stats['STOCKS'],
        mode='lines+markers',
        name=player2_name
    ))

    fig.update_layout(
        title='Total Stocks (Steals + Blocks) Each Season',
        xaxis_title='Season',
        yaxis_title='Total Stocks',
        xaxis=dict(type='category', categoryorder='array', categoryarray=combined_seasons, tickangle=-45),  # Ensure x-axis is categorical and labels are rotated
        legend_title='Players',
        template='plotly_dark'
    )

    return fig

# Function to create a line chart for total missed attempts each season using Plotly
def create_total_missed_attempts_chart(player1_career_stats, player2_career_stats, player1_name, player2_name):
    # Ensure 'SEASON_ID' is converted to numerical values for sorting
    player1_career_stats['SEASON_ID_NUM'] = player1_career_stats['SEASON_ID'].str[:4].astype(int)
    player2_career_stats['SEASON_ID_NUM'] = player2_career_stats['SEASON_ID'].str[:4].astype(int)

    # Sort the data by the numerical 'SEASON_ID'
    player1_career_stats = player1_career_stats.sort_values(by='SEASON_ID_NUM')
    player2_career_stats = player2_career_stats.sort_values(by='SEASON_ID_NUM')

    # Combine and sort the seasons to ensure proper ordering
    combined_seasons = sorted(set(player1_career_stats['SEASON_ID'].tolist() + player2_career_stats['SEASON_ID'].tolist()))

    # Calculate missed attempts
    player1_career_stats['MISSED_ATTEMPTS'] = player1_career_stats['FGA'] - player1_career_stats['FGM']
    player2_career_stats['MISSED_ATTEMPTS'] = player2_career_stats['FGA'] - player2_career_stats['FGM']

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=player1_career_stats['SEASON_ID'],
        y=player1_career_stats['MISSED_ATTEMPTS'],
        mode='lines+markers',
        name=player1_name
    ))

    fig.add_trace(go.Scatter(
        x=player2_career_stats['SEASON_ID'],
        y=player2_career_stats['MISSED_ATTEMPTS'],
        mode='lines+markers',
        name=player2_name
    ))

    fig.update_layout(
        title='Total Missed Attempts Each Season',
        xaxis_title='Season',
        yaxis_title='Total Missed Attempts',
        xaxis=dict(type='category', categoryorder='array', categoryarray=combined_seasons, tickangle=-45),  # Ensure x-axis is categorical and labels are rotated
        legend_title='Players',
        template='plotly_dark'
    )

    return fig

# Function to create a line chart for total assists each season using Plotly
def create_total_assists_chart(player1_career_stats, player2_career_stats, player1_name, player2_name):
    # Ensure 'SEASON_ID' is converted to numerical values for sorting
    player1_career_stats['SEASON_ID_NUM'] = player1_career_stats['SEASON_ID'].str[:4].astype(int)
    player2_career_stats['SEASON_ID_NUM'] = player2_career_stats['SEASON_ID'].str[:4].astype(int)

    # Sort the data by the numerical 'SEASON_ID'
    player1_career_stats = player1_career_stats.sort_values(by='SEASON_ID_NUM')
    player2_career_stats = player2_career_stats.sort_values(by='SEASON_ID_NUM')

    # Combine and sort the seasons to ensure proper ordering
    combined_seasons = sorted(set(player1_career_stats['SEASON_ID'].tolist() + player2_career_stats['SEASON_ID'].tolist()))

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=player1_career_stats['SEASON_ID'],
        y=player1_career_stats['AST'],
        mode='lines+markers',
        name=player1_name
    ))

    fig.add_trace(go.Scatter(
        x=player2_career_stats['SEASON_ID'],
        y=player2_career_stats['AST'],
        mode='lines+markers',
        name=player2_name
    ))

    fig.update_layout(
        title='Total Assists Each Season',
        xaxis_title='Season',
        yaxis_title='Total Assists',
        xaxis=dict(type='category', categoryorder='array', categoryarray=combined_seasons, tickangle=-45),  # Ensure x-axis is categorical and labels are rotated
        legend_title='Players',
        template='plotly_dark'
    )

    return fig


# Streamlit app
st.title("NBA Player Comparison")

# Initialize session state for player names and career stats
if 'player1' not in st.session_state:
    st.session_state['player1'] = ""
if 'player2' not in st.session_state:
    st.session_state['player2'] = ""
if 'player1_career_stats' not in st.session_state:
    st.session_state['player1_career_stats'] = None
if 'player2_career_stats' not in st.session_state:
    st.session_state['player2_career_stats'] = None
if 'show_clear' not in st.session_state:
    st.session_state['show_clear'] = False
if 'show_in_depth' not in st.session_state:
    st.session_state['show_in_depth'] = False

# Clear session state
def clear_state():
    st.session_state.clear()
    st.experimental_rerun()

# Get all players for the dropdown
all_players = get_all_players()

# Input fields for player names using selectbox with search
player1_name = st.selectbox("Select the first player", options=[""] + all_players, index=0, key="player1")
player2_name = st.selectbox("Select the second player", options=[""] + all_players, index=0, key="player2")

if st.button("Compare Players"):
    try:
        if player1_name == "" or player2_name == "":
            st.error("Please select both players to compare.")
        else:
            # Get player IDs
            player1_id = get_player_id(player1_name)
            player2_id = get_player_id(player2_name)

            # Fetch and clean career stats
            player1_career_stats = get_clean_career_stats(player1_id)
            player2_career_stats = get_clean_career_stats(player2_id)

            # Store career stats in session state
            st.session_state['player1_career_stats'] = player1_career_stats
            st.session_state['player2_career_stats'] = player2_career_stats

            # Calculate average stats
            player1_avg_stats = calculate_avg_stats(player1_career_stats)
            player2_avg_stats = calculate_avg_stats(player2_career_stats)

            # Normalize stats for fair comparison
            player1_norm_stats = normalize_stats(player1_avg_stats)
            player2_norm_stats = normalize_stats(player2_avg_stats)

            # Create interactive radar chart
            radar_chart = create_interactive_radar_chart(player1_norm_stats, player2_norm_stats, player1_name, player2_name)
            st.plotly_chart(radar_chart)

            # Calculate career PER
            player1_career_per = calculate_career_per(player1_career_stats)
            player2_career_per = calculate_career_per(player2_career_stats)

            st.write(f"{player1_name} Career PER: {player1_career_per}")
            st.write(f"{player2_name} Career PER: {player2_career_per}")

            st.session_state['show_clear'] = True
            st.session_state['show_in_depth'] = True
        
    except ValueError as e:
        st.error(e)

# Show in-depth comparisons button only when both players have been compared
if st.session_state['show_in_depth']:
    if st.button("In-Depth Comparisons"):
        player1_career_stats = st.session_state['player1_career_stats']
        player2_career_stats = st.session_state['player2_career_stats']
        points_chart = create_total_points_chart(player1_career_stats, player2_career_stats, st.session_state['player1'], st.session_state['player2'])
        rebounds_chart = create_total_rebounds_chart(player1_career_stats, player2_career_stats, st.session_state['player1'], st.session_state['player2'])
        stocks_chart = create_total_stocks_chart(player1_career_stats, player2_career_stats, st.session_state['player1'], st.session_state['player2'])
        missed_attempts_chart = create_total_missed_attempts_chart(player1_career_stats, player2_career_stats, st.session_state['player1'], st.session_state['player2'])
        assists_chart = create_total_assists_chart(player1_career_stats, player2_career_stats, st.session_state['player1'], st.session_state['player2'])
        st.plotly_chart(points_chart)
        st.plotly_chart(rebounds_chart)
        st.plotly_chart(missed_attempts_chart)
        st.plotly_chart(stocks_chart)
        st.plotly_chart(assists_chart)

# Show clear button only when both players have been compared
if st.session_state['show_clear']:
    if st.button("Clear"):
        clear_state()
