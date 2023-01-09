from collections import namedtuple
from data.characters import Characters
import data.event_bit as event_bit
import data.npc_bit as npc_bit
from event.event_reward import RewardType

NameBit = namedtuple("NameBit", ["name", "bit", "reward_types", "gate_character"], defaults={'reward_types' : RewardType.NONE})
CHAR_ESPER_REWARD = RewardType.CHARACTER | RewardType.ESPER
ANY_REWARD = RewardType.CHARACTER | RewardType.ESPER | RewardType.ITEM
ESPER_ITEM_REWARD =  RewardType.ESPER | RewardType.ITEM
ITEM_REWARD =  RewardType.ITEM


from constants.entities import (
    TERRA, LOCKE, CYAN, SHADOW,
    EDGAR, SABIN, CELES, STRAGO,
    RELM, SETZER, MOG, GAU, GOGO,
    UMARO
)

AUCTION1 =  NameBit("Auction1", event_bit.AUCTION_BOUGHT_ESPER1, ESPER_ITEM_REWARD, None)
AUCTION2 = NameBit("Auction2", event_bit.AUCTION_BOUGHT_ESPER2, ESPER_ITEM_REWARD, None)
ANCIENT_CASTLE = NameBit("Ancient Castle", event_bit.GOT_RAIDEN, ANY_REWARD, EDGAR)
BAREN_FALLS = NameBit("Baren Falls", event_bit.NAMED_GAU, RewardType.CHARACTER, SABIN)
BURNING_HOUSE = NameBit("Burning House", event_bit.DEFEATED_FLAME_EATER, ANY_REWARD, STRAGO)
COLLAPSING_HOUSE = NameBit("Collapsing House", event_bit.FINISHED_COLLAPSING_HOUSE, ANY_REWARD, SABIN)
DARYLS_TOMB = NameBit("Daryl's Tomb", event_bit.DEFEATED_DULLAHAN, ANY_REWARD, SETZER)
DOMA_SIEGE = NameBit("Doma Siege", event_bit.FINISHED_DOMA_WOB, ANY_REWARD, CYAN)
DOMA_DREAM_DOOR = NameBit("Doma Dream Door", event_bit.DEFEATED_STOOGES, ESPER_ITEM_REWARD, CYAN)
DOMA_DREAM_AWAKEN = NameBit("Doma Dream Awaken", event_bit.FINISHED_DOMA_WOR, CHAR_ESPER_REWARD, CYAN)
DOMA_DREAM_THRONE = NameBit("Doma Dream Throne", event_bit.GOT_ALEXANDR, ESPER_ITEM_REWARD, CYAN)
EBOTS_ROCK = NameBit("Ebot's Rock", event_bit.DEFEATED_HIDON, ANY_REWARD, STRAGO)
ESPER_MOUNTAIN = NameBit("Esper Mountain", event_bit.DEFEATED_ULTROS_ESPER_MOUNTAIN, ANY_REWARD, RELM)
FANATICS_TOWER_LEADER = NameBit("Fanatic's Tower Leader", event_bit.DEFEATED_MAGIMASTER, ESPER_ITEM_REWARD, STRAGO)
FANATICS_TOWER_FOLLOWER = NameBit("Fanatic's Tower Follower", event_bit.RECRUITED_STRAGO_FANATICS_TOWER, CHAR_ESPER_REWARD, STRAGO)
FIGARO_CASTLE_THRONE = NameBit("Figaro Castle Throne", event_bit.NAMED_EDGAR, ANY_REWARD, EDGAR)
FIGARO_CASTLE_ENGINE = NameBit("Figaro Castle Engine", event_bit.DEFEATED_TENTACLES_FIGARO, ANY_REWARD, EDGAR)
FLOATING_CONT_ARRIVE = NameBit("Floating Cont. Arrive", event_bit.RECRUITED_SHADOW_FLOATING_CONTINENT, CHAR_ESPER_REWARD, SHADOW)
FLOATING_CONT_BEAST = NameBit("Floating Cont. Beast", event_bit.DEFEATED_ATMAWEAPON, ESPER_ITEM_REWARD, SHADOW)
FLOATING_CONT_ESCAPE = NameBit("Floating Cont. Escape", event_bit.FINISHED_FLOATING_CONTINENT, CHAR_ESPER_REWARD, SHADOW)
GAUS_FATHERS_HOUSE = NameBit("Gau's Father's House", event_bit.RECRUITED_SHADOW_GAU_FATHER_HOUSE, ANY_REWARD, SHADOW)
IMPERIAL_CAMP = NameBit("Imperial Camp", event_bit.FINISHED_IMPERIAL_CAMP, ANY_REWARD, SABIN)
KEFKAS_TOWER_AMBUSH = NameBit("Kefka's Tower Ambush", event_bit.DEFEATED_INFERNO, RewardType.NONE, None)
KEFKAS_TOWER_CELL_BEAST = NameBit("Kefka's Tower Cell Beast", event_bit.DEFEATED_ATMA, ITEM_REWARD, None)
KEFKAS_TOWER_GUARDIAN = NameBit("Kefka's Tower Guardian", event_bit.DEFEATED_GUARDIAN, RewardType.NONE, None)
KEFKAS_TOWER_LEFT_STATUE = NameBit("KT Left Triad Statue", event_bit.DEFEATED_DOOM, RewardType.NONE, None)
KEFKAS_TOWER_MIDDLE_STATUE = NameBit("KT Mid Triad Statue", event_bit.DEFEATED_POLTERGEIST, RewardType.NONE, None)
KEFKAS_TOWER_RIGHT_STATUE = NameBit("KT Right Triad Statue", event_bit.DEFEATED_GODDESS, RewardType.NONE, None)
KOHLINGEN_CAFE = NameBit("Kohlingen Cafe", event_bit.RECRUITED_SHADOW_KOHLINGEN, ANY_REWARD, SETZER)
LETE_RIVER = NameBit("Lete River", event_bit.RODE_RAFT_LETE_RIVER, ANY_REWARD, TERRA)
LONE_WOLF_CHASE = NameBit("Lone Wolf Chase", event_bit.CHASING_LONE_WOLF7, ANY_REWARD, MOG)
LONE_WOLF_MOOGLE_ROOM = NameBit("Lone Wolf Moogle Room", event_bit.GOT_BOTH_REWARDS_LONE_WOLF, ANY_REWARD, MOG)
NARSHE_MOOGLE_DEFENSE = NameBit("Narshe Moogle Defense", event_bit.FINISHED_MOOGLE_DEFENSE, ANY_REWARD, MOG)
MAGITEK_FACTORY_TRASH = NameBit("Magitek Factory Trash", event_bit.GOT_IFRIT_SHIVA, ESPER_ITEM_REWARD, CELES)
MAGITEK_FACTORY_GUARD = NameBit("Magitek Factory Guard", event_bit.DEFEATED_NUMBER_024, ESPER_ITEM_REWARD, CELES)
MAGITEK_FACTORY_FINISH = NameBit("Magitek Factory Finish", event_bit.DEFEATED_CRANES, CHAR_ESPER_REWARD, CELES)
MOBLIZ_ATTACK = NameBit("Mobliz Attack", event_bit.RECRUITED_TERRA_MOBLIZ, ANY_REWARD, TERRA)
MT_KOLTS = NameBit("Mt. Kolts", event_bit.DEFEATED_VARGAS, ANY_REWARD, SABIN)
MT_ZOZO = NameBit("Mt. Zozo", event_bit.FINISHED_MT_ZOZO, ANY_REWARD, CYAN)
NARSHE_BATTLE = NameBit("Narshe Battle", event_bit.FINISHED_NARSHE_BATTLE, ANY_REWARD, None)
NARSHE_WEAPON_SHOP = NameBit("Narshe Weapon Shop", event_bit.GOT_RAGNAROK, ESPER_ITEM_REWARD, LOCKE)
NARSHE_WEAPON_SHOP_MINES = NameBit("Narshe Weapon Shop Mines", event_bit.GOT_BOTH_REWARDS_WEAPON_SHOP, ITEM_REWARD, LOCKE)
OPERA_HOUSE_DISRUPTION = NameBit("Opera House Disruption", event_bit.FINISHED_OPERA_DISRUPTION, ANY_REWARD, CELES)
OWZERS_MANSION = NameBit("Owzer's Mansion", event_bit.DEFEATED_CHADARNOOK, ANY_REWARD, RELM)
PHANTOM_TRAIN = NameBit("Phantom Train", event_bit.GOT_PHANTOM_TRAIN_REWARD, ANY_REWARD, SABIN)
PHOENIX_CAVE = NameBit("Phoenix Cave", event_bit.RECRUITED_LOCKE_PHOENIX_CAVE, ANY_REWARD, LOCKE)
SEALED_GATE = NameBit("Sealed Gate", npc_bit.BLOCK_SEALED_GATE, ANY_REWARD, TERRA)
SEARCH_THE_SKIES = NameBit("Search The Skies", event_bit.DEFEATED_DOOM_GAZE, ANY_REWARD, SETZER)
SERPENT_TRENCH = NameBit("Serpent Trench", event_bit.GOT_SERPENT_TRENCH_REWARD, ANY_REWARD, GAU)
SOUTH_FIGARO_PRISONER = NameBit("South Figaro Prisoner", event_bit.FREED_CELES, ANY_REWARD, CELES)
SOUTH_FIGARO_CAVE = NameBit("South Figaro Cave", event_bit.DEFEATED_TUNNEL_ARMOR, ANY_REWARD, LOCKE)
TRITOCH_CLIFF = NameBit("Tritoch Cliff", event_bit.GOT_TRITOCH, ESPER_ITEM_REWARD, None)
TZEN_THIEF = NameBit("Tzen Thief", event_bit.BOUGHT_ESPER_TZEN, ESPER_ITEM_REWARD, None)
UMAROS_CAVE = NameBit("Umaro's Cave", event_bit.RECRUITED_UMARO_WOR, ANY_REWARD, UMARO)
VELDT = NameBit("Veldt", event_bit.VELDT_REWARD_OBTAINED, CHAR_ESPER_REWARD, GAU)
VELDT_CAVE = NameBit("Veldt Cave", event_bit.DEFEATED_SR_BEHEMOTH, ANY_REWARD, SHADOW)
WHELK_GATE = NameBit("Whelk Gate", event_bit.DEFEATED_WHELK, ANY_REWARD, TERRA)
ZONE_EATER = NameBit("Zone Eater", event_bit.RECRUITED_GOGO_WOR, ANY_REWARD, GOGO)
ZOZO_TOWER = NameBit("Zozo Tower", event_bit.GOT_ZOZO_REWARD, ANY_REWARD, TERRA)

