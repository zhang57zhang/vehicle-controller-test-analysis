"""
DBC文件解析服务

使用cantools库解析DBC文件，提取Message和Signal定义。
支持DBC、ARXML和XML格式的CAN数据库文件。
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import cantools.database


# 配置日志
logger = logging.getLogger(__name__)


class DBCParserError(Exception):
    """DBC解析错误基类"""

    pass


class FileFormatError(DBCParserError):
    """文件格式错误"""

    pass


class ParseError(DBCParserError):
    """解析错误"""

    pass


class DBCParser:
    """
    DBC文件解析器

    提供DBC文件的加载、解析和数据提取功能。
    """

    def __init__(self, dbc_file_path: str):
        """
        初始化DBC解析器

        Args:
            dbc_file_path: DBC文件路径

        Raises:
            FileFormatError: 文件格式不支持时
        """
        self.dbc_file_path = Path(dbc_file_path)
        self.db: Optional[cantools.database.Database] = None
        self._validate_file_format()

    def _validate_file_format(self) -> None:
        """
        验证文件格式

        Raises:
            FileFormatError: 当文件格式不支持时
        """
        ext = self.dbc_file_path.suffix.lower()
        supported_extensions = {".dbc", ".arxml", ".xml"}

        if ext not in supported_extensions:
            raise FileFormatError(
                f"Unsupported DBC file format: {ext}. Supported formats: {supported_extensions}"
            )

        if not self.dbc_file_path.exists():
            raise FileNotFoundError(f"DBC file not found: {self.dbc_file_path}")

    def load(self) -> None:
        """
        加载DBC文件

        Raises:
            ParseError: 文件解析失败时
        """
        try:
            logger.info(f"Loading DBC file: {self.dbc_file_path}")
            self.db = cantools.database.load_file(str(self.dbc_file_path))
            logger.info(f"Successfully loaded DBC file with {len(self.db.messages)} messages")
        except Exception as e:
            logger.error(f"Failed to load DBC file: {str(e)}", exc_info=True)
            raise ParseError(f"Failed to parse DBC file: {str(e)}")

    def get_messages(self) -> List[Dict[str, Any]]:
        """
        获取所有消息定义

        Returns:
            消息定义列表，每个消息包含：
                - frame_id: CAN帧ID
                - name: 消息名称
                - length: 数据长度（字节）
                - cycle_time: 发送周期（毫秒）
                - senders: 发送者列表
                - comment: 注释
                - signals: 信号列表

        Raises:
            ParseError: DBC未加载时
        """
        if not self.db:
            raise ParseError("DBC file not loaded. Call load() first.")

        messages = []
        for msg in self.db.messages:
            message_data = {
                "frame_id": msg.frame_id,
                "name": msg.name,
                "length": msg.length,
                "cycle_time": msg.cycle_time,
                "senders": list(msg.senders) if msg.senders else [],
                "comment": msg.comment if hasattr(msg, "comment") else None,
                "signals": self._extract_signals(msg),
            }
            messages.append(message_data)

        logger.info(f"Extracted {len(messages)} messages from DBC")
        return messages

    def get_nodes(self) -> List[Dict[str, Any]]:
        """
        获取所有节点定义

        Returns:
            节点定义列表
        """
        if not self.db:
            raise ParseError("DBC file not loaded. Call load() first.")

        nodes = []
        if hasattr(self.db, "nodes") and self.db.nodes:
            for node in self.db.nodes:
                node_data = {
                    "name": node.name if hasattr(node, "name") else str(node),
                    "comment": node.comment if hasattr(node, "comment") else None,
                }
                nodes.append(node_data)

        return nodes

    def get_dbc_structure(self) -> Dict[str, Any]:
        """
        获取DBC完整结构（Node -> Message -> Signal）

        Returns:
            DBC结构树
        """
        if not self.db:
            raise ParseError("DBC file not loaded. Call load() first.")

        nodes_map: Dict[str, Dict[str, Any]] = {}

        for msg in self.db.messages:
            senders = list(msg.senders) if msg.senders else ["Unknown"]

            for sender in senders:
                if sender not in nodes_map:
                    nodes_map[sender] = {"name": sender, "messages": {}}

                if msg.name not in nodes_map[sender]["messages"]:
                    nodes_map[sender]["messages"][msg.name] = {
                        "frame_id": msg.frame_id,
                        "name": msg.name,
                        "length": msg.length,
                        "cycle_time": msg.cycle_time,
                        "comment": msg.comment if hasattr(msg, "comment") else None,
                        "signals": [],
                    }

                for signal in msg.signals:
                    signal_data = {
                        "name": signal.name,
                        "full_name": f"{msg.name}.{signal.name}",
                        "start": signal.start,
                        "length": signal.length,
                        "byte_order": signal.byte_order,
                        "is_signed": signal.is_signed,
                        "scale": signal.scale,
                        "offset": signal.offset,
                        "minimum": signal.minimum,
                        "maximum": signal.maximum,
                        "unit": signal.unit,
                        "comment": signal.comment if hasattr(signal, "comment") else None,
                    }
                    nodes_map[sender]["messages"][msg.name]["signals"].append(signal_data)

        if "Unknown" in nodes_map and len(nodes_map) > 1:
            unknown_msgs = nodes_map.pop("Unknown")
            for msg_name, msg_data in unknown_msgs["messages"].items():
                for node_name in nodes_map:
                    nodes_map[node_name]["messages"][msg_name] = msg_data
                    break

        return {
            "nodes": list(nodes_map.values()),
            "node_count": len(nodes_map),
            "message_count": sum(len(n["messages"]) for n in nodes_map.values()),
            "signal_count": sum(
                len(m["signals"]) for n in nodes_map.values() for m in n["messages"].values()
            ),
        }

    def _extract_signals(self, message) -> List[Dict[str, Any]]:
        """
        从消息中提取信号信息

        Args:
            message: cantools消息对象

        Returns:
            信号定义列表
        """
        signals = []
        for signal in message.signals:
            signal_data = {
                "name": signal.name,
                "start": signal.start,
                "length": signal.length,
                "byte_order": signal.byte_order,
                "is_signed": signal.is_signed,
                "scale": signal.scale,
                "offset": signal.offset,
                "minimum": signal.minimum,
                "maximum": signal.maximum,
                "unit": signal.unit,
                "comment": signal.comment if hasattr(signal, "comment") else None,
                "choices": signal.choices if hasattr(signal, "choices") else None,
            }
            signals.append(signal_data)

        return signals

    def get_message_by_name(self, message_name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取消息定义

        Args:
            message_name: 消息名称

        Returns:
            消息定义，未找到时返回None

        Raises:
            ParseError: DBC未加载时
        """
        if not self.db:
            raise ParseError("DBC file not loaded. Call load() first.")

        try:
            msg = self.db.get_message_by_name(message_name)
            return {
                "frame_id": msg.frame_id,
                "name": msg.name,
                "length": msg.length,
                "cycle_time": msg.cycle_time,
                "senders": msg.senders,
                "comment": msg.comment if hasattr(msg, "comment") else None,
                "signals": self._extract_signals(msg),
            }
        except KeyError:
            logger.warning(f"Message not found: {message_name}")
            return None

    def get_message_by_frame_id(self, frame_id: int) -> Optional[Dict[str, Any]]:
        """
        根据帧ID获取消息定义

        Args:
            frame_id: CAN帧ID

        Returns:
            消息定义，未找到时返回None

        Raises:
            ParseError: DBC未加载时
        """
        if not self.db:
            raise ParseError("DBC file not loaded. Call load() first.")

        try:
            msg = self.db.get_message_by_frame_id(frame_id)
            return {
                "frame_id": msg.frame_id,
                "name": msg.name,
                "length": msg.length,
                "cycle_time": msg.cycle_time,
                "senders": msg.senders,
                "comment": msg.comment if hasattr(msg, "comment") else None,
                "signals": self._extract_signals(msg),
            }
        except KeyError:
            logger.warning(f"Message not found for frame_id: {frame_id}")
            return None

    def get_all_signal_names(self) -> List[str]:
        """
        获取所有信号名称

        Returns:
            信号名称列表

        Raises:
            ParseError: DBC未加载时
        """
        if not self.db:
            raise ParseError("DBC file not loaded. Call load() first.")

        signal_names = []
        for msg in self.db.messages:
            for signal in msg.signals:
                signal_names.append(signal.name)

        logger.info(f"Found {len(signal_names)} unique signals")
        return signal_names

    def get_summary(self) -> Dict[str, Any]:
        """
        获取DBC文件摘要信息

        Returns:
            摘要信息字典，包含：
                - file_name: 文件名
                - message_count: 消息数量
                - signal_count: 信号数量
                - messages: 消息列表（简要信息）

        Raises:
            ParseError: DBC未加载时
        """
        if not self.db:
            raise ParseError("DBC file not loaded. Call load() first.")

        signal_count = sum(len(msg.signals) for msg in self.db.messages)

        messages_summary = []
        for msg in self.db.messages:
            messages_summary.append(
                {
                    "frame_id": msg.frame_id,
                    "name": msg.name,
                    "signal_count": len(msg.signals),
                    "length": msg.length,
                }
            )

        return {
            "file_name": self.dbc_file_path.name,
            "message_count": len(self.db.messages),
            "signal_count": signal_count,
            "messages": messages_summary,
        }

    def decode_message(
        self, frame_id: int, data: bytes, allow_truncated: bool = False
    ) -> Dict[str, Any]:
        """
        解码CAN消息

        Args:
            frame_id: CAN帧ID
            data: CAN数据（字节）
            allow_truncated: 是否允许截断数据

        Returns:
            解码后的信号字典

        Raises:
            ParseError: DBC未加载或解码失败时
        """
        if not self.db:
            raise ParseError("DBC file not loaded. Call load() first.")

        try:
            decoded = self.db.decode_message(frame_id, data, allow_truncated=allow_truncated)
            return decoded
        except Exception as e:
            logger.error(f"Failed to decode message {frame_id}: {str(e)}")
            raise ParseError(f"Failed to decode message: {str(e)}")


def parse_dbc_file(dbc_file_path: str) -> Dict[str, Any]:
    """
    便捷函数：解析DBC文件并返回完整数据

    Args:
        dbc_file_path: DBC文件路径

    Returns:
        包含DBC解析结果的字典

    Raises:
        FileFormatError: 文件格式不支持时
        ParseError: 文件解析失败时
    """
    parser = DBCParser(dbc_file_path)
    parser.load()
    return parser.get_summary()


def get_message_signals(dbc_file_path: str, message_name: str) -> List[Dict[str, Any]]:
    """
    便捷函数：获取指定消息的所有信号

    Args:
        dbc_file_path: DBC文件路径
        message_name: 消息名称

    Returns:
        信号定义列表

    Raises:
        FileFormatError: 文件格式不支持时
        ParseError: 文件解析失败时
    """
    parser = DBCParser(dbc_file_path)
    parser.load()
    message = parser.get_message_by_name(message_name)

    if not message:
        return []

    return message["signals"]
