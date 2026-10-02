Application name: Quest city tour

Application purpose: Provide hosts with a tool that will allow their guests to do self guided, gamified city tour. The tour route will be determined by a series of consequitive quests that needs to be resolved in order to unlock the next location. On top of resolving the task, the players needs to be take and upload picture with the quested landmark, so they create a memory. There will be a leaderboard based on the agregated time for resolving the quest. There will be also ability for one or two hints per task. Hind 1 will add 10 minutes of penalty and hint 2 will add aditional 15 minutes of penalty.

Administration: the initial version will not have admin panel but controlled via configuration files or database entries. The solution needs to be scalable so cms to be created on next stage

Game definition: one game is a series of quiz questions. It is uniquely identifie. Each game has its own leaderboard

Teams definition: a group of team members share the same team identifier.

Team and game relationship: many to many. One team can participate to several games.

Game process:
- Team is defined by the administrator
- Team is assigned to a game
- Each team member can open the game by opening a link givven by the administrator
- A team player lands to a welcome page with the rules
- A team player starts the game and start receiving tasks. When the task is resolved, the team player is asked to upload an image with the landmark of the task.
- A team member can open up to two hints and that adds up penalty to their time.
- When a task is resolved, the player gets tourist information with interesting facts about the landmark.
- Each task resolution time duration is recorded.
- When the last task of the quiz is resolved, the acumulated time of the team is calculated and added to the leaderboard.
- The application displays the leaderboard together with a custom message that can be configured by the admin for the specific team.