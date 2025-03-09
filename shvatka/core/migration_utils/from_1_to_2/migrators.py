from shvatka.core.migration_utils import models_0
from shvatka.core.models.dto import scn, action
from shvatka.core.models.dto import hints


def bonus_key_0_to_1(bonus_key: models_0.BonusKey) -> action.BonusKey:
    return action.BonusKey(text=bonus_key.text, bonus_minutes=bonus_key.bonus_minutes)


def hint_0_to_1(hint: models_0.AnyHint) -> hints.AnyHint:
    match hint:
        case models_0.TextHint(text=text):
            return hints.TextHint(text=text)
        case models_0.GPSHint(latitude=latitude, longitude=longitude):
            return hints.GPSHint(latitude=latitude, longitude=longitude)
        case models_0.VenueHint as vh:
            return hints.VenueHint(
                latitude=vh.latitude,
                longitude=vh.longitude,
                title=vh.title,
                address=vh.address,
                foursquare_id=vh.foursquare_id,
                foursquare_type=vh.foursquare_type,
            )
        case models_0.PhotoHint(file_guid=file_guid, caption=caption):
            return hints.PhotoHint(file_guid=file_guid, caption=caption)
        case models_0.AudioHint(file_guid=file_guid, caption=caption, thumb_guid=thumb_guid):
            return hints.AudioHint(file_guid=file_guid, thumb_guid=thumb_guid, caption=caption)
        case models_0.VideoHint(file_guid=file_guid, caption=caption, thumb_guid=thumb_guid):
            return hints.VideoHint(file_guid=file_guid, thumb_guid=thumb_guid, caption=caption)
        case models_0.DocumentHint(file_guid=file_guid, caption=caption, thumb_guid=thumb_guid):
            return hints.DocumentHint(file_guid=file_guid, caption=caption, thumb_guid=thumb_guid)
        case models_0.AnimationHint(file_guid=file_guid, caption=caption, thumb_guid=thumb_guid):
            return hints.AnimationHint(file_guid=file_guid, caption=caption, thumb_guid=thumb_guid)
        case models_0.VoiceHint(file_guid=file_guid, caption=caption):
            return hints.VoiceHint(file_guid=file_guid, caption=caption)
        case models_0.VideoNoteHint(file_guid=guid):
            return hints.VideoNoteHint(file_guid=guid)
        case models_0.ContactHint as ch:
            return hints.ContactHint(
                phone_number=ch.phone_number,
                first_name=ch.first_name,
                last_name=ch.last_name,
                vcard=ch.vcard,
            )
        case models_0.StickerHint(file_guid=guid):
            return hints.StickerHint(file_guid=guid)
        case _:
            raise RuntimeError("unknown hint type")


def time_hint_0_to_1(time_hint: models_0.TimeHint) -> hints.TimeHint:
    return hints.TimeHint(
        time=time_hint.time,
        hint=[hint_0_to_1(hint) for hint in time_hint.hint],
    )


def hints_0_to_1(hints: models_0.HintsList) -> scn.HintsList:
    return scn.HintsList([time_hint_0_to_1(hint) for hint in hints])


def level_0_to_1(level: models_0.LevelScenario) -> scn.LevelScenario:
    conditions: list[action.AnyCondition] = [action.KeyWinCondition(set(level.keys))]
    if level.bonus_keys:
        conditions.append(
            action.KeyBonusCondition({bonus_key_0_to_1(b) for b in level.bonus_keys})
        )
    return scn.LevelScenario(
        id=level.id,
        time_hints=hints_0_to_1(level.time_hints),
        conditions=scn.Conditions(conditions),
        __model_version__=1,
    )


def game_0_to_1(game: models_0.GameScenario) -> scn.GameScenario:
    return scn.GameScenario(
        name=game.name, levels=[level_0_to_1(lvl) for lvl in game.levels], __model_version__=1
    )
