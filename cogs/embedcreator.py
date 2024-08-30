import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select, Modal, TextInput
import asyncio
import json
import os

with open('config.json', 'r') as f:
    config = json.load(f)

DEV_IDS = [int(id) for id in config['devID']]

class changeTitle(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Enter New Title")
        self.original_embed = original_embed
        self.newTitle = TextInput(label="Title", default=original_embed.title, required=False)
        self.add_item(self.newTitle)

    async def on_submit(self, interaction: discord.Interaction):
        self.original_embed.title = self.newTitle.value
        await interaction.response.edit_message(embed=self.original_embed)

class changeDescription(Modal):
    def __init__(self, original_embed: discord.Embed, original_content: str):
        super().__init__(title="Enter New Description")
        self.original_embed = original_embed
        self.newDescription = TextInput(label="Description", default=original_embed.description, required=False, style=discord.TextStyle.paragraph)
        self.newContent = TextInput(
            label="Message Content",
            default=original_content,  # Prefill with the original content
            required=False,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.newDescription)
        self.add_item(self.newContent)

    async def on_submit(self, interaction: discord.Interaction):
        self.original_embed.description = self.newDescription.value
        new_content = self.newContent.value
        await interaction.response.edit_message(content=new_content, embed=self.original_embed)

class addField(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Enter New Field Info")
        self.original_embed = original_embed
        self.newTitle = TextInput(label="Title of field", placeholder="Type here...", required=True)
        self.newValue = TextInput(label="Value of field", placeholder="Type here...", required=True)
        self.inline = TextInput(label="Inline?", placeholder="Yes/No", required=True)
        self.add_item(self.newTitle)
        self.add_item(self.newValue)
        self.add_item(self.inline)

    async def on_submit(self, interaction: discord.Interaction):
        inline_bool = None
        if self.inline.value.lower() == "yes":
            inline_bool = True
        elif self.inline.value.lower() == "no":
            inline_bool = False
        else:
            await interaction.response.send_message("Inline must be 'Yes' or 'No'.", ephemeral=True)
            return

        self.original_embed.add_field(name=self.newTitle, value=self.newValue, inline=inline_bool)
        await interaction.response.edit_message(embed=self.original_embed)

class RemoveField(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Remove Field from Embed")
        self.original_embed = original_embed
        self.field_index = TextInput(
            label="Field Index to Remove",
            placeholder="Enter the index of the field to remove (1 for the first field, etc.)",
            required=True
        )
        self.add_item(self.field_index)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            index = int(self.field_index.value) - 1
            embed_dict = self.original_embed.to_dict()
            if "fields" in embed_dict and len(embed_dict["fields"]) > index:
                del embed_dict["fields"][index]
                new_embed = discord.Embed.from_dict(embed_dict)

                await interaction.response.edit_message(embed=new_embed)
            else:
                await interaction.response.send_message("Invalid field index.", ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Please enter a valid number for the field index.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

class EditField(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Edit Field")
        self.original_embed = original_embed
        self.field_index = TextInput(
            label="Field Index to edit",
            placeholder="1 for first field, etc)",
            required=True
        )
        self.newTitle = TextInput(label="New title of field", placeholder="Type here...", required=True)
        self.newValue = TextInput(label="New value of field", placeholder="Type here...", required=True)
        self.inline = discord.ui.TextInput(
            label="Inline? (Yes/No)",
            placeholder="Yes or No",
            required=True
        )
        self.add_item(self.field_index)
        self.add_item(self.newTitle)
        self.add_item(self.newValue)
        self.add_item(self.inline)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            inline_input = self.inline.value.strip().lower()
            if inline_input == "yes":
                inline_bool = True
            elif inline_input == "no":
                inline_bool = False
            else:
                await interaction.response.send_message("Inline must be 'Yes' or 'No'.", ephemeral=True)
                return
            index = int(self.field_index.value) - 1
            embed_dict = self.original_embed.to_dict()
            if "fields" in embed_dict and len(embed_dict["fields"]) > index:
                embed_dict["fields"][index]["name"] = self.newTitle.value
                embed_dict["fields"][index]["value"] = self.newValue.value
                embed_dict["fields"][index]["inline"] = inline_bool
                new_embed = discord.Embed.from_dict(embed_dict)

                await interaction.response.edit_message(embed=new_embed)
            else:
                await interaction.response.send_message("Invalid field index.", ephemeral=True)

        except ValueError:
            await interaction.response.send_message("Please enter a valid number for the field index.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

class AddURL(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Enter New Field Info")
        self.original_embed = original_embed
        self.newURL = TextInput(label="URL", default=original_embed.url, required=False)
        self.add_item(self.newURL)

    async def on_submit(self, interaction: discord.Interaction):
        self.original_embed.url = self.newURL.value
        await interaction.response.edit_message(embed=self.original_embed)

class SetAuthor(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Enter New Author Info")
        self.original_embed = original_embed
        self.newName = TextInput(label="Name", default=original_embed.author.name, required=False)
        self.newIcon = TextInput(label="Icon URL", default=original_embed.author.icon_url, required=False)
        self.newURL = TextInput(label="URL", default=original_embed.author.url, required=False)
        self.add_item(self.newName)
        self.add_item(self.newIcon)
        self.add_item(self.newURL)

    async def on_submit(self, interaction: discord.Interaction):
        self.original_embed.set_author(name=self.newName.value, icon_url=self.newIcon.value, url=self.newURL.value)
        await interaction.response.edit_message(embed=self.original_embed)

class SelectColor(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Select Color")
        self.original_embed = original_embed
        self.newColor = TextInput(label="HEX Code", required=True)
        self.add_item(self.newColor)

    async def on_submit(self, interaction: discord.Interaction):
        self.original_embed.color = discord.Color.from_str("0x" + self.newColor.value)
        await interaction.response.edit_message(embed=self.original_embed)

class Thumbnail(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Select Thumbnail")
        self.original_embed = original_embed
        self.thumbnail = TextInput(label="Image URL", default=original_embed.thumbnail.url, required=False)
        self.add_item(self.thumbnail)

    async def on_submit(self, interaction: discord.Interaction):
        self.original_embed.set_thumbnail(url=self.thumbnail.value)
        await interaction.response.edit_message(embed=self.original_embed)

class Footer(Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Set Footer")
        self.original_embed = original_embed
        self.footertext = TextInput(label="Footer Text", default=original_embed.footer.text, required=False)
        self.footericon = TextInput(label="Footer Icon URL", default=original_embed.footer.icon_url, required=False)
        self.add_item(self.footertext)
        self.add_item(self.footericon)

    async def on_submit(self, interaction: discord.Interaction):
        self.original_embed.set_footer(text=self.footertext, icon_url=self.footericon)
        await interaction.response.edit_message(embed=self.original_embed)

class Image (Modal):
    def __init__(self, original_embed: discord.Embed):
        super().__init__(title="Set Image")
        self.original_embed = original_embed
        self.imageurl = TextInput(label="Image URL", default=original_embed.image.url, required=False)
        self.add_item(self.imageurl)

    async def on_submit(self, interaction: discord.Interaction):
        self.original_embed.set_image(url=self.imageurl)
        await interaction.response.edit_message(embed=self.original_embed)

class EmbedCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="create_embed")
    async def create_embed(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.administrator:
            original_content = ""
            embed = discord.Embed(title="Embed Creator", description="Please use the buttons below to edit this embed!")
            embed.color = discord.Color.from_str("0x" + "#ff2929")
            embed.set_author(name=interaction.user, icon_url=interaction.user.avatar.url)
            embed.set_thumbnail(url="https://images-ext-1.discordapp.net/external/CX8j8C2jGASw8HGroq0vIMrT4KwyzZVMoybKMDritFc/https/cdn.discordapp.com/icons/493063429129502720/a_152d897749da45e310f195129b41aff0.gif")
            button1 = Button(label="Title", style=discord.ButtonStyle.blurple, custom_id="change_title")
            button2 = Button(label="    Description", style=discord.ButtonStyle.blurple, custom_id="change_description")
            button3 = Button(label="Add Field", style=discord.ButtonStyle.green, custom_id="add_field")
            button4 = Button(label="Remove Field", style=discord.ButtonStyle.danger, custom_id="remove_field")
            button5 = Button(label="Edit Field", style=discord.ButtonStyle.blurple, emoji="\U0000270f", custom_id="edit_field")
            button6 = Button(label="URL", style=discord.ButtonStyle.blurple, emoji="\U0001f310", custom_id="add_url")
            button7 = Button(label="Color", style=discord.ButtonStyle.blurple, custom_id="set_color")
            button8 = Button(label="Author", style=discord.ButtonStyle.blurple, custom_id="set_author", emoji="\U0001f9d1")
            button9 = Button(label="Thumbnail", style=discord.ButtonStyle.green, custom_id="thumbnail")
            button10 = Button(label="Footer", style=discord.ButtonStyle.green, custom_id="footer")
            button11 = Button(label="Image", style=discord.ButtonStyle.green, custom_id="image", emoji="\U0001f5bc")
            button12 = Button(label="Send Embed", style=discord.ButtonStyle.green, custom_id="sendembed")
            embed.set_footer(text="Bot developed by dim1337", icon_url="https://images-ext-1.discordapp.net/external/RWw3RHqMl6MFezmrxGTPhqxEQXexWkF0vXLkOA_Fr44/%3Fsize%3D1024/https/cdn.discordapp.com/avatars/772336857970114590/a_f34d91ed491fe30dcc1e44b72c195b86.gif")

        else:
            interaction.response.send_message("You do not have permission to use this command.")

        view = View()
        view.add_item(button1)
        view.add_item(button2)
        view.add_item(button3)
        view.add_item(button4)
        view.add_item(button5)
        view.add_item(button6)
        view.add_item(button7)
        view.add_item(button8)
        view.add_item(button9)
        view.add_item(button10)
        view.add_item(button11)
        view.add_item(button12)
        await interaction.response.send_message(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        original_content = "    "
        if interaction.type == discord.InteractionType.component:
            original_message = interaction.message
            original_embed = original_message.embeds[0]
            if interaction.user.guild_permissions.administrator:
                if interaction.data['custom_id'] == 'change_title':
                    await interaction.response.send_modal(changeTitle(original_embed))
                elif interaction.data['custom_id'] == 'change_description':
                    await interaction.response.send_modal(changeDescription(original_embed=original_embed, original_content=original_message.content))
                elif interaction.data['custom_id'] == 'add_field':
                    await interaction.response.send_modal(addField(original_embed))
                elif interaction.data['custom_id'] == 'remove_field':
                    await interaction.response.send_modal(RemoveField(original_embed))
                elif interaction.data['custom_id'] == 'edit_field':
                    await interaction.response.send_modal(EditField(original_embed))
                elif interaction.data['custom_id'] == 'add_url':
                    await interaction.response.send_modal(AddURL(original_embed))
                elif interaction.data['custom_id'] == 'set_color':
                    await interaction.response.send_modal(SelectColor(original_embed))
                elif interaction.data['custom_id'] == 'set_author':
                    await interaction.response.send_modal(SetAuthor(original_embed))
                elif interaction.data['custom_id'] == 'thumbnail':
                    await interaction.response.send_modal(Thumbnail(original_embed))
                elif interaction.data['custom_id'] == 'footer':
                    await interaction.response.send_modal(Footer(original_embed))
                elif interaction.data['custom_id'] == 'image':
                    await interaction.response.send_modal(Image(original_embed))
                elif interaction.data['custom_id'] == 'sendembed':
                    await interaction.response.send_message("Please mention a channel or provide a channel ID.", ephemeral=False)

                    def check(m):
                        return m.author == interaction.user and (m.content.startswith("<#") or m.content.isdigit())

                    try:
                        msg = await self.bot.wait_for("message", check=check, timeout=60)

                        if msg.content.startswith("<#"):
                            channel_id = int(msg.content[2:-1])
                        else:
                            channel_id = int(msg.content)

                        channel = interaction.guild.get_channel(channel_id)
                        if channel and isinstance(channel, discord.TextChannel):
                            await channel.send(content=original_message.content, embed=original_embed)
                            await interaction.followup.send(f"Embed sent to {channel.mention}!", ephemeral=True)
                        else:
                            await interaction.followup.send("Invalid channel. Please try again.", ephemeral=True)
                    except asyncio.TimeoutError:
                        await interaction.followup.send("You took too long to respond!", ephemeral=True)
            else:
                await interaction.response.send_message("Not permitted.")

async def setup(bot):
    await bot.add_cog(EmbedCreator(bot))
