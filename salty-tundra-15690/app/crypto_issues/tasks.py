# tasks.py

from celery import shared_task
from .models import Repository
import git
import subprocess
import json
import os
from django.conf import settings
import logging
from celery.utils.log import get_task_logger
import time

logger = logging.getLogger(__name__)



@shared_task(bind=True)
def test_task(self):
    logger.info("Test task started, simulating delay.")
    time.sleep(10)  # Simulate a processing delay
    self.request.delivery_info['acknowledged'] = False  # Simulate delayed acknowledgment
    logger.info("Test task executed successfully!")
    return "Success"


@shared_task
def analyze_repository(repo_id):

    logger.info(f"Task dispatched for repository ID: {repo_id}")
    try:
        # Add logic here
        logger.info(f"Successfully analyzed repository ID: {repo_id}")
    except Exception as e:
        logger.error(f"Error analyzing repository ID {repo_id}: {str(e)}")
        raise

    try:
        repository = Repository.objects.get(id=repo_id)
        repository.status = 'processing'
        repository.save()

        repo_url = repository.repo_url
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        clone_dir = os.path.join(settings.BASE_DIR, 'tmp', repo_name)

        # Clone or pull the repository
        try:
            if os.path.exists(clone_dir):
                repo = git.Repo(clone_dir)
                repo.remotes.origin.pull()
                logger.info(f"Updated repository {repo_url}")
            else:
                git.Repo.clone_from(repo_url, clone_dir)
                logger.info(f"Cloned repository {repo_url}")
        except git.GitCommandError as e:
            logger.error(f"Git clone/pull failed for {repo_url}: {str(e)}")
            repository.status = 'failed'
            repository.analysis_result = {'error': f"Git error: {str(e)}"}
            repository.save()
            return

        # Run Bandit analysis
        try:
            command = ['bandit', '-r', clone_dir, '-f', 'json']
            logger.info(f"Running Bandit command: {' '.join(command)}")
            bandit_result = subprocess.check_output(command, stderr=subprocess.STDOUT)
            bandit_analysis = json.loads(bandit_result)
        except subprocess.CalledProcessError as e:
            logger.error(f"Bandit failed for {repo_url}: {e.output.decode()}")
            bandit_analysis = {'error': e.output.decode()}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON output from Bandit: {str(e)}")
            bandit_analysis = {'error': 'Invalid Bandit JSON output'}

        # Combine results
        repository.analysis_result = {
            'bandit': bandit_analysis,
            'custom_crypto': analyze_crypto(clone_dir),
        }
        repository.status = 'completed'
        repository.save()
        logger.info(f"Analysis completed for {repo_url}")

    except Repository.DoesNotExist:
        logger.error(f"Repository with ID {repo_id} does not exist.")
    except Exception as e:
        repository.status = 'failed'
        repository.analysis_result = {'error': str(e)}
        repository.save()
        logger.error(f"Error processing repository {repo_id}: {str(e)}")

def analyze_crypto(repo_dir):
    import ast

    insecure_functions = ['md5', 'sha1', 'AES.new', 'DES', 'ARC4']
    insecure_uses = []

    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        tree = ast.parse(f.read(), filename=file_path)
                except (SyntaxError, UnicodeDecodeError):
                    continue  # Skip files with syntax errors or decoding issues

                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func = node.func
                        if isinstance(func, ast.Attribute):
                            func_name = f"{func.value.id}.{func.attr}" if hasattr(func.value, 'id') else func.attr
                        elif isinstance(func, ast.Name):
                            func_name = func.id
                        else:
                            continue

                        if func_name in insecure_functions:
                            insecure_uses.append({
                                'function': func_name,
                                'line': node.lineno,
                                'file': file_path.replace(repo_dir, '')
                            })

    return {'insecure_crypto_uses': insecure_uses}


