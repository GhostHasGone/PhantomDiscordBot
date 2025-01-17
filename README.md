# Discord Bot Setup Guide

This guide will walk you through setting up and running the Discord bot. All necessary files, including `config.json` and `main.py`, are already included in the folder. Follow these steps carefully to get your bot running.

---

## Prerequisites

Before you begin, ensure you have the following:
1. The newest version of Python installed on your system. [Download Python](https://www.python.org/downloads/)
2. A Discord account with access to create a bot via the [Discord Developer Portal](https://discord.com/developers/applications).

---

## Step 1: Install Dependencies

1. Double-click the `install_dependencies.bat` file included in the folder.
2. This will install all the required Python libraries for the bot.

---

## Step 2: Set Up the Configuration File

1. Open the `config.json` file in the folder.
2. Fill in the required information:
   - **BOT_TOKEN**: Your bot token (from the Discord Developer Portal).
   - **MODMAIL_CATEGORY_ID**: The ID of the category where modmail channels should be created.
   - **ALLOWED_ROLE_IDS**: A list of role IDs that should have access to modmail channels (e.g., `[123456789012345678]`).
   - **ALLOWED_ROLE_MENTION**: The mention string for the allowed role (e.g., `<@&ROLE_ID>`).
   - **WELCOME_CHANNEL**: The channel ID for welcome messages.
   - **GUILD_ID**: Your Discord server's ID.
   - **RULES_CHANNEL**: The mention string for your server's rules channel (e.g., `<#CHANNEL_ID>`).
   - **TEXT_LOG_CHANNEL_ID**: The channel ID for logging text messages.
   - **IMAGE_LOG_CHANNEL_ID**: The channel ID for logging image attachments.

---

## Step 3: Open the Folder in Terminal

1. Right-click in the folder containing the bot files and select **Open in Terminal**.
2. Ensure the terminal's file path points to the folder where the bot is located.

---

## Step 4: Run the Bot

1. In the terminal, type the following command and press Enter:
   ```bash
   py main.py
