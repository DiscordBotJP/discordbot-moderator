import discord
from discord import app_commands
from discord.ext import commands
from daug.utils.dpyexcept import excepter
from daug.utils.dpylog import dpylogger
from utils.ops_log import emit_component_error
from utils.ops_log import emit_exception_event

MESSAGE_CREATE_VOICE = """新しくボイスチャンネルを作成しました。"""


async def create_voice(interaction: discord.Interaction):
    await interaction.response.send_message('新しくVCを作成します', ephemeral=True)
    new_channel = await interaction.guild.create_voice_channel(
        name=f'{interaction.user.display_name}の部屋',
        category=interaction.guild.get_channel(interaction.channel.category_id),
    )
    await new_channel.send(f'{interaction.user.mention} {MESSAGE_CREATE_VOICE}')


async def create_private_thread_with_voice(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    if interaction.user.voice is None:
        await interaction.followup.send('VCに入ってから操作してください', ephemeral=True)
        return
    if not isinstance(interaction.user.voice.channel, discord.channel.VoiceChannel):
        await interaction.response.send_message('VCに入ってから操作してください', ephemeral=True)
        return
    thread = await interaction.channel.create_thread(
        name=interaction.user.voice.channel.name,
        auto_archive_duration=60,
        type=None,
        invitable=False,
    )
    try:
        mentions = ' '.join([m.mention for m in interaction.user.voice.channel.members])
        await thread.send(f'VC専用チャットを用意しました {mentions}')
    except discord.errors.Forbidden:
        await interaction.followup.send('スレッドにユーザーを追加する権限がありません', ephemeral=True)
        return
    except discord.errors.HTTPException:
        await interaction.followup.send('招待に失敗しました', ephemeral=True)
        return
    await thread.send(view=ThreadManageButtons())
    message = f'{interaction.user.mention}\nVC専用チャンネルを作成しました\n{thread.mention}'
    await interaction.followup.send(message, ephemeral=True)


class ThreadManageButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        await emit_component_error(interaction, error, item)

    @discord.ui.button(label='VCと名前を同期する', row=0, style=discord.ButtonStyle.green, custom_id='voice_channel_thread:sync_name')
    @excepter
    @dpylogger
    async def _invite_voice_members_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.voice is None:
            await interaction.followup.send('VCに入ってから操作してください', ephemeral=True)
            return
        if not isinstance(interaction.user.voice.channel, discord.channel.VoiceChannel):
            await interaction.response.send_message('VCに入ってから操作してください', ephemeral=True)
            return
        await interaction.channel.edit(name=interaction.user.voice.channel)
        await interaction.followup.send('VCと名前を同期しました', ephemeral=True)

    @discord.ui.button(label='VCとメンバーを同期する', row=0, style=discord.ButtonStyle.green, custom_id='voice_channel_thread:sync_member')
    @excepter
    @dpylogger
    async def _invite_voice_members_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if interaction.user.voice is None:
            await interaction.followup.send('VCに入ってから操作してください', ephemeral=True)
            return
        if not isinstance(interaction.user.voice.channel, discord.channel.VoiceChannel):
            await interaction.response.send_message('VCに入ってから操作してください', ephemeral=True)
            return
        thread_members = await interaction.channel.fetch_members()
        voice_members = interaction.user.voice.channel.members
        for thread_member in thread_members:
            if thread_member.id not in [m.id for m in voice_members]:
                try:
                    await interaction.channel.remove_user(thread_member)
                except discord.errors.Forbidden:
                    await interaction.followup.send('スレッドからユーザーを退出させる権限がありません', ephemeral=True)
                except discord.errors.HTTPException:
                    await interaction.followup.send('ユーザーを退出させるのに失敗しました', ephemeral=True)
        for voice_member in voice_members:
            if voice_member.id not in [m.id for m in thread_members]:
                try:
                    await interaction.channel.add_user(voice_member)
                except discord.errors.Forbidden:
                    await interaction.followup.send('スレッドにユーザーを招待する権限がありません', ephemeral=True)
                except discord.errors.HTTPException:
                    await interaction.followup.send('ユーザーの招待に失敗しました', ephemeral=True)
        await interaction.followup.send('VCとメンバーを同期しました', ephemeral=True)


class EditRoomModal(discord.ui.Modal, title='VC設定を更新する'):
    def __init__(self, target_voice_channel: discord.VoiceChannel, old_name: str, old_user_limit: int):
        super().__init__()
        self.target_voice_channel = target_voice_channel
        self.old_name = old_name
        self.old_user_limit = old_user_limit
        self.name = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label='新しい部屋の名前',
            default=old_name,
            required=True,
        )
        self.add_item(self.name)
        self.status = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label='チャンネルステータス',
            required=False,
        )
        self.add_item(self.status)
        self.user_limit = discord.ui.TextInput(
            style=discord.TextStyle.short,
            label='上限人数（0で上限なし）',
            default=old_user_limit,
            required=True,
        )
        self.add_item(self.user_limit)

    @excepter
    @dpylogger
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        payload = {}
        embed=discord.Embed()
        payload['name'] = self.name.value
        embed.add_field(name='部屋名', value=self.name.value)
        if self.status.value:
            payload['status'] = self.status.value
            embed.add_field(name='チャンネルステータス', value=self.status.value)
        payload['user_limit'] = int(self.user_limit.value)
        embed.add_field(name='人数上限', value=self.user_limit.value if int(self.user_limit.value) != 0 else 'なし')
        await self.target_voice_channel.edit(**payload)
        await interaction.followup.send('VC設定を更新しました', ephemeral=True)
        await self.target_voice_channel.send(
            f'{interaction.user.mention}\nVC設定を更新しました',
            embed=embed,
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await emit_exception_event(
            'command_error',
            'Voice channel modal failed',
            error,
            actor=str(interaction.user.id) if interaction.user else None,
            safe_details={
                'guildId': interaction.guild_id,
                'channelId': interaction.channel_id,
            },
        )
        message = 'VC設定の更新中にエラーが発生しました。入力内容を確認してもう一度お試しください。'
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


class VoiceChannelConfigButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,
    ) -> None:
        await emit_component_error(interaction, error, item)

    @discord.ui.button(label='入室中のVC設定を更新する', emoji='🔧', row=0, style=discord.ButtonStyle.blurple, custom_id='voice_channel:update')
    @excepter
    @dpylogger
    async def _update_voice_channel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.voice is None:
            await interaction.response.send_message('VCに入ってから操作してください', ephemeral=True)
            return
        if not isinstance(interaction.user.voice.channel, discord.channel.VoiceChannel):
            await interaction.response.send_message('VCに入ってから操作してください', ephemeral=True)
            return
        vc = interaction.user.voice.channel
        await interaction.response.send_modal(EditRoomModal(target_voice_channel=vc, old_name=vc.name, old_user_limit=vc.user_limit))

    @discord.ui.button(label='VC入室者専用チャットを作成する', emoji='📝', row=1, style=discord.ButtonStyle.green, custom_id='voice_channel:thread')
    @excepter
    @dpylogger
    async def _create_thread_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_private_thread_with_voice(interaction)

    @discord.ui.button(label='新しくVCを作成する', emoji='🗣️', row=2, style=discord.ButtonStyle.green, custom_id='voice_channel:create')
    @excepter
    @dpylogger
    async def _create_voice_channel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await create_voice(interaction)


class VoiceChannelPanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(VoiceChannelConfigButton())

    @app_commands.command(name='vc操作パネル設置', description='VC関連操作パネルを設置します')
    @app_commands.guild_only()
    @excepter
    @dpylogger
    async def _put_button_edit_panel_app_command(self, interaction: discord.Interaction):
        await interaction.response.send_message('VC関連操作パネルを設置します', ephemeral=True)
        await interaction.channel.send(view=VoiceChannelConfigButton())

    @commands.Cog.listener()
    @excepter
    async def on_message(self, message: discord.Message):
        try:
            await self._handle_thread_menu_message(message)
        except Exception as error:
            await emit_exception_event(
                'command_error',
                'Thread menu message failed',
                error,
                actor=str(message.author.id) if message.author else None,
                safe_details={
                    'guildId': message.guild.id if message.guild else None,
                    'channelId': message.channel.id if message.channel else None,
                    'messageId': message.id,
                },
            )
            raise

    async def _handle_thread_menu_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.author.system:
            return
        if message.guild is None:
            return
        if message.channel.type is discord.ChannelType.private_thread:
            if message.channel.owner != self.bot.user:
                return
            if message.content in ['メニュー', 'ボタン', 'ボタンメニュー', 'メニューボタン']:
                await message.channel.send(view=ThreadManageButtons())
                return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceChannelPanelCog(bot))
