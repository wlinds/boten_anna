import requests, json, datetime

def get_following_users(user, token):
    """Gets list of followers."""
    headers = {"Authorization": "Bearer {}".format(token)}
    url = "https://api.github.com/users/{}/following".format(user)

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        following_users = response.json()
        return [user["login"] for user in following_users]
    else:
        return []

def check_for_recent_commits(user, following_users, token):
    """Checks if the followed users have made any recent commits."""
    time_now = datetime.datetime.utcnow()
    commits = []
    for u in following_users:
        headers = {f"Authorization": "Bearer {token}"}
        url = f"https://api.github.com/users/{u}/repos"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                commits_url = repo["commits_url"].split("{")[0]
                response = requests.get(commits_url, headers=headers)
                if response.status_code == 200:
                    repo_commits = response.json()
                    for commit in repo_commits:
                        commit_date = datetime.datetime.strptime(commit["commit"]["author"]["date"],
                                                                 "%Y-%m-%dT%H:%M:%SZ")
                        if commit_date > time_now - datetime.timedelta(days=2):
                            commits.append((u, repo["name"], commit["commit"]["message"]))
    return commits

def main():
    user = "wlinds"
    with open("keys.json") as f:
        keys = json.load(f)

    token = keys["GITHUB"]
    following_users = get_following_users(user, token)
    recent_commits = check_for_recent_commits(user, following_users, token)

    if recent_commits:
        print("Recent commits:")
        for u, repo, message in recent_commits:
            print(f"- User: {u}, Repository: {repo}, Commit Message: {message}")
    else:
        print("No recent commits.")

if __name__ == "__main__":
    main()