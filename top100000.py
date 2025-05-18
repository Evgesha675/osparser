import aiohttp
import asyncio
import csv

CLIENT_ID = ""
CLIENT_SECRET = ""
MAX_USERS = 10000
PER_PAGE = 50
CONCURRENT_REQUESTS = 10  # кол-во параллельных запросов деталей пользователей

async def get_access_token(session):
    url = "https://osu.ppy.sh/oauth/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "public"
    }
    async with session.post(url, data=data) as resp:
        resp.raise_for_status()
        json_resp = await resp.json()
        return json_resp["access_token"]

async def get_top_users(session, token, page=1, per_page=50):
    url = f"https://osu.ppy.sh/api/v2/rankings/osu/performance?page={page}&per_page={per_page}"
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(url, headers=headers) as resp:
        resp.raise_for_status()
        json_resp = await resp.json()
        return json_resp.get("ranking", [])

async def get_user_details(session, user_id, token):
    url = f"https://osu.ppy.sh/api/v2/users/{user_id}/osu"
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(url, headers=headers) as resp:
        resp.raise_for_status()
        return await resp.json()

def write_header(filename):
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank",  # порядковый номер
            "user_id", "username", "country_code", "country_name",
            "global_rank", "country_rank", "pp", "level", "accuracy",
            "play_count", "play_time_hours", "total_score", "ranked_score",
            "playstyle", "join_date", "supporter", "profile_colour",
            "avatar_url", "profile_url", "twitter", "discord", "youtube", "twitch", "website"
        ])

def write_user(filename, user, rank):
    stats = user.get("statistics", {})
    level = stats.get("level", {}).get("current")
    play_time_hours = round(stats.get("play_time", 0) / 3600)

    playstyle = user.get("playstyle")
    if isinstance(playstyle, list):
        playstyle_str = ", ".join(playstyle)
    elif isinstance(playstyle, str):
        playstyle_str = playstyle
    else:
        playstyle_str = ""

    with open(filename, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            rank,
            user.get("id"),
            user.get("username"),
            user.get("country", {}).get("code"),
            user.get("country", {}).get("name"),
            stats.get("global_rank"),
            stats.get("country_rank"),
            stats.get("pp"),
            level,
            stats.get("hit_accuracy"),
            stats.get("play_count"),
            play_time_hours,
            stats.get("total_score"),
            stats.get("ranked_score"),
            playstyle_str,
            user.get("join_date"),
            user.get("is_supporter"),
            user.get("profile_colour"),
            user.get("avatar_url"),
            f"https://osu.ppy.sh/users/{user.get('id')}",
            user.get("twitter_url"),
            user.get("discord"),
            user.get("youtube_url"),
            user.get("twitch_url"),
            user.get("website")
        ])

async def main():
    filename = "osu_top_1_10000.csv"
    write_header(filename)

    async with aiohttp.ClientSession() as session:
        try:
            token = await get_access_token(session)
        except Exception as e:
            print("Ошибка получения токена:", e)
            return

        start_rank = 0
        end_rank = 20000
        per_page = PER_PAGE

        start_page = (start_rank - 1) // per_page + 1  # 200
        end_page = (end_rank - 1) // per_page + 1      # 400

        all_count = 0

        for page in range(start_page, end_page + 1):
            try:
                ranking = await get_top_users(session, token, page, per_page)
            except Exception as e:
                print(f"Ошибка получения топа на странице {page}:", e)
                break

            if not ranking:
                print("Данных больше нет.")
                break

            user_ids = [user.get("user", {}).get("id") for user in ranking if user.get("user", {}).get("id")]

            semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

            async def sem_get_user(uid):
                async with semaphore:
                    try:
                        user_detail = await get_user_details(session, uid, token)
                        return user_detail
                    except Exception as e:
                        print(f"Ошибка для пользователя {uid}:", e)
                        return None

            users_details = await asyncio.gather(*[sem_get_user(uid) for uid in user_ids])

            count_added = 0
            for i, user_detail in enumerate(users_details):
                if user_detail:
                    rank = (page - 1) * per_page + i + 1  # правильный ранг
                    if start_rank <= rank <= end_rank:
                        write_user(filename, user_detail, rank)
                        print(f"✓ {rank}. {user_detail.get('username')}")
                        count_added += 1

            if count_added == 0:
                print("Не удалось добавить новых пользователей, прерываем.")
                break

            all_count += count_added

    print(f"Готово. Всего пользователей записано: {all_count}")


if __name__ == "__main__":
    asyncio.run(main())
