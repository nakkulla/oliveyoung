"""
개선된 통합 도구 모듈
기존 코드와의 호환성을 위해 유지되는 레거시 함수들
새로운 코드에서는 core 모듈 사용을 권장
"""

import os
import json
import warnings
from typing import Any, Dict, Optional

# 새로운 코어 모듈 임포트
from core import config_manager, TelegramBot, Logger

# 레거시 호환성을 위한 전역 설정
script_directory = os.path.dirname(os.path.abspath(__file__))
conf = os.path.join(script_directory, 'config.json')

def load_config():
    """레거시: 설정 로드 (권장하지 않음 - config_manager 사용 권장)"""
    warnings.warn(
        "load_config()는 deprecated입니다. core.config_manager를 사용하세요.",
        DeprecationWarning,
        stacklevel=2
    )
    return config_manager._config

def fjson(user: str, *args) -> Any:
    """레거시: 설정값 가져오기 (권장하지 않음 - config_manager.get() 사용 권장)"""
    warnings.warn(
        "fjson()는 deprecated입니다. config_manager.get()을 사용하세요.",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        return config_manager.get(user, *args)
    except Exception:
        raise Exception(f"Error loading config: {args}")

def folder_maker(folder: str, *args):
    """폴더 생성 유틸리티 (계속 사용 가능)"""
    os.makedirs(folder, exist_ok=True)
    for arg in args:
        os.makedirs(os.path.join(folder, arg), exist_ok=True)

class MyBot:
    """
    레거시 텔레그램 봇 클래스 (호환성 유지)
    새로운 코드에서는 core.TelegramBot 사용 권장
    """
    
    def __init__(self, token: str, id: str):
        warnings.warn(
            "MyBot은 deprecated입니다. core.TelegramBot을 사용하세요.",
            DeprecationWarning,
            stacklevel=2
        )
        
        self.token = token
        self.id = id
        self.telegram_bot = TelegramBot(token, id)
        self.value = None
    
    def send_message(self, text: str):
        """메시지 전송"""
        try:
            self.telegram_bot.send_message_sync(text)
        except Exception as e:
            print(f"메시지 전송 실패: {e}")
    
    def send_photo(self, path: str):
        """사진 전송"""
        try:
            self.telegram_bot.send_photo_sync(path)
        except Exception as e:
            print(f"사진 전송 실패: {e}")
    
    def send_document(self, path: str):
        """문서 전송"""
        try:
            if os.path.exists(path):
                # 임시로 기본 Bot 사용
                import asyncio
                from telegram import Bot
                
                bot = Bot(self.token)
                
                async def send_doc():
                    with open(path, 'rb') as doc:
                        await bot.send_document(chat_id=self.id, document=doc)
                
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(send_doc())
                except RuntimeError:
                    asyncio.run(send_doc())
                    
        except Exception as e:
            print(f"문서 전송 실패: {e}")

# 기존 코드 호환성을 위한 전역 변수
try:
    config = load_config()
except:
    config = {}

# 마이그레이션 가이드 출력
def show_migration_guide():
    """마이그레이션 가이드 출력"""
    print("""
🔄 **코드 마이그레이션 가이드**

기존 코드:
```python
import tools
bot = tools.MyBot(tools.fjson('ilsun','telegram','token'), tools.fjson('ilsun','telegram','id'))
```

새로운 코드:
```python
from core import TelegramBot, config_manager
bot = TelegramBot()  # 자동으로 설정에서 로드
```

기존 코드:
```python
user_id = tools.fjson('ilsun', 'srt', 'id')
```

새로운 코드:
```python
from core import config_manager
user_id = config_manager.get('ilsun', 'srt', 'id')
```

자세한 내용은 /CLAUDE.md 파일을 참조하세요.
    """)

if __name__ == "__main__":
    show_migration_guide()