ANCIENT_CASTLE_DRAGON = NameBit("Ancient Castle Dragon", event_bit.DEFEATED_ANCIENT_CASTLE_DRAGON, RewardType.ITEM, EDGAR)
FANATICS_TOWER_DRAGON = NameBit("Fanatic's Tower Dragon", event_bit.DEFEATED_FANATICS_TOWER_DRAGON, RewardType.ITEM, None)
KEFKAS_TOWER_DRAGON_G = NameBit("Kefka's Tower Dragon G", event_bit.DEFEATED_KEFKA_TOWER_DRAGON_G, RewardType.ITEM, None)
KEFKAS_TOWER_DRAGON_S = NameBit("Kefka's Tower Dragon S", event_bit.DEFEATED_KEFKA_TOWER_DRAGON_S, RewardType.ITEM, None)
MT_ZOZO_DRAGON = NameBit("Mt. Zozo Dragon", event_bit.DEFEATED_MT_ZOZO_DRAGON, RewardType.ITEM, CYAN)
NARSHE_DRAGON = NameBit("Narshe Dragon", event_bit.DEFEATED_NARSHE_DRAGON, RewardType.ITEM, None)
OPERA_HOUSE_DRAGON = NameBit("Opera House Dragon", event_bit.DEFEATED_OPERA_HOUSE_DRAGON, RewardType.ITEM, None)
PHOENIX_CAVE_DRAGON = NameBit("Phoenix Cave Dragon", event_bit.DEFEATED_PHOENIX_CAVE_DRAGON, RewardType.ITEM, None)

