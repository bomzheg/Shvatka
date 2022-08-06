KEY_PREFIXES = ("SH", "СХ")

NOT_SUPERGROUP_ERROR = (
    "Для создания команды сначала преобразуйте группу в супергруппу. "
    "Рекомендуется к прочтению https://telegra.ph/Preobrazovanie-gruppy-v-supergruppu-08-25"
)
INVALID_KEY_ERROR = (
    f"Ключ должен содержать один из префиксов ({', '.join(KEY_PREFIXES)}), "
    f"использовать можно только цифры заглавные латинские и кириллические буквы "
)
