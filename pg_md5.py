from passlib.apps import postgres_context
import getpass
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Generate postgres compatible MD5 password hash")
    parser.add_argument("--user", type=str, required=True,
                    help="Postgres username")
    args = parser.parse_args()

    md5  =  postgres_context.encrypt(getpass.getpass(), user=args.user)

    print(md5)

# Main Program
if __name__ == "__main__":
    # Launch main menu
    main()