# Checks - Index is used for objective condition ids
all_checks = [
    AUCTION1,
    AUCTION2,
    ANCIENT_CASTLE,
    BAREN_FALLS,
    BURNING_HOUSE,
    COLLAPSING_HOUSE,
    DARYLS_TOMB,
    DOMA_SIEGE,
    DOMA_DREAM_DOOR,
    DOMA_DREAM_AWAKEN,
    DOMA_DREAM_THRONE,
    EBOTS_ROCK,
    ESPER_MOUNTAIN,
    FANATICS_TOWER_FOLLOWER,
    FANATICS_TOWER_LEADER,
    FIGARO_CASTLE_THRONE,
    FIGARO_CASTLE_ENGINE,
    FLOATING_CONT_ARRIVE,
    FLOATING_CONT_BEAST,
    FLOATING_CONT_ESCAPE,
    GAUS_FATHERS_HOUSE,
    IMPERIAL_CAMP,
    KOHLINGEN_CAFE,
    LETE_RIVER,
    LONE_WOLF_CHASE,
    LONE_WOLF_MOOGLE_ROOM,
    MAGITEK_FACTORY_TRASH,
    MAGITEK_FACTORY_GUARD,
    MAGITEK_FACTORY_FINISH,
    MOBLIZ_ATTACK,
    MT_KOLTS,
    MT_ZOZO,
    NARSHE_BATTLE,
    NARSHE_WEAPON_SHOP,
    NARSHE_WEAPON_SHOP_MINES,
    OPERA_HOUSE_DISRUPTION,
    OWZERS_MANSION,
    PHANTOM_TRAIN,
    PHOENIX_CAVE,
    SEALED_GATE,
    SEARCH_THE_SKIES,
    SERPENT_TRENCH,
    SOUTH_FIGARO_PRISONER,
    SOUTH_FIGARO_CAVE,
    TRITOCH_CLIFF,
    TZEN_THIEF,
    UMAROS_CAVE,
    VELDT,
    VELDT_CAVE,
    WHELK_GATE,
    ZONE_EATER,
    ZOZO_TOWER,

    # Dragons
    ANCIENT_CASTLE_DRAGON,
    FANATICS_TOWER_DRAGON,
    KEFKAS_TOWER_DRAGON_G,
    KEFKAS_TOWER_DRAGON_S,
    MT_ZOZO_DRAGON,
    NARSHE_DRAGON,
    OPERA_HOUSE_DRAGON,
    PHOENIX_CAVE_DRAGON,
    
    KEFKAS_TOWER_CELL_BEAST,
    KEFKAS_TOWER_AMBUSH,        # 59
    KEFKAS_TOWER_GUARDIAN,      # 60
    KEFKAS_TOWER_LEFT_STATUE,   # 61
    KEFKAS_TOWER_MIDDLE_STATUE, # 62
    KEFKAS_TOWER_RIGHT_STATUE,  # 63

    NARSHE_MOOGLE_DEFENSE
]

# Used to determine some flag limitations (i.e. starting espers)
CHARACTER_ESPER_ONLY_REWARDS = len([check for check in all_checks if check.reward_types == RewardType.CHARACTER | RewardType.ESPER])

check_name = {check.bit: check.name for (idx, check) in enumerate(all_checks)}
name_check = {check.name: check.bit for (idx, check) in enumerate(all_checks)}

RECRUITABLE_DRAGONS = [
    ANCIENT_CASTLE_DRAGON,
    FANATICS_TOWER_DRAGON,
    MT_ZOZO_DRAGON,
    NARSHE_DRAGON,
    OPERA_HOUSE_DRAGON,
    PHOENIX_CAVE_DRAGON,
]
