from shvatka.models.enums.played import Played

KEY_PREFIXES = ("SH", "СХ")

INVALID_KEY_ERROR = (
    f"Ключ должен содержать один из префиксов ({', '.join(KEY_PREFIXES)}), "
    f"использовать можно только цифры заглавные латинские и кириллические буквы "
)

WAIVER_STATUS_MEANING = {
    Played.yes: "Играют",
    Played.no: "Не играют",
    Played.think: "Размышляют",
}
