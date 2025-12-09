Escape From Peru - ROS Edition
This project is a ROS-based adaptation of the "Escape From Peru" game. It transforms a standalone Pygame application into a distributed system using ROS nodes, topics, custom messages, services, and parameters.

📋 1. Dependencies and Installation
Before running the game, ensure you have the following dependencies installed.

System Requirements
ROS Noetic (Ubuntu 20.04)

Python 3

Pygame: Required for the game graphics and logic.

Gnome Terminal: Required to spawn separate input windows via the launcher.

Installation Commands
Run the following commands in your terminal to install the necessary libraries:

Bash

# Install Pygame
pip3 install pygame

# Install Gnome Terminal (if using WSL or minimal Ubuntu)
sudo apt-get update
sudo apt-get install gnome-terminal
Build the Package
Navigate to your workspace:

Bash

cd ~/catkin_ws
Compile the package and source the environment:

Bash

catkin_make
source devel/setup.bash

**2. How to Run the Game**
Option A: The Launcher (Recommended)
This is the easiest way. It launches all nodes simultaneously (Game, Control, User Input, and Result Display).

Bash

roslaunch escape_peru_ros start_game.launch
Option B: Manual Execution (Node by Node)
If you need to debug, you can run each node in a separate terminal (remember to run roscore first and source devel/setup.bash in every terminal).

Terminal 1 (Core): roscore

Terminal 2 (Game Logic): rosrun escape_peru_ros game_node.py

Terminal 3 (Controller): rosrun escape_peru_ros control_node.py

Terminal 4 (Results): rosrun escape_peru_ros result_node.py

Terminal 5 (User Input): rosrun escape_peru_ros info_user.py

**3. Node-to-Node Communication Overview**
The system is distributed across four main nodes. Here is how they communicate:

1. Node: info_user
Function: Requests player data (Name, Username, Age) via the terminal.


Publication: Publishes this data to the topic /user_information using a custom message (user_msg).

2. Node: control_node
Function: Acts as a remote controller. Captures keyboard inputs (Arrows, Space, R, ESC).


Publication: Sends commands (e.g., "UP", "DOWN") to the topic /keyboard_control using std_msgs/String.

3. Node: game_node (Main Node)

Function: Handles game physics, graphics (Pygame), and logic.

Subscriptions:

Listens to /user_information to start the Welcome Phase.

Listens to /keyboard_control to move the player.


Publication: Sends the final score to /result_information (std_msgs/Int64) when the game ends.

Services Server:

/difficulty (SetGameDifficulty): Changes game speed (Easy/Medium/Hard). Only works in Phase 1.


/user_score (GetUserScore): Returns the last recorded score.

Parameters:

Reads /change_player_color (Int): Changes character color (1=Red, 2=Purple, 3=Blue).


Writes /screen_param (String): Updates the current game phase (phase1, phase2, phase3).

4. Node: result_node
Function: Displays the final results.

Subscriptions:

Listens to /user_information to know the player's name.

Listens to /result_information to print the final score.

**4. Operator Commands (Runtime Configuration)**
While the game is running, you can open a new terminal to interact with the system using ROS Services and Parameters.

Change Player Color
Use rosparam set to change the color in real-time:

Bash

# 1 = Red, 2 = Purple (Default), 3 = Blue
rosparam set /change_player_color 1
Change Difficulty
Only works in Phase 1 (Start Screen).

Bash

# Options: 'easy', 'medium', 'hard'
rosservice call /difficulty "change_difficulty: 'hard'"
Get Last Score
Retrieve the score of the last game played.

Bash

rosservice call /user_score "username: 'player'"
Controls
Click on the small "MANDO ROS" window to control the game.

UP Arrow / Space: Jump / Start Game.

DOWN Arrow: Duck.

R: Restart Game (on Game Over screen).

ESC: Quit.
