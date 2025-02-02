# ©2025 GhostHasGone
# Add 'ghosthasgone' on Discord for support or inquiries.

# ======================================================================================================================================================================================
# Imports

import discord
import asyncio
import logging
import os
import datetime
import random
import string
import json
import sys

from discord.ext import commands

VERSION = "1.1.5"
VERSION_DATE = "January 31th, 2025"

# ======================================================================================================================================================================================
# Important Stuff

# Load the configuration from the JSON file
try:
	with open("config.json", "r") as config_file:
		config = json.load(config_file)
except (FileNotFoundError, json.decoder.JSONDecodeError):
	print('Error: "config.json" file not found or is incorrectly formatted.\nExiting...')
	input()
	sys.exit()

try:
	BOT_TOKEN = config["BOT_TOKEN"]

	GUILD_ID = config["GUILD_ID"]

	MODMAIL_CATEGORY_ID = config["MODMAIL_CATEGORY_ID"]

	MOD_ROLE_ID = config["MOD_ROLE_ID"]
	MOD_ROLE_MENTION = config["MOD_ROLE_MENTION"]

	ADMIN_ROLE_ID = config["ADMIN_ROLE_ID"]
	ADMIN_ROLE_MENTION = config["ADMIN_ROLE_MENTION"]

	WELCOME_CHANNEL_ID = config["WELCOME_CHANNEL_ID"]
	RULES_CHANNEL_ID = config["RULES_CHANNEL_ID"]
	TEXT_LOG_CHANNEL_ID = config["TEXT_LOG_CHANNEL_ID"]
	IMAGE_LOG_CHANNEL_ID = config["IMAGE_LOG_CHANNEL_ID"]

	ACTIVITY_PING_ROLE_ID = config["ACTIVITY_PING_ROLE_ID"]

	SERVICER_ROLE_ID = config["SERVICER_ROLE_ID"]
except KeyError:
	print('Error: "config.json" file is missing required fields.\nExiting...')
	input()
	sys.exit()

# just here to make my IDE look pretty <3
text_log_channel = None
image_log_channel = None

# Create a bot instance with a command prefix
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
bot.remove_command("help")

def is_staff(member: discord.Member, has_mod: bool, has_admin: bool, has_servicer: bool) -> bool:
	# Check if the member has admin permissions
	if has_servicer and any(role.id in SERVICER_ROLE_ID for role in member.roles):
		return True

	if member.guild_permissions.administrator:
		return True

	# If the command requires admin and the member does not have it, return False
	if has_admin and any(role.id in ADMIN_ROLE_ID for role in member.roles):
		return True

	if has_mod and any(role.id in MOD_ROLE_ID for role in member.roles):
		return True

	return False

# ======================================================================================================================================================================================
# When Bot starts

@bot.event
async def on_ready():
	global text_log_channel, image_log_channel

	print(f"Bot is logged in as {bot.user}")
	await bot.change_presence(activity=discord.Game(name="ModMail"))


	if TEXT_LOG_CHANNEL_ID is not None:
		text_log_channel = bot.get_channel(TEXT_LOG_CHANNEL_ID)
	if image_log_channel is not None:
		image_log_channel = bot.get_channel(IMAGE_LOG_CHANNEL_ID)
	logger.info(f"\n \nLogs:\n")


# ======================================================================================================================================================================================
# The buttons for the ModMail Interactions
# Part One: "Resolved"

class ModmailView(discord.ui.View):

	def __init__(self, guild: discord.Guild, allowed_roles: list[int]):

		super().__init__(timeout=None)
		self.guild = guild
		self.allowed_roles = allowed_roles

	@discord.ui.button(label="Resolved", style=discord.ButtonStyle.success)
	async def resolved_button(self, button: discord.ui.Button, interaction: discord.Interaction):

		# Update permissions to restrict access to staff only
		overwrites = {
			self.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
		}

		embed = discord.Embed(
			title="✅ Resolved Issue",
			description="\n> The issue is resolved.\n> \n> Only staff have access to the channel now.",
			color=colors["yellow"]
		)
		embed.set_footer(
			text="This message was written by server staff.",
		)

		# Load modmail logs
		modmail_logs = load_modmail_logs()
		user_id = None
		channel = interaction.channel

		for uid, data in modmail_logs.items():
			if data["channel_id"] == channel.id:
				user_id = uid
				break

		if user_id:
			modmail_logs[user_id]["status"] = "resolved"
			save_modmail_logs(modmail_logs)
		for role_id in self.allowed_roles:
			role = self.guild.get_role(role_id)
			if role:
				overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
			else:
				print(f"Error in 'ModmailView.resolved_button': \"role\" is {str(role)}")
				return
		await interaction.response.send_message(embed=embed)

		# Add "(R)" to the resolved channel name
		new_name = f"(R) {channel.name}"
		logger.info(f"ticket '{channel.name}' has been resolved.")
		await channel.edit(name=new_name)
		await channel.edit(overwrites=overwrites)

	# ======================================================================================================================================================================================
	# The buttons for the ModMail Interactions
	# Part One: "Closed"

	@discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
	async def close_button(self, button: discord.ui.Button, interaction: discord.Interaction):

		# Check if the user has permission to use this button
		if not is_staff(interaction.user, True, True, True):
			await interaction.response.send_message("You don't have permission to close this thread.", ephemeral=True)
			return

		embed = discord.Embed(
			title="🚫 Channel Deletion",
			description="> This channel will be deleted in a few seconds.",
			color=colors["red"]
		)
		embed.set_footer(
			text="This message was written by server staff.",
		)

		# Load modmail logs
		modmail_logs = load_modmail_logs()
		user_id = None
		channel = interaction.channel

		for uid, data in modmail_logs.items():
			if data["channel_id"] == channel.id:
				user_id = uid
				break

		if user_id:
			modmail_logs[user_id]["status"] = "resolved"
			save_modmail_logs(modmail_logs)
		await interaction.response.send_message(embed=embed)

		# Wait for 5 seconds
		await asyncio.sleep(5)

		channel = interaction.channel
		logger.info(f"ticket '{interaction.channel}' has been closed.")
		await channel.delete(reason="Modmail thread closed.")


# ======================================================================================================================================================================================
# Configure logging for all bot actions and messages

# Ensure the logs directory exists
LOG_FOLDER = "logs"

logger = logging.getLogger(__name__)

os.makedirs(LOG_FOLDER, exist_ok=True)

if os.path.exists("assets/colors.json"):
	with open("assets/colors.json", "r") as file:
		colors = json.load(file)
else:
	logger.warning('The file "assets/colors.json" is missing. Please download it.')

os.makedirs("logs/images", exist_ok=True)

log_file_path = os.path.join(LOG_FOLDER, "logs.txt")

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(levelname)s - %(message)s",
	handlers=[
		logging.FileHandler(log_file_path, encoding="utf-8"),
		logging.StreamHandler(),
	],
)

