import time, datetime
from homeassistant.components import websocket_api
import voluptuous as vol
from homeassistant.const import (
    CONF_TOKEN, 
    CONF_NAME,
    STATE_OFF, 
    STATE_ON, 
    STATE_PLAYING, 
    STATE_PAUSED,
    STATE_UNAVAILABLE
)

from .manifest import manifest

CLOUD_MUSIC_SERVER = "cloud_music_server"
CLOUD_MUSIC_CLIENT = "cloud_music_client"
SCHEMA_WEBSOCKET = websocket_api.BASE_COMMAND_MESSAGE_SCHEMA.extend(
    {
        "type": CLOUD_MUSIC_SERVER,
        vol.Optional("data"): dict,
    }
)

class MediaPlayerWebSocket():

    # 初始化
    def __init__(self, media_player):
        # 播放器相同字段
        self.media_player = media_player

        self.hass = media_player.hass
        # 监听web播放器的更新
        self.hass.components.websocket_api.async_register_command(
            CLOUD_MUSIC_SERVER,
            self.update,
            SCHEMA_WEBSOCKET
        )

    async def async_update(self, hass, connection, msg):
            data = msg['data']
            # print(data)
            cloud_music = hass.data[manifest.domain]
            # 消息类型
            action = data.get('action')
            if action == 'update':
                # 进度
                media_position = data.get('media_position')
                if media_position is not None:
                    self.media_player._attr_media_position = media_position
                    self.media_player._attr_media_position_updated_at = datetime.datetime.now()                    
                # 总时长
                media_duration = data.get('media_duration')
                if media_duration is not None:
                    self.media_player._attr_media_duration = media_duration
                # 音量
                volume_level = data.get('volume_level')
                if volume_level is not None:
                    self.media_player._attr_volume_level = volume_level
                # 静音
                is_volume_muted = data.get('is_volume_muted')
                if is_volume_muted is not None:
                    self.media_player._attr_is_volume_muted = is_volume_muted
            elif action == 'pause':
                self.media_player._state = STATE_PAUSED
            elif action == 'play':
                self.media_player._state = STATE_PLAYING
            elif action == 'previous':
                cloud_music.previous()
            elif action == 'next':
                cloud_music.next()
            
            await self.media_player.async_update()

    def play(self):
        # 播放
        self.fire_event({"action": "play"})
    
    def pause(self):
        # 暂停
        self.fire_event({"action": "pause"})
    
    def seek(self, position):
        # 设置进度
        self.fire_event({"media_position": position})

    def mute_volume(self, mute):
        # 静音
        self.fire_event({"is_volume_muted": mute})

    def set_volume_level(self, volume):
        # 设置音量
        self.fire_event({"volume_level": volume})

    def volume_up(self):
        # 增加音量
        current_volume = self.volume_level
        if current_volume < 1:
            self.set_volume_level(current_volume + 0.1)

    def volume_down(self):
        # 减少音量
        current_volume = self.volume_level
        if current_volume > 0:
            self.set_volume_level(current_volume - 0.1)

    def stop(self):
        # 停止
        self.fire_event({"action": "pause"})

    def set_rate(self, rate):
        # 设置播放速度
        return 1

    def fire_event(self, data):
        self.hass.bus.fire(CLOUD_MUSIC_CLIENT, data)