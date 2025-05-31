"""時間を取得するための抽象インターフェース

DDDの観点から、ドメイン層は純粋に保たれるべきであり、
現在時刻などの副作用のある操作は抽象化される必要があります。
"""

from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    """時間を取得するための抽象インターフェース

    このインターフェースにより、ドメインエンティティは具体的な
    時間取得の実装に依存せず、テスト時には固定時刻を使用できます。
    """

    @abstractmethod
    def now(self) -> datetime:
        """現在時刻を取得します

        Returns:
            datetime: 現在時刻
        """
        pass


class SystemClock(Clock):
    """現在時刻を返す本番用の Clock 実装

    実際のシステム時刻を使用する本番環境用の実装です。
    """

    def now(self) -> datetime:
        """システムの現在時刻を返します

        Returns:
            datetime: システムの現在時刻
        """
        return datetime.now()


class FixedClock(Clock):
    """固定時刻を返すテスト用の Clock 実装

    ユニットテストで時刻が変動しないようにするための実装です。
    """

    def __init__(self, fixed_time: datetime):
        """固定時刻を設定して初期化

        Args:
            fixed_time: 常に返される固定時刻
        """
        self._fixed_time = fixed_time

    def now(self) -> datetime:
        """設定された固定時刻を返します

        Returns:
            datetime: 初期化時に設定された固定時刻
        """
        return self._fixed_time
