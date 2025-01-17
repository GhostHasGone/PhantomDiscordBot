# ©2025 GhostHasGone
# Add 'ghosthasgone' on Discord for support or inquiries.

# ======================================================================================================================================================================================
# Imports

import discord
from discord.ext import commands
import asyncio
import logging
import random
import os
import random
import string
import json
from discord import Color as c

# ======================================================================================================================================================================================
# Important Stuff

# Load the configuration from the JSON file
with open("config.json", "r") as config_file:
	config = json.load(config_file)

# Extract values from the config
BOT_TOKEN = config["BOT_TOKEN"]
MODMAIL_CATAGORY_ID = config["MODMAIL_CATAGORY_ID"]
ALLOWED_ROLE_IDS = config["ALLOWED_ROLE_IDS"]
ALLOWED_ROLE_MENTION = config["ALLOWED_ROLE_MENTION"]
WELCOME_CHANNEL = config["WELCOME_CHANNEL"]
GUILD_ID = config["GUILD_ID"]
RULES_CHANNEL = config["RULES_CHANNEL"]
TEXT_LOG_CHANNEL_ID = config["TEXT_LOG_CHANNEL_ID"]
IMAGE_LOG_CHANNEL_ID = config["IMAGE_LOG_CHANNEL_ID"]
VERSION = "1.3.1"
VERSION_DATE = "January 16th, 2025"

# Create a bot instance with a command prefix
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# ======================================================================================================================================================================================
# The buttons for the ModMail Interactions
# Part One: "Resolved"

class ModmailView(discord.ui.View):
	def __init__(self, guild, allowed_roles, modmail_user):
		super().__init__(timeout=None)
		self.guild = guild
		self.allowed_roles = allowed_roles
		self.modmail_user = modmail_user

	@discord.ui.button(label="Resolved", style=discord.ButtonStyle.success)
	async def resolved_button(self, interaction: discord.Interaction, button: discord.ui.Button):

		# Update permissions to restrict access to staff only
		overwrites = {
			self.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False, ),
		}

		for role_id in self.allowed_roles:
			role = self.guild.get_role(role_id)
			if role:
				overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

				embed = discord.Embed(
					title="Resolved Issue",
					description="\n> The issue is now resolved.\n> \n> Only staff have access to the channel now.",
					color=discord.Color.yellow()
				)
				embed.set_footer(
			text="This message was written by server staff.",
			)
		await interaction.response.send_message(embed=embed)

		# Add "(R)" to the resolved channel name
		channel = interaction.channel
		new_name = f"(R) {channel.name}"
		await channel.edit(name=new_name)
		await channel.edit(overwrites=overwrites)

# ======================================================================================================================================================================================
# The buttons for the ModMail Interactions
# Part One: "Closed"

	@discord.ui.button(label="Close", style=discord.ButtonStyle.danger)
	async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
		# Check if the user has permission to use this button
		if not any(role.id in self.allowed_roles for role in interaction.user.roles):
			await interaction.response.send_message("You don't have permission to close this thread.", ephemeral=True)
			return

		embed = discord.Embed(
					title="Channel Deletion",
					description="> This channel will be deleted in a few seconds.",
					color=discord.Color.red()
				)
		embed.set_footer(
			text="This message was written by server staff.",
			)
		await interaction.response.send_message(embed=embed)

		# Wait for 5 seconds
		await asyncio.sleep(5)

		channel = interaction.channel
		await channel.delete(reason="Modmail thread closed.")

# ======================================================================================================================================================================================
# Configure logging for all bot actions and messages

# Ensure the logs directory exists
log_folder = "logs"
os.makedirs(log_folder, exist_ok=True)
with open("assets/colors.json", "r") as file:
	colors = json.load(file)

os.makedirs("logs/images", exist_ok=True)

# Full path for the logs file
log_file_path = os.path.join(log_folder, "logs.txt")

# Configure logging
logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(levelname)s - %(message)s",
	handlers=[
		logging.FileHandler(log_file_path, encoding="utf-8"),  # Log to logs/logs.txt
		logging.StreamHandler(),  # Print logs to the console
	],
)
logger = logging.getLogger(__name__)