logger.info("\n")
logger.info("=" * 50)
logger.info("BOT STARTED")
logger.info("=" * 50)

# ======================================================================================================================================================================================
# Configure modmail logging

# Ensure the modmail JSON file exists
MODMAIL_LOG_FILE = "logs/modmail_logs.json"

if not os.path.exists(MODMAIL_LOG_FILE):
	with open(MODMAIL_LOG_FILE, "w") as file:
		json.dump({}, file, indent=4)


def load_modmail_logs():
	if not os.path.exists("logs/modmail_logs.json"):
		with open("logs/modmail_logs.json", "w") as file:
			json.dump({}, file, indent=4)
	with open("logs/modmail_logs.json", "r") as file:
		return json.load(file)


# Save modmail logs to JSON file
def save_modmail_logs(modmail_logs):
	with open("logs/modmail_logs.json", "w") as file:
		json.dump(modmail_logs, file, indent=4)


# Load active modmail from JSON
active_modmail = load_modmail_logs()


# ======================================================================================================================================================================================
# Bot event for messages
# Part One: Text-Logs Channel and Text Log File

@bot.event
async def on_message(message):
	# Makes sure it shows nothing from the bot
	if message.author.bot:
		return

	# Ensure the log channels exist in the bot's known channels
	if not text_log_channel or not image_log_channel:
		print("Log channels not found. Ensure the bot has access to the target server.")
	else:
		# Log text-based messages in test-logs channel and Logs file
		if message.content and not isinstance(message.channel, discord.DMChannel):
			embed = discord.Embed(
				title=f"Message from {message.author} in {message.channel}",
				description=f"> {message.content}",
				color=colors["green"]
			)

			# Send embed in text-logs channel
			await text_log_channel.send(embed=embed)

			# Send log to the logger
			logger.info(f"Message from {message.author} in #{message.channel}: '{message.content}'")

	# ======================================================================================================================================================================================
	# Bot event for messages
	# Part Two: Image-Logs Channel and Image Log Folder

	# Ensure the images directory exists
	image_folder = "logs/images"
	os.makedirs(image_folder, exist_ok=True)  # Creates the folder if it doesn't exist

	# Log messages with images in channel and sends a message to the Logs file
	if message.attachments:
		for attachment in message.attachments:
			if attachment.content_type and attachment.content_type.startswith("image/"):
				if image_log_channel is not None:
					await image_log_channel.send(
						content=f"**Image from {message.author} in {message.channel}:**",
						file=await attachment.to_file()
					)
				# Generate a scrambled 20-letter name
				scrambled_name = ''.join(random.choices(string.ascii_letters, k=20))

				# Construct the new filename
				original_filename = attachment.filename
				scrambled_filename = f"{scrambled_name} - {original_filename}"
				image_path = os.path.join(image_folder, scrambled_filename)  # Use os.path.join for cross-platform compatibility

				# Save the file with the new filename
				await attachment.save(image_path)
				logger.info(f"Image from {message.author} saved: {image_path}")

	# ======================================================================================================================================================================================
	# Bot event for messages
	# Part Three: If DM'd the word "Contact"

	# Check if it's a DM and not from a bot
	if message.guild is None and not message.author.bot:
		if message.content.strip().lower() == "contact":
			# Load current modmail data
			modmail_logs = load_modmail_logs()
			guild = bot.get_guild(GUILD_ID)

			if guild is None:
				await message.author.send("Could not retrieve the server. Please contact the server administrators.")
				return

			# Fetch the category
			category = discord.utils.get(guild.categories, id=MODMAIL_CATEGORY_ID)
			if category is None:
				await message.author.send("Modmail category is not configured properly. Please contact the server administrators.")
				return

			# Check if user already has an open modmail
			if str(message.author.id) in modmail_logs and modmail_logs[str(message.author.id)]["status"] == "open":
				existing_channel_id = modmail_logs[str(message.author.id)]["channel_id"]
				existing_channel = guild.get_channel(existing_channel_id)

				if existing_channel:
					embed = discord.Embed(
						title="🚫 Modmail Already Open!",
						description=f"> You already have an active modmail open.\n> \n> {existing_channel.mention}",
						color=colors["red"]
					)
					embed.set_footer(text="If you believe this is a mistake, contact the staff directly.")
					await message.author.send(f"### {message.author.mention} ModMail Error!", embed=embed)
					logger.info(f"{message.author.name} (@{message.author.id}) attempted to reach modmail, ticket already exists: '{message.author.name}'")
					return

			overwrites = {
				guild.default_role: discord.PermissionOverwrite(read_messages=False),
				message.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
			}

			for role_id in MOD_ROLE_ID:
				role = guild.get_role(role_id)
				if role:
					overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

			# Add permissions for allowed roles
			for role_id in MOD_ROLE_ID:
				role = guild.get_role(role_id)
				if role:
					overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

			# Create the channel
			channel_name = f"{message.author.name}"
			channel = await guild.create_text_channel(
				name=channel_name,
				category=category,
				overwrites=overwrites,
				topic=f"Modmail thread for {message.author}",
				reason="Modmail channel creation"
			)

			embed = discord.Embed(
				title="📃 Modmail Thread",
				description=f"> Modmail initiated by {message.author.mention}. \n> \n> Please describe your issue and how we can assist you.",
				color=colors["blue"]
			)
			embed.set_footer(text="Use the buttons below to manage this thread.")

			view = ModmailView(guild=guild, allowed_roles=[MOD_ROLE_ID, ADMIN_ROLE_ID, SERVICER_ROLE_ID])
			await channel.send(f"### {MOD_ROLE_MENTION} Come help!", embed=embed, view=view)

			# Notify the user
			embed = discord.Embed(
				title="📃 ModMail",
				description=f"> A modmail has been created, click below to view the ticket:\n> \n> {channel.mention}",
				color=colors["green"]
			)
			embed.set_footer(text="This message was written by server staff.")
			await message.author.send(f"### {message.author.mention} Thank you for reaching out!", embed=embed)
			logger.info(f"{message.author.name} (@{message.author.id}) created a ticket: '{message.author.name}'")

			modmail_logs[str(message.author.id)] = {
				"user": message.author.name,
				"user_id": message.author.id,
				"channel_id": channel.id,
				"status": "open",
				"date": str(message.created_at)
			}

			save_modmail_logs(modmail_logs)

		# ======================================================================================================================================================================================
		# Bot event for messages
		# Part Four: If DM'd the word "Help"

		elif message.content.strip().lower() == "help":

			embed = discord.Embed(
				title="🆘 Hello! I am at yor service!",
				description="\n> My job is to allow you to message staff! \n> \n> Simply type the word **'contact'** and the staff will be notified!",
				color=colors["yellow"]
			)
			embed.set_footer(
				text="This message was written by server staff.",
			)
			await message.author.send(f"### {message.author.mention} Here to help!", embed=embed)

		# ======================================================================================================================================================================================
		# Bot event for messages
		# Part Five: If DM'd anything other than those words

		else:

			embed = discord.Embed(
				title="👎 Unknown Command!",
				description="\n> Type **'help'** for assistance",
				color=colors["red"]
			)
			embed.set_footer(
				text="This message was written by server staff.",
			)
			await message.author.send(f"### {message.author.mention} Hmmm...", embed=embed)

	await bot.process_commands(message)  # Process commands normally


