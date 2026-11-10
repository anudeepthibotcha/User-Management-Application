import argparse

from app import get_db_connection, init_db


def main():

    parser = argparse.ArgumentParser(
        description="Assign an admin or user role to an existing account."
    )

    parser.add_argument(
        "username",
        help="Existing account username",
    )

    parser.add_argument(
        "role",
        choices=("admin", "user"),
        help="Role to assign",
    )

    args = parser.parse_args()

    # Make sure the database schema is up to date.
    init_db()

    connection = get_db_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE accounts
            SET role = ?
            WHERE username = ?
            """,
            (args.role, args.username),
        )

        connection.commit()

        if cursor.rowcount == 0:
            print(
                f"No account found with username: {args.username}"
            )
            raise SystemExit(1)

        print(
            f"Role for '{args.username}' has been "
            f"set to '{args.role}'."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()