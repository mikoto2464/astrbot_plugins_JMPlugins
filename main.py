import os
import re
from datetime import datetime
import random
from PicImageSearch import Ascii2D, Network, Google
from PicImageSearch.model import GoogleResponse

from jmcomic import JmOption, JmAlbumDetail, JmHtmlClient, JmModuleConfig, JmApiClient, create_option_by_file, \
    JmSearchPage, JmPhotoDetail, JmImageDetail, JmCategoryPage, JmMagicConstants

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.core import AstrBotConfig
from astrbot.core.message.components import Plain, Reply, File, Nodes

from astrbot.core.platform import MessageType
import json

from astrbot.core.star.filter.permission import PermissionType
from astrbot.api.star import StarTools

global last_Picture_time, Current_Picture_time, CoolDownTime, flag01, white_list_group, white_list_user, block_list
global last_random_time, Current_random_time, flag02
global last_search_picture_time, Current_search_picture_time, flag03
global last_search_comic_time, Current_search_comic_time, flag04
global ispicture

option_url = "./data/plugins/astrbot_plugins_JMPlugins/option.yml"

global white_list_path, history_json_path, datadir, blocklist_path


def check_is_6or7_digits(str):
    return bool(re.match(r'^\d{1,7}$', str))


def get_number_from_str(str):
    num_list = re.findall(r'\d+', str)
    result_number = ""
    for i in range(len(num_list)):
        result_number += num_list[i]

    return result_number


global option