# ======================================================================================================================================================================================
# Bot Event for member joins:
# Part One: DM the Member

@bot.event
async def on_member_join(member: discord.Member):
	rules_channel = bot.get_channel(RULES_CHANNEL_ID)

	try:
		embed = discord.Embed(
			title="🎉 Welcome!",
			description=f"> Thank you for joining {member.guild.name}!\n> We're happy to get the chance to chat with you!\n> \n> - Make sure to check out the Rules:\n> {rules_channel}\n> \n> - Chat and Enjoy our wonderful server",
			color=colors["gold"]
		)
		embed.set_footer(
			text="This message was written by server staff.",
		)

		await member.send(embed=embed)
	except discord.Forbidden:
		print(f"Could not send a DM to {member.name}. They may have DMs disabled.")

	# ======================================================================================================================================================================================
	# Bot Event for member joins:
	# Part Two: Send to Welcome Channel

	# Define the channel to send the message
	welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
	# Create the embed
	embed = discord.Embed(
		title="🎉 Welcome to the Server!",
		description=(
			f"> Hey {member.mention}, welcome to **{member.guild.name}**!\n"
			f"> We're so excited to have you here!\n> \n"
			f"> Please remember to read the Rules in {rules_channel}."
		),
		color=colors["gold"]
	)
	embed.set_thumbnail(url=member.avatar.url)  # User's profile picture
	embed.set_footer(
		text=f"Member #{len(member.guild.members)}",
	)
	# Send the embed in the channel
	await welcome_channel.send(f"{member.mention}", embed=embed)

	# ======================================================================================================================================================================================
	# Bot Event for member joins:
	# Part Three: Log it in the Text-Logs Channel and the Text-Log File

	embed = discord.Embed(
		title=f"Member Joined!",
		description=f"> {member.name}\n> \n> ({member.mention})",
		color=colors["orange"]
	)
	embed.set_thumbnail(url=member.avatar.url)  # User's profile picture
	embed.set_footer(
		text=f"Member #{len(member.guild.members)}",
	)

	# Send embed in text-logs channel
	if text_log_channel is not None:
		await text_log_channel.send(embed=embed)

	# Log when a new member joins
	logger.info(f"Member joined: {member.name} (ID: {member.id}).")


# ======================================================================================================================================================================================
# When a member leaves or gets banned/kicked from the server

@bot.event
async def on_member_remove(member: discord.Member):
	# Log when a member leaves
	logger.info(f"Member left: {member.name} (ID: {member.id}).")

	embed = discord.Embed(
		title=f"Member Left!",
		description=f"> {member.name}",
		color=colors["orange"]
	)
	embed.set_thumbnail(url=member.avatar.url)  # User's profile picture
	embed.set_footer(
		text=f"Member #{len(member.guild.members)}",
	)

	# Send embed in text-logs channel
	if text_log_channel is not None:
		await text_log_channel.send(embed=embed)


# ======================================================================================================================================================================================
# Bot added to a server

@bot.event
async def on_guild_join(guild: discord.Guild):
	invite = await guild.text_channels[0].create_invite()
	invite_str = f"https://discord.gg/{invite.code}"
	# Log when the bot is added to a new guild
	logger.info(f"Bot added to guild: {guild.name} (ID: {guild.id}). Members: {len(guild.members)} Link: {invite_str}")

	embed = discord.Embed(
		title=f"Bot added to a Server:",
		description=f"> {guild.name}, ID: {guild.id}).\n> Link: {invite_str}",
		color=colors["white"]
	)

	# Send embed in text-logs channel
	if text_log_channel is not None:
		await text_log_channel.send(embed=embed)


# ======================================================================================================================================================================================
# Bot removed from Server

@bot.event
async def on_guild_remove(guild: discord.Guild):
	# Log when the bot is removed from a guild
	logger.info(f"Bot removed from guild: {guild.name} (ID: {guild.id}).")

	embed = discord.Embed(
		title=f"Bot Removed from Server:",
		description=f"> {guild.name}, ID: {guild.id}).",
		color=colors["white"]
	)

	# Send embed in text-logs channel
	if text_log_channel is not None:
		await text_log_channel.send(embed=embed)


# ======================================================================================================================================================================================
# An Error happens in the code

@bot.event
async def on_error(event):
	# Log any errors that occur in events
	logger.error(f"Error in event '{event}':", exc_info=True)

	embed = discord.Embed(
		title=f"Error in {event}",
		description=f"> ",
		color=colors["dark_red"]
	)

	# Send embed in text-logs channel
	if text_log_channel is not None:
		await text_log_channel.send(embed=embed)


# ======================================================================================================================================================================================
# Message Delete

@bot.event
async def on_message_delete(message: discord.Message):
	if message.author.bot:
		return
	else:
		if message.guild:  # Check if the message was in a guild (not a DM)
			logger.info(f"Message from {message.author} deleted in #{message.channel}: '{message.content}'")

			embed = discord.Embed(
				title=f"Message from {message.author} deleted in {message.channel}",
				description=f"> {message.content}",
				color=colors["red"]
			)

			# Send embed in text-logs channel
			if text_log_channel is not None:
				await text_log_channel.send(embed=embed)
		else:
			return


# ======================================================================================================================================================================================
# Message Edit

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
	if before.author.bot:
		return
	else:
		if before.guild:  # Check if the message was in a guild (not a DM)
			logger.info(
				f"Message from {before.author} edited in #{before.channel}:\n"
				f"- Before: '{before.content}'\n"
				f"- After: '{after.content}'"
			)

			embed = discord.Embed(
				title=f"Message from {before.author} deleted in {after.channel}",
				description=(
					f"Message from {before.author} edited in #{before.channel}:\n"
					f"> - Before: '{before.content}'\n"
					f"> - After: '{after.content}'"
				),
				color=colors["yellow"]
			)

			# Send embed in text-logs channel
			if text_log_channel is not None:
				await text_log_channel.send(embed=embed)
		else:
			return


# ======================================================================================================================================================================================
# EVERYONE COMMANDS (Power Level 0)
# ======================================================================================================================================================================================
# Help Command 'Done' Button