# Log "Bot Started"
logger.info("=======================================================================================")
logger.info("BOT STARTED ===========================================================================")
logger.info("=======================================================================================")

# ======================================================================================================================================================================================
# When Bot starts

@bot.event
async def on_ready():
	global text_log_channel, image_log_channel

	# Set Status
	print(f"Bot is logged in as {bot.user}") # States the bot user
	await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ModMail")) # Status "listening to ModMail"

	# Fetch the text and image log channels
	text_log_channel = bot.get_channel(TEXT_LOG_CHANNEL_ID)
	image_log_channel = bot.get_channel(IMAGE_LOG_CHANNEL_ID)

	print("\nLOGS: \n") # Prints logs handle

# ======================================================================================================================================================================================
# Bot event for messages
# Part One: Text-Logs Channel and Text Log File

@bot.event
async def on_message(message):
	# Makes sure it shows nothing from the bot
	if message.author.bot:
		return
	else:

		# Ensure the log channels exist in the bot's known channels
		if not text_log_channel or not image_log_channel:
			print("Log channels not found. Ensure the bot has access to the target server.")


		# Log text-based messages in test-logs channel and Logs file
		if message.content and not isinstance(message.channel, discord.DMChannel): 

			embed = discord.Embed(
				title=(f"Message from {message.author} in {message.channel}"),
				description=(f"> {message.content}"),
				color=discord.Color.green(),
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

				guild = bot.get_guild(GUILD_ID)
				
				if guild is None:
					await message.author.send("Could not retrieve the server. Please contact the server administrators.")
					return
				
				# Fetch the category
				category = discord.utils.get(guild.categories, id=MODMAIL_CATAGORY_ID)
				if category is None:
					await message.author.send("Modmail category is not configured properly. Please contact the server administrators.")
					return
				
				# Create permissions for the user and allowed roles
				overwrites = {
					guild.default_role: discord.PermissionOverwrite(read_messages=False),  # Deny access to everyone by default
					message.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),  # Allow the user
				}
				
				# Add permissions for allowed roles
				for role_id in ALLOWED_ROLE_IDS:
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
				title="Modmail Thread",
				description=f"> Modmail initiated by {message.author.mention}. \n> \n> Please describe your issue and how we can assist you.",
				color=discord.Color.blue()
			)
				embed.set_footer(
				text="Use the buttons below to manage this thread",
				)

				view = ModmailView(guild=guild, allowed_roles=ALLOWED_ROLE_IDS, modmail_user=message.author)
				await channel.send(f"### {ALLOWED_ROLE_MENTION} Come help!", embed=embed, view=view)

				# Notify the user
				embed = discord.Embed(
					title="ShedMail",
					description=(f"> A modmail has been created, click below to view the ticket:\n> \n> {channel.mention}"),
					color=discord.Color.green()
				)
				embed.set_footer(
				text="This message was written by server staff.",
				)
				await message.author.send(f"### {message.author.mention} Thank you for reaching out!", embed=embed)

# ======================================================================================================================================================================================
# Bot event for messages
# Part Four: If DM'd the word "Help"

			elif message.content.strip().lower() == "help":

				embed = discord.Embed(
				title="Hello! I am ShedMail, Your friendly modmail bot!",
				description="\n> My job is to allow you to message staff! \n> \n> Simply type the word **'contact'** and the staff will be notified!",
				color=discord.Color.yellow()
				)
				embed.set_footer(
				text="This message was written by server staff.",
				)
				await message.author.send(f"### {message.author.mention} ShedMail, here to help!", embed=embed)
			
# ======================================================================================================================================================================================
# Bot event for messages
# Part Five: If DM'd anything other than those words

			else:

				embed = discord.Embed(
					title="Unknown Command!",
					description="\n> Type **'help'** for assistance",
					color=discord.Color.red()
				)
				embed.set_footer(
				text="This message was written by server staff.",
				)
				await message.author.send(f"### {message.author.mention} Hmmm...", embed=embed)

		await bot.process_commands(message)  # Process commands normally

