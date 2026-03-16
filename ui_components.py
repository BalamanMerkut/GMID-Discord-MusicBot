import discord
from discord.ui import View, Button

class MusicControlView(View):
    def __init__(self, music_player):
        super().__init__(timeout=None)
        self.music_player = music_player
        self.update_button_emojis()

    def get_emoji(self, name):
        """Helper to find a custom emoji by name in the guild."""
        if not self.music_player.voice_client or not self.music_player.voice_client.guild:
            return None
        return discord.utils.get(self.music_player.voice_client.guild.emojis, name=name)

    def update_button_emojis(self):
        """Initializes button emojis with custom server emojis if available."""
        # Map button custom_ids to emoji names
        emoji_map = {
            "pause_resume": "rew",
            "stop": "unnamed__1_removebgpreview1",
            "skip": "skip",
            "loop": "rewe",
            "shuffle": "re"
        }
        
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id in emoji_map:
                custom = self.get_emoji(emoji_map[child.custom_id])
                if custom:
                    child.emoji = custom
                    child.label = None # Remove label if custom emoji found

    async def update_view(self, interaction, state):
        """Helper to update the embed with a new state icon."""
        state_file = self.music_player.get_state_file(state)
        embed = interaction.message.embeds[0]
        
        # Ensure emojies are up to date on every interaction
        self.update_button_emojis()
        
        if state_file:
            embed.set_thumbnail(url=f"attachment://{state}.png")
            await interaction.response.edit_message(attachments=[state_file], embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="⏯️", style=discord.ButtonStyle.primary, custom_id="pause_resume")
    async def pause_resume_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.music_player.is_paused():
            await self.music_player.resume(interaction)
            await self.update_view(interaction, "play")
        else:
            await self.music_player.pause(interaction)
            await self.update_view(interaction, "pause")

    @discord.ui.button(label="⏹️", style=discord.ButtonStyle.danger, custom_id="stop")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_player.stop(interaction)

    @discord.ui.button(label="⏭️", style=discord.ButtonStyle.secondary, custom_id="skip")
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_player.skip(interaction)

    @discord.ui.button(label="🔁", style=discord.ButtonStyle.secondary, custom_id="loop")
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_player.toggle_loop(interaction)
        state = "loop" if self.music_player.loop else "play"
        await self.update_view(interaction, state)

    @discord.ui.button(label="🔀", style=discord.ButtonStyle.secondary, custom_id="shuffle")
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_player.shuffle_queue(interaction)
        state = "shuffle" if self.music_player.shuffle else "play"
        await self.update_view(interaction, state)
