System modules:

Landmarks/tasks
This module is responsible collecting information for all landmarks that can be included in a game. One landmark is one quiz task.
The landmark shall have the following properties:
- Name
- Picture of the task
- Task
- Correct answer
- Hint 1
- Hint 2
- Landmark tourist information
- Landmark information picture

Games:
- Game name
- List of tasks
- Leaderboard
- Game intro

Teams:
- Team name
- Number of participants
- Exit message

Front end requirements:
- Responsive, mobile first design is needed. The application is going to be used most of the time on mobile phones
- Session needs to be preserved. If a game player closes the application window by mistake, when it is reopened the progress needs to be preserved.
- Session sharing: if multiple team members open the game, they need to be to the up to date task, meaning that the progress of the game needs to be centrally recorded
- Platform: for the first version the application will be just website used in a browser

Platform requirements
- The application will be hosted on azure platform. For website/web app, database, roles definitions - azure native components needs to be used