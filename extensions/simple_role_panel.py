import discord
from discord import app_commands
from discord.ext import commands
from daug.utils import extract_role_mentions
from daug.utils.dpyexcept import excepter
from daug.utils.dpylog import dpylogger
from daug.constants import COLOUR_EMBED_GRAY
from utils.ops_log import emit_component_error


class RoleSettingButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        await emit_component_error(interaction, error, item)

    @discord.ui.button(label='ロールを付ける', style=discord.ButtonStyle.blurple, custom_id='role:button:add')
    @excepter
    @dpylogger
    async def _add_role_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        role = extract_role_mentions(interaction.guild, interaction.message.embeds[0].description)[0]
        await interaction.user.add_roles(role)
        await interaction.followup.send(f'{role.mention} ロールを付けました', ephemeral=True)

    @discord.ui.button(label='ロールを外す', style=discord.ButtonStyle.red, custom_id='role:button:remove')
    @excepter
    @dpylogger
    async def _remove_role_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        role = extract_role_mentions(interaction.guild, interaction.message.embeds[0].description)[0]
        await interaction.user.remove_roles(role)
        await interaction.followup.send(f'{role.mention} ロールを外しました', ephemeral=True)


class SimpleRolePanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.bot.add_view(RoleSettingButtons())

    @app_commands.command(name='簡易ロールパネル設置ボタン', description='メンバーがロールを付け外しできるボタンを設置します')
    @app_commands.rename(role='ロール')
    @app_commands.describe(role='付け外し対象のロール')
    @app_commands.guild_only()
    @excepter
    @dpylogger
    async def _put_panel_role_app_command(self, interaction: discord.Interaction, role: discord.Role):
        if not interaction.user.resolved_permissions.administrator:
            await interaction.response.send_message('管理者専用コマンドです', ephemeral=True)
            return
        await interaction.response.send_message('メンバーがロールを付け外しできるボタンを設置します', ephemeral=True)
        await interaction.channel.send(
            embed=discord.Embed(description=f'ボタンを押すと {role.mention} ロールを付け外しできます', color=COLOUR_EMBED_GRAY),
            view=RoleSettingButtons(),
        )
        return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SimpleRolePanelCog(bot))
