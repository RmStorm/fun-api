import os
import requests


def main():
    headers = {"authorization": f"Bearer {os.environ['TOKEN']}"}

    gh_api_url = os.environ['GITHUB_API_URL']
    gh_repo = os.environ['GITHUB_REPOSITORY']
    gh_run_id = os.environ['GITHUB_RUN_ID']
    gh_preceding_run_id = os.environ.get('PRECEDING_RUN_ID')

    print(gh_preceding_run_id)
    print("Will scrape two url's:")
    print(f'{gh_api_url}/repos/{gh_repo}/actions/runs/{gh_run_id}/jobs')
    print(f'{gh_api_url}/repos/{gh_repo}/actions/runs/{gh_preceding_run_id}/jobs')

    r = requests.get(f'{gh_api_url}/repos/{gh_repo}/actions/runs/{gh_run_id}/jobs', headers=headers)
    r.raise_for_status()
    actual_wf_jobs = r.json()

    r = requests.get(f'{gh_api_url}/repos/{gh_repo}/actions/runs/{gh_preceding_run_id}/jobs', headers=headers)
    r.raise_for_status()
    preceding_wf_jobs = r.json()

    total_action_dict = {os.environ["PRECEDING_RUN_NAME"]: preceding_wf_jobs,
                         os.environ["GITHUB_WORKFLOW"]: actual_wf_jobs}

    for wf_name, wf_jobs in total_action_dict.items():
        print(f'- {wf_name}')
        for job in wf_jobs['jobs']:
            print(f'  - {job["name"]}')
            for step in job['steps']:
                print(f'    - {step["name"]}')


if __name__ == '__main__':
    main()