class DoneButton(discord.ui.View):
	def __init__(self, author_id: int):
		super().__init__(timeout=None)
		self.author_id = author_id  # Store the original command author's ID

	@discord.ui.button(label="Done", style=discord.ButtonStyle.primary)
	async def done_button(self, button: discord.ui.Button, interaction: discord.Interaction):
		"""Handles the 'Done' button press event."""
		# Ensure only the original user can delete the message
		if interaction.user.id == self.author_id:
			await interaction.message.delete()  # Delete the help embed
			await interaction.response.defer()  # Prevent "interaction failed" message
		else:
			await interaction.response.send_message(
				"❌ You are not allowed to delete this message!", ephemeral=True
			)


# ======================================================================================================================================================================================
# HELP MENU INFORMATION

HELP_DESCRIPTION = (
	"> **📌 Basic Commands:**\n"
	"> **`!help`** → Displays this help menu.\n"
	"> **`!topic`** → Picks a fun discussion topic.\n"
	"> **`!slap @user`** → Slap another user.\n"
	"\n"
	"> **⚔️ Moderator Commands:**\n"
	"> **`!version`** → Displays the bot version and release date.\n"
	"> **`!activity`** → Pings the activity role (If configured).\n"
	"> **`!member @user`** → Shows all of a member's information.\n"
	"> **`!say <message>`** → Allows you to say anything as the bot.\n"
	"> **`!bans`** → Shows why a user got banned.\n"
	"> **`!warn @user <reason>`** → Warns a member.\n"
	"> **`!warns @user`** → Displays the warn info for a member.\n"
	"> **`!mute @user <duration(add 's', 'm', 'h', etc.> <reason>`** → Mutes a member.\n"
	"\n"
	"> **⚙️ System Commands (Admins Only):**\n"
	"> **`!ban @user <reason>`** → Bans a user (Admin only).\n"
	"> **`!restart`** → Restarts the bot safely (Admin only).\n"
	"> **`!ping`** → Displays bot latency (Admin only).\n"
	"\n"
	"> **📩 ModMail System:**\n"
	"> Send '**contact**' in a DM to this bot to create a ModMail thread.\n"
	"> If you already have an open thread, it will provide the link instead.\n"
)


# ======================================================================================================================================================================================
# Help Command Embed

@bot.command(name="help")
@commands.cooldown(1, 60, commands.BucketType.user)
async def help_command(ctx: commands.Context):
	await ctx.message.delete()

	# Create embed with all the information in the description field
	embed = discord.Embed(
		title="**🆘 Bot Help Menu**",
		description=HELP_DESCRIPTION,
		color=colors["blue"]
	)
	embed.set_footer(text="For support, contact 'ghosthasgone' on Discord.")

	view = DoneButton(ctx.author.id)  # Pass the author's ID to restrict button usage
	await ctx.send(f"### {ctx.author.mention} Here's what I can do:", embed=embed, view=view)

	logger.info(f"{ctx.author} triggered the 'help' command in {ctx.channel}. Output sent.")


@help_command.error
async def help_error(ctx, error):
	await ctx.message.delete()
	if isinstance(error, commands.CommandOnCooldown):
		embed = discord.Embed(
			title="> ⏳ Cooldown!",
			description=f"> This command is on cooldown! \n> Try again in `{error.retry_after:.2f}` seconds.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} triggered the 'help' command in {ctx.channel}. Output not sent due to cooldown.")


# ======================================================================================================================================================================================
# Slap Command

@bot.command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def slap(ctx: discord.ext.commands.Context, member: discord.Member = None):
	await ctx.message.delete()

	# Check if a user is mentioned
	if not member:
		# Create an embed for invalid command usage
		embed = discord.Embed(
			title="🙁 Invalid Command",
			description=" \n> You must mention a user when using the `!slap` command.\n> \n> Proper usage is '!slap @user' \n",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		logger.info(f"{ctx.author} triggered the 'slap' command in {ctx.channel}. Output not sent due to no mention.")

		# Send the embed as a reply
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)  # Auto-delete after 10 seconds
		return

	# List of slap GIF URLs
	slap_gifs = json.load(open("assets/slaps.json", "r"))

	# Randomly select a slap GIF
	selected_gif = random.choice(slap_gifs)

	# Create the embed for the slap action
	embed = discord.Embed(
		title="✋ Slap!",
		description=f"\n> **{ctx.author.mention} slapped {member.mention}!**\n",
		color=colors["purple"]
	)
	embed.set_image(url=selected_gif)

	# Send the embed
	await ctx.send(f"### {member.mention} Got Slapped!", embed=embed)

	# Log the command use
	logger.info(f"{ctx.author} triggered the 'slap' command in {ctx.channel}. Output sent.")


@slap.error
async def slap_error(ctx, error):
	await ctx.message.delete()
	if isinstance(error, commands.CommandOnCooldown):
		embed = discord.Embed(
			title="⏳ Cooldown!",
			description=f"> This command is on cooldown! \n> Try again in `{error.retry_after:.2f}` seconds.",
			color=colors["red"]
		)
		embed.set_footer(text=f"This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} triggered the 'slap' command in {ctx.channel}. Output not sent due to cooldown.")
		return


# ======================================================================================================================================================================================
# Topic Command

current_index = 0  # Global index to track the current topic


@bot.command()
@commands.cooldown(1, 15, commands.BucketType.user)
async def topic(ctx: commands.Context):
	global current_index

	topics = json.load(open("assets/topics.json", "r"))  # Load the topics from the topics.json

	if current_index < len(topics):  # Ensure index is within bounds
		await ctx.message.delete()
		selected_topic = topics[current_index]

		# Create an embed
		embed = discord.Embed(
			title="💬 Let's Talk About...",
			description=f" \n> **{selected_topic}**\n",
			color=colors["gold"]
		)
		embed.set_footer(text="Enjoy the discussion!")

		# Send the embed
		await ctx.send(f"### {ctx.author.mention} Wants to Yap!", embed=embed)

		# Move to the next topic
		current_index += 1

		logger.info(f"{ctx.author} triggered the 'topic' command in {ctx.channel}. Output sent.")
	else:
		# Reset or notify users that topics are finished
		await ctx.send("All topics have been discussed! Restarting...")
		logger.info(f"{ctx.author} triggered the topic command in {ctx.channel} (restarting). Output sent.")
		current_index = 0  # Reset to the beginning


@topic.error
async def topic_error(ctx, error):
	await ctx.message.delete()
	if isinstance(error, commands.CommandOnCooldown):
		embed = discord.Embed(
			title="⏳ Cooldown!",
			description=f"> This command is on cooldown! \n> Try again in `{error.retry_after:.2f}` seconds.",
			color=colors["red"]
		)
		embed.set_footer(text=f"This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} triggered the 'topic' command in {ctx.channel}. Output not sent due to cooldown.")
		return


# ======================================================================================================================================================================================
# MODERATOR COMMANDS (Power Level 1)
# ======================================================================================================================================================================================
# Activity Ping

