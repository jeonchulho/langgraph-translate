"""Discord bot for translation service."""
import os
import logging
from typing import Optional

import discord
from discord import app_commands
import requests
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is required")


class TranslationBot(discord.Client):
    """Discord bot for translation."""
    
    def __init__(self):
        """Initialize the bot."""
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        """Setup hook for bot initialization."""
        await self.tree.sync()
        logger.info("Command tree synced")
    
    async def on_ready(self):
        """Event handler for bot ready."""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")


# Initialize bot
bot = TranslationBot()


@bot.tree.command(name="translate", description="Translate text between English and Korean")
@app_commands.describe(text="Text to translate")
async def translate_command(interaction: discord.Interaction, text: str):
    """
    Slash command to translate text.
    
    Args:
        interaction: Discord interaction
        text: Text to translate
    """
    await interaction.response.defer()
    
    try:
        # Call backend API
        response = requests.post(
            f"{BACKEND_URL}/api/translate",
            json={"text": text},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Create embed for result
            embed = discord.Embed(
                title="Translation Result",
                color=discord.Color.green()
            )
            
            # Add fields
            embed.add_field(
                name="Original Text",
                value=result["original"][:1024],  # Discord limit
                inline=False
            )
            
            language_name = "English" if result["detected_language"] == "en" else "Korean"
            embed.add_field(
                name="Detected Language",
                value=language_name,
                inline=True
            )
            
            embed.add_field(
                name="Quality Score",
                value=f"{result['quality_score']:.2f}",
                inline=True
            )
            
            embed.add_field(
                name="Translation",
                value=result["translation"][:1024],  # Discord limit
                inline=False
            )
            
            # Add quality indicator
            quality = result["quality_score"]
            if quality >= 0.7:
                embed.set_footer(text="✅ High quality translation")
            elif quality >= 0.5:
                embed.set_footer(text="⚠️ Moderate quality translation")
            else:
                embed.set_footer(text="❌ Low quality translation")
            
            await interaction.followup.send(embed=embed)
        else:
            error_detail = response.json().get("detail", "Unknown error")
            await interaction.followup.send(
                f"❌ Translation failed: {error_detail}",
                ephemeral=True
            )
    
    except requests.Timeout:
        await interaction.followup.send(
            "❌ Translation request timed out. Please try again.",
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"Translation error: {e}")
        await interaction.followup.send(
            f"❌ An error occurred: {str(e)}",
            ephemeral=True
        )


@bot.tree.command(name="help", description="Show translation bot help")
async def help_command(interaction: discord.Interaction):
    """
    Slash command to show help.
    
    Args:
        interaction: Discord interaction
    """
    embed = discord.Embed(
        title="Translation Bot Help",
        description="AI-powered English ↔ Korean translation service",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="/translate <text>",
        value="Translate text between English and Korean. The bot automatically detects the language.",
        inline=False
    )
    
    embed.add_field(
        name="/help",
        value="Show this help message",
        inline=False
    )
    
    embed.add_field(
        name="Features",
        value="• Automatic language detection\n"
              "• AI quality validation\n"
              "• High-quality translations using GPT-4",
        inline=False
    )
    
    embed.set_footer(text="Powered by LangGraph Translation Service")
    
    await interaction.response.send_message(embed=embed)


def main():
    """Run the Discord bot."""
    if not DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN not set")
        return
    
    logger.info("Starting Discord bot...")
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
