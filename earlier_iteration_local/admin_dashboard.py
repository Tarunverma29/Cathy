from local_db import get_conn


def show_users():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT telegram_user_id, username, first_name, last_seen
        FROM telegram_users
        ORDER BY last_seen DESC;
        """
    )

    users = cur.fetchall()

    print("\nRegistered Users:")
    print("-" * 60)

    for u in users:
        print(f"ID: {u[0]} | Username: {u[1]} | Name: {u[2]} | Last Seen: {u[3]}")

    print("\nTotal Users:", len(users))

    cur.close()
    conn.close()


if __name__ == "__main__":
    show_users()