@bot.command()
async def activity(ctx: commands.Context):
	await ctx.message.delete()

	# Check if the user has the moderator role
	has_role = is_staff(ctx.author, True, True, True)
	if not has_role:
		embed = discord.Embed(
			title="❌ Permission Denied",
			description="> You need a **Moderator Role** to use this command.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'activity' in {ctx.channel} but lacks permissions.")
		return  # Exit early before applying cooldown

	# Apply cooldown only if user has the proper role
	if ctx.command.is_on_cooldown(ctx):
		retry_after = ctx.command.get_cooldown_retry_after(ctx)
		embed = discord.Embed(
			title="⏳ Cooldown!",
			description=f"> This command is on cooldown! Try again in `{retry_after:.2f}` seconds.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} tried 'activity' in {ctx.channel}, but it's on cooldown.")
		return

	# Apply cooldown manually
	ctx.command.reset_cooldown(ctx)  # Ensures that only successful attempts trigger the cooldown

	# Fetch the role
	activity_ping_role = ctx.guild.get_role(ACTIVITY_PING_ROLE_ID)

	# Check if an Activity Ping role is configured
	if ACTIVITY_PING_ROLE_ID == 0:
		embed = discord.Embed(
			title="❌ Activity Ping Not Configured",
			description="> There is no Activity Ping role set up.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention} No Activity Ping Available!", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} tried to use 'activity' in {ctx.channel}, but no Activity Ping role is set.")
		return

	if not activity_ping_role:
		embed = discord.Embed(
			title="❌ Invalid Role",
			description="> The Activity Ping role ID in the configuration is invalid.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention} Error!", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} tried to use 'activity' in {ctx.channel}, but the role ID is invalid.")
		return

	# Send the ping message
	embed = discord.Embed(
		title="📢 Activity Alert!",
		description=f"> **It's time to get active!**",
		color=colors["green"]
	)
	embed.set_footer(text=f"Requested by {ctx.author.display_name}")

	await ctx.send(f"### {activity_ping_role.mention} Hello!", embed=embed)
	logger.info(f"{ctx.author} triggered the 'activity' command in {ctx.channel}. Activity role pinged.")


# ======================================================================================================================================================================================
# Bot Version Command

@bot.command()
async def version(ctx: discord.ext.commands.Context):
	await ctx.message.delete()

	# Check if the user has the moderator role
	has_role = is_staff(ctx.author, True, True, True)
	if not has_role:
		embed = discord.Embed(
			title="❌ Permission Denied",
			description="> You need a **Moderator Role** to use this command.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'version' in {ctx.channel} but lacks permissions.")
		return  # Exit early before applying cooldown

	# Apply cooldown only if user has the proper role
	if ctx.command.is_on_cooldown(ctx):
		retry_after = ctx.command.get_cooldown_retry_after(ctx)
		embed = discord.Embed(
			title="⏳ Cooldown!",
			description=f"> This command is on cooldown! Try again in `{retry_after:.2f}` seconds.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} tried 'version' in {ctx.channel}, but it's on cooldown.")
		return

	# Apply cooldown manually after permission check
	ctx.command.reset_cooldown(ctx)

	# Create and send the version embed
	embed = discord.Embed(
		title="🔔 Version",
		description=f"> You are currently using {VERSION}\n> \n> Released on {VERSION_DATE}",
		color=colors["fuchsia"]
	)
	embed.set_footer(text="Add 'ghosthasgone' on Discord for Support or Inquiries.")
	view = DoneButton(ctx.author.id)
	await ctx.channel.send(f"### {ctx.author.mention} Version and Support:", embed=embed, view=view)

	# Log the command use
	logger.info(f"{ctx.author.mention} triggered the 'version' command in {ctx.channel}. Output sent.")


# ======================================================================================================================================================================================
# Member Info Command

@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)  # 10-second cooldown per user
async def member(ctx: commands.Context, member: discord.Member = None):
	await ctx.message.delete()

	# Check if the user has a moderator role
	has_role = is_staff(ctx.author, True, True, True)
	if not has_role:
		embed = discord.Embed(
			title="❌ Permission Denied",
			description="> You need a **Moderator Role** to use this command.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'member' in {ctx.channel} but lacks permissions.")
		return

	# If no member is mentioned, use the command author
	if member is None:
		member = ctx.author

	# Fetch user avatar and banner (if available)
	avatar_url = member.avatar.url if member.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
	banner_url = member.banner.url if member.banner else None

	# Get role names (excluding @everyone)
	roles = sorted(member.roles, key=lambda role: role.position, reverse=True)  # Sort by position (highest first)
	roles = [role.mention for role in roles if role != ctx.guild.default_role]  # Exclude @everyone
	roles = ", ".join(roles) if roles else "No roles"

	# Get account creation and join dates
	created_at = member.created_at.strftime("%B %d, %Y (%I:%M %p)")
	joined_at = member.joined_at.strftime("%B %d, %Y (%I:%M %p)")

	# Check if the user is boosting the server
	is_boosting = "Boosting" if member.premium_since else "Not Boosting"

	# User status and activity
	status = str(member.status).title()
	activity = (
		f"{member.activity.type.name.title()} {member.activity.name}" if member.activity else "None"
	)

	# Embed for user info
	embed = discord.Embed(
		title=f"📄 Member Information - {member.display_name}\n ",
		description=(

			f"\n> 👤 **Username**:\n>  **-->** {member.name}\n> "
			f"\n> 🆔 **User ID:**\n>  **-->** {member.id}\n> "
			f"\n> 📛 **Nickname:**\n>  **-->** {member.nick}\n> "
			f"\n> 📅 **Account Created:**\n>  **-->** {created_at}\n> "
			f"\n> 📥 **Joined Server:**\n>  **-->** {joined_at}\n> "
			f"\n> 🌟 **Boost Status:**\n>  **-->** {is_boosting}\n> "
			f"\n> 🎭 **Roles:**\n>  **-->** {roles}\n> "
			f"\n> 📶 **Status:**\n>  **-->** {status}\n> "
			f"\n> 🎮 **Activity:**\n>  **-->** {activity}"

		),
		color=colors["blue"]
	)
	embed.set_thumbnail(url=avatar_url)
	if banner_url:
		embed.set_image(url=banner_url)

	embed.set_footer(text=f"Requested by {ctx.author.display_name}")
	view = DoneButton(ctx.author.id)
	await ctx.send(f"### {ctx.author.mention}", embed=embed, view=view)
	logger.info(f"{ctx.author} triggered 'member' for {member} in {ctx.channel}.")


# Handle cooldown only for authorized users
@member.error
async def member_error(ctx, error):
	await ctx.message.delete()
	if isinstance(error, commands.CommandOnCooldown):
		embed = discord.Embed(
			title="⏳ Cooldown!",
			description=f"> This command is on cooldown! Try again in `{error.retry_after:.2f}` seconds.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} triggered 'member' in {ctx.channel}, but it's on cooldown.")