# ======================================================================================================================================================================================
# Bot Event for memmber joins:
# Part One: DM the Member

@bot.event
async def on_member_join(member):

	try:
		embed = discord.Embed(
			title="Welcome!",
			description=(f"> Thank you for joining {member.guild.name}!\n> We're happy to get the chance to chat with you!\n> \n> - Make sure to check out the Rules:\n> {RULES_CHANNEL}\n> \n> - Chat and Enjoy our wonderful server"),
			color=discord.Color.green()
		)
		embed.set_footer(
			text="This message was written by server staff.",
		)

		await member.send(embed=embed)
	except discord.Forbidden:
		print(f"Could not send a DM to {member.name}. They may have DMs disabled.")

# ======================================================================================================================================================================================
# Bot Event for memmber joins:
# Part Two: Send to Welcome Channel

	# Define the channel to send the message
	wlcmchannel = bot.get_channel(WELCOME_CHANNEL)
	# Create the embed
	embed = discord.Embed(
		title="Welcome to the Server!",
		description=(
			f"> Hey {member.mention}, welcome to **{member.guild.name}**!\n"
			f"> We're so excited to have you here!\n> \n"
			f"> Please remember to read the Rules in {RULES_CHANNEL}."
		),
		color=colors["gold"]
	)
	embed.set_thumbnail(url=member.avatar.url)  # User's profile picture
	embed.set_footer(
		text=f"Member #{len(member.guild.members)}",
	)
	# Send the embed in the channel
	await wlcmchannel.send(embed=embed)

# ======================================================================================================================================================================================
# Bot Event for memmber joins:
# Part Three: Log it in the Text-Logs Channel and the Text-Log File

	embed = discord.Embed(
				title=(f"Member Joined!"),
				description=(f"> {member.name}\n> \n> ({member.mention})"),
				color=colors["orange"]
			)
	embed.set_thumbnail(url=member.avatar.url)  # User's profile picture
	embed.set_footer(
		text=f"Member #{len(member.guild.members)}",
		)

			# Send embed in text-logs channel
	await text_log_channel.send(embed=embed)

			# Log when a new member joins
	logger.info(f"Member joined: {member.name} (ID: {member.id}).")

# ======================================================================================================================================================================================
# When a member leaves or gets banned/kicked from the server

@bot.event
async def on_member_remove(member):
	# Log when a member leaves
	logger.info(f"Member left: {member.name} (ID: {member.id}).")

	embed = discord.Embed(
				title=(f"Member Left!"),
				description=(f"> {member.name}"),
				color=colors["orange"]
			)
	embed.set_thumbnail(url=member.avatar.url)  # User's profile picture
	embed.set_footer(
		text=f"Member #{len(member.guild.members)}",
		)

			# Send embed in text-logs channel
	await text_log_channel.send(embed=embed)

# ======================================================================================================================================================================================
# Bot added to a server

@bot.event
async def on_guild_join(guild):
	invite = await guild.text_channels[0].create_invite()
	invite_str = f"https://discord.gg/{invite.code}"
	# Log when the bot is added to a new guild
	logger.info(f"Bot added to guild: {guild.name} (ID: {guild.id}). Members: {len(guild.members)} Link: {invite_str}")

	embed = discord.Embed(
				title=(f"Bot added to a Server:"),
				description=(f"> {guild.name}, ID: {guild.id}).\n> Link: {invite_str}"),
				color=colors["black"]
			)

			# Send embed in text-logs channel
	await text_log_channel.send(embed=embed)

# ======================================================================================================================================================================================
# Bot removed from Server

@bot.event
async def on_guild_remove(guild):
	# Log when the bot is removed from a guild
	logger.info(f"Bot removed from guild: {guild.name} (ID: {guild.id}).")

	embed = discord.Embed(
				title=(f"Bot Removed from Server:"),
				description=(f"> {guild.name}, ID: {guild.id})."),
				color=colors["black"]
			)

			# Send embed in text-logs channel
	await text_log_channel.send(embed=embed)

# ======================================================================================================================================================================================
# An Error happens in the code

