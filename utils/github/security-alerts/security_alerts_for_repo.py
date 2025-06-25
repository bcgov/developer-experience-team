import argparse
import os
from itertools import groupby
from github import Github


def get_github_client():
	token = os.environ.get("GITHUB_TOKEN")
	if not token:
		raise EnvironmentError("GITHUB_TOKEN environment variable not set")
	return Github(token)


def get_security_alerts_for_repo(github_client, org, repo_name):
	repo = github_client.get_repo(f"{org}/{repo_name}")
	return repo.get_codescan_alerts()


def parse_arguments():
	parser = argparse.ArgumentParser(description="Get security alerts for a GitHub repository.")
	parser.add_argument("org", help="GitHub organization name")
	parser.add_argument("repo", help="GitHub repository name")
	args = parser.parse_args()
	org = args.org
	repo_name = args.repo
	return org, repo_name


def print_alerts(org, repo_name, alerts):
	if not alerts:
		print(f"No security alerts found for repo '{org}/{repo_name}'")
	else:
		alerts = sorted(alerts, key=lambda a: a.tool.name, reverse=True)
		grouped_alerts = groupby(alerts, lambda x: x.tool.name)
		for tool_name, alerts_for_tool in grouped_alerts:
			alerts_list = list(alerts_for_tool)
			print(f"===========Tool: {tool_name}, Number of alerts: {len(alerts_list)}============")
			for alert in alerts_list:
				print(
					f"Event: [ Number: '{alert.number}', Rule: '{alert.rule.description}', Tool: '{alert.tool.name}', Created at: '{alert.created_at}']")


def main():
	gh = get_github_client()

	# read repo name from the arguments passed to the script using argparse
	org, repo_name = parse_arguments()

	# print out the arguments passed to the script and pause for user confirmation
	print(f"Retrieving security alerts for repo '{org}/{repo_name}'")
	confirm = input("Press Enter to continue or Ctrl+C to cancel...")

	# get the security alerts for the repo
	alerts = get_security_alerts_for_repo(gh, org, repo_name)

	print_alerts(org, repo_name, alerts)


if __name__ == '__main__':
	main()