# ======================================================================================================================================================================================
# Say Command

@bot.command()
async def say(ctx: commands.Context, *, message: str = None):
	await ctx.message.delete()  # Delete the command message

	# Check if the user has the correct roles
	has_role = is_staff(ctx.author, True, True, True)
	if not has_role:
		embed = discord.Embed(
			title="❌ Permission Denied",
			description="> You need the **Moderator** role to use this command.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'say' in {ctx.channel} but lacks permissions.")
		return

	# Ensure there is a message to send
	if not message:
		embed = discord.Embed(
			title="❌ Invalid Usage",
			description="> You must provide a message to send.\n> **Example:** `!say Hello everyone!`",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'say' in {ctx.channel} but provided no message.")
		return

	# Prevent @everyone or @here abuse
	if "@everyone" in message or "@here" in message:
		embed = discord.Embed(
			title="🚫 Mention Restriction",
			description="> You **cannot** use `@everyone` or `@here` in this command.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} tried to use 'say' but attempted @everyone or @here mentions.")
		return

	# Send the message exactly as written, preserving all formatting
	await ctx.send(message)
	logger.info(f"{ctx.author} used 'say' in {ctx.channel}: '{message}'")

# ======================================================================================================================================================================================
# Warn Command Files

# Ensure moderation folder exists
WARN_FOLDER = "moderation/warns"
os.makedirs(WARN_FOLDER, exist_ok=True)

# Function to load warnings
def load_warns():
	warns = {}
	for file in os.listdir(WARN_FOLDER):
		if file.endswith(".json"):
			with open(os.path.join(WARN_FOLDER, file), "r") as f:
				warns[file.replace(".json", "")] = json.load(f)
	return warns

# Function to save warnings
def save_warn(user_id, data):
	with open(os.path.join(WARN_FOLDER, f"{user_id}.json"), "w") as f:
		json.dump(data, f, indent=4)

# Load warns initially
warns = load_warns()

# ======================================================================================================================================================================================
# Warn Command

@bot.command()
async def warn(ctx: commands.Context, member: discord.Member = None, *, reason: str = None):
	await ctx.message.delete()

	# Ensure the user issuing the warning has moderator, admin, or servicer role
	has_role = is_staff(ctx.author, True, True, True)
	if not has_role:
		embed = discord.Embed(title="❌ Permission Denied", description="> You need the **Moderator** Role or above to use this command.", color=colors["red"])
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'warn' in {ctx.channel} but lacks permissions.")
		return

	# Ensure a user is mentioned and a reason is provided
	if not member or not reason:
		embed = discord.Embed(title="❌ Invalid Command Usage", description="> Use `!warn @user <reason>` to warn a user.", color=colors["red"])
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} attempted to use 'warn' in {ctx.channel} but provided invalid arguments.")
		return

	# Ensure the user being warned is not a moderator, admin, or servicer
	if is_staff(member, True, True, True):
		embed = discord.Embed(title="❌ Cannot Warn Staff", description="> You cannot warn a **Moderator, Administrator, or Servicer**.", color=colors["red"])
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} attempted to warn {member}, but they have a protected role.")
		return

	# Load existing warnings for the user
	user_id = str(member.id)
	warns = load_warns().get(str(user_id), [])

	# Add the new warning
	warns.append({
		"warned_by": str(ctx.author),
		"warned_by_id": ctx.author.id,
		"reason": reason,
		"date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
	})
	save_warn(user_id, warns)

	# Send confirmation
	embed = discord.Embed(title="⚠️ User Warned", description=f"> **{member}** has been warned.\n> **Reason:** {reason}", color=colors["orange"])
	embed.set_footer(text=f"Warned by {ctx.author.display_name}")
	view = DoneButton(ctx.author.id)
	await ctx.send(f"### {ctx.author.mention}", embed=embed, view=view)
	logger.info(f"{ctx.author} warned {member} for: {reason}")


# ======================================================================================================================================================================================
# Warns Command
@bot.command(name="warns")
async def warns_command(ctx: commands.Context, member: discord.Member = None):
	await ctx.message.delete()

	# Ensure the user has a moderator role
	has_role = is_staff(ctx.author, True, True, True)
	if not has_role:
		embed = discord.Embed(title="❌ Permission Denied", description="> You need the **Moderator** Role or above to use this command.", color=colors["red"])
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'warns' in {ctx.channel} but lacks permissions.")
		return

	# Load warnings
	warns = load_warns()

	# Show warnings for a specific user
	if member:
		user_id = str(member.id)
		if user_id in warns and warns[user_id]:
			warn_list = "\n".join([f"> **Date:** {warn['date']}\n> **Reason:** {warn['reason']}\n> **Warned By:** {warn['warned_by']}\n" for warn in warns[user_id]])
			embed = discord.Embed(title=f"⚠️ Warnings for {member.display_name}", description=warn_list, color=colors["orange"])
			view = DoneButton(ctx.author.id)
			await ctx.send(f"### {ctx.author.mention}", embed=embed, view=view)
			logger.info(f"{ctx.author} checked warnings for {member} in {ctx.channel}.")
		else:
			embed = discord.Embed(title="✅ No Warnings", description=f"> **{member}** has no recorded warnings.", color=colors["green"])
			await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
			logger.info(f"{ctx.author} checked warnings for {member} in {ctx.channel}, but none were found.")
		return

	# Show all warnings
	if warns:
		all_warns = "\n".join([f"> **{bot.get_user(int(user))}** ({user}) -  **Warnings:** {len(warns[user])}\n" for user in warns])
		embed = discord.Embed(title="⚠️ All User Warnings", description=all_warns, color=colors["orange"])
		view = DoneButton(ctx.author.id)
		await ctx.send(f"### {ctx.author.mention}", embed=embed, view=view)
		logger.info(f"{ctx.author} checked all warnings in {ctx.channel}.")
	else:
		embed = discord.Embed(title="✅ No Warnings Recorded", description="> There are no recorded warnings.", color=colors["green"])
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} checked all warnings in {ctx.channel}, but none were found.")

# ======================================================================================================================================================================================
# Ban Info Command

