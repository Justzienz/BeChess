from flask import Flask, jsonify, request
import json
import os
from flask_cors import CORS  # Import CORS

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

CURRENT_TOURNAMENT_FILE = 'current_tournament.json'
TOURNAMENTS_FILE = 'tournaments.json'

# Initialize the current tournament file if it doesn't exist
if not os.path.exists(CURRENT_TOURNAMENT_FILE):
    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump({}, f)

#Create new tournament
@app.route('/api/tournament/create', methods=['POST'])
def create_tournament():
    data = request.json
    tournament = {
        'name': data['name'],
        'date': data['date'],
        'players': data['players'],
        'round-1': [],
        'round-2': [],
        'round-3': [],
        'round-4': [],
        'round-5': [],
        'round-6': []
    }
    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump(tournament, f, indent=4)
    return jsonify({'message': 'Current tournament created!'}), 201

def add_round_pairings(pairings):
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)

    for i in range(1,7):
        if not tournament['round-'+str(i)]:
            break
    tournament['round-'+str(i)] = pairings

    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump(tournament, f, indent=4)

#add or edit round
@app.route('/api/tournament/round', methods=['POST'])
def add_round():
    data = request.json
    matches = data['matches']
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)
    tournament['round-'+str(data['roundNumber'])] = matches

    for match in matches:
        for player in tournament['players']:
            if player['name'] == match['player1']:
                player['opponents'].append(match['player2'])
                player['color_history'].append("W")
                if match['result'] == "1-0":
                    player['score'] += 1
                elif match['result'] == '0.5-0.5':
                    player['score'] += 0.5
            if player['name'] == match['player2']:
                player['opponents'].append(match['player1'])
                player['color_history'].append("B")
                if match['result'] == "0-1":
                    player['score'] += 1
                elif match['result'] == '0.5-0.5':
                    player['score'] += 0.5

    
    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump(tournament, f, indent=4)
    
    return jsonify({'message': 'Round added!'}), 201


#add player to the data and the algorithm
@app.route('/api/tournament/add_player', methods=['POST'])
def add_player():
    data = request.json
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)

    player = {
            "name": data["player"],
            "score": 0,
            "color_history": [],
            "opponents": [],
            "bye": 0,
            "active": 1
        }
    tournament['players'].append(player)
    
    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump(tournament, f, indent=4)
    
    return jsonify({'message': 'Player added!'}), 201


@app.route('/api/tournament/add_late_joiner', methods=['POST'])
def add_late_joiner():
    data = request.json
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)

    player = {
            "name": data["player"],
            "score": 1,
            "color_history": [],
            "opponents": [],
            "bye": 1,
            "active": 1
    }
    
    tournament['players'].append(player)
    
    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump(tournament, f, indent=4)
    
    return jsonify({'message': 'Late Joiner Added'}), 201


@app.route('/api/tournament/remove_player', methods=['POST'])
def remove_player():
    data = request.json
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)

    players = tournament['players']
    for player in players:
        if player['name'] == data['player']:
            player['active'] = 0
        
    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump(tournament, f, indent=4)

    
    return jsonify({'message': 'Player removed!'}), 201


@app.route('/api/tournament/complete', methods=['POST'])
def complete_tournament():
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)

    # Append completed tournament to tournaments file
    if os.path.exists(TOURNAMENTS_FILE):
        with open(TOURNAMENTS_FILE, 'r') as f:
            tournaments = json.load(f)
    else:
        tournaments = []

    tournaments.append(tournament)
    
    with open(TOURNAMENTS_FILE, 'w') as f:
        json.dump(tournaments, f, indent=4)

    # Clear current tournament file
    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump({}, f)

    return jsonify({'message': 'Tournament completed and saved!'}), 201




#THE ENDPOINTS FOR THE TOURNAMENT ALGORITHM
class Player:
    def __init__(self, name, score, color_history, opponents, bye, active):
        self.name = name
        self.score = score
        self.color_history = color_history  # Track color history ('W' for White, 'B' for Black)
        self.opponents = opponents  # Track opponents played to avoid rematches
        self.bye = bye  # Track if the player has had a bye
        self.active = active  # Track if the player is currently playing in the tournament

    def __repr__(self):
        return f"{self.name}"


class SwissTournament:
    def __init__(self,players):
        self.players = []
        self.rounds = []
        for player in players:
            self.players.append(Player(player['name'], player['score'], player['color_history'], player['opponents'], player['bye'], player['active']))


    def pair_round(self):
        # Sort players by score (descending), then by name (for consistency)
        active_players = [p for p in self.players if p.active]
        active_players.sort(key=lambda p: (-p.score, p.name))
        
        if len(active_players) % 2 != 0:
            active_players = active_players[::-1]
            for p in active_players:
                if not p.bye:
                    active_players.remove(p)
                    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
                        tournament = json.load(f)

                    players = tournament['players']
                    for player in players:
                        if player['name'] == p.name:
                            player['bye'] = 1
                            with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
                                json.dump(tournament, f, indent=4)
                            break
                    break
            active_players = active_players[::-1]

        pairings = []
        used = set()

        # Pair players
        for i, player in enumerate(active_players):
            if player in used:
                continue

            # Try to find the best opponent for the player
            for j in range(i + 1, len(active_players)):
                opponent = active_players[j]
                if opponent not in used and opponent.name not in player.opponents:
                    # Avoid rematches
                    pairings.append((player, opponent))
                    used.add(player)
                    used.add(opponent)

                    # Assign colors
                    self.assign_colors(player, opponent)
                    # Track opponents
                    player.opponents.append(opponent.name)
                    opponent.opponents.append(player.name)
                    break
            else:
                # If no opponent is found, assign a bye
                if player not in used and not player.bye:  # Ensure player hasn't already had a bye
                    pairings.append((player, None))
                    player.bye = True
                    player.score += 1  # Bye gives 1 point
                    used.add(player)

        self.rounds.append(pairings)
        print("TEST \n\n\n")
        print(pairings)
        print('TEST \n\n\n')
        return pairings

    def assign_colors(self, player1, player2):
        # Assign colors based on color history
        if player1.color_history.count('W') > player1.color_history.count('B'):
            player1.color_history.append('B')
            player2.color_history.append('W')
        else:
            player1.color_history.append('W')
            player2.color_history.append('B')



@app.route('/api/tournament/pair_round', methods=['POST'])
def pair_round():
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)
    players = tournament["players"]
    the_round = SwissTournament(players)
    pairing = the_round.pair_round()
    final_pairings = []
    for player1,player2 in pairing:
        final_pairings.append({'player1':player1.name,'player2':player2.name,'result':"0-0"})

    add_round_pairings(final_pairings)
    return 'success', 201

@app.route('/api/tournament/results', methods=['GET'])
def results():
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)
    rList = [tournament["players"],[]]
    rounds = rList[1]

    for i in range(1,7):
        if tournament['round-'+str(i)]:
            round = {}
            round["roundNumber"] = i
            round["matches"] = tournament['round-'+str(i)]
            rounds.append(round)
        else:
            break
    
    return rList

@app.route('/api/tournament/delete_round', methods=['POST'])
def delete_round():
    with open(CURRENT_TOURNAMENT_FILE, 'r') as f:
        tournament = json.load(f)

    for i in range(1,7):
        if not tournament['round-'+str(i)]:
            i -= 1
            break
    
    tournament['round-'+str(i)] = []
    with open(CURRENT_TOURNAMENT_FILE, 'w') as f:
        json.dump(tournament, f, indent=4)
    return 'success'+str(i), 201

if __name__ == '__main__':
    app.run(debug=True)
