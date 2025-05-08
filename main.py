import os
import re
from datetime import datetime
import random
from PicImageSearch import BaiDu, Iqdb, Ascii2D, EHentai, Network, Google

import jmcomic
from jmcomic import JmOption, JmAlbumDetail, JmHtmlClient, JmModuleConfig, JmApiClient, create_option_by_file, \
    JmSearchPage, JmPhotoDetail, JmImageDetail

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.message.components import Plain, Reply, File, Nodes

from astrbot.core.platform import MessageType
import json

from astrbot.core.star.filter.permission import PermissionType

global last_Picture_time, Current_Picture_time, CoolDownTime, flag01, white_list_group, white_list_user
global last_random_time, Current_random_time, flag02
global last_search_picture_time, Current_search_picture_time, flag03
global last_search_comic_time, Current_search_comic_time, flag04
global ispicture
last_Picture_time = 0
CoolDownTime = 15
ispicture = False
option_url = "./data/plugins/astrbot_plugins_JMPlugins/option.yml"
white_list_path = "./data/plugins/astrbot_plugins_JMPlugins/white_list.json"
history_json_path = "./data/plugins/astrbot_plugins_JMPlugins/history.json"



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
    def __init__(self, context: Context):
        super().__init__(context)
        global option, last_Picture_time, white_list_group, white_list_user, last_random_time, Current_random_time, flag02, last_search_picture_time, flag03, last_search_comic_time, Current_search_comic_time, flag04
        option = create_option_by_file(option_url)
        last_search_picture_time = 0
        last_Picture_time = 0
        last_random_time = 0
        last_search_comic_time = 0

        with open(white_list_path, 'r') as file:
            data = json.load(file)
            white_list_group = data["groupIDs"]
            white_list_user = data["userIDs"]

        if not os.path.exists(history_json_path):
            with open(history_json_path, 'w') as file:
                json.dump([], file)

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

        #判断是否发送图片还是只发送名字
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
                picture_node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Image.fromFileSystem("./data/plugins/astrbot_plugins_JMPlugins/result.jpg")
                    ]
                )
                resNode = Nodes(
                    nodes=[node, picture_node]
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
                picture_node = Node(
                    uin=botid,
                    name="仙人",
                    content=
                    [
                        Plain("封面下载失败，请窒息")
                    ]
                )
                resNode = Nodes(
                    nodes=[node, picture_node]
                )
                yield event.chain_result([resNode])

        else:
            #只发送名字
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
        file_url = f'file://{abs_history_json_path}'
        print(file_url)

        chain = [
            File(file=file_url, name="历史记录.json")
        ]

        yield event.chain_result(chain)

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
                engin = Ascii2D(client=client, base_url="https://ascii2d.obfs.dev")
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

    # @filter.command("benzi")
    # async def jm_benzi_command(self, event: AstrMessageEvent):
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
    #             cookies = "523=CSUd6eWOci42C24Aeltpw_XNdWBt5Nx7hD5H2X0HryVFRQ9aG-Y_3LtxbVA44-kQtQhkTkNO2hcCDKyn69ph6hnFo36ty8__vXi6gILtSDJzECySjMTgM1-T9AilgvIlbqwRAm8P7rU7eBzPJSmoM5x7JkAq72FbfCJZvbZbZC0GAyUurcOL2N0unNKLzuQ9U8bPxgAMBNBw4g50ULLGSN7_gR7UQkLxRzzp3fuf1PEqm6uDBEpLuwJnjFlcrtfVH_FPwdiXEAtI7tO8TmsIEKPoO6pnb_64FcF_xQD5FDhTPuBJkylYEV7-48zVAB1YkrAYZHrqeB5ngIbmAnvSbFVrbsi0tqJCQYVKjL3ZoY8-yR5UXURzg5YSGpi0v38AsGsxBw4WraMkyh16yfwGWIRLSkXuWAJvrvEc3xQlp6DYxjISM8M2nfIrIurnP6KG5j2mc6H5mLcbFRJX9L_NuhBQbSjieu8Bf9oU"
    #             async with Network(cookies=cookies, proxies="http://127.0.0.1:12334") as client:
    #                 engin = Google(client=client)
    #                 result = await engin.search(file=image_url)
    #
    #                 res02 = result.raw
    #                 print(result.url)
    #                 rescount=len(res02)
    #                 resStr = ""
    #                 if rescount==0:
    #                     yield event.plain_result("未找到相关结果")
    #                     return
    #                 else:
    #                     count=0
    #                     for row in res02:
    #                         resStr += f"{row.title}\n{row.url}\n"
    #                         count+=1
    #                         if count==3:
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
