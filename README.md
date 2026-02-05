# Pomodoro Timer Plugin for StreamController

A simple Pomodoro timer plugin for [StreamController](https://github.com/StreamController/StreamController) with visual feedback when complete.

![Pomodoro Timer](store/thumbnail.png)

## Features

- Configurable timer duration
- Visual blinking effect when timer completes
- Customizable blink colors (including transparent)
- Option to disable blinking
- Single button operation: press to start, press to reset

## Installation

### From StreamController Store

1. Open StreamController
2. Go to the Store
3. Search for "Pomodoro Timer"
4. Click Install

### Manual Installation

1. Download or clone this repository

2. Copy the plugin folder to your StreamController plugins directory:

   **Flatpak (Linux):**
   ```bash
   cp -r pomodoro ~/.var/app/com.core447.StreamController/data/plugins/com_cuflt_pomodoro
   ```

   **Native (Linux):**
   ```bash
   cp -r pomodoro ~/.config/StreamController/plugins/com_cuflt_pomodoro
   ```

3. Restart StreamController

4. Add the "Pomodoro" action to any button

## Usage

- **Press button** when idle: Starts the countdown
- **Press button** while running: Stops and resets to idle
- **Press button** while blinking: Stops blinking and resets to idle

## Configuration

In the action settings you can configure:

| Setting | Description | Default |
|---------|-------------|---------|
| Duration (minutes) | Timer duration in minutes | 25 |
| Enable blinking | Toggle color blinking when finished | On |
| Color 1 | Primary finish color | Red |
| Color 2 | Secondary blink color | Blue |

Set color alpha to 0 for transparent (no color).

## Requirements

- StreamController 1.5.0-beta.5 or later
