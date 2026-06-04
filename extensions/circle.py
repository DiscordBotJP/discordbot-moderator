import discord
from discord import app_commands
from discord.ext import commands
from daug.utils.dpyexcept import excepter
from daug.utils.dpylog import dpylogger
from utils.ops_log import emit_component_error

PERMISSION_OVERWRITE_ALL = discord.PermissionOverwrite(
    read_messages=False,
    connect=False,
)
PERMISSION_OVERWRITE_GUEST = discord.PermissionOverwrite(
    read_messages=True,
    connect=True,
)
PERMISSION_OVERWRITE_OWNER = discord.PermissionOverwrite(
    read_messages=True,
    connect=True,
    manage_channels=True,
    manage_permissions=True,
    manage_messages=True,
)


MESSAGE_CREATE_TEXT = """あなたが管理者のテキストチャンネルを用意しました。
チャンネルの編集画面から名前の変更やメンバーの招待などの設定を行ってください。
"""


async def create_text(interaction: discord.Interaction):
    await interaction.response.send_message('サークル用TCを作成します', ephemeral=True)
    new_channel = await interaction.guild.create_text_channel(
        name=f'{interaction.user.display_name}の部屋',
        category=interaction.guild.get_channel(interaction.channel.category_id),
        overwrites={
            interaction.guild.default_role: PERMISSION_OVERWRITE_ALL,
            interaction.user: PERMISSION_OVERWRITE_OWNER,
        }
    )
    await new_channel.send(f'{interaction.user.mention} {MESSAGE_CREATE_TEXT}')


class CreateTextButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        await emit_component_error(interaction, error, item)

    @discord.ui.button(label='新規サークル作成', style=discord.ButtonStyle.green, custom_id='circle:create')
    @excepter
    @dpylogger
    async def a_line(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_text(interaction)


class CircleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(CreateTextButton())

    @app_commands.command(name='サークル作成ボタン設置', description='メンバーがサークル用TCを作成できるボタンを設置します')
    @app_commands.guild_only()
    @excepter
    @dpylogger
    async def _put_button_create_circle_app_command(self, interaction: discord.Interaction):
        if not interaction.user.resolved_permissions.manage_channels:
            await interaction.response.send_message('ここは自分の部屋じゃないよ！', ephemeral=True)
            return
        await interaction.response.send_message('メンバーがサークル用TCを作成できるボタンを設置します', ephemeral=True)
        await interaction.channel.send(view=CreateTextButton())

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CircleCog(bot))
