import random
import json
import os
from datetime import datetime, timedelta

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(PLUGIN_DIR, "omikuji_data.json")
CONFIG_FILE = os.path.join(PLUGIN_DIR, "fortune_config.json")

class GetModelPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 注册一个名为 "query_current_model" 的工具
        self.agent_tools = [OmikujiPlugin(self.context)]

@register("omikuji", "Suzukaze", "每日运势抽签插件", "1.0.0")
class OmikujiPlugin(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self.timezone_offset = self.config.get("timezone_offset", 8)
        self.reset_hour = self.config.get("reset_hour", 0)
        self._fortune = self._load_fortune_config()

    def _load_fortune_config(self):
        if not os.path.exists(CONFIG_FILE):
            logger.warning(f"配置文件 {CONFIG_FILE} 不存在，使用内置默认值")
            return self._default_fortune()

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载 fortune_config.json 失败: {e}，使用内置默认值")
            return self._default_fortune()

    @staticmethod
    def _default_fortune():
        return {
            "fortune_table": [
                {"name": "大吉", "probability": 5},
                {"name": "中吉", "probability": 10},
                {"name": "小吉", "probability": 15},
                {"name": "吉", "probability": 25},
                {"name": "末吉", "probability": 25},
                {"name": "凶", "probability": 15},
                {"name": "大凶", "probability": 5},
            ],
            "lucky_items": [
                "御守", "硬币", "书签", "钥匙", "石头", "花瓣", "羽毛", "铃铛",
                "纽扣", "树枝", "玻璃珠", "贝壳", "橡果",
            ],
            "lucky_colors": [
                "赤", "青", "黄", "緑", "白", "黒", "金", "銀", "紫", "橙",
            ],
            "lucky_directions": [
                "東", "西", "南", "北", "東南", "東北", "西南", "西北",
            ],
            "descriptions": {
                "大吉": [
                    "今日运势极佳，万事顺遂，心想事成。",
                    "运势极好，今天做什么都会很顺利。",
                    "大吉大利，今天是个好日子，适合做出重要决定。",
                ],
                "中吉": [
                    "运势不错，努力会有回报。",
                    "今日运势良好，保持积极心态会更好。",
                    "中吉之兆，适合与人合作共事。",
                ],
                "小吉": [
                    "运势略好，小事可成。",
                    "今日运势小吉，平淡中带着些许好运。",
                    "小吉，适合处理日常事务。",
                ],
                "吉": [
                    "运势平稳，无大起大落。",
                    "今日运势普通，保持平常心即可。",
                    "吉，适合稳步推进各项工作。",
                ],
                "末吉": [
                    "运势勉强尚可，需多加留意。",
                    "末吉之兆，有波折但结果尚可。",
                    "运势平平，小心驶得万年船。",
                ],
                "凶": [
                    "今日运势不佳，凡事需谨慎。",
                    "凶，今天尽量避免做出重要决定。",
                    "运势略有不好，宜静不宜动。",
                ],
                "大凶": [
                    "今日大凶，诸事不宜，建议低调行事。",
                    "运势极差，今天最好避免冒险行为。",
                    "大凶之兆，宜守不宜攻，保持耐心。",
                ],
            },
        }

    async def initialize(self):
        pass

    def _today(self):
        now = datetime.utcnow() + timedelta(hours=self.timezone_offset)
        if now.hour < self.reset_hour:
            now -= timedelta(days=1)
        return now.strftime("%Y-%m-%d")

    def _load(self):
        if not os.path.exists(DATA_FILE):
            return {}
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            return {}

    def _save(self, data):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def _draw(self):
        table = self._fortune["fortune_table"]
        total = sum(item["probability"] for item in table)
        r = random.randint(1, total)
        acc = 0
        for item in table:
            acc += item["probability"]
            if r <= acc:
                return item["name"]
        return table[-1]["name"]

    def _attachments(self):
        return (
            random.choice(self._fortune["lucky_items"]),
            random.choice(self._fortune["lucky_colors"]),
            random.choice(self._fortune["lucky_directions"]),
        )

    def _desc(self, fortune):
        descs = self._fortune["descriptions"].get(fortune, ["运势未知。"])
        return random.choice(descs)

    def _cleanup(self, data):
        cutoff = (
            datetime.utcnow() + timedelta(hours=self.timezone_offset) - timedelta(days=30)
        ).strftime("%Y-%m-%d")
        for k in list(data.keys()):
            if k < cutoff:
                del data[k]
        return data

    def _do_draw(self, user_id):
        today = self._today()
        data = self._load()

        if today in data and user_id in data[today]:
            return data[today][user_id]

        fortune = self._draw()
        item, color, direction = self._attachments()
        desc = self._desc(fortune)

        result = {
            "fortune": fortune,
            "lucky_item": item,
            "lucky_color": color,
            "lucky_direction": direction,
            "description": desc,
        }

        data.setdefault(today, {})[user_id] = result
        data = self._cleanup(data)
        self._save(data)

        return result

    @filter.command("抽签")
    async def draw_cn(self, event: AstrMessageEvent):
        """抽取今日运势签文"""
        r = self._do_draw(event.get_sender_id())
        yield event.plain_result(
            f"🎋 今日运势\n"
            f"运势：{r['fortune']}\n"
            f"幸运物：{r['lucky_item']}\n"
            f"幸运颜色：{r['lucky_color']}\n"
            f"幸运方向：{r['lucky_direction']}\n"
            f"运势描述：{r['description']}"
        )

    @filter.command("omikuji")
    async def draw_jp(self, event: AstrMessageEvent):
        """おみくじを引く"""
        r = self._do_draw(event.get_sender_id())
        yield event.plain_result(
            f"🎋 今日运势\n"
            f"运势：{r['fortune']}\n"
            f"幸运物：{r['lucky_item']}\n"
            f"幸运颜色：{r['lucky_color']}\n"
            f"幸运方向：{r['lucky_direction']}\n"
            f"运势描述：{r['description']}"
        )

    @filter.command("运势")
    async def fortune_view(self, event: AstrMessageEvent):
        """查看今日运势"""
        today = self._today()
        user_id = event.get_sender_id()
        data = self._load()

        if today in data and user_id in data[today]:
            r = data[today][user_id]
            yield event.plain_result(
                f"🎋 今日运势\n"
                f"运势：{r['fortune']}\n"
                f"幸运物：{r['lucky_item']}\n"
                f"幸运颜色：{r['lucky_color']}\n"
                f"幸运方向：{r['lucky_direction']}\n"
                f"运势描述：{r['description']}"
            )
        else:
            yield event.plain_result("你今天还没有抽签哦，发送 /抽签 来抽取今日运势吧！")

    async def terminate(self):
        pass
