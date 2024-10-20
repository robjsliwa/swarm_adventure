# Swarm Adventure

## Overview

This is a companion repo for my article [Tales from the Swarm: Crafting an Adventure Game using the OpenAI Swarm Library](). This project demonstrates how to build a text-based adventure game using the OpenAI Swarm library, which is a lightweight multi-agent orchestration framework. The game features a main story agent driving the narration and interactions, along with NPC agents that handle dialogues and actions.

The game allows players to explore a world of three locations, interact with NPCs like a weapon smith and armorer, and move between locations, all while leveraging the Swarm library’s `routines` and `handoffs` concepts.

## Features

- **Multi-agent orchestration**: The game uses multiple agents to handle different roles, such as the main story and NPC interactions.
- **Player navigation**: Move through locations like "The Dark Forest," "The Castle," and "The Cavern."
- **Interactive NPCs**: Speak to the armorer and weapon smith, who offer inventory and conversation options.
- **Dynamic storytelling**: The game generates narrative based on the player's location and actions.

## Setup and Installation

To run this project, follow these steps:

1. Clone this repository to your local machine.
   
   ```bash
   git clone https://github.com/robjsliwa/swarm_adventure.git
   cd swarm_adventure
   ```

2. Install the required dependencies:
   
   ```bash
   pip install git+ssh://git@github.com/openai/swarm.git
   pip install python-dotenv
   ```

3. Set your OpenAI API key in a `.env` file:
   
   ```bash
   echo "OPENAI_API_KEY=your-openai-key" > .env
   ```

4. Run the game:

   ```bash
   python main.py
   ```

## How It Works

- **Locations and connections**: The game world consists of predefined locations and connections between them.
- **Agents**: Swarm agents handle different aspects of the game. The main agent controls the story flow, while NPC agents handle specific interactions.
- **Tools**: Custom functions are defined to handle player movement, location descriptions, and NPC inventory interactions.

## License

This project is open source and available under the [MIT License](LICENSE).