@bot.command()
async def bans(ctx: commands.Context, user_query: str = None):
	await ctx.message.delete()

	# Check if the user has the admin role
	has_role = is_staff(ctx.author, False, True, True)
	if not has_role:
		embed = discord.Embed(
			title="❌ Permission Denied",
			description="> You need the **Moderator** role to use this command.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'bans' in {ctx.channel} but lacks permissions.")
		return

	# Load bans
	bans = load_bans()

	if not bans:
		embed = discord.Embed(
			title="📜 No Bans Found",
			description="> There are **no recorded bans** in the system.",
			color=colors["green"]
		)
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} checked the ban list in {ctx.channel}. No bans found.")
		return

	# If no user is specified, show the full ban list
	if not user_query:
		ban_list = "\n".join([f"> **{data['user']}**\n> \n> **ID:** ({data['user_id']})\n>  **Reason:** {data['reason']}\n> **Banned by:** {data['banned_by']}\n" for data in bans.values()])

		embed = discord.Embed(
			title="🚫 Ban List",
			description=ban_list if ban_list else "> No bans recorded.",
			color=colors["red"]
		)
		view = DoneButton(ctx.author.id)
		embed.set_footer(text="Use !bans <user> to search for a specific user.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, view=view)
		logger.info(f"{ctx.author} checked the full ban list in {ctx.channel}.")
		return

	# Search for the user by ID, username, or mention
	user_query = user_query.strip("<@!>")  # Remove mention formatting if applicable
	found_ban = None

	for user_id, data in bans.items():
		if user_query == user_id or user_query.lower() == data["user"].lower():
			found_ban = data
			break

	if found_ban:
		embed = discord.Embed(
			title="🚫 Ban Record Found",
			description=(
				f"> **User:** \n> {found_ban['user']} (`{found_ban['user_id']}`)\n> "
				f"\n> **Banned By:**\n> {found_ban['banned_by']} (`{found_ban['banned_by_id']}`)\n> "
				f"\n> **Reason:**\n> {found_ban['reason']}\n> "
				f"\n> **Date:**\n> {found_ban['date']}"
			),
			color=colors["red"]
		)
		view = DoneButton(ctx.author.id)
		embed.set_footer(text="Use !bans to see all bans.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, view=view)
		logger.info(f"{ctx.author} searched for {user_query} in {ctx.channel} and found a ban record.")
	else:
		embed = discord.Embed(
			title="📜 No Ban Record Found",
			description=f"> No ban record found for **{user_query}**.",
			color=colors["green"]
		)
		await ctx.send(embed=embed, delete_after=10)
		logger.info(f"{ctx.author} searched for {user_query} in {ctx.channel} but no record was found.")

# ======================================================================================================================================================================================
# Mute Command & Buttons

# Unmute button class
class UnmuteButton(discord.ui.View):
	def __init__(self, moderator_id, member):
		super().__init__(timeout=None)
		self.moderator_id = moderator_id
		self.member = member

	@discord.ui.button(label="Unmute", style=discord.ButtonStyle.danger, custom_id="unmute_button")
	async def done_button(self, button: discord.ui.Button, interaction: discord.Interaction):
		# Ensure only the moderator who issued the mute can unmute
		if interaction.user.id != self.moderator_id:
			await interaction.response.send_message("You are not authorized to unmute this user.", ephemeral=True)
			return

		# Unmute the user
		try:
			await self.member.edit(communication_disabled_until=None)
			await interaction.response.send_message(f"✅ **{self.member} has been unmuted!**", ephemeral=False)
			await asyncio.sleep(3)
			await interaction.delete_original_response()

			# Log the unmute action
			logger.info(f"{interaction.user} unmuted {self.member}")

		except discord.Forbidden:
			await interaction.response.send_message("❌ I lack the permissions to unmute this user.", ephemeral=True)

@bot.command()
async def mute(ctx: commands.Context, member: discord.Member = None, duration: str = None, *, reason: str = None):
	await ctx.message.delete()

	# Ensure the user issuing the mute has moderator, admin, or servicer role
	has_role = is_staff(ctx.author, True, True, True)
	if not has_role:
		embed = discord.Embed(title="❌ Permission Denied", description="> You need the **Moderator** Role or above to use this command.", color=0xFF0000)
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'mute' in {ctx.channel} but lacks permissions.")
		return

	# Ensure a user is mentioned, a duration is provided, and a reason is given
	if not member or not duration or not reason:
		embed = discord.Embed(title="❌ Invalid Command Usage", description="> Use `!mute @user <duration> <reason>` to mute a user.\n> Example: `!mute @User 10m Spamming`", color=0xFF0000)
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} attempted to use 'mute' in {ctx.channel} but provided invalid arguments.")
		return

	# Ensure the user being muted is not a moderator, admin, or servicer
	if is_staff(member, True, True, True):
		embed = discord.Embed(title="❌ Cannot Mute Staff", description="> You cannot mute a **Moderator, Administrator, or Servicer**.", color=0xFF0000)
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} attempted to mute {member}, but they have a protected role.")
		return

	# Convert duration to seconds
	time_multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
	try:
		unit = duration[-1]
		if unit not in time_multipliers or not duration[:-1].isdigit():
			raise ValueError
		mute_seconds = int(duration[:-1]) * time_multipliers[unit]
	except ValueError:
		embed = discord.Embed(title="❌ Invalid Duration Format", description="> Use a valid format: `Xs`, `Xm`, `Xh`, `Xd` (e.g., `10m` for 10 minutes)", color=0xFF0000)
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} provided an invalid duration for 'mute' command.")
		return

	# Apply timeout (mute) to the user
	try:
		until = discord.utils.utcnow() + datetime.timedelta(seconds=mute_seconds)
		await member.edit(communication_disabled_until=until, reason=reason)
	except discord.Forbidden:
		embed = discord.Embed(title="❌ Mute Failed", description="> I lack permission to mute this user.", color=0xFF0000)
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.error(f"Failed to mute {member} due to insufficient bot permissions.")
		return

	# Log the mute as a warning
	user_id = str(member.id)
	warns = load_warns().get(user_id, [])

	warns.append({
		"warned_by": str(ctx.author),
		"warned_by_id": ctx.author.id,
		"reason": f"[MUTE] {reason} (Duration: {duration})",
		"date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S")
	})
	save_warn(user_id, warns)

	view = UnmuteButton(ctx.author.id, member)  # Unmute button
	done_view = DoneButton(ctx.author.id)  # Your existing Done button
	# Combine both views
	combined_view = discord.ui.View()
	for child in view.children:
		combined_view.add_item(child)
	for child in done_view.children:
		combined_view.add_item(child)

	# Send confirmation
	embed = discord.Embed(title="🔇 User Muted", description=f"> **{member}** has been muted for **{duration}**.\n> **Reason:** {reason}", color=0xFFA500)
	embed.set_footer(text=f"Muted by {ctx.author.display_name}")
	await ctx.send(f"### {ctx.author.mention}", embed=embed, view=combined_view)
	logger.info(f"{ctx.author} muted {member} for {duration} due to: {reason}")

# ======================================================================================================================================================================================
# ADMIN COMMANDS (Power Level 2)
# ======================================================================================================================================================================================
# Moderation Ban Files Config

# Ensure moderation folder exists
MODERATION_FOLDER = "moderation"
BAN_LOG_FILE = os.path.join(MODERATION_FOLDER, "bans.json")
os.makedirs(MODERATION_FOLDER, exist_ok=True)


