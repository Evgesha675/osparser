import requests
import re

CLIENT_ID = "40897"
CLIENT_SECRET = "bLDoG2uhbU09Q4HvXYbbh6Sc0UrP5rc3TdGVjm5e"

def get_access_token():
    url = "https://osu.ppy.sh/oauth/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "public"
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_user_details(user_id, token):
    url = f"https://osu.ppy.sh/api/v2/users/{user_id}/osu"
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def parse_user_id_from_url(url):
    match = re.search(r'/users/(\d+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError("Неверный URL профиля osu!")

def format_playstyle(playstyle):
    if isinstance(playstyle, list):
        return ", ".join(playstyle)
    elif isinstance(playstyle, str):
        return playstyle
    return ""

def escape_csv_field(value):
    if value is None:
        return ""
    text = str(value)
    if ',' in text or '"' in text or '\n' in text:
        text = text.replace('"', '""')
        return f'"{text}"'
    return text

def main():
    url = input("Введите ссылку на профиль osu!: ").strip()
    try:
        user_id = parse_user_id_from_url(url)
    except ValueError as e:
        print(e)
        return

    try:
        token = get_access_token()
        user = get_user_details(user_id, token)
    except Exception as e:
        print("Ошибка при запросе данных:", e)
        return

    stats = user.get("statistics", {})
    level = stats.get("level", {}).get("current", "N/A")
    play_time_hours = round(stats.get("play_time", 0) / 3600)
    playstyle_str = format_playstyle(user.get("playstyle"))

    fields = [
        "rank", "user_id", "username", "country_code", "country_name",
        "global_rank", "country_rank", "pp", "level", "accuracy",
        "play_count", "play_time_hours", "total_score", "ranked_score",
        "playstyle", "join_date", "supporter", "profile_colour",
        "avatar_url", "profile_url", "twitter", "discord", "youtube",
        "twitch", "website"
    ]

    data = {
        "rank": user.get("rank", "N/A"),
        "user_id": user.get("id"),
        "username": user.get("username"),
        "country_code": user.get("country", {}).get("code"),
        "country_name": user.get("country", {}).get("name"),
        "global_rank": stats.get("global_rank"),
        "country_rank": stats.get("country_rank"),
        "pp": stats.get("pp"),
        "level": level,
        "accuracy": stats.get("hit_accuracy"),
        "play_count": stats.get("play_count"),
        "play_time_hours": play_time_hours,
        "total_score": stats.get("total_score"),
        "ranked_score": stats.get("ranked_score"),
        "playstyle": playstyle_str,
        "join_date": user.get("join_date"),
        "supporter": user.get("is_supporter"),
        "profile_colour": user.get("profile_colour"),
        "avatar_url": user.get("avatar_url"),
        "profile_url": f"https://osu.ppy.sh/users/{user.get('id')}",
        "twitter": user.get("twitter_url"),
        "discord": user.get("discord"),
        "youtube": user.get("youtube_url"),
        "twitch": user.get("twitch_url"),
        "website": user.get("website"),
    }

    # Вывод заголовка
    print(",".join(fields))
    # Вывод данных в одной строке
    print(",".join(escape_csv_field(data.get(field, "")) for field in fields))


if __name__ == "__main__":
    main()
