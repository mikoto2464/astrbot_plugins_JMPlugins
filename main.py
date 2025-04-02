import os
import re
from datetime import datetime

import jmcomic
from jmcomic import JmOption, JmAlbumDetail, JmHtmlClient, JmModuleConfig, JmApiClient, create_option_by_file

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.message.components import Plain, Reply, File

from astrbot.core.platform import MessageType
import json

from astrbot.core.star.filter.permission import PermissionType

global last_Picture_time, Current_Picture_time, CoolDownTime, flag01, white_list_group, white_list_user
last_Picture_time = 0
CoolDownTime = 30
option_url = "./data/plugins/astrbot_plugins_JMPlugins/option.yml"
white_list_path = "./data/plugins/astrbot_plugins_JMPlugins/white_list.json"
history_json_path = "./data/plugins/astrbot_plugins_JMPlugins/history.json"


def check_is_6or7_digits(str):
    return bool(re.match(r'^\d{1,7}$', str))

def get_number_from_str(str):
    num_list=re.findall(r'\d+', str)
    result_number=""
    for i in range(len(num_list)):
        result_number+=num_list[i]

    return result_number


global option


@register("JMPlugins", "orchidsziyou", "查询本子名字插件", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        global option, last_Picture_time, white_list_group, white_list_user
        option = create_option_by_file(option_url)
        last_Picture_time = 0

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
        global last_Picture_time, Current_Picture_time, flag01,Cover_tag
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
            if len(name)<10:
                yield event.plain_result("请输入正确的编号")
                return
            else:
                name =get_number_from_str(name)
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

        # 检测是否为NonR
        tags = album.tags
        if len(tags) > 0:
            if "全年龄" in tags:
                pass

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

        if Cover_tag == 1:
            message_chain = [
                Reply(id=event.message_obj.message_id),
                Plain("...\n"),
                Plain(f"id:{album.id}\n"),
                Plain(f"本子名称：{album.name}\n"),
                Plain(f"作者：{album.author}"),
            ]
        else:
            message_chain = [
                Reply(id=event.message_obj.message_id),
                Plain("...\n"),
                Plain(f"本子名称：{album.name}\n"),
                Plain(f"作者：{album.author}"),
            ]

        yield event.chain_result(message_chain)

    @filter.permission_type(PermissionType.ADMIN)
    @jm_command_group.command("promote")
    async def jm_promote_command(self, event: AstrMessageEvent, type: str,name:str):
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
    async def jm_demote_command(self, event: AstrMessageEvent, type: str,name:str):
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