# Function to load bans
def load_bans():
	if not os.path.exists(BAN_LOG_FILE):
		with open(BAN_LOG_FILE, "w") as file:
			json.dump({}, file)
	try:
		with open(BAN_LOG_FILE, "r") as file:
			return json.load(file)
	except json.JSONDecodeError:
		return {}


# Function to save bans
def save_bans(ban_data):
	with open(BAN_LOG_FILE, "w") as file:
		json.dump(ban_data, file, indent=4)


# ======================================================================================================================================================================================
# Ban Command

@bot.command()
async def ban(ctx: commands.Context, member: discord.Member = None, *, reason: str = None):
	await ctx.message.delete()

	# Check if the user has the admin role
	has_role = is_staff(ctx.author, False, True, True)
	if not has_role:
		embed = discord.Embed(
			title="❌ Permission Denied",
			description="> You need an `Administrator Role` to use this command.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'ban' in {ctx.channel} but lacks permissions.")
		return

	# Ensure a valid user is mentioned
	if not member:
		embed = discord.Embed(
			title="❌ Invalid Command Usage",
			description="> You must mention a **valid user** to ban.\n> **Example:** `!ban @user Spamming`",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} attempted to use 'ban' in {ctx.channel} but did not mention a user.")
		return

	# Ensure a reason is provided
	if not reason:
		embed = discord.Embed(
			title="❌ No Reason Provided",
			description="> You must provide a reason for banning this user.\n> **Example:** `!ban @user Spamming in chat`",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.info(f"{ctx.author} attempted to ban {member} but did not provide a reason.")
		return

	# Check if the member is bannable
	if not ctx.guild.me.guild_permissions.ban_members:
		embed = discord.Embed(
			title="⚠️ Missing Permissions",
			description="> I do not have permission to ban members.",
			color=colors["orange"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.warning(f"Bot does not have permission to ban members.")
		return

	# Ensure the user is not trying to ban someone with a higher or equal role
	if member.top_role >= ctx.author.top_role:
		embed = discord.Embed(
			title="⚠️ Action Forbidden",
			description="> You **cannot** ban someone with a higher or equal role to yourself.",
			color=colors["orange"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.warning(f"{ctx.author} attempted to ban {member}, but they have a higher or equal role.")
		return

	# Ban the user
	try:
		await member.ban(reason=reason)

		# Log the ban in the JSON file
		bans[str(member.id)] = {
			"user": str(member.global_name),
			"user_id": member.id,
			"banned_by": str(ctx.author),
			"banned_by_id": ctx.author.id,
			"reason": reason,
			"date": str(ctx.message.created_at)
		}
		save_bans(bans)

		# Send confirmation
		embed = discord.Embed(
			title="🔨 User Banned",
			description=f"> **{member}** has been banned from the server.\n> **Reason:** {reason}",
			color=colors["red"]
		)
		view = DoneButton(ctx.author.id)
		embed.set_footer(text=f"Banned by {ctx.author.display_name}")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, view=view)
		logger.info(f"{ctx.author} banned {member} for: {reason}")

	except discord.Forbidden:
		embed = discord.Embed(
			title="⚠️ Action Forbidden",
			description="> I **cannot** ban this user. They may have a higher role than me.",
			color=colors["orange"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.warning(f"{ctx.author} attempted to ban {member}, but bot lacks permissions.")

	except Exception as e:
		embed = discord.Embed(
			title="❌ Error",
			description="> An error occurred while trying to ban this user.",
			color=colors["red"]
		)
		embed.set_footer(text="Please contact an administrator.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
		logger.error(f"Error while banning {member}: {e}")


# ======================================================================================================================================================================================
# Restart Bot

@bot.command()
async def restart(ctx: commands.Context):
	await ctx.message.delete()

	# Check if the user has the "Administrator" or "Servicer" role
	has_role = is_staff(ctx.author, False, True, True)
	if not has_role:
		embed = discord.Embed(
			title="❌ Permission Denied",
			description="> You need the `Administrator` role to restart the bot.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to restart the bot but lacks permissions.")
		return

	# Notify that the bot is restarting
	embed = discord.Embed(
		title="🔄 Restarting Bot",
		description=f"> Bot is restarting... \n> **Triggered by:** {ctx.author.mention}",
		color=colors["orange"]
	)
	embed.set_footer(text="Please wait for the bot to come back online.")
	restart_message = await ctx.send(f"### {ctx.author.mention}", embed=embed)

	logger.info(f"{ctx.author} triggered the bot restart.")

	# Wait for 3 seconds before deleting the message
	await asyncio.sleep(3)
	await restart_message.delete()

	try:
		# Gracefully close the bot
		await bot.close()

		# Restart the bot
		python = sys.executable
		os.execl(python, python, *sys.argv)

	except Exception as e:
		logger.error(f"Failed to restart the bot: {e}")
		embed = discord.Embed(title="❌ Restart Failed",
							  description=f"> An error occurred while restarting the bot.\n> \n> `{str(e)}`",
							  color=colors["red"])
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)


# ======================================================================================================================================================================================
# Ping Command

@bot.command()
async def ping(ctx: commands.Context):
	await ctx.message.delete()

	# Check if the user has the required role (Administrator or Servicer)
	has_role = any(role.id in ADMIN_ROLE_ID or role.id in SERVICER_ROLE_ID for role in ctx.author.roles)
	if not has_role:
		embed = discord.Embed(
			title="❌ Permission Denied",
			description="> You need the `Administrator` role to use this command.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} attempted to use 'ping' in {ctx.channel} but lacks permissions.")
		return  # Exit early before applying cooldown

	# Apply cooldown only if user has the proper role
	if ctx.command.is_on_cooldown(ctx):
		retry_after = ctx.command.get_cooldown_retry_after(ctx)
		embed = discord.Embed(
			title="⏳ Cooldown!",
			description=f"> This command is on cooldown! Try again in `{retry_after:.2f}` seconds.",
			color=colors["red"]
		)
		embed.set_footer(text="This message was written by server staff.")
		await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=5)
		logger.info(f"{ctx.author} tried 'ping' in {ctx.channel}, but it's on cooldown.")
		return

	# Apply cooldown manually after permission check
	ctx.command.reset_cooldown(ctx)

	# Get bot latency
	latency = round(bot.latency * 1000)  # Convert to milliseconds

	# Create the embed
	embed = discord.Embed(
		title="🏓 Ping, Pong!",
		description=f"> Bot Latency: `{latency}ms`",
		color=colors["green"]
	)
	embed.set_footer(text="This message was written by server staff.")

	# Send the embed
	await ctx.send(f"### {ctx.author.mention}", embed=embed, delete_after=10)
	logger.info(f"{ctx.author.mention} triggered the 'ping' command in {ctx.channel}. Output sent.")


# ======================================================================================================================================================================================
# Run the bot

if __name__ == "__main__":
	# Load bans
	bans = load_bans()

	bot.run(BOT_TOKEN)

# Saucywan was here.
