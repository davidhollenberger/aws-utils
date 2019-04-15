# AWS Utils

Just some random scripts.

## iterm_profile.py

Generates iTerm Dynamic Profiles.

Example usage:

```
pipenv run python iterm_profile.py -u foo
```

Copies dynamic profile to `~/Library/Application Support/iTerm2/DynamicProfiles`.

## Alias

Here's the alias I use to make updating iterm profile easier.  Something similar could also be setup in cron to run on a schedule.

```
alias itp="cd ~/git/aws-utils && pipenv run python iterm_profile.py -u <username> && cd -"
```
