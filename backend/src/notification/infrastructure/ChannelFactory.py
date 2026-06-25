from src.notification.domain.Channel import ChannelConfig, ChannelType
from src.notification.domain.PushMessage import ChannelAdapter
from src.notification.infrastructure.adapters.WeComAdapter import WeComAdapter
from src.notification.infrastructure.adapters.FeishuAdapter import FeishuAdapter
from src.notification.infrastructure.adapters.DingTalkAdapter import DingTalkAdapter


def create_channel_adapter(config: ChannelConfig) -> ChannelAdapter:
    if config.type == ChannelType.WECOM:
        return WeComAdapter(config)
    elif config.type == ChannelType.FEISHU:
        return FeishuAdapter(config)
    elif config.type == ChannelType.DINGTALK:
        return DingTalkAdapter(config)
    else:
        raise ValueError(f"Unsupported channel type: {config.type}")
