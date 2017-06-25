from enum import Enum

class States(Enum):
    online_motivation = 0
    ad_acceptance = 1
    mission_skill = 2
    consumption_ability = 3

class Actions(Enum):
    show_ad = 0
    send_award = 1
    increase_difficulty = 2
    decrease_difficulty = 3
    goods_recommend = 4

class Engagements(Enum):
    online = 0
    transaction = 1
    mission_completed = 2
    mission_failed = 3
    level_up = 4

class Events(Enum):
    ad_closed = 0
    ad_opened = 1
    offline = 2
    mission_start = 3

