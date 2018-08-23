from passlib.apps import postgres_context
import getpass
import argparse
import secrets
import string

def main():
    parser = argparse.ArgumentParser(
        description="Generate postgres compatible MD5 password hash")
    parser.add_argument("--user", type=str, required=True,
                    help="Postgres username")
    parser.add_argument("--newpass",action='store_true')
    args = parser.parse_args()

    print("username: ", args.user)
    
    if args.newpass:
        #https://stackoverflow.com/questions/3854692/generate-password-in-python
        alphabet = string.ascii_letters + string.digits
        password = ''.join(secrets.choice(alphabet) for i in range(20)) # for a 20-character password
        md5 = postgres_context.encrypt(password, user=args.user)
        print("password: ", password)
        print("md5: ", md5)
    else:
        md5  =  postgres_context.encrypt(getpass.getpass(), user=args.user)
        print("md5: ", md5)


# Main Program
if __name__ == "__main__":
    # Launch main menu
    main()