@register("JMPlugins", "orchidsziyou", "查询本子名字插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        global option, last_Picture_time, white_list_group, white_list_user, last_random_time, Current_random_time, flag02, last_search_picture_time, flag03, last_search_comic_time, Current_search_comic_time, flag04
        option = create_option_by_file(option_url)
        last_search_picture_time = 0
        last_Picture_time = 0
        last_random_time = 0
        last_search_comic_time = 0

        # 加载设置
        global ispicture, CoolDownTime
        self.config = config
        CoolDownTime = self.config["CD_Time"]
        if self.config["IsPicture"] >= 1:
            ispicture = True
        else:
            ispicture = False
        print(ispicture, CoolDownTime)

        # 加载白名单
        global datadir, white_list_path, history_json_path, blocklist_path, block_list
        datadir = StarTools.get_data_dir("astrbot_plugins_JMPlugins")
        print(datadir)
        white_list_path = os.path.join(datadir, "white_list.json")
        history_json_path = os.path.join(datadir, "history.json")
        blocklist_path = os.path.join(datadir, "block_list.json")

        if not os.path.exists(white_list_path):
            with open(white_list_path, 'w') as file:
                json.dump({"groupIDs": [], "userIDs": []}, file)
        else:
            with open(white_list_path, 'r') as file:
                data = json.load(file)
                white_list_group = data["groupIDs"]
                white_list_user = data["userIDs"]

        if not os.path.exists(history_json_path):
            with open(history_json_path, 'w') as file:
                json.dump([], file)

        if not os.path.exists(blocklist_path):
            with open(blocklist_path, 'w') as file:
                json.dump({"albumID": []}, file)
        else:
            with open(blocklist_path, 'r') as file:
                data = json.load(file)
                block_list = data["albumID"]

    @filter.command_group("JM")
    async def jm_command_group(self, event: AstrMessageEvent):
        ...

    @jm_command_group.command("name")
    async def jm_name_command(self, event: AstrMessageEvent, name: str):
        global last_Picture_time, Current_Picture_time, flag01, Cover_tag, flag02
        Cover_tag = 0
        '''这是一个 获取本子名字 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return
            Current_Picture_time = int(datetime.now().timestamp())
            time_diff_in_seconds = Current_Picture_time - last_Picture_time
            last_Picture_time = Current_Picture_time
            if time_diff_in_seconds < CoolDownTime:
                cd_time = CoolDownTime - time_diff_in_seconds
                if flag01 == 0:
                    flag01 += 1
                    yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
                else:
                    flag01 += 1
                return

            flag01 = 0

        if not check_is_6or7_digits(name):
            if len(name) < 10:
                yield event.plain_result("请输入正确的编号")
                return
            else:
                name = get_number_from_str(name)
                Cover_tag = 1
                if not check_is_6or7_digits(name):
                    yield event.plain_result("未检测到正确的编号")
                    return

        # 检测是否在黑名单中
        if name in block_list:
            yield event.plain_result("该本子已被屏蔽,请窒息")
            return

        album = ''
        try:
            client = JmOption.copy_option(option).new_jm_client()
            page = client.search_site(search_query=name)
            album: JmAlbumDetail = page.single_album
        except:
            yield event.plain_result("未找到该本子")
            return

        # 放入json当中
        data = []
        try:
            with open(history_json_path, "r") as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []  # 如果文件不存在，创建一个空列表

        existing_ids = [item["id"] for item in data]

        if str(album.id) not in existing_ids:
            newdata = {
                "id": str(album.id),
                "data": {
                    "times": 1,
                    "names": album.name
                }
            }
            data.append(newdata)
            with open(history_json_path, "w") as json_file:
                json.dump(data, json_file)
        else:
            for item in data:
                if item["id"] == str(album.id):
                    item["data"]["times"] += 1
                    break
            with open(history_json_path, "w") as json_file:
                json.dump(data, json_file)

        # 判断是否发送图片还是只发送名字
        botid = event.get_self_id()
        from astrbot.api.message_components import Node, Plain, Image

        if ispicture:
            # 下载封面
            try:
                photo: JmPhotoDetail = album.getindex(0)
                photo01 = client.get_photo_detail(photo.photo_id, False)
                image: JmImageDetail = photo01[0]
                if os.path.exists('./data/plugins/astrbot_plugins_JMPlugins/result.jpg'):
                    os.remove('./data/plugins/astrbot_plugins_JMPlugins/result.jpg')
                client.download_by_image_detail(image, './data/plugins/astrbot_plugins_JMPlugins/result.jpg')

                # 给图片添加防gank
                if os.path.exists('./data/plugins/astrbot_plugins_JMPlugins/result.jpg'):
                    from PIL import Image as ProcessImage
                    original_image = ProcessImage.open('./data/plugins/astrbot_plugins_JMPlugins/result.jpg')
                    # 获取原始图片的宽度和高度
                    width, height = original_image.size
                    # 创建一张新的空白图片，大小为原图的宽度和五倍高度
                    new_image = ProcessImage.new('RGB', (width, height * 5), color=(255, 255, 255))
                    # 将原图粘贴到新图片的下半部分
                    new_image.paste(original_image, (0, height * 4))
                    # 保存最终结果
                    new_image.save('./data/plugins/astrbot_plugins_JMPlugins/result.jpg')

                node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Plain("...\n"),
                        Plain(f"id:{album.id}\n"),
                        Plain(f"本子名称：{album.name}\n"),
                        Plain(f"作者：{album.author}"),
                    ]
                )
                tag_node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain("...\n"),
                        Plain(f"tags：{album.tags}\n")
                    ]
                )
                picture_node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Image.fromFileSystem("./data/plugins/astrbot_plugins_JMPlugins/result.jpg")
                    ]
                )
                resNode = Nodes(
                    nodes=[node, tag_node, picture_node]
                )
                yield event.chain_result([resNode])

            except Exception as e:
                print(e)
                node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Plain("...\n"),
                        Plain(f"id:{album.id}\n"),
                        Plain(f"本子名称：{album.name}\n"),
                        Plain(f"作者：{album.author}"),
                    ]
                )
                tag_node = Node(
                    uin=botid,
                    name="仙人",
                    content=[
                        Plain("...\n"),
                        Plain(f"tags：{album.tags}\n")
                    ]
                )
                RIP_node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Plain("封面下载失败或者发送失败")
                    ]
                )
                resNode = Nodes(
                    nodes=[node, tag_node, RIP_node]
                )
                yield event.chain_result([resNode])

        else:
            # 只发送名字
            node = Node(
                uin=botid,
                name="仙人",
                content=
                [
                    Plain("...\n"),
                    Plain(f"id:{album.id}\n"),
                    Plain(f"本子名称：{album.name}\n"),
                    Plain(f"作者：{album.author}"),
                    Plain(f"tags：{album.tags}\n")
                ]
            )
            yield event.chain_result([node])

    @jm_command_group.command("rand")
    async def jm_rand_command(self, event: AstrMessageEvent):
        ''' 这是一个 获取随机本子 指令'''
        global last_random_time, Current_random_time, flag02, Cover_tag2
        Cover_tag2 = 0
        '''这是一个 获取本子名字 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return
            Current_random_time = int(datetime.now().timestamp())
            time_diff_in_seconds = Current_random_time - last_random_time
            last_random_time = Current_random_time
            if time_diff_in_seconds < CoolDownTime:
                cd_time = CoolDownTime - time_diff_in_seconds
                if flag02 == 0:
                    flag02 += 1
                    yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
                else:
                    flag02 += 1
                return

            flag02 = 0
        # 随机获取本子
        random_album = random.randint(1, 1100000)
        album = ''
        empty_tag = 0
        try:
            client = JmOption.copy_option(option).new_jm_client()
            page = client.search_site(search_query=random_album)
            album: JmAlbumDetail = page.single_album
        except:
            empty_tag = 1
        chain = []
        if empty_tag == 1:
            chain = [
                Reply(id=event.message_obj.message_id),
                Plain("...\n"),
                Plain(f"随机本子：id：{random_album}\n"),
                Plain("该本子不存在或已下架:(")
            ]
        else:
            chain = [
                Reply(id=event.message_obj.message_id),
                Plain("...\n"),
                Plain(f"随机本子：id：{random_album}\n"),
                Plain(f"本子名称：{album.name}\n"),
                Plain(f"作者：{album.author}"),
            ]
        yield event.chain_result(chain)

    @jm_command_group.command("key")
    async def jm_key_command(self, event: AstrMessageEvent, key: str):
        ''' 这是一个 根据关键字搜索本子 指令'''
        global last_search_comic_time, Current_search_comic_time, flag04
        Cover_tag2 = 0
        '''这是一个 获取本子名字 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return
            Current_search_comic_time = int(datetime.now().timestamp())
            time_diff_in_seconds = Current_search_comic_time - last_search_comic_time
            last_search_comic_time = Current_search_comic_time
            if time_diff_in_seconds < CoolDownTime:
                cd_time = CoolDownTime - time_diff_in_seconds
                if flag04 == 0:
                    flag04 += 1
                    yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
                else:
                    flag04 += 1
                return

            flag04 = 0

        album = ''
        empty_tag = 0
        try:
            client = JmOption.copy_option(option).new_jm_client()
            album: JmSearchPage = client.search_site(search_query=key, page=1)
        except:
            empty_tag = 1

        if empty_tag == 1:
            yield event.plain_result("未找到该关键字相关的本子")
        else:
            str = ''
            for album_id, title in album:
                str += f"{album_id}:{title}\n"

            botid = event.get_self_id()
            from astrbot.api.message_components import Node, Plain, Image
            node = Node(
                uin=botid,
                name="仙人",
                content=[
                    Plain(str)
                ]
            )
            yield event.chain_result([node])

    @filter.permission_type(PermissionType.ADMIN)
    @jm_command_group.command("promote")
    async def jm_promote_command(self, event: AstrMessageEvent, type: str, name: str):
        ''' 这是一个 晋升某人的权限 的指令'''
        if type == "group":
            if name in white_list_group:
                yield event.plain_result("该群已经在白名单中")
                return
            else:
                white_list_group.append(name)
                with open(white_list_path, 'w') as file:
                    data = {
                        "groupIDs": white_list_group,
                        "userIDs": white_list_user,
                    }
                    json.dump(data, file)
                yield event.plain_result("该群已成功加入白名单")
        if type == "user":
            if name in white_list_user:
                yield event.plain_result("该用户已经在白名单中")
                return
            else:
                white_list_user.append(name)
                with open(white_list_path, 'w') as file:
                    data = {
                        "groupIDs": white_list_group,
                        "userIDs": white_list_user,
                    }
                    json.dump(data, file)
                yield event.plain_result("该用户已成功加入白名单")

    @filter.permission_type(PermissionType.ADMIN)
    @jm_command_group.command("demote")
    async def jm_demote_command(self, event: AstrMessageEvent, type: str, name: str):
        ''' 这是一个 撤销某人的权限 的指令'''
        if type == "group":
            if name in white_list_group:
                white_list_group.remove(name)
                with open(white_list_path, 'w') as file:
                    data = {
                        "groupIDs": white_list_group,
                        "userIDs": white_list_user,
                    }
                    json.dump(data, file)
                yield event.plain_result("该群已成功撤销白名单")
            else:
                yield event.plain_result("该群不在白名单中")
        if type == "user":
            if name in white_list_user:
                white_list_user.remove(name)
                with open(white_list_path, 'w') as file:
                    data = {
                        "groupIDs": white_list_group,
                        "userIDs": white_list_user,
                    }
                    json.dump(data, file)
                yield event.plain_result("该用户已成功撤销白名单")
            else:
                yield event.plain_result("该用户不在白名单中")

    @jm_command_group.command("block")
    async def jm_block_command_group(self, event: AstrMessageEvent, type: str, album_id: str):
        ''' 这是一个 封面黑名单 指令组'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        if type == "add":
            if album_id in block_list:
                yield event.plain_result("该本子已经在黑名单中")
                return
            else:
                block_list.append(album_id)
                with open(blocklist_path, 'w') as file:
                    data = {
                        "albumID": block_list,
                    }
                    json.dump(data, file)
                yield event.plain_result("该本子已成功加入黑名单")
        if type == "remove":
            if album_id in block_list:
                block_list.remove(album_id)
                with open(blocklist_path, 'w') as file:
                    data = {
                        "albumID": block_list,
                    }
                    json.dump(data, file)
                yield event.plain_result("该本子已成功移除黑名单")

    @jm_command_group.command("history")
    async def jm_history_command(self, event: AstrMessageEvent):
        '''这是一个 获取本子历史记录 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        abs_history_json_path = os.path.abspath(history_json_path)
        file_url = f"file://{abs_history_json_path}"
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        assert isinstance(event, AiocqhttpMessageEvent)
        if (event.get_message_type() == MessageType.FRIEND_MESSAGE):
            user_id = event.get_sender_id()
            client = event.bot
            payloads2 = {
                "user_id": user_id,
                "message": [
                    {
                        "type": "file",
                        "data": {
                            "file": file_url,
                        }
                    }
                ]
            }
            response = await client.api.call_action('send_private_msg', **payloads2)  # 调用 协议端  API
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            group_id = event.get_group_id()
            client = event.bot
            payloads2 = {
                "group_id": group_id,
                "message": [
                    {
                        "type": "file",
                        "data": {
                            "file": file_url,
                        }
                    }
                ]
            }
            response = await client.api.call_action('send_group_msg', **payloads2)  # 调用 协议端

    @jm_command_group.command("rank")
    async def jm_rank_command(self, event: AstrMessageEvent, time: str):
        ''' 这是一个 排行榜 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        if time not in ['m', 'w', 'a', 'd']:
            yield event.plain_result("参数错误，请使用m/w/d/a")
            return

        try:
            client = JmOption.copy_option(option).new_jm_client()
            page = ""
            hint = ""
            if time == 'm':
                hint = "本月热门本子："
                page: JmCategoryPage = client.categories_filter(
                    page=1,
                    time=JmMagicConstants.TIME_MONTH,
                    category=JmMagicConstants.CATEGORY_ALL,
                    order_by=JmMagicConstants.ORDER_BY_VIEW,
                )
            elif time == 'w':
                hint = "本周热门本子："
                page: JmCategoryPage = client.categories_filter(
                    page=1,
                    time=JmMagicConstants.TIME_WEEK,
                    category=JmMagicConstants.CATEGORY_ALL,
                    order_by=JmMagicConstants.ORDER_BY_VIEW,
                )
            elif time == 'd':
                hint = "今日热门本子："
                page: JmCategoryPage = client.categories_filter(
                    page=1,
                    time=JmMagicConstants.TIME_TODAY,
                    category=JmMagicConstants.CATEGORY_ALL,
                    order_by=JmMagicConstants.ORDER_BY_VIEW,
                )
            elif time == 'a':
                hint = "全部热门本子："
                page: JmCategoryPage = client.categories_filter(
                    page=1,
                    time=JmMagicConstants.TIME_ALL,
                    category=JmMagicConstants.CATEGORY_ALL,
                    order_by=JmMagicConstants.ORDER_BY_VIEW,
                )
            result_str = ""
            for aid, title in page:
                result_str += f"{aid}:{title}\n"

            botid = event.get_self_id()
            from astrbot.api.message_components import Node, Plain, Image
            node = Node(
                uin=botid,
                name="仙人",
                content=[
                    Plain(f"{hint}：\n{result_str}")
                ]
            )
            yield event.chain_result([node])
        except:
            yield event.plain_result("搜索失败")
            return

    @jm_command_group.command("help")
    async def jm_help_command(self, event: AstrMessageEvent):
        ''' 这是一个 帮助 指令'''
        str = ""
        str += "本插件提供以下指令：\n"
        str += "name [id]：获取本子名称(以及封面图)\n"
        str += "rank [m/w/d/a]：获取本子排行榜\n"
        str += "rand：随机获取本子\n"
        str += "key [关键字]：根据关键字搜索本子\n"
        str += "history：获取本子历史记录\n"
        str += "对图片回复/search   ：搜索图片\n"

        botid = event.get_self_id()
        from astrbot.api.message_components import Node, Plain, Image
        node = Node(
            uin=botid,
            name="仙人",
            content=[
                Plain(str)
            ]
        )
        yield event.chain_result([node])

    @filter.command("search")
    async def jm_search_command(self, event: AstrMessageEvent):
        ''' 这是一个 搜索图片 指令'''
        if event.get_message_type() == MessageType.FRIEND_MESSAGE:
            if event.get_sender_id() not in white_list_user:
                yield event.plain_result("该指令仅限管理员使用")
                return
        if event.get_message_type() == MessageType.GROUP_MESSAGE:
            if event.get_group_id() not in white_list_group:
                yield event.plain_result("该群没有权限使用该指令")
                return

        global last_search_picture_time, Current_search_picture_time, flag03
        Current_search_picture_time = int(datetime.now().timestamp())
        time_diff_in_seconds = Current_search_picture_time - last_search_picture_time
        last_search_picture_time = Current_search_picture_time
        if time_diff_in_seconds < CoolDownTime:
            cd_time = CoolDownTime - time_diff_in_seconds
            if flag03 == 0:
                flag03 += 1
                yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
            else:
                flag03 += 1
            return
        flag03 = 0

        image_url = ''
        message_chain = event.get_messages()
        for msg in message_chain:
            # print(msg)
            # print("\n")
            if msg.type == 'Image':
                PictureID = msg.file
                print(f"图片ID: {PictureID}")
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payloads2 = {
                    "file_id": PictureID
                }
                response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                # print(response)
                image_url = response['file']

            elif msg.type == 'Reply':
                # 处理回复消息
                from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
                assert isinstance(event, AiocqhttpMessageEvent)
                client = event.bot
                payload = {
                    "message_id": msg.id
                }
                response = await client.api.call_action('get_msg', **payload)  # 调用 协议端  API
                # print(response)
                reply_msg = response['message']
                for msg in reply_msg:
                    if msg['type'] == 'image':
                        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
                            AiocqhttpMessageEvent
                        assert isinstance(event, AiocqhttpMessageEvent)
                        client = event.bot
                        payloads2 = {
                            "file_id": msg['data']['file']
                        }
                        response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
                        image_url = response['file']

        print(f"图片URL: {image_url}")
        if image_url == '':
            yield event.plain_result("未检测到图片")
            return
        else:
            try:
                # ascii2d暂时没反应
                engin = Ascii2D(base_url="https://ascii2d.obfs.dev")
                resp = await engin.search(file=image_url)
                raw = resp.raw
                count = 0
                result_str = ''
                for r in raw:
                    if (r.url == ""):
                        continue
                    result_str += f"{count}:{r.url}\n"
                    count += 1
                    if count == 2:
                        break
                if count == 0:
                    yield event.plain_result("未找到相似图片")
                else:
                    botid = event.get_self_id()
                    from astrbot.api.message_components import Node, Plain, Image
                    node = Node(
                        uin=botid,
                        name="仙人",
                        content=[
                            Plain("找到相似图片：\n"),
                            Plain(result_str)
                        ]
                    )
                    yield event.chain_result([node])

            except Exception as e:
                print(e)
                yield event.plain_result("搜索图片失败")

    # @filter.command("google")
    # async def jm_google_command(self, event: AstrMessageEvent):
    #     ''' 这是一个 搜索图片 指令'''
    #     if event.get_message_type() == MessageType.FRIEND_MESSAGE:
    #         if event.get_sender_id() not in white_list_user:
    #             yield event.plain_result("该指令仅限管理员使用")
    #             return
    #     if event.get_message_type() == MessageType.GROUP_MESSAGE:
    #         if event.get_group_id() not in white_list_group:
    #             yield event.plain_result("该群没有权限使用该指令")
    #             return
    #
    #     global last_search_picture_time, Current_search_picture_time, flag03
    #     Current_search_picture_time = int(datetime.now().timestamp())
    #     time_diff_in_seconds = Current_search_picture_time - last_search_picture_time
    #     last_search_picture_time = Current_search_picture_time
    #     if time_diff_in_seconds < CoolDownTime:
    #         cd_time = CoolDownTime - time_diff_in_seconds
    #         if flag03 == 0:
    #             flag03 += 1
    #             yield event.plain_result(f"进CD了，请{cd_time}秒后再试")
    #         else:
    #             flag03 += 1
    #         return
    #     flag03 = 0
    #
    #     image_url = ''
    #     message_chain = event.get_messages()
    #     for msg in message_chain:
    #         # print(msg)
    #         # print("\n")
    #         if msg.type == 'Image':
    #             PictureID = msg.file
    #             print(f"图片ID: {PictureID}")
    #             from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    #             assert isinstance(event, AiocqhttpMessageEvent)
    #             client = event.bot
    #             payloads2 = {
    #                 "file_id": PictureID
    #             }
    #             response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
    #             # print(response)
    #             image_url = response['file']
    #
    #         elif msg.type == 'Reply':
    #             # 处理回复消息
    #             from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
    #             assert isinstance(event, AiocqhttpMessageEvent)
    #             client = event.bot
    #             payload = {
    #                 "message_id": msg.id
    #             }
    #             response = await client.api.call_action('get_msg', **payload)  # 调用 协议端  API
    #             # print(response)
    #             reply_msg = response['message']
    #             for msg in reply_msg:
    #                 if msg['type'] == 'image':
    #                     from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import \
    #                         AiocqhttpMessageEvent
    #                     assert isinstance(event, AiocqhttpMessageEvent)
    #                     client = event.bot
    #                     payloads2 = {
    #                         "file_id": msg['data']['file']
    #                     }
    #                     response = await client.api.call_action('get_image', **payloads2)  # 调用 协议端  API
    #                     image_url = response['file']
    #
    #     print(f"图片URL: {image_url}")
    #     if image_url == '':
    #         yield event.plain_result("未检测到图片")
    #         return
    #     else:
    #         try:
    #             # async with Network(proxies="http://127.0.0.1:12334") as client:
    #             #     engin = EHentai(client=client, is_ex=False, similar=True, covers=False)
    #             #     # result = await search_engin(engin,image_path)  # 使用 await 来等待异步函数
    #             #     result = await engin.search(file=image_url)
    #             cookie = "NID=524=cs5kw-q_FYZlcFdaOs7dFEGnFCWs3Pde4JzYaM8_tsgStTXcsxkrtVQgZrtkVQgvwGsYvTNcmQJFa3qN9TpYGQv5Fr9T19jHrwgEdVw2vraNQ2Kjva1y6ikxBzOy2vO02H0bikIr_4sPBf-cV3lw5oZ4fF_t-v6FKs9R7RDHvPg7LMUO5lzp3QsKJpEmaGIOD7f14XGfrxeA-XCCLX4ZHjrgvsHd1xlqcKxIsMfVKhEyYhJtA6zXV3EkBzY6cUA"
    #             async with Network(cookies=cookie, proxies="http://127.0.0.1:12334") as client:
    #                 engin = Google(client=client)
    #                 resp: GoogleResponse = await engin.search(file=image_url)
    #
    #                 res02 = resp.raw
    #                 rescount = len(res02)
    #                 resStr = ""
    #                 if rescount == 0:
    #                     yield event.plain_result("未找到相关结果")
    #                     return
    #                 else:
    #                     count = 0
    #                     for row in res02:
    #                         resStr += f"{row.title}\n{row.url}\n"
    #                         count += 1
    #                         if count == 6:
    #                             break
    #
    #                     botid = event.get_self_id()
    #                     from astrbot.api.message_components import Node, Plain, Image
    #                     node = Node(
    #                         uin=botid,
    #                         name="仙人",
    #                         content=[
    #                             Plain("找到相似图片：\n"),
    #                             Plain(resStr)
    #                         ]
    #                     )
    #                     yield event.chain_result([node])
    #
    #         except Exception as e:
    #             print(e)
    #             yield event.plain_result("搜索图片失败")