@bot.event
async def on_error(event):
	# Log any errors that occur in events
	logger.error(f"Error in event '{event}':", exc_info=True)

	embed = discord.Embed(
				title=(f"Error in {event}"),
				description=(f"> "),
				color=colors["dark_red"]
			)

			# Send embed in text-logs channel
	await text_log_channel.send(embed=embed)

# ======================================================================================================================================================================================
# Message Delete

@bot.event
async def on_message_delete(message):
	if message.guild:  # Check if the message was in a guild (not a DM)
		logger.info(f"Message from {message.author} deleted in #{message.channel}: '{message.content}'")

		embed = discord.Embed(
				title=(f"Message from {message.author} deleted in {message.channel}"),
				description=(f"> {message.content}"),
				color=colors["red"]
			)

			# Send embed in text-logs channel
		await text_log_channel.send(embed=embed)
	else:
		return

# ======================================================================================================================================================================================
# Message Edit

@bot.event
async def on_message_edit(before, after):
	if before.guild:  # Check if the message was in a guild (not a DM)
		logger.info(
			f"Message from {before.author} edited in #{before.channel}:\n"
			f"- Before: '{before.content}'\n"
			f"- After: '{after.content}'"
		)

		embed = discord.Embed(
				title=(f"Message from {before.author} deleted in {after.channel}"),
				description=(
			f"Message from {before.author} edited in #{before.channel}:\n"
			f"> - Before: '{before.content}'\n"
			f"> - After: '{after.content}'"
		),
			color=colors["yellow"]
		)

			# Send embed in text-logs channel
		await text_log_channel.send(embed=embed)
	else:
	   return

# ======================================================================================================================================================================================
# REGULAR COMMANDS
# Version and support command

@bot.command()
async def version(ctx):
	await ctx.message.delete()
	# Check if the user has any of the allowed roles
	has_role = any(role.id in ALLOWED_ROLE_IDS for role in ctx.author.roles)
	if has_role:

		embed = discord.Embed(
			title="Version",
			description=(f"> You are currently using {VERSION}\n> \n> Released on {VERSION_DATE}"),
			color=colors["fuchsia"]
		)
		embed.set_footer(
			text="Add 'ghosthasgone' on Discord for Support or Inquiries.",
		)

		await ctx.channel.send(f"### {ctx.author.mention} Version and Support:", embed=embed, delete_after=10)
	else:
		await ctx.channel.send(f"{ctx.author.mention} You don't have permission to run this command.", delete_after=5)

# ======================================================================================================================================================================================
# Slap Command

@bot.command()
async def slap(ctx, member: discord.Member):
	await ctx.message.delete()
	# List of 10 slap GIF URLs

	slap_gifs = json.load(open("assets/slaps.json", "r"))

	# Randomly select a slap GIF
	selected_gif = random.choice(slap_gifs)

	# Create the embed
	embed = discord.Embed(
		title="Slap!",
		description=f"\n> **{ctx.author.mention} slapped {member.mention}!**\n",
		color=colors['red']
	)
	embed.set_image(url=selected_gif)

	# Send the embed
	await ctx.send(f"### {member.mention} Got Slapped!", embed=embed)

# ======================================================================================================================================================================================
# Topic Command

current_index = 0 # Global index to track the current topic

@bot.command()
async def topic(ctx):
	global current_index

	topics = json.load(open("assets/topics.json", "r")) # Load the topics from the topics.json

	if current_index < len(topics):  # Ensure index is within bounds
			await ctx.message.delete()
			selected_topic = topics[current_index]

			# Create an embed
			embed = discord.Embed(
				title="Let's Talk About...",
				description=(f" \n> **{selected_topic}**\n"),
				color=colors["gold"]
			)
			embed.set_footer(text="Enjoy the discussion!")

			# Send the embed
			await ctx.send(f"### Let's Yap!", embed=embed)

			# Move to the next topic
			current_index += 1
	else:
		# Reset or notify users that topics are finished
		await ctx.send("All topics have been discussed! Restarting...")
		current_index = 0  # Reset to the beginning

# ======================================================================================================================================================================================
# Run the bot

bot.run(BOT_TOKEN)
