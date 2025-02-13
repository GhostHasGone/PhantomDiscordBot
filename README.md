# **Discord Bot Setup Guide**

This guide will walk you through setting up and running the Discord bot. All necessary files, including `config.json` and `main.py`, are already included. Follow these steps carefully to get your bot running.

---

## **Prerequisites**

Before you begin, ensure you have the following:
1. The **latest version of Python** installed. [Download Python](https://www.python.org/downloads/)
2. A **Discord account** with access to the [Discord Developer Portal](https://discord.com/developers/applications) to create and manage your bot.
3. The necessary permissions in your Discord server to create channels, manage roles, and configure settings.
4. Make sure that you have the permission roles that are below you also. (i.e. If you're the owner, you still need the designated Admin and Mod roles)
5. Role Hierarchy: Everyone (Power Level 0), Mod (Power Level 1), Admin (Power Level 2), and Servicer (Power Level 3)
---

## **Step 1: Install Dependencies**

1. **Double-click** the `install_dependencies.bat` file included in the folder.
2. This will automatically install all required Python libraries needed for the bot.

---

## **Step 2: Set Up the Configuration File**

1. Open the `config.json` file in any text editor.
2. Fill in the required fields:
   - **BOT_TOKEN**: Your bot token (from the Discord Developer Portal).
   - **GUILD_ID**: The ID of your Discord server.
   - **STATUS_TYPE**: Should be one of the following: "Playing", "Streaming", "Listening", "Watching", "Competing"
   - **STATUS_TEXT**: The text that is combined with the status type (e.g., 'YouTube' to make 'Watching Youtube')
   - **RULES_CHANNEL_ID**: The category ID where modmail threads should be created.
   - **WELCOME_CHANNEL_ID**: Role ID that has access to modmail (e.g., `[123456789012345678]`).
   - **MOD_ROLE_ID**: The mention string for the moderator role (e.g., `<@&ROLE_ID>`).
   - **MOD_ROLE_MENTION**: The role ID for admin role (LIMIT TO ONE).
   - **ADMIN_ROLE_ID**: Mention for the admin role (e.g., `<@&ROLE_ID>`).
   - **ADMIN_ROLE_MENTION**: The channel ID where welcome messages should be sent.
   - **MODMAIL_CATEGORY_ID**: Mention string for your rules channel (e.g., `<#CHANNEL_ID>`).
   - **TEXT_LOG_CHANNEL_ID**: The channel ID for logging text messages.
   - **IMAGE_LOG_CHANNEL_ID**: The channel ID for logging image attachments.
   - **ACTIVITY_PING_ROLE_ID**: Role ID for users who will receive activity pings.
   - **SERVICER_ROLE_ID**: Role ID for servicers (CAN RUN ALL COMMANDS).

---

## **Step 3: Open the Folder in Terminal**

1. **Right-click** in the folder containing the bot files and select **Open in Terminal**.
2. Ensure the terminal’s path is set to the correct folder.

---

## **Step 4: Run the Bot**

1. In the terminal, type the following command and press **Enter**:
   ```bash
   py main.py
   ```
2. The bot should now start, logging its status in the terminal and logging files.

---

## **Bot Features**

### **1. Modmail System**
   - Private messaging between members and staff.
   - Automatically creates modmail threads under a specified category.
   - Includes interactive buttons to resolve or close tickets.

### **2. Welcome System**
   - Sends a custom welcome message to new members in a designated channel.
   - Logs when members join or leave.

### **3. Role-Specific Commands**
   - Restricts commands to authorized roles.
   - Prevents misuse of admin-level features.

### **4. Logging System**
   - **Text Logs:** Saves messages to a log file, log channel, and the terminal.
   - **Image Logs:** Stores images in a dedicated folder and the dedicated images channel.

### **5. Interactive Commands**
   - `/version` - Displays bot version and release date (Mod or above only).
   - `/slap @user` - Posts a fun slap GIF.
   - `/topic` - Provides a discussion topic.
   - `/say <message>` - Allows authorized users to send bot messages (Mod or above only).
   - `/afk <reason>` - sets the afk of a user, removes it when a message from user is sent.

### **6. Moderation Tools**
   - `/ban @user <reason>` - Bans users with proper role checks (Admin or above only).
   - `/bans` - Retrieves ban records (Mod or above only).
   - `/member @user` - Shows user info (Mod or above only).
   - `/restart` - Safely restarts the bot (Admin or above only).
   - `/ping` - Displays bot latency (Admin or above only).
   - `/warn` & `/warns` - Warns a member and allows you to view their warns (Mod or above only).
   - `/mute` - Mutes a member and stores it with 'warns' (Mod or above only).

### **7. Customization & Setup**
   - Configurable via `config.json`.
   - One-click setup with `install_dependencies.bat`.
   - Enhanced error handling to prevent crashes.

---

## **Troubleshooting**

### **Bot Doesn't Respond to Commands**
1. Make sure the bot **has the correct permissions** in your Discord server.
2. Ensure the bot **is online** and running in the terminal.
3. Double-check the **command prefix** (default: `/`).
4. Make sure **your role has permission** to use the command.

### **Modmail System Isn’t Working**
- Ensure the **modmail category exists** and matches the `MODMAIL_CATEGORY_ID` in `config.json`.
- The bot **must have permission** to create channels.

### **Logging Issues**
- If text or image logs **are not working**, check:
  - That `TEXT_LOG_CHANNEL_ID` and `IMAGE_LOG_CHANNEL_ID` are **not set to 0** if logging is required.
  - The bot **has permission** to send messages in the logging channels.

### **Other Errors**
- If you see errors in the terminal, **restart the bot** and check `logs.txt` for details.
- If problems persist, contact **GhostHasGone** on Discord.

---

## **Credits**
- **Developed by:** GhostHasGone  
- **Special Thanks:** Saucywan  
