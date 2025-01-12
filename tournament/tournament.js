const matchesSection = document.getElementById('tournament-board-section');

let matches;
let players;
function calculatePlayerPoints(matches) {
    const points = {};
    matches.forEach(match => {
        // Initialize player points if not already set
        points[match.player1] = points[match.player1] || 0;
        points[match.player2] = points[match.player2] || 0;

        // Update points based on the match result
        if (match.result === '1-0') {
            points[match.player1] += 1; // Player 1 wins
        } else if (match.result === '0-1') {
            points[match.player2] += 1; // Player 2 wins
        } else if (match.result === '0.5-0.5') {
            points[match.player1] += 0.5; // Draw
            points[match.player2] += 0.5; // Draw
        }
    });
    return points;
}

function displayMatches(matches, round_number) {
    if (round_number > 0) {
        let allMatches = matches.flatMap(round => round.matches)
        matches = matches[round_number - 1].matches
        matchesSection.innerHTML = ''; // Clear previous matches
        const playerPoints = calculatePlayerPoints(allMatches);

        matches.forEach((match, index) => {
            const matchDiv = document.createElement('div');
            matchDiv.className = 'pair';
            matchDiv.innerHTML = `
                <div class="player-info">
                    <h1 class="montserrat-300 player-name" style="color:black;">${match.player1}</h1>
                    <h1 class="montserrat-300 player-points" style="color:black;">${playerPoints[match.player1]}</h1>
                </div>
                <div class="game-result" style="color: white;">
                    <h1 class="game-result-text">${match.result}</h1>
                    <h4 class="game-result-text">${index + 1}</h4> <!-- Match number -->
                </div>
                <div class="player-info">
                    <h1 class="montserrat-300 player-name" style="color:black;">${match.player2}</h1>
                    <h1 class="montserrat-300 player-points" style="color:black;">${playerPoints[match.player2]}</h1>
                </div>
            `;
            matchesSection.appendChild(matchDiv);
        });
    } else {
        matchesSection.innerHTML = '';
        players.forEach((player, index) => {
            const matchDiv = document.createElement('div');
            matchDiv.className = 'pair';
            matchDiv.innerHTML = `
                    <h1 class="montserrat-300" style="color:white;">${player.name} ~~~~~ ${player.score} points</h1>
            `;
            matchesSection.appendChild(matchDiv);
        });
    }
}

function fetchMatches() {
    fetch('http://localhost:5000/api/tournament/results') // Adjust to your endpoint
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(tournament => {
            // Extract matches from the first tournament
            if (tournament.length > 0) {
                players = tournament[0];
                matches = tournament[1];
                const toursSection = document.getElementById("tours-section");
                const numOfButtons = toursSection.childElementCount - 2;
                for (let i = 1 + numOfButtons; i < matches.length+1; i++) {
                    // Your code here   
                    const button = document.createElement("button");
                    button.innerText = String(i); // Button text
                    button.className = "tour-button montserrat-500 round-buttons";
                    button.onclick = function() { changeRound(i); }; 
                    toursSection.appendChild(button);
                }
                displayMatches(matches, 0);
            } else {
                console.log('No tournaments found');
            }
        })
        .catch(error => {
            console.error('Error fetching matches:', error);
        });
}

fetchMatches();


function changeRound(round) {
    displayMatches(matches,round);
    const buttons = document.querySelectorAll('.tour-button');
    const activeButton = document.querySelector('.tour-button-active');

    // Check if the clicked button is already active
    let isActiveButtonClicked = false;

    buttons.forEach(button => {
        // If the clicked button is active, mark it
        if (button.innerText == round || (button.innerText.trim() === '🏠' && round == '0')) {
            if (activeButton && activeButton === button) {
                isActiveButtonClicked = true; // The active button was clicked
            } else {
                // Remove active style from the current active button
                if (activeButton) {
                    activeButton.classList.remove('tour-button-active');
                    activeButton.classList.add('tour-button');
                }

                // Add active style to the clicked button
                button.classList.remove('tour-button');
                button.classList.add('tour-button-active');
            }
        }
    });

    // If the active button was clicked, do nothing
    if (isActiveButtonClicked) {
        return; // Exit the function without making changes
    }
}


function copyLink() {
    const linkToCopy = "blablabla"; // The link you want to copy

    // Copy the link to the clipboard
    navigator.clipboard.writeText(linkToCopy).then(() => {
        // Show the notification
        const notification = document.getElementById('copyNotification');
        notification.style.display = 'block';

        // Hide the notification after 2 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 2000);
    }).catch(err => {
        console.error('Could not copy text: ', err);
    });
};


async function addPlayer() { 
    const userInput = prompt("Please enter the name:");
    if (userInput !== null && userInput.trim() !== "") {
        try {
            const response = await fetch('http://localhost:5000/api/tournament/add_player', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ player: userInput }),
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Player added:', data);
                fetchMatches();
            } else {
                console.error('Error:', response.statusText);
            }
        } catch (error) {
            console.error('Network error:', error);
        }
    }
}

async function removePlayer() { 
    const userInput = prompt("Please enter the name:");
    if (userInput !== null && userInput.trim() !== "") {
        try {
            const response = await fetch('http://localhost:5000/api/tournament/remove_player', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ player: userInput }),
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Player removed:', data);
            } else {
                console.error('Error:', response.statusText);
            }
        } catch (error) {
            console.error('Network error:', error);
        }
    }
}

async function generateRound() { 
    try {
        const response = await fetch('http://localhost:5000/api/tournament/pair_round', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}),
        });

        if (response.ok) {
            // If the response is plain text, read it as text
            const data = await response.text(); // Use text() instead of json()
            console.log('Round Generated:', data); // Expecting 'success'
            const toursSection = document.getElementById("tours-section");
            const numOfButtons = toursSection.childElementCount - 2;
            
            fetchMatches();
            changeRound(numOfButtons+1);
        } else {
            const errorText = await response.text();
            console.error('Error:', response.statusText, errorText);
        }
    } catch (error) {
        console.error('Network error:', error);
    }
}

async function deleteRound() { 
    try {
        const response = await fetch('http://localhost:5000/api/tournament/delete_round', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({}),
        });

        if (response.ok) {
            // If the response is plain text, read it as text
            const data = await response.text(); // Use text() instead of json()
            console.log('Round Deleted:', data); // Expecting 'success'
            const toursSection = document.getElementById("tours-section");
            toursSection.lastChild.remove();
            fetchMatches();
        } else {
            const errorText = await response.text();
            console.error('Error:', response.statusText, errorText);
        }
    } catch (error) {
        console.error('Network error:', error);
    }
}
