# AWS Utils

Just some random scripts.

## iterm_profile.py

Generates iTerm Dynamic Profiles.

Example usage:

```
python iterm_profile.py --user foo --profile <aws_profile> --region <region> [--profile <another_aws_profile> --region <another_region>]
```

Copies dynamic profile to `~/Library/Application Support/iTerm2/DynamicProfiles`.

### Alias

Here's the alias I use to make updating iterm profile easier.  Something similar could also be setup in cron to run on a schedule.

```
alias itp="cd ~/git/aws-utils && source .venv/bin/activate && python iterm_profile.py --user <username> --profile <profile1> --profile <profile2> --region us-east-1 --region us-east-2 && cd -"
```

## aws-ri-check.py

Calculate AWS Reserved Instance utilization.
