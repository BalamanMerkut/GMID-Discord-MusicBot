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
            "pause_resume": "gmid_pause" if self.music_player.voice_client and self.music_player.voice_client.is_playing() else "gmid_play",
            "stop": "gmid_stop",
            "skip": "gmid_skip",
            "loop": "gmid_loop",
            "shuffle": "gmid_shuffle"
        }
        
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id in emoji_map:
                emoji_name = emoji_map[child.custom_id]
                custom = self.get_emoji(emoji_name)
                if custom:
                    child.emoji = custom
                    # If previously it was "fine", it might have been because of the default emojis being used as labels.
                    # We will set label to None to try and let the custom emoji fill the button.
                    child.label = None
                else:
                    # Fallback to defaults if custom not found (yet)
                    defaults = {
                        "gmid_play": "▶️",
                        "gmid_pause": "⏸️",
                        "gmid_stop": "⏹️",
                        "gmid_skip": "⏭️",
                        "gmid_loop": "🔁",
                        "gmid_shuffle": "🔀"
                    }
                    child.emoji = defaults.get(emoji_name, child.emoji)

    async def update_view(self, interaction, state_name):
        """Helper to update the embed with a new state icon."""
        # Defer immediately to stop thinking status and capture response
        if not interaction.response.is_done():
            try:
                await interaction.response.defer()
            except:
                pass

        state_file = self.music_player.get_state_file(state_name)
        embed = interaction.message.embeds[0] if interaction.message.embeds else None
        
        # Ensure emojies are up to date on every interaction
        self.update_button_emojis()
        
        if state_file and embed:
            embed.set_thumbnail(url=f"attachment://{state_file.filename}")
            
        try:
            # Edit the message the button is on directly to avoid creating duplicates
            await interaction.message.edit(embed=embed, view=self, attachments=[state_file] if state_file else [])
            
            # If we haven't responded to the interaction yet, defer it to avoid "Interaction failed"
            if not interaction.response.is_done():
                await interaction.response.defer()
        except Exception as e:
            print(f"DEBUG: update_view error: {e}")
            # Fallback for some interaction types if direct message edit fails (e.g., ephemeral responses)
            if not interaction.response.is_done():
                await interaction.response.defer()
            # Use edit_original_response as a fallback, ensuring attachments are handled
            await interaction.edit_original_response(embed=embed, view=self, attachments=[state_file] if state_file else [])

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
        await interaction.response.defer(ephemeral=True)
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
