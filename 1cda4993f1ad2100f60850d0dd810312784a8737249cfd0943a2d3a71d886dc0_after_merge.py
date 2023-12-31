    def repo_info_model(self, task, repo_id):

        github_url = task['given']['github_url']

        self.logger.info("Beginning filling the repo_info model for repo: " + github_url + "\n")

        owner, repo = self.get_owner_repo(github_url)

        url = 'https://api.github.com/graphql'

        query = """
            {
                repository(owner:"%s", name:"%s"){
                    updatedAt
                    hasIssuesEnabled
                    issues(states:OPEN) {
                        totalCount
                    }
                    hasWikiEnabled
                    forkCount
                    defaultBranchRef {
                        name
                    }
                    watchers {
                        totalCount
                    }
                    id
                    licenseInfo {
                        name
                        url
                    }
                    stargazers {
                        totalCount
                    }
                    codeOfConduct {
                        name
                        url
                    }
                    issue_count: issues {
                        totalCount
                    }
                    issues_closed: issues(states:CLOSED) {
                        totalCount
                    }
                    pr_count: pullRequests {
                        totalCount
                    }
                    pr_open: pullRequests(states: OPEN) {
                        totalCount
                    }
                    pr_closed: pullRequests(states: CLOSED) {
                        totalCount
                    }
                    pr_merged: pullRequests(states: MERGED) {
                        totalCount
                    }
                    ref(qualifiedName: "master") {
                        target {
                            ... on Commit {
                                history(first: 0){
                                    totalCount
                                }
                            }
                        }
                    }
                }
            }
        """ % (owner, repo)

        # Hit the graphql endpoint and retry 3 times in case of failure
        num_attempts = 0
        success = False
        while num_attempts < 3:
            self.logger.info("Hitting endpoint: {} ...\n".format(url))
            r = requests.post(url, json={'query': query}, headers=self.headers)
            self.update_gh_rate_limit(r)

            try:
                data = r.json()
            except:
                data = json.loads(json.dumps(r.text))

            if 'errors' in data:
                self.logger.info("Error!: {}".format(data['errors']))
                if data['errors'][0]['message'] == 'API rate limit exceeded':
                    self.update_gh_rate_limit(r)
                    continue

            if 'data' in data:
                success = True
                data = data['data']['repository']
                break
            else:
                self.logger.info("Request returned a non-data dict: {}\n".format(data))
                if data['message'] == 'Not Found':
                    self.logger.info("Github repo was not found or does not exist for endpoint: {}\n".format(url))
                    break
                if data['message'] == 'You have triggered an abuse detection mechanism. Please wait a few minutes before you try again.':
                    self.update_gh_rate_limit(r, temporarily_disable=True)
                    continue
                if data['message'] == 'Bad credentials':
                    self.update_gh_rate_limit(r, bad_credentials=True)
                    continue
            num_attempts += 1
        if not success:
            self.register_task_failure(self.task, repo_id, "Failed to hit endpoint: {}".format(url))
            return

        # Get committers count info that requires seperate endpoint
        committers_count = self.query_committers_count(owner, repo)

        # Put all data together in format of the table
        self.logger.info(f'Inserting repo info for repo with id:{repo_id}, owner:{owner}, name:{repo}\n')
        rep_inf = {
            'repo_id': repo_id,
            'last_updated': data['updatedAt'] if 'updatedAt' in data else None,
            'issues_enabled': data['hasIssuesEnabled'] if 'hasIssuesEnabled' in data else None,
            'open_issues': data['issues']['totalCount'] if data['issues'] else None,
            'pull_requests_enabled': None,
            'wiki_enabled': data['hasWikiEnabled'] if 'hasWikiEnabled' in data else None,
            'pages_enabled': None,
            'fork_count': data['forkCount'] if 'forkCount' in data else None,
            'default_branch': data['defaultBranchRef']['name'] if data['defaultBranchRef'] else None,
            'watchers_count': data['watchers']['totalCount'] if data['watchers'] else None,
            'UUID': None,
            'license': data['licenseInfo']['name'] if data['licenseInfo'] else None,
            'stars_count': data['stargazers']['totalCount'] if data['stargazers'] else None,
            'committers_count': committers_count,
            'issue_contributors_count': None,
            'changelog_file': None,
            'contributing_file': None,
            'license_file': data['licenseInfo']['url'] if data['licenseInfo'] else None,
            'code_of_conduct_file': data['codeOfConduct']['url'] if data['codeOfConduct'] else None,
            'security_issue_file': None,
            'security_audit_file': None,
            'status': None,
            'keywords': None,
            'commit_count': data['ref']['target']['history']['totalCount'] if data['ref'] else None,
            'issues_count': data['issue_count']['totalCount'] if data['issue_count'] else None,
            'issues_closed': data['issues_closed']['totalCount'] if data['issues_closed'] else None,
            'pull_request_count': data['pr_count']['totalCount'] if data['pr_count'] else None,
            'pull_requests_open': data['pr_open']['totalCount'] if data['pr_open'] else None,
            'pull_requests_closed': data['pr_closed']['totalCount'] if data['pr_closed'] else None,
            'pull_requests_merged': data['pr_merged']['totalCount'] if data['pr_merged'] else None,
            'tool_source': self.tool_source,
            'tool_version': self.tool_version,
            'data_source': self.data_source
        }

        result = self.db.execute(self.repo_info_table.insert().values(rep_inf))
        self.logger.info(f"Primary Key inserted into repo_info table: {result.inserted_primary_key}\n")
        self.results_counter += 1

        # Note that the addition of information about where a repository may be forked from, and whether a repository is archived, updates the `repo` table, not the `repo_info` table.
        forked = self.is_forked(owner, repo)
        archived = self.is_archived(owner, repo)
        archived_date_collected = None
        if archived is not False:
            archived_date_collected = archived
            archived = 1
        else:
            archived = 0

        rep_additional_data = {
            'forked_from': forked,
            'repo_archived': archived,
            'repo_archived_date_collected': archived_date_collected
        }
        result = self.db.execute(self.repo_table.update().where(repo_table.c.repo_id==repo_id).values(rep_additional_data))
        self.logger.info(f"Primary Key inserted into repo table: {result.inserted_primary_key}\n")

        self.logger.info(f"Inserted info for {owner}/{repo}\n")

        # Register this task as completed
        self.register_task_completion(self.task, repo_id, "repo_info